from pathlib import Path
import hashlib
import os
import subprocess
import sys


SUPPORTED_SUFFIXES = {".pdf", ".xlsx", ".docx", ".hwpx"}
IMPLEMENTED_SUFFIXES = {".xlsx", ".docx", ".hwpx"}
HWP_SUFFIX = ".hwp"


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def get_file_extension(file_path: str | Path) -> str:
    return Path(file_path).suffix.lower()


def calculate_file_hash(file_path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resource_path(relative_path: str | Path) -> Path:
    relative = Path(relative_path)
    candidates: list[Path] = []

    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / relative)

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / relative)

    candidates.append(Path(__file__).resolve().parents[1] / relative)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def get_safe_output_path(original_file_path: str | Path, output_dir: str | Path, prefix: str = "masked_") -> str:
    original_path = Path(original_file_path)
    output_folder = Path(output_dir)
    candidate = ensure_unique_path(output_folder / f"{prefix}{original_path.name}")
    ensure_not_same_path(original_path, candidate)
    return str(candidate)


def ensure_not_same_path(original_file_path: str | Path, output_file_path: str | Path) -> None:
    original_path = Path(original_file_path).resolve()
    output_path = Path(output_file_path).resolve()
    if original_path == output_path:
        raise ValueError("원본 파일과 결과 파일 경로가 같습니다. 다른 저장 폴더를 선택하세요.")


def is_writable_directory(output_dir: str | Path) -> bool:
    output_path = Path(output_dir)
    if not output_path.exists() or not output_path.is_dir():
        return False
    probe = output_path / ".write_test"
    try:
        probe.write_text("test", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def open_folder_in_explorer(folder_path: str | Path) -> None:
    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError("저장 폴더를 열 수 없습니다. 폴더가 이동되었는지 확인하세요.")
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(path)])


def make_masked_output_path(input_path: Path, output_folder: Path) -> Path:
    return Path(get_safe_output_path(input_path, output_folder))


def is_supported_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_SUFFIXES


def is_implemented_file(path: Path) -> bool:
    return path.suffix.lower() in IMPLEMENTED_SUFFIXES


def is_hwp_file(path: Path) -> bool:
    return path.suffix.lower() == HWP_SUFFIX
