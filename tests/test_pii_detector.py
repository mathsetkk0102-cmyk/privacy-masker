from pathlib import Path

from core.pii_detector import PiiDetector, SAMPLE_TEXT, build_sample_detection_items


def test_sample_text_detects_required_types() -> None:
    items = PiiDetector().detect_text(
        SAMPLE_TEXT,
        {"file_path": "sample.pdf", "file_type": "PDF", "page_or_sheet": "샘플", "location": "샘플"},
    )
    types = {item.pii_type for item in items}
    assert "전화번호" in types
    assert "이메일" in types
    assert "주민등록번호" in types
    assert "생년월일" in types
    assert "주소" in types
    assert "계좌번호" in types
    assert "학교명" in types


def test_clear_patterns_are_auto_selected() -> None:
    items = PiiDetector().detect_text(SAMPLE_TEXT, {"file_path": "sample.pdf"})
    by_type = {item.pii_type: item for item in items}
    assert by_type["전화번호"].selected is True
    assert by_type["전화번호"].review_status == "자동선택"
    assert by_type["이메일"].selected is True
    assert by_type["이메일"].review_status == "자동선택"


def test_ambiguous_patterns_need_review() -> None:
    items = PiiDetector().detect_text(SAMPLE_TEXT, {"file_path": "sample.pdf"})
    by_type = {item.pii_type: item for item in items}
    assert by_type["이름"].selected is False
    assert by_type["이름"].review_status == "확인 필요"
    assert by_type["주소"].review_status == "확인 필요"
    assert by_type["계좌번호"].review_status == "확인 필요"
    assert by_type["학교명"].review_status == "확인 필요"


def test_detection_items_include_masked_text() -> None:
    items = PiiDetector().detect_text(SAMPLE_TEXT, {"file_path": "sample.pdf"})
    assert all(item.masked_text for item in items)
    assert any(item.masked_text == "010-****-5678" for item in items)


def test_duplicate_detection_is_limited() -> None:
    items = PiiDetector().detect_text(SAMPLE_TEXT, {"file_path": "sample.pdf"})
    originals = [item.original_text for item in items]
    assert len(originals) == len(set(originals))
    assert len(items) <= 8


def test_build_sample_detection_items_uses_each_selected_file() -> None:
    items = build_sample_detection_items([Path("a.pdf"), Path("b.docx")])
    file_names = {Path(item.file_path).name for item in items}
    assert file_names == {"a.pdf", "b.docx"}


def test_email_before_korean_sentence_suffix_is_detected_without_suffix() -> None:
    items = PiiDetector().detect_text("이메일은 teacher@school.kr입니다.", {"file_path": "sample.pdf"})
    email = next(item for item in items if item.pii_type == "이메일")

    assert email.original_text == "teacher@school.kr"
    assert email.selected is True
    assert email.review_status == "자동선택"
    assert email.confidence == "높음"


def test_name_before_role_particle_and_school_are_detected_separately() -> None:
    items = PiiDetector().detect_text(
        "홍길동 학생은 니코초등학교에 재학 중입니다.",
        {"file_path": "sample.pdf"},
    )

    name = next(item for item in items if item.pii_type == "이름")
    school = next(item for item in items if item.pii_type == "학교명")

    assert name.original_text == "홍길동"
    assert name.selected is False
    assert name.review_status == "확인 필요"
    assert school.original_text == "니코초등학교"
    assert school.review_status == "확인 필요"


def test_email_match_does_not_include_korean_suffix() -> None:
    items = PiiDetector().detect_text("teacher@school.kr입니다.", {"file_path": "sample.pdf"})
    originals = [item.original_text for item in items]

    assert "teacher@school.kr" in originals
    assert all("입니다" not in original for original in originals)


def test_homeroom_teacher_label_detects_teacher_name() -> None:
    items = PiiDetector().detect_text("담임교사: 홍길동", {"file_path": "sample.pdf"})
    name = next(item for item in items if item.pii_type == "이름")

    assert name.original_text == "홍길동"
    assert name.review_status == "확인 필요"
    assert name.selected is False


def test_compound_teacher_word_does_not_detect_prefix_as_name() -> None:
    items = PiiDetector().detect_text("지도교사와 협의해 일정을 조정했습니다.", {"file_path": "sample.pdf"})
    originals = [item.original_text for item in items]

    assert "지도" not in originals


def test_resident_number_with_foreigner_or_sample_tail_is_detected() -> None:
    items = PiiDetector().detect_text("주민등록번호: 821010-5678901", {"file_path": "sample.pdf"})
    resident_number = next(item for item in items if item.pii_type == "주민등록번호")

    assert resident_number.original_text == "821010-5678901"
    assert resident_number.masked_text == "******-*******"
    assert resident_number.selected is True
    assert resident_number.review_status == "자동선택"
