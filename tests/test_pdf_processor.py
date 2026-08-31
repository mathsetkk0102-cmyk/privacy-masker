from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

from processors.pdf_processor import PdfProcessor
from services.ocr_service import OcrWord


class FakeOCRService:
    def is_tesseract_available(self) -> bool:
        return True

    def extract_words(self, _image) -> list[OcrWord]:
        return [
            OcrWord("담임교사", 40, 40, 80, 20, 92),
            OcrWord("홍길동", 130, 40, 60, 20, 91),
        ]


def create_text_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "홍길동")
    page.insert_text((72, 100), "010-1234-5678")
    page.insert_text((72, 128), "teacher@school.kr")
    page.insert_text((72, 156), "900101-1234567")
    document.save(str(path))
    document.close()


def pdf_text(path: Path) -> str:
    with fitz.open(path) as document:
        return "\n".join(page.get_text("text") for page in document)


def test_pdf_detects_text_pdf_pii(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.pdf"
    create_text_pdf(input_path)

    processor = PdfProcessor()
    items = processor.detect(input_path)
    types = {item.pii_type for item in items}

    assert processor.classify_pdf(input_path) == "text_pdf"
    assert "전화번호" in types
    assert "이메일" in types
    assert "주민등록번호" in types
    assert any(item.page_or_sheet == "page 1" for item in items)

    by_type = {item.pii_type: item for item in items}
    assert by_type["전화번호"].review_status == "자동선택"
    assert by_type["이메일"].review_status == "자동선택"


def test_pdf_redacts_only_selected_items_and_keeps_original(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.pdf"
    output_dir = tmp_path / "out"
    create_text_pdf(input_path)

    processor = PdfProcessor()
    items = processor.detect(input_path)
    for item in items:
        item.selected = item.pii_type == "전화번호"

    output_path = Path(processor.apply_masking(input_path, output_dir, items))

    assert output_path.exists()
    assert output_path.name == "masked_sample.pdf"
    assert "010-1234-5678" in pdf_text(input_path)
    assert "010-1234-5678" not in pdf_text(output_path)
    assert "teacher@school.kr" in pdf_text(output_path)


def test_pdf_ocr_assist_detects_image_like_teacher_name(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.pdf"
    create_text_pdf(input_path)

    processor = PdfProcessor(ocr_service=FakeOCRService())
    items = processor.detect(input_path)

    name = next(item for item in items if item.pii_type == "이름" and item.original_text == "홍길동")

    assert name.location.startswith("OCR page 1 bbox")
    assert name.review_status == "확인 필요"
    assert name.selected is False
    assert name.metadata["source"] == "ocr_assist"


def test_pdf_ocr_assist_selected_item_can_be_applied(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.pdf"
    output_dir = tmp_path / "out"
    create_text_pdf(input_path)

    processor = PdfProcessor(ocr_service=FakeOCRService())
    items = processor.detect(input_path)
    selected_name = next(item for item in items if item.pii_type == "이름" and item.location.startswith("OCR page"))
    selected_name.selected = True

    output_path = Path(processor.apply_masking(input_path, output_dir, items))

    assert output_path.exists()
    assert output_path.name == "masked_sample.pdf"
