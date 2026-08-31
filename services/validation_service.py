from pathlib import Path

from core.file_utils import (
    get_safe_output_path,
    is_hwp_file,
    is_implemented_file,
    is_supported_file,
    is_writable_directory,
)
from core.models import DetectionItem


def file_status(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "처리 가능"
    if is_implemented_file(path):
        return "처리 가능"
    if suffix == ".hwpx":
        return "지원 예정"
    if is_hwp_file(path):
        return "HWP는 현재 안정 지원 대상이 아닙니다. HWPX로 변환 후 처리하세요."
    if is_supported_file(path):
        return "지원 예정"
    return "지원 안 함"


def validate_output_folder(path: str | Path) -> tuple[bool, str]:
    output_path = Path(path)
    if not output_path.exists():
        return False, "저장 폴더가 없습니다. 다른 폴더를 선택하세요."
    if not output_path.is_dir():
        return False, "저장 위치가 폴더가 아닙니다. 다른 폴더를 선택하세요."
    if not is_writable_directory(output_path):
        return False, "저장 폴더에 쓰기 권한이 없습니다. 다른 폴더를 선택하세요."
    return True, ""


def validate_save_request(
    input_files: list[Path],
    output_dir: str | Path | None,
    detections: list[DetectionItem],
) -> list[str]:
    errors: list[str] = []
    if not input_files:
        errors.append("처리할 파일을 선택하세요.")
    if not output_dir:
        errors.append("저장 폴더를 선택하세요.")
        return errors

    output_path = Path(output_dir)
    is_valid_folder, folder_message = validate_output_folder(output_path)
    if not is_valid_folder:
        errors.append(folder_message)

    selected_items = [item for item in detections if item.selected]
    if not selected_items:
        errors.append("선택된 마스킹 항목이 없습니다. 검토 화면에서 항목을 선택하세요.")

    for input_file in input_files:
        if is_hwp_file(input_file):
            errors.append("HWP 파일은 현재 안정 지원 대상이 아닙니다. HWPX로 변환 후 처리하세요.")
            continue
        if not input_file.exists():
            errors.append(f"{input_file.name}: 원본 파일을 찾을 수 없습니다. 파일 위치를 확인하세요.")
            continue
        if not input_file.is_file():
            errors.append(f"{input_file.name}: 원본 파일을 읽을 수 없습니다.")
            continue
        if not is_supported_file(input_file):
            errors.append(f"{input_file.name}: 지원하지 않는 파일 형식입니다.")
            continue
        try:
            safe_path = get_safe_output_path(input_file, output_path)
            Path(safe_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            errors.append(f"{input_file.name}: {exc}")
    return errors
