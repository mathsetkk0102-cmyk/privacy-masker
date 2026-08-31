import pytest

from services.ocr_service import OCRService, describe_ocr_status, is_tesseract_available


def test_tesseract_status_check_does_not_raise() -> None:
    available = is_tesseract_available()
    assert isinstance(available, bool)
    assert describe_ocr_status()


def test_missing_tesseract_returns_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    service = OCRService()
    monkeypatch.setattr(service, "is_tesseract_available", lambda: False)

    with pytest.raises(RuntimeError, match="Tesseract OCR 설치"):
        service.extract_words(None)  # type: ignore[arg-type]
