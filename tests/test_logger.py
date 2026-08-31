import csv
from pathlib import Path
import pytest

from core.logger import LOG_COLUMNS, CsvAuditLogger
from core.models import BatchProcessingResult, DetectionItem, ProcessingResult


def make_item() -> DetectionItem:
    return DetectionItem(
        id="1",
        file_path="secret.pdf",
        file_type="PDF",
        page_or_sheet="1",
        location="PDF 1쪽",
        pii_type="전화번호",
        original_text="010-1234-5678",
        masked_text="010-****-5678",
        confidence="높음",
        review_status="자동선택",
        selected=True,
    )


def test_logger_creates_csv_with_expected_columns(tmp_path: Path) -> None:
    log_path = CsvAuditLogger(tmp_path).write_run_log([Path("secret.pdf")], [make_item()])
    assert log_path.exists()

    with log_path.open(encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == LOG_COLUMNS
        row = next(reader)

    assert row["detected_count"] == "1"
    assert row["selected_count"] == "1"


def test_logger_does_not_write_original_or_masked_text(tmp_path: Path) -> None:
    log_path = CsvAuditLogger(tmp_path).write_run_log([Path("secret.pdf")], [make_item()])
    text = log_path.read_text(encoding="utf-8-sig")
    assert "original_text" not in text
    assert "masked_text" not in text
    assert "010-1234-5678" not in text
    assert "010-****-5678" not in text


def test_logger_writes_utf8_sig(tmp_path: Path) -> None:
    log_path = CsvAuditLogger(tmp_path).write_run_log([Path("secret.pdf")], [make_item()])
    assert log_path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_logger_uses_only_allowed_columns(tmp_path: Path) -> None:
    result = ProcessingResult(
        original_file_path="secret.pdf",
        output_file_path=str(tmp_path / "masked_secret.pdf"),
        file_type="PDF",
        detected_count=1,
        selected_count=1,
        need_review_count=0,
        success=True,
    )
    log_path = CsvAuditLogger(tmp_path).write_batch_log(BatchProcessingResult(results=[result], output_dir=str(tmp_path)))
    with log_path.open(encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == LOG_COLUMNS
        row = next(reader)
    assert "original_text" not in row
    assert "masked_text" not in row


def test_logger_failure_can_be_captured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    logger = CsvAuditLogger(tmp_path)

    def fail_write(_batch: BatchProcessingResult) -> Path:
        raise OSError("cannot write")

    monkeypatch.setattr(logger, "write_batch_log", fail_write)
    with pytest.raises(OSError, match="cannot write"):
        logger.write_batch_log(BatchProcessingResult())
