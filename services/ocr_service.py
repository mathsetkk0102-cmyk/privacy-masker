from dataclasses import dataclass
import shutil
from typing import Any

from PIL import Image


@dataclass
class OcrWord:
    text: str
    left: int
    top: int
    width: int
    height: int
    confidence: float

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.left + self.width, self.top + self.height)


class OCRService:
    def is_tesseract_available(self) -> bool:
        return shutil.which("tesseract") is not None

    def status_message(self) -> str:
        if self.is_tesseract_available():
            return "OCR 상태: Tesseract가 감지되었습니다. 스캔 PDF는 OCR 결과 검토가 필요합니다."
        return "스캔 PDF를 처리하려면 Tesseract OCR 설치가 필요합니다."

    def extract_words(self, image: Image.Image) -> list[OcrWord]:
        if not self.is_tesseract_available():
            raise RuntimeError("스캔 PDF를 처리하려면 Tesseract OCR 설치가 필요합니다.")

        pytesseract = self._load_pytesseract()
        last_error: Exception | None = None
        for lang in ("kor+eng", "eng", None):
            try:
                kwargs: dict[str, Any] = {"output_type": pytesseract.Output.DICT}
                if lang:
                    kwargs["lang"] = lang
                data = pytesseract.image_to_data(image, **kwargs)
                return self._words_from_data(data)
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"OCR 처리 중 오류가 발생했습니다. 파일을 확인하거나 텍스트 PDF인지 확인하세요. ({last_error})")

    @staticmethod
    def _load_pytesseract():
        try:
            import pytesseract
        except ImportError as exc:
            raise RuntimeError("pytesseract 패키지가 설치되어 있지 않습니다.") from exc
        return pytesseract

    @staticmethod
    def _words_from_data(data: dict) -> list[OcrWord]:
        words: list[OcrWord] = []
        for index, raw_text in enumerate(data.get("text", [])):
            text = str(raw_text).strip()
            if not text:
                continue
            try:
                confidence = float(data.get("conf", [])[index])
            except (TypeError, ValueError):
                confidence = -1
            if confidence < 0:
                continue
            words.append(
                OcrWord(
                    text=text,
                    left=int(data["left"][index]),
                    top=int(data["top"][index]),
                    width=int(data["width"][index]),
                    height=int(data["height"][index]),
                    confidence=confidence,
                )
            )
        return words


def is_tesseract_available() -> bool:
    return OCRService().is_tesseract_available()


def describe_ocr_status() -> str:
    return OCRService().status_message()
