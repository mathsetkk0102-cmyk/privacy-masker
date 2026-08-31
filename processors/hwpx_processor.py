from collections import defaultdict
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

from core.file_utils import make_masked_output_path
from core.models import DetectionItem
from core.pii_detector import PiiDetector
from processors.base_processor import BaseProcessor


class HwpxProcessor(BaseProcessor):
    file_type = "hwpx"
    supported_suffixes = {".hwpx"}

    def __init__(self, detector: PiiDetector | None = None) -> None:
        self.detector = detector or PiiDetector()
        self.parse_errors: list[str] = []

    def supports(self, file_path: str | Path) -> bool:
        path = Path(file_path)
        return path.suffix.lower() == ".hwpx" and zipfile.is_zipfile(path)

    def detect(self, file_path: str | Path) -> list[DetectionItem]:
        input_path = Path(file_path)
        if not self.supports(input_path):
            raise ValueError("HWPX 파일을 여는 중 오류가 발생했습니다. 파일이 손상되었는지 확인하세요.")

        self.parse_errors = []
        detections: list[DetectionItem] = []
        with zipfile.ZipFile(input_path, "r") as package:
            for xml_path in self._xml_paths(package):
                try:
                    root = ET.fromstring(package.read(xml_path))
                except ET.ParseError as exc:
                    self.parse_errors.append(f"{xml_path}: {exc}")
                    continue

                for node_index, element, text_kind, text in self._iter_text_nodes(root):
                    source = {
                        "file_path": str(input_path),
                        "file_type": self.file_type,
                        "page_or_sheet": "HWPX",
                        "location": f"{xml_path}::{text_kind}_node[{node_index}]",
                    }
                    for item in self.detector.detect_text(text, source):
                        item.note = "HWPX XML 텍스트에서 탐지됨"
                        item.metadata = {
                            "xml_path": xml_path,
                            "node_index": node_index,
                            "text_kind": text_kind,
                        }
                        detections.append(item)

        return detections

    def apply_masking(self, file_path: str | Path, output_dir: str | Path, items: list[DetectionItem]) -> str:
        input_path = Path(file_path)
        output_folder = Path(output_dir)
        output_path = make_masked_output_path(input_path, output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        selected_items = [
            item for item in items if item.selected and Path(item.file_path) == input_path and item.metadata.get("xml_path")
        ]
        if not selected_items:
            raise ValueError("선택된 마스킹 항목이 없습니다. 검토 화면에서 항목을 선택하세요.")

        grouped = self._group_by_xml_path(selected_items)
        with zipfile.ZipFile(input_path, "r") as source_zip, zipfile.ZipFile(output_path, "w") as target_zip:
            for info in source_zip.infolist():
                data = source_zip.read(info.filename)
                if info.filename in grouped:
                    data = self._masked_xml_bytes(data, grouped[info.filename], info.filename)
                target_zip.writestr(info, data)

        return str(output_path)

    def save_masked_copy(self, input_path: Path, output_path: Path, detections: list[DetectionItem]) -> None:
        result = self.apply_masking(input_path, output_path.parent, detections)
        Path(result).replace(output_path)

    def _masked_xml_bytes(self, data: bytes, items: list[DetectionItem], xml_path: str) -> bytes:
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            raise ValueError(f"HWPX 내부 XML을 읽는 중 일부 오류가 발생했습니다: {xml_path}: {exc}") from exc

        grouped_by_node = self._group_by_node(items)
        for node_index, element, text_kind, text in self._iter_text_nodes(root):
            node_items = grouped_by_node.get((node_index, text_kind), [])
            if not node_items:
                continue
            replaced = text
            for item in node_items:
                replaced = replaced.replace(item.original_text, item.masked_text, 1)
            if text_kind == "text":
                element.text = replaced
            else:
                element.tail = replaced

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _xml_paths(package: zipfile.ZipFile) -> list[str]:
        xml_files = [name for name in package.namelist() if name.lower().endswith(".xml")]

        def priority(name: str) -> tuple[int, str]:
            lower = name.lower()
            if lower.startswith(("contents/", "bodytext/")) or "section" in lower:
                return (0, name)
            return (1, name)

        return sorted(xml_files, key=priority)

    @staticmethod
    def _iter_text_nodes(root: ET.Element):
        node_index = 0
        for element in root.iter():
            if element.text and element.text.strip():
                yield node_index, element, "text", element.text
                node_index += 1
            if element.tail and element.tail.strip():
                yield node_index, element, "tail", element.tail
                node_index += 1

    @staticmethod
    def _group_by_xml_path(items: list[DetectionItem]) -> dict[str, list[DetectionItem]]:
        grouped: dict[str, list[DetectionItem]] = defaultdict(list)
        for item in items:
            grouped[str(item.metadata["xml_path"])].append(item)
        return grouped

    @staticmethod
    def _group_by_node(items: list[DetectionItem]) -> dict[tuple[int, str], list[DetectionItem]]:
        grouped: dict[tuple[int, str], list[DetectionItem]] = defaultdict(list)
        for item in items:
            grouped[(int(item.metadata["node_index"]), str(item.metadata["text_kind"]))].append(item)
        return grouped
