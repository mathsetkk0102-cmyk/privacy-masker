from pathlib import Path

from PySide6.QtWidgets import QStackedWidget

from app.screens.detection_progress_screen import DetectionProgressScreen
from app.screens.file_select_screen import FileSelectScreen
from app.screens.output_folder_screen import OutputFolderScreen
from app.screens.result_screen import ResultScreen
from app.screens.review_table_screen import ReviewTableScreen
from app.screens.save_confirm_screen import SaveConfirmScreen
from core.models import BatchProcessingResult, DetectionItem, ProcessingResult, WorkflowState
from core.pii_detector import build_sample_detection_items
from services.export_service import ExportService
from services.validation_service import validate_save_request


class WizardController(QStackedWidget):
    def __init__(self) -> None:
        super().__init__()
        self.state = WorkflowState()

        self.file_screen = FileSelectScreen()
        self.output_screen = OutputFolderScreen()
        self.progress_screen = DetectionProgressScreen()
        self.review_screen = ReviewTableScreen()
        self.save_screen = SaveConfirmScreen()
        self.result_screen = ResultScreen()
        self.export_service = ExportService()

        for screen in (
            self.file_screen,
            self.output_screen,
            self.progress_screen,
            self.review_screen,
            self.save_screen,
            self.result_screen,
        ):
            self.addWidget(screen)

        self.file_screen.next_requested.connect(self.go_to_output_folder)
        self.output_screen.back_requested.connect(lambda: self.setCurrentWidget(self.file_screen))
        self.output_screen.next_requested.connect(self.go_to_detection)
        self.progress_screen.back_requested.connect(lambda: self.setCurrentWidget(self.output_screen))
        self.progress_screen.detection_finished.connect(self.go_to_review)
        self.review_screen.back_requested.connect(lambda: self.setCurrentWidget(self.progress_screen))
        self.review_screen.next_requested.connect(self.go_to_save_confirm)
        self.save_screen.back_requested.connect(lambda: self.setCurrentWidget(self.review_screen))
        self.save_screen.save_requested.connect(self.save_results)
        self.result_screen.restart_requested.connect(self.restart)

    def go_to_output_folder(self, files: list[str]) -> None:
        self.state.input_files = [Path(file) for file in files]
        self.output_screen.set_file_count(len(self.state.input_files))
        self.setCurrentWidget(self.output_screen)

    def go_to_detection(self, output_folder: str) -> None:
        self.state.output_folder = Path(output_folder)
        self.progress_screen.start_demo_detection(self.state.input_files)
        self.setCurrentWidget(self.progress_screen)

    def go_to_review(self) -> None:
        self.state.detections = []
        self.state.processing_errors = []

        if not self.state.input_files:
            self.state.detections = build_sample_detection_items([])
        else:
            for input_file in self.state.input_files:
                try:
                    self.state.detections.extend(self.export_service.detect_file(input_file))
                except Exception as exc:
                    self.state.processing_errors.append(f"{input_file.name}: {exc}")

        self.review_screen.load_items(self.state.detections)
        self.setCurrentWidget(self.review_screen)

    def go_to_save_confirm(self, items: list[DetectionItem]) -> None:
        self.state.detections = items
        self.save_screen.load_summary(self.state)
        self.setCurrentWidget(self.save_screen)

    def save_results(self) -> None:
        self.save_screen.set_saving(True)
        try:
            validation_errors = validate_save_request(self.state.input_files, self.state.output_folder, self.state.detections)
            if validation_errors:
                batch_result = build_validation_failure_result(
                    self.state.input_files,
                    self.state.output_folder,
                    self.state.detections,
                    validation_errors,
                )
            else:
                batch_result = self.export_service.export_files(
                    self.state.input_files,
                    self.state.output_folder,
                    self.state.detections,
                )
                if self.state.processing_errors:
                    batch_result.log_error_message = "\n".join(
                        [batch_result.log_error_message, "분석 실패 항목:", *self.state.processing_errors]
                    ).strip()
            self.result_screen.load_result(batch_result)
            self.setCurrentWidget(self.result_screen)
        finally:
            self.save_screen.set_saving(False)

    def restart(self) -> None:
        self.state = WorkflowState()
        self.file_screen.reset()
        self.output_screen.reset()
        self.review_screen.clear()
        self.setCurrentWidget(self.file_screen)


def build_validation_failure_result(
    input_files: list[Path],
    output_folder: str | Path | None,
    detections: list[DetectionItem],
    validation_errors: list[str],
) -> BatchProcessingResult:
    error_message = "\n".join(validation_errors)
    output_dir = str(output_folder) if output_folder else ""
    results: list[ProcessingResult] = []

    if input_files:
        for input_file in input_files:
            file_items = [item for item in detections if Path(item.file_path) == input_file]
            results.append(
                ProcessingResult(
                    original_file_path=str(input_file),
                    output_file_path="",
                    file_type=input_file.suffix.upper().lstrip(".") or "UNKNOWN",
                    detected_count=len(file_items),
                    selected_count=sum(1 for item in file_items if item.selected),
                    need_review_count=sum(1 for item in file_items if item.review_status == "확인 필요"),
                    success=False,
                    error_message=error_message,
                    log_written=False,
                )
            )
    else:
        results.append(
            ProcessingResult(
                original_file_path="저장 요청",
                output_file_path="",
                file_type="UNKNOWN",
                detected_count=len(detections),
                selected_count=sum(1 for item in detections if item.selected),
                need_review_count=sum(1 for item in detections if item.review_status == "확인 필요"),
                success=False,
                error_message=error_message,
                log_written=False,
            )
        )

    return BatchProcessingResult(
        results=results,
        output_dir=output_dir,
        log_error_message=error_message,
    )
