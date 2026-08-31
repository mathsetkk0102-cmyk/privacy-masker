from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DetectionItem:
    id: str
    file_path: str
    file_type: str
    page_or_sheet: str
    location: str
    pii_type: str
    original_text: str
    masked_text: str
    confidence: str
    review_status: str
    selected: bool
    note: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def file_name(self) -> str:
        return Path(self.file_path).name


@dataclass
class WorkflowState:
    input_files: list[Path] = field(default_factory=list)
    output_folder: Path | None = None
    detections: list[DetectionItem] = field(default_factory=list)
    processing_errors: list[str] = field(default_factory=list)


@dataclass
class ProcessingResult:
    original_file_path: str
    output_file_path: str
    file_type: str
    detected_count: int
    selected_count: int
    need_review_count: int
    success: bool
    error_message: str = ""
    log_written: bool = False

    @property
    def original_file_name(self) -> str:
        return Path(self.original_file_path).name

    @property
    def output_file_name(self) -> str:
        return Path(self.output_file_path).name if self.output_file_path else ""


@dataclass
class BatchProcessingResult:
    results: list[ProcessingResult] = field(default_factory=list)
    log_file_path: str = ""
    output_dir: str = ""
    log_error_message: str = ""

    @property
    def success_count(self) -> int:
        return sum(1 for result in self.results if result.success)

    @property
    def fail_count(self) -> int:
        return sum(1 for result in self.results if not result.success)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def success(self) -> bool:
        return self.fail_count == 0 and not self.log_error_message
