from pathlib import Path
import re

import fitz
from PIL import Image, ImageDraw

from core.file_utils import make_masked_output_path
from core.masking_rules import REVIEW_NEEDS_REVIEW
from core.models import DetectionItem
from core.pii_detector import PiiDetector
from processors.base_processor import BaseProcessor
from services.ocr_service import OCRService, OcrWord


OCR_NOTE = "OCR 결과입니다. 누락 또는 오탐 가능성이 있습니다. 반드시 검토하세요."


class ScannedPdfProcessor(BaseProcessor):
    file_type = "scanned_pdf"
    supported_suffixes = {".pdf"}
    render_zoom = 2.0

    def __init__(self, detector: PiiDetector | None = None, ocr_service: OCRService | None = None) -> None:
        self.detector = detector or PiiDetector()
        self.ocr_service = ocr_service or OCRService()

    def detect(self, file_path: str | Path) -> list[DetectionItem]:
        if not self.ocr_service.is_tesseract_available():
            raise RuntimeError("스캔 PDF를 처리하려면 Tesseract OCR 설치가 필요합니다.")

        input_path = Path(file_path)
        detections: list[DetectionItem] = []
        with fitz.open(input_path) as document:
            for page_index, page in enumerate(document):
                image = self._render_page(page)
                words = self.ocr_service.extract_words(image)
                ocr_text = " ".join(word.text for word in words)
                source = {
                    "file_path": str(input_path),
                    "file_type": self.file_type,
                    "page_or_sheet": f"page {page_index + 1}",
                    "location": f"OCR page {page_index + 1}",
                }
                page_items = self.detector.detect_text(ocr_text, source)
                for item in page_items:
                    bbox, confidence = self._bbox_for_text(item.original_text, words)
                    item.location = self._format_location(page_index + 1, bbox)
                    item.confidence = "보통" if confidence >= 70 else "낮음"
                    item.review_status = REVIEW_NEEDS_REVIEW
                    item.selected = False
                    item.note = OCR_NOTE
                    detections.append(item)
        return detections

    def apply_masking(self, file_path: str | Path, output_dir: str | Path, items: list[DetectionItem]) -> str:
        input_path = Path(file_path)
        output_folder = Path(output_dir)
        output_path = make_masked_output_path(input_path, output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        selected = [item for item in items if item.selected and Path(item.file_path) == input_path]
        if not selected:
            raise ValueError("선택된 마스킹 항목이 없습니다. 검토 화면에서 항목을 선택하세요.")

        selected_by_page: dict[int, list[tuple[int, int, int, int]]] = {}
        for item in selected:
            parsed = self._parse_location(item.location)
            if parsed is None:
                continue
            page_number, bbox = parsed
            selected_by_page.setdefault(page_number, []).append(bbox)

        output_document = fitz.open()
        with fitz.open(input_path) as source_document:
            for page_index, page in enumerate(source_document):
                page_number = page_index + 1
                image = self._render_page(page)
                draw = ImageDraw.Draw(image)
                for bbox in selected_by_page.get(page_number, []):
                    draw.rectangle(bbox, fill="black")

                png_bytes = self._image_to_png_bytes(image)
                new_page = output_document.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(new_page.rect, stream=png_bytes)

        output_document.save(str(output_path), garbage=4, deflate=True)
        output_document.close()
        return str(output_path)

    def save_masked_copy(self, input_path: Path, output_path: Path, detections: list[DetectionItem]) -> None:
        result = self.apply_masking(input_path, output_path.parent, detections)
        Path(result).replace(output_path)

    def _render_page(self, page: fitz.Page) -> Image.Image:
        matrix = fitz.Matrix(self.render_zoom, self.render_zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

    @staticmethod
    def _image_to_png_bytes(image: Image.Image) -> bytes:
        from io import BytesIO

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _bbox_for_text(self, text: str, words: list[OcrWord]) -> tuple[tuple[int, int, int, int], float]:
        target = self._normalize(text)
        best: tuple[int, int, int, int] | None = None
        best_conf = 0.0
        for start in range(len(words)):
            combined = ""
            boxes: list[tuple[int, int, int, int]] = []
            confidences: list[float] = []
            for word in words[start:]:
                combined += self._normalize(word.text)
                boxes.append(word.bbox)
                confidences.append(word.confidence)
                if combined == target:
                    best = self._merge_boxes(boxes)
                    best_conf = sum(confidences) / len(confidences)
                    return best, best_conf
                if not target.startswith(combined):
                    break
        return best or (0, 0, 0, 0), best_conf

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", "", text)

    @staticmethod
    def _merge_boxes(boxes: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
        left = min(box[0] for box in boxes)
        top = min(box[1] for box in boxes)
        right = max(box[2] for box in boxes)
        bottom = max(box[3] for box in boxes)
        padding = 3
        return (max(0, left - padding), max(0, top - padding), right + padding, bottom + padding)

    @staticmethod
    def _format_location(page_number: int, bbox: tuple[int, int, int, int]) -> str:
        x1, y1, x2, y2 = bbox
        return f"OCR page {page_number} bbox {x1},{y1},{x2},{y2}"

    @staticmethod
    def _parse_location(location: str) -> tuple[int, tuple[int, int, int, int]] | None:
        match = re.search(r"OCR page (\d+) bbox (\d+),(\d+),(\d+),(\d+)", location)
        if not match:
            return None
        page_number = int(match.group(1))
        bbox = tuple(int(match.group(index)) for index in range(2, 6))
        return page_number, bbox
