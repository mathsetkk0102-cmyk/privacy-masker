import re
import uuid
from collections.abc import Iterable
from pathlib import Path

from core.masking_rules import (
    default_confidence,
    default_review_status,
    default_selected,
    mask_value,
)
from core.models import DetectionItem


SAMPLE_TEXT = """홍길동 학생은 니코초등학교에 재학 중입니다.
연락처는 010-1234-5678이고 이메일은 teacher@school.kr입니다.
주민등록번호는 900101-1234567입니다.
생년월일은 1990.01.01입니다.
주소는 서울특별시 강남구 역삼동입니다.
계좌번호는 123-456-789012입니다."""


class PiiDetector:
    def detect_text(self, text: str, source: dict) -> list[DetectionItem]:
        occupied_ranges: list[tuple[int, int]] = []
        items: list[DetectionItem] = []

        detectors = (
            self.detect_resident_numbers,
            self.detect_phone_numbers,
            self.detect_emails,
            self.detect_birth_dates,
            self.detect_school_names,
            self.detect_addresses,
            self.detect_account_numbers,
            self.detect_names,
        )

        for detector in detectors:
            for pii_type, value, start, end, note in detector(text):
                if self._overlaps_existing(start, end, occupied_ranges):
                    continue
                occupied_ranges.append((start, end))
                items.append(self._make_item(pii_type, value, source, start, end, note))

        return items

    def detect_phone_numbers(self, text: str) -> Iterable[tuple[str, str, int, int, str]]:
        pattern = re.compile(r"(?<!\d)(?:01[016789]|0[2-6][1-5]?)[- ]?\d{3,4}[- ]?\d{4}(?!\d)")
        yield from self._yield_matches("전화번호", pattern, text, "정규식 기반 전화번호 후보")

    def detect_emails(self, text: str) -> Iterable[tuple[str, str, int, int, str]]:
        pattern = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?![A-Za-z0-9_%+-])")
        yield from self._yield_matches("이메일", pattern, text, "정규식 기반 이메일 후보")

    def detect_resident_numbers(self, text: str) -> Iterable[tuple[str, str, int, int, str]]:
        pattern = re.compile(r"(?<!\d)\d{6}-?[1-8]\d{6}(?!\d)")
        yield from self._yield_matches("주민등록번호", pattern, text, "정규식 기반 주민등록번호 후보")

    def detect_birth_dates(self, text: str) -> Iterable[tuple[str, str, int, int, str]]:
        separated = re.compile(r"(?<!\d)(?:19|20)\d{2}[.\-/](?:0?[1-9]|1[0-2])[.\-/](?:0?[1-9]|[12]\d|3[01])(?!\d)")
        compact = re.compile(r"(?<!\d)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?!\d)")
        yield from self._yield_matches("생년월일", separated, text, "날짜 구분자 기반 생년월일 후보")
        yield from self._yield_matches("생년월일", compact, text, "6자리 생년월일 후보")

    def detect_account_numbers(self, text: str) -> Iterable[tuple[str, str, int, int, str]]:
        hyphenated = re.compile(r"(?<!\d)\d{2,6}(?:-\d{2,6}){2,4}(?!\d)")
        compact = re.compile(r"(?<!\d)\d{10,14}(?!\d)")
        yield from self._yield_matches("계좌번호", hyphenated, text, "숫자/하이픈 기반 계좌번호 후보")
        yield from self._yield_matches("계좌번호", compact, text, "긴 숫자열 기반 계좌번호 후보")

    def detect_addresses(self, text: str) -> Iterable[tuple[str, str, int, int, str]]:
        sido = r"(?:서울특별시|부산광역시|대구광역시|인천광역시|광주광역시|대전광역시|울산광역시|세종특별자치시|경기도|강원도|충청북도|충청남도|전라북도|전라남도|경상북도|경상남도|제주특별자치도|서울시|부산시|대구시|인천시|광주시|대전시|울산시)"
        district = r"[가-힣]{1,12}(?:시|군|구)"
        town = r"[가-힣0-9]{1,12}(?:읍|면|동|로|길)"
        pattern = re.compile(rf"{sido}\s+{district}\s+{town}")
        yield from self._yield_matches("주소", pattern, text, "주소 키워드 기반 후보")

    def detect_school_names(self, text: str) -> Iterable[tuple[str, str, int, int, str]]:
        pattern = re.compile(r"[가-힣A-Za-z0-9]{2,30}(?:초등학교|중학교|고등학교|대학교)")
        yield from self._yield_matches("학교명", pattern, text, "학교명 키워드 기반 후보")

    def detect_names(self, text: str) -> Iterable[tuple[str, str, int, int, str]]:
        patterns = (
            re.compile(r"(?:성명|이름|담당자|담임교사|담임|교사명|교사)\s*[:：]?\s*([가-힣]{2,4})(?![가-힣])"),
            re.compile(r"(?<![가-힣])([가-힣]{2,4})\s+(?:학생|교사|담당자|님)(?:은|는|이|가|을|를|의|과|와)?(?![가-힣])"),
        )
        for pattern in patterns:
            for match in pattern.finditer(text):
                value = match.group(1)
                start, end = match.span(1)
                yield ("이름", value, start, end, "문맥 기반 이름 후보")

        stripped = text.strip()
        common_surnames = "김이박최정강조윤장임한오서신권황안송전홍유고문양손배백허남노심하곽성차주우구민류진"
        if re.fullmatch(rf"[{common_surnames}][가-힣]{{1,3}}", stripped):
            start = text.index(stripped)
            end = start + len(stripped)
            yield ("이름", stripped, start, end, "단독 텍스트 기반 이름 후보")

    def _make_item(self, pii_type: str, value: str, source: dict, start: int, end: int, note: str) -> DetectionItem:
        review_status = default_review_status(pii_type)
        return DetectionItem(
            id=str(uuid.uuid4()),
            file_path=str(source.get("file_path", "샘플_문서.pdf")),
            file_type=str(source.get("file_type", "PDF")),
            page_or_sheet=str(source.get("page_or_sheet", "샘플 텍스트")),
            location=str(source.get("location", f"문자 {start}-{end}")),
            pii_type=pii_type,
            original_text=value,
            masked_text=mask_value(pii_type, value),
            confidence=default_confidence(pii_type),
            review_status=review_status,
            selected=default_selected(pii_type),
            note=note,
        )

    @staticmethod
    def _yield_matches(
        pii_type: str,
        pattern: re.Pattern,
        text: str,
        note: str,
    ) -> Iterable[tuple[str, str, int, int, str]]:
        for match in pattern.finditer(text):
            yield (pii_type, match.group(0), match.start(), match.end(), note)

    @staticmethod
    def _overlaps_existing(start: int, end: int, ranges: list[tuple[int, int]]) -> bool:
        return any(start < existing_end and end > existing_start for existing_start, existing_end in ranges)


def build_sample_detection_items(input_files: list[Path]) -> list[DetectionItem]:
    detector = PiiDetector()
    targets = input_files or [Path("샘플_문서.pdf")]
    items: list[DetectionItem] = []
    for input_file in targets:
        # 문서 처리 모듈 연결 전 샘플 탐지
        items.extend(
            detector.detect_text(
                SAMPLE_TEXT,
                {
                    "file_path": str(input_file),
                    "file_type": input_file.suffix.upper().lstrip(".") or "PDF",
                    "page_or_sheet": "샘플 텍스트",
                    "location": "샘플 텍스트",
                },
            )
        )
    return items
