from pathlib import Path

from core.file_utils import make_masked_output_path
from core.logger import CsvAuditLogger
from core.models import BatchProcessingResult, DetectionItem, ProcessingResult
from processors.base_processor import BaseProcessor
from processors.docx_processor import DocxProcessor
from processors.hwp_processor_stub import HwpProcessorStub
from processors.hwpx_processor import HwpxProcessor
from processors.pdf_processor import PdfProcessor
from processors.scanned_pdf_processor import ScannedPdfProcessor
from processors.xlsx_processor import XlsxProcessor


class ExportService:
    def __init__(self, processors: list[BaseProcessor] | None = None) -> None:
        self.pdf_processor = PdfProcessor()
        self.scanned_pdf_processor = ScannedPdfProcessor()
        self.processors = processors or [self.pdf_processor, XlsxProcessor(), DocxProcessor(), HwpxProcessor(), HwpProcessorStub()]

    def detect_file(self, file_path: str | Path) -> list[DetectionItem]:
        processor = self.get_processor(file_path)
        return processor.detect(file_path)

    def export_files(
        self,
        input_files: list[Path],
        output_dir: str | Path,
        items: list[DetectionItem],
    ) -> BatchProcessingResult:
        output_path = Path(output_dir)
        grouped_items = self.group_items_by_file(items)
        results: list[ProcessingResult] = []

        for input_path in input_files:
            file_items = grouped_items.get(input_path, [])
            selected_items = [item for item in file_items if item.selected]
            try:
                expected_output = make_masked_output_path(input_path, output_path)
                processor = self.get_processor(input_path)
                if isinstance(processor, HwpProcessorStub):
                    processor.apply_masking(input_path, output_path, file_items)
                if not selected_items:
                    raise ValueError("선택된 마스킹 항목이 없습니다. 검토 화면에서 항목을 선택하세요.")
                actual_output = Path(processor.apply_masking(input_path, output_path, file_items))
                results.append(self._result_for_file(input_path, actual_output, file_items, True, ""))
            except Exception as exc:
                expected_output = output_path / f"masked_{input_path.name}"
                results.append(self._result_for_file(input_path, expected_output, file_items, False, str(exc)))

        batch_result = BatchProcessingResult(results=results, output_dir=str(output_path))
        self._write_log_safely(batch_result, output_path)
        return batch_result

    def get_processor(self, file_path: str | Path) -> BaseProcessor:
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            pdf_type = self.pdf_processor.classify_pdf(path)
            if pdf_type == "text_pdf":
                return self.pdf_processor
            if pdf_type == "scanned_pdf":
                return self.scanned_pdf_processor
            raise ValueError("PDF 파일을 여는 중 오류가 발생했습니다. 파일이 손상되었거나 암호로 보호되어 있는지 확인하세요.")
        for processor in self.processors:
            if processor.supports(path):
                return processor
        suffix = path.suffix.lower()
        if suffix == ".hwp":
            raise ValueError("HWP 파일은 현재 안정 지원 대상이 아닙니다. HWPX로 변환 후 처리하세요.")
        if suffix == ".hwpx":
            raise ValueError("HWPX 파일을 여는 중 오류가 발생했습니다. 파일이 손상되었는지 확인하세요.")
        raise ValueError("지원하지 않는 파일입니다. 현재 단계에서는 PDF, XLSX, DOCX, HWPX만 처리할 수 있습니다.")

    @staticmethod
    def group_items_by_file(items: list[DetectionItem]) -> dict[Path, list[DetectionItem]]:
        grouped: dict[Path, list[DetectionItem]] = {}
        for item in items:
            grouped.setdefault(Path(item.file_path), []).append(item)
        return grouped

    @staticmethod
    def _result_for_file(
        input_path: Path,
        output_path: Path,
        file_items: list[DetectionItem],
        success: bool,
        error_message: str,
    ) -> ProcessingResult:
        return ProcessingResult(
            original_file_path=str(input_path),
            output_file_path=str(output_path),
            file_type=input_path.suffix.upper().lstrip(".") or "UNKNOWN",
            detected_count=len(file_items),
            selected_count=sum(1 for item in file_items if item.selected),
            need_review_count=sum(1 for item in file_items if item.review_status == "확인 필요"),
            success=success,
            error_message=error_message,
        )

    @staticmethod
    def _write_log_safely(batch_result: BatchProcessingResult, output_dir: Path) -> None:
        try:
            log_path = CsvAuditLogger(output_dir).write_batch_log(batch_result)
            batch_result.log_file_path = str(log_path)
            for result in batch_result.results:
                result.log_written = True
        except Exception as exc:
            batch_result.log_error_message = f"로그 파일 저장에 실패했습니다. 저장 폴더 권한을 확인하세요. ({exc})"
            for result in batch_result.results:
                result.log_written = False


def preview_output_name(input_path: Path, output_folder: Path) -> Path:
    return make_masked_output_path(input_path, output_folder)
