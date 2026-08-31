import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from app.wizard_controller import WizardController, build_validation_failure_result
from core.models import DetectionItem
from services.validation_service import validate_save_request


def make_item(path: Path, selected: bool = True) -> DetectionItem:
    return DetectionItem(
        id="1",
        file_path=str(path),
        file_type=path.suffix.upper().lstrip("."),
        page_or_sheet="Sheet1",
        location="A1",
        pii_type="전화번호",
        original_text="010-1234-5678",
        masked_text="010-****-5678",
        confidence="높음",
        review_status="자동선택",
        selected=selected,
    )


class FailingExportService:
    def export_files(self, *_args, **_kwargs):
        raise AssertionError("export_files must not be called for validation errors")


def app_instance() -> QApplication:
    return QApplication.instance() or QApplication([])


def assert_validation_failure_result(input_files, output_dir, detections, expected_message: str) -> None:
    errors = validate_save_request(input_files, output_dir, detections)
    result = build_validation_failure_result(input_files, output_dir, detections, errors)

    assert errors
    assert any(expected_message in error for error in errors)
    assert result.success is False
    assert result.log_file_path == ""
    assert result.log_error_message
    assert expected_message in result.log_error_message
    assert result.fail_count >= 1
    assert all(item.success is False for item in result.results)
    assert all(item.log_written is False for item in result.results)


def test_validation_failure_result_for_missing_output_folder(tmp_path: Path) -> None:
    input_file = tmp_path / "sample.xlsx"
    input_file.write_text("sample", encoding="utf-8")

    assert_validation_failure_result([input_file], None, [make_item(input_file)], "저장 폴더를 선택하세요")


def test_validation_failure_result_for_invalid_output_folder(tmp_path: Path) -> None:
    input_file = tmp_path / "sample.xlsx"
    missing_output_dir = tmp_path / "missing-output"
    input_file.write_text("sample", encoding="utf-8")

    assert_validation_failure_result([input_file], missing_output_dir, [make_item(input_file)], "저장 폴더가 없습니다")
    assert not list(tmp_path.glob("masking_log_*.csv"))


def test_validation_failure_result_for_no_selected_items(tmp_path: Path) -> None:
    input_file = tmp_path / "sample.xlsx"
    input_file.write_text("sample", encoding="utf-8")

    assert_validation_failure_result([input_file], tmp_path, [make_item(input_file, selected=False)], "선택된 마스킹 항목이 없습니다")
    assert not list(tmp_path.glob("masking_log_*.csv"))


def test_validation_failure_result_for_unsupported_file(tmp_path: Path) -> None:
    input_file = tmp_path / "sample.txt"
    input_file.write_text("sample", encoding="utf-8")

    assert_validation_failure_result([input_file], tmp_path, [make_item(input_file)], "지원하지 않는 파일 형식입니다")


def test_validation_failure_result_for_hwp_file(tmp_path: Path) -> None:
    input_file = tmp_path / "sample.hwp"
    input_file.write_text("sample", encoding="utf-8")

    assert_validation_failure_result([input_file], tmp_path, [make_item(input_file)], "HWP 파일은 현재 안정 지원 대상이 아닙니다")


def test_validation_failure_result_for_missing_original_file(tmp_path: Path) -> None:
    input_file = tmp_path / "missing.xlsx"

    assert_validation_failure_result([input_file], tmp_path, [make_item(input_file)], "원본 파일을 찾을 수 없습니다")


def test_save_results_does_not_call_export_for_validation_errors(tmp_path: Path) -> None:
    app_instance()
    input_file = tmp_path / "sample.xlsx"
    input_file.write_text("sample", encoding="utf-8")

    controller = WizardController()
    controller.export_service = FailingExportService()
    controller.state.input_files = [input_file]
    controller.state.output_folder = tmp_path
    controller.state.detections = [make_item(input_file, selected=False)]

    controller.save_results()

    text = controller.result_screen.result_text.toPlainText()
    assert "상태: 일부 실패 또는 확인 필요" in text
    assert "로그 저장 실패 또는 미실행" in text
    assert "선택된 마스킹 항목이 없습니다" in text
    assert not list(tmp_path.glob("masking_log_*.csv"))


def test_save_results_handles_missing_output_folder_without_export(tmp_path: Path) -> None:
    app_instance()
    input_file = tmp_path / "sample.xlsx"
    input_file.write_text("sample", encoding="utf-8")

    controller = WizardController()
    controller.export_service = FailingExportService()
    controller.state.input_files = [input_file]
    controller.state.output_folder = None
    controller.state.detections = [make_item(input_file)]

    controller.save_results()

    text = controller.result_screen.result_text.toPlainText()
    assert "상태: 일부 실패 또는 확인 필요" in text
    assert "저장 폴더를 선택하세요" in text
    assert "로그 저장 실패 또는 미실행" in text
    assert not list(tmp_path.glob("masking_log_*.csv"))


def test_save_results_does_not_call_export_for_unsupported_file(tmp_path: Path) -> None:
    app_instance()
    input_file = tmp_path / "sample.txt"
    input_file.write_text("sample", encoding="utf-8")

    controller = WizardController()
    controller.export_service = FailingExportService()
    controller.state.input_files = [input_file]
    controller.state.output_folder = tmp_path
    controller.state.detections = [make_item(input_file)]

    controller.save_results()

    text = controller.result_screen.result_text.toPlainText()
    assert "상태: 일부 실패 또는 확인 필요" in text
    assert "지원하지 않는 파일 형식입니다" in text
    assert not list(tmp_path.glob("masking_log_*.csv"))
