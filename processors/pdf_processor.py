from pathlib import Path
import re

import fitz
from PIL import Image

from core.file_utils import make_masked_output_path
from core.masking_rules import REVIEW_NEEDS_REVIEW
from core.models import DetectionItem
from core.pii_detector import PiiDetector
from processors.base_processor import BaseProcessor
from services.ocr_service import OCRService, OcrWord


OCR_ASSIST_NOTE = "OCR 보조 탐지 결과입니다. 이미지/특수 글자 영역일 수 있으므로 반드시 검토하세요."


class PdfProcessor(BaseProcessor):
    file_type = "pdf"
    supported_suffixes = {".pdf"}
    min_text_chars = 30
    render_zoom = 2.0

    def __init__(self, detector: PiiDetector | None = None, ocr_service: OCRService | None = None) -> None:
        self.detector = detector or PiiDetector()
        self.ocr_service = ocr_service or OCRService()

    def supports(self, file_path: str | Path) -> bool:
        path = Path(file_path)
        return path.suffix.lower() == ".pdf" and self.classify_pdf(path) == "text_pdf"

    def classify_pdf(self, file_path: str | Path) -> str:
        try:
            with fitz.open(file_path) as document:
                if document.is_encrypted:
                    return "unknown_pdf"
                page_lengths = [len(page.get_text("text").strip()) for page in document]
        except Exception:
            return "unknown_pdf"

        total_text = sum(page_lengths)
        if total_text >= self.min_text_chars:
            return "text_pdf"
        if total_text == 0:
            return "scanned_pdf"
        return "scanned_pdf"

    def detect(self, file_path: str | Path) -> list[DetectionItem]:
        input_path = Path(file_path)
        pdf_type = self.classify_pdf(input_path)
        if pdf_type != "text_pdf":
            raise ValueError("텍스트 PDF가 아닙니다. 스캔 PDF 처리 흐름을 사용하세요.")

        detections: list[DetectionItem] = []
        with fitz.open(input_path) as document:
            for page_index, page in enumerate(document):
                text = page.get_text("text")
                source = {
                    "file_path": str(input_path),
                    "file_type": self.file_type,
                    "page_or_sheet": f"page {page_index + 1}",
                    "location": f"page {page_index + 1}",
                }
                text_items = self.detector.detect_text(text, source)
                for item in text_items:
                    rect_count = len(page.search_for(item.original_text))
                    if rect_count:
                        item.note = f"텍스트 PDF redaction 대상입니다. 같은 페이지의 같은 원문 {rect_count}개 위치가 함께 마스킹될 수 있습니다."
                    else:
                        item.note = "텍스트 위치를 다시 찾지 못할 수 있습니다."
                    detections.append(item)
                detections.extend(self._detect_ocr_assist(input_path, page_index, page, text_items))
        return detections

    def apply_masking(self, file_path: str | Path, output_dir: str | Path, items: list[DetectionItem]) -> str:
        input_path = Path(file_path)
        output_folder = Path(output_dir)
        output_path = make_masked_output_path(input_path, output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        with fitz.open(input_path) as document:
            selected = [item for item in items if item.selected and Path(item.file_path) == input_path]
            if not selected:
                raise ValueError("선택된 마스킹 항목이 없습니다. 검토 화면에서 항목을 선택하세요.")

            for item in selected:
                page_index = self._page_index(item.page_or_sheet)
                if page_index is None or page_index >= len(document):
                    continue
                page = document[page_index]
                rects = self._rects_for_item(page, item)
                for rect in rects:
                    page.add_redact_annot(rect, text=item.masked_text, fill=(1, 1, 1), text_color=(0, 0, 0))

            for page in document:
                page.apply_redactions()

            document.save(str(output_path), garbage=4, deflate=True, clean=True)

        return str(output_path)

    def save_masked_copy(self, input_path: Path, output_path: Path, detections: list[DetectionItem]) -> None:
        with fitz.open(input_path) as document:
            selected = [item for item in detections if item.selected and Path(item.file_path) == input_path]
            for item in selected:
                page_index = self._page_index(item.page_or_sheet)
                if page_index is None or page_index >= len(document):
                    continue
                page = document[page_index]
                for rect in self._rects_for_item(page, item):
                    page.add_redact_annot(rect, text=item.masked_text, fill=(1, 1, 1), text_color=(0, 0, 0))
            for page in document:
                page.apply_redactions()
            document.save(str(output_path), garbage=4, deflate=True, clean=True)

    def selected_originals_remaining(self, output_path: str | Path, selected_items: list[DetectionItem]) -> list[str]:
        remaining: list[str] = []
        with fitz.open(output_path) as document:
            text = "\n".join(page.get_text("text") for page in document)
        for item in selected_items:
            if item.original_text in text and item.original_text not in remaining:
                remaining.append(item.original_text)
        return remaining

    @staticmethod
    def _page_index(page_or_sheet: str) -> int | None:
        match = re.search(r"page\s+(\d+)", page_or_sheet)
        if not match:
            return None
        return int(match.group(1)) - 1

    def _detect_ocr_assist(
        self,
        input_path: Path,
        page_index: int,
        page: fitz.Page,
        text_items: list[DetectionItem],
    ) -> list[DetectionItem]:
        if not self.ocr_service.is_tesseract_available():
            return []

        image = self._render_page(page)
        words = self.ocr_service.extract_words(image)
        if not words:
            return []

        ocr_text = " ".join(word.text for word in words)
        source = {
            "file_path": str(input_path),
            "file_type": self.file_type,
            "page_or_sheet": f"page {page_index + 1}",
            "location": f"OCR page {page_index + 1}",
        }
        existing = {(item.pii_type, item.original_text) for item in text_items}
        ocr_items: list[DetectionItem] = []
        for item in self.detector.detect_text(ocr_text, source):
            if (item.pii_type, item.original_text) in existing:
                continue
            bbox, confidence = self._bbox_for_text(item.original_text, words)
            if bbox == (0, 0, 0, 0):
                continue
            item.location = self._format_ocr_location(page_index + 1, bbox)
            item.confidence = "보통" if confidence >= 70 else "낮음"
            item.review_status = REVIEW_NEEDS_REVIEW
            item.selected = False
            item.note = OCR_ASSIST_NOTE
            item.metadata["source"] = "ocr_assist"
            item.metadata["bbox"] = list(bbox)
            item.metadata["render_zoom"] = self.render_zoom
            ocr_items.append(item)
        return ocr_items

    def _render_page(self, page: fitz.Page) -> Image.Image:
        matrix = fitz.Matrix(self.render_zoom, self.render_zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

    def _rects_for_item(self, page: fitz.Page, item: DetectionItem) -> list[fitz.Rect]:
        ocr_bbox = self._ocr_bbox(item)
        if ocr_bbox is not None:
            zoom = float(item.metadata.get("render_zoom") or self.render_zoom)
            x1, y1, x2, y2 = ocr_bbox
            return [fitz.Rect(x1 / zoom, y1 / zoom, x2 / zoom, y2 / zoom)]
        return list(page.search_for(item.original_text))

    @staticmethod
    def _ocr_bbox(item: DetectionItem) -> tuple[int, int, int, int] | None:
        bbox = item.metadata.get("bbox")
        if isinstance(bbox, list) and len(bbox) == 4:
            return tuple(int(value) for value in bbox)
        match = re.search(r"OCR page \d+ bbox (\d+),(\d+),(\d+),(\d+)", item.location)
        if match:
            return tuple(int(match.group(index)) for index in range(1, 5))
        return None

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
    def _format_ocr_location(page_number: int, bbox: tuple[int, int, int, int]) -> str:
        x1, y1, x2, y2 = bbox
        return f"OCR page {page_number} bbox {x1},{y1},{x2},{y2}"
