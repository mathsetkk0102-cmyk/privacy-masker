import csv
from datetime import datetime
from pathlib import Path

from core.file_utils import ensure_unique_path
from core.models import BatchProcessingResult, DetectionItem, ProcessingResult
from services.security_audit_service import sanitize_log_row


LOG_COLUMNS = [
    "processed_at",
    "original_file_name",
    "original_file_path",
    "output_file_name",
    "output_file_path",
    "file_type",
    "detected_count",
    "selected_count",
    "need_review_count",
    "success",
    "error_message",
]


class CsvAuditLogger:
    def __init__(self, output_folder: Path) -> None:
        self.output_folder = output_folder

    def write_batch_log(self, batch_result: BatchProcessingResult) -> Path:
        self.output_folder.mkdir(parents=True, exist_ok=True)
        log_name = f"masking_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        log_path = ensure_unique_path(self.output_folder / log_name)
        processed_at = datetime.now().isoformat(timespec="seconds")

        rows = [self._row_from_result(processed_at, result) for result in batch_result.results]
        with log_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=LOG_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return log_path

    def write_run_log(
        self,
        input_files: list[Path],
        detections: list[DetectionItem],
        file_results: dict[Path, tuple[bool, Path | None, str]] | None = None,
    ) -> Path:
        results: list[ProcessingResult] = []
        for input_file in input_files or [Path("샘플_문서.pdf")]:
            success, output_file, error_message = self._result_for_file(input_file, file_results)
            file_items = [item for item in detections if Path(item.file_path) == input_file]
            results.append(
                ProcessingResult(
                    original_file_path=str(input_file),
                    output_file_path=str(output_file),
                    file_type=input_file.suffix.upper().lstrip(".") or "SAMPLE",
                    detected_count=len(file_items) if file_items else len(detections),
                    selected_count=sum(1 for item in file_items if item.selected) if file_items else sum(1 for item in detections if item.selected),
                    need_review_count=sum(1 for item in file_items if item.review_status == "확인 필요")
                    if file_items
                    else sum(1 for item in detections if item.review_status == "확인 필요"),
                    success=success,
                    error_message=error_message,
                )
            )
        return self.write_batch_log(BatchProcessingResult(results=results, output_dir=str(self.output_folder)))

    def _row_from_result(self, processed_at: str, result: ProcessingResult) -> dict:
        output_path = Path(result.output_file_path) if result.output_file_path else Path("")
        row = {
            "processed_at": processed_at,
            "original_file_name": Path(result.original_file_path).name,
            "original_file_path": str(Path(result.original_file_path).parent),
            "output_file_name": output_path.name,
            "output_file_path": str(output_path.parent) if result.output_file_path else "",
            "file_type": result.file_type,
            "detected_count": result.detected_count,
            "selected_count": result.selected_count,
            "need_review_count": result.need_review_count,
            "success": "true" if result.success else "false",
            "error_message": result.error_message,
        }
        return sanitize_log_row(row, LOG_COLUMNS)

    def _result_for_file(
        self,
        input_file: Path,
        file_results: dict[Path, tuple[bool, Path | None, str]] | None,
    ) -> tuple[bool, Path, str]:
        default_output = self.output_folder / f"masked_{input_file.name}"
        if not file_results:
            return True, default_output, ""
        success, output_path, error_message = file_results.get(input_file, (False, None, "처리 결과를 찾을 수 없습니다."))
        return success, output_path or default_output, error_message
