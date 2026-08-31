from pathlib import Path

from core.models import DetectionItem
from processors.base_processor import BaseProcessor


class HwpProcessorStub(BaseProcessor):
    file_type = "hwp"
    supported_suffixes = {".hwp"}

    def detect(self, input_path: str | Path) -> list[DetectionItem]:
        raise ValueError("HWP 파일은 현재 안정 지원 대상이 아닙니다. HWPX로 변환 후 처리하세요.")

    def apply_masking(self, file_path: str | Path, output_dir: str | Path, items: list[DetectionItem]) -> str:
        raise ValueError("HWP 파일은 현재 안정 지원 대상이 아닙니다. HWPX로 변환 후 처리하세요.")

    def save_masked_copy(self, input_path: Path, output_path: Path, detections: list[DetectionItem]) -> None:
        raise ValueError("HWP 파일은 현재 안정 지원 대상이 아닙니다. HWPX로 변환 후 처리하세요.")
