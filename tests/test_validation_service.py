from pathlib import Path

from core.models import DetectionItem
from services.validation_service import file_status, validate_save_request


def make_selected_item(path: Path) -> DetectionItem:
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
        selected=True,
    )


def test_validate_no_files(tmp_path: Path) -> None:
    errors = validate_save_request([], tmp_path, [])
    assert "처리할 파일을 선택하세요." in errors


def test_validate_no_output_folder(tmp_path: Path) -> None:
    input_file = tmp_path / "a.xlsx"
    input_file.write_text("x", encoding="utf-8")
    errors = validate_save_request([input_file], None, [make_selected_item(input_file)])
    assert "저장 폴더를 선택하세요." in errors


def test_validate_missing_input_file(tmp_path: Path) -> None:
    input_file = tmp_path / "missing.xlsx"
    errors = validate_save_request([input_file], tmp_path, [make_selected_item(input_file)])
    assert any("원본 파일을 찾을 수 없습니다" in error for error in errors)


def test_validate_no_selected_items(tmp_path: Path) -> None:
    input_file = tmp_path / "a.xlsx"
    input_file.write_text("x", encoding="utf-8")
    item = make_selected_item(input_file)
    item.selected = False
    errors = validate_save_request([input_file], tmp_path, [item])
    assert "선택된 마스킹 항목이 없습니다. 검토 화면에서 항목을 선택하세요." in errors


def test_hwp_status_message() -> None:
    assert "HWPX로 변환 후 처리하세요" in file_status(Path("sample.hwp"))
