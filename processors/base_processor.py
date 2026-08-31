from abc import ABC, abstractmethod
from pathlib import Path

from core.models import DetectionItem


class BaseProcessor(ABC):
    file_type = "base"
    supported_suffixes: set[str] = set()

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.supported_suffixes

    @abstractmethod
    def detect(self, file_path: str | Path) -> list[DetectionItem]:
        raise NotImplementedError

    @abstractmethod
    def apply_masking(self, file_path: str | Path, output_dir: str | Path, items: list[DetectionItem]) -> str:
        raise NotImplementedError

    def save_masked_copy(self, input_path: Path, output_path: Path, detections: list[DetectionItem]) -> None:
        raise NotImplementedError
