from pathlib import Path

import pytest

from core.models import DetectionItem
from processors.base_processor import BaseProcessor
from services.export_service import ExportService


class FakeProcessor(BaseProcessor):
    file_type = "fake"
    supported_suffixes = {".fake"}

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def detect(self, file_path: str | Path) -> list[DetectionItem]:
        return []

    def apply_masking(self, file_path: str | Path, output_dir: str | Path, items: list[DetectionItem]) -> str:
        if self.should_fail:
            raise RuntimeError("forced failure")
        output_path = Path(output_dir) / f"masked_{Path(file_path).name}"
        output_path.write_text("masked", encoding="utf-8")
        return str(output_path)


def make_item(path: Path, selected: bool = True) -> DetectionItem:
    return DetectionItem(
        id=str(path),
        file_path=str(path),
        file_type="fake",
        page_or_sheet="fake",
        location="fake",
        pii_type="전화번호",
        original_text="010-1234-5678",
        masked_text="010-****-5678",
        confidence="높음",
        review_status="자동선택",
        selected=selected,
    )


def test_group_items_by_file(tmp_path: Path) -> None:
    first = tmp_path / "a.fake"
    second = tmp_path / "b.fake"
    grouped = ExportService.group_items_by_file([make_item(first), make_item(second)])
    assert set(grouped.keys()) == {first, second}


def test_export_continues_when_one_processor_fails(tmp_path: Path) -> None:
    ok_file = tmp_path / "ok.fake"
    fail_file = tmp_path / "fail.fake"
    ok_file.write_text("ok", encoding="utf-8")
    fail_file.write_text("fail", encoding="utf-8")
    service = ExportService(processors=[FakeProcessor(should_fail=False)])

    # Make one item unselected so that file fails validation while the other succeeds.
    items = [make_item(ok_file, True), make_item(fail_file, False)]
    result = service.export_files([ok_file, fail_file], tmp_path, items)

    assert result.success_count == 1
    assert result.fail_count == 1
    assert result.log_file_path


def test_export_returns_processing_results(tmp_path: Path) -> None:
    input_file = tmp_path / "ok.fake"
    input_file.write_text("ok", encoding="utf-8")
    result = ExportService(processors=[FakeProcessor()]).export_files([input_file], tmp_path, [make_item(input_file)])

    assert len(result.results) == 1
    assert result.results[0].success is True
    assert result.results[0].selected_count == 1
    assert result.results[0].log_written is True


def test_export_does_not_put_plaintext_in_log(tmp_path: Path) -> None:
    input_file = tmp_path / "ok.fake"
    input_file.write_text("ok", encoding="utf-8")
    result = ExportService(processors=[FakeProcessor()]).export_files([input_file], tmp_path, [make_item(input_file)])

    log_text = Path(result.log_file_path).read_text(encoding="utf-8-sig")
    assert "010-1234-5678" not in log_text
    assert "010-****-5678" not in log_text


def test_export_keeps_file_success_when_log_write_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    input_file = tmp_path / "ok.fake"
    input_file.write_text("ok", encoding="utf-8")

    def fail_log(*_args, **_kwargs):
        raise OSError("log failed")

    monkeypatch.setattr("services.export_service.CsvAuditLogger.write_batch_log", fail_log)
    result = ExportService(processors=[FakeProcessor()]).export_files([input_file], tmp_path, [make_item(input_file)])

    assert result.success_count == 1
    assert result.results[0].success is True
    assert result.results[0].log_written is False
    assert "로그 파일 저장에 실패했습니다" in result.log_error_message
