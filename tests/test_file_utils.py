from pathlib import Path

import pytest

from core.file_utils import (
    calculate_file_hash,
    ensure_not_same_path,
    ensure_unique_path,
    get_file_extension,
    get_safe_output_path,
    is_writable_directory,
    make_masked_output_path,
)


def test_make_masked_output_path(tmp_path: Path) -> None:
    output = make_masked_output_path(Path("report.pdf"), tmp_path)
    assert output.name == "masked_report.pdf"


def test_ensure_unique_path_adds_number(tmp_path: Path) -> None:
    existing = tmp_path / "masked_report.pdf"
    existing.write_text("sample", encoding="utf-8")
    unique = ensure_unique_path(existing)
    assert unique.name == "masked_report_2.pdf"


def test_get_file_extension() -> None:
    assert get_file_extension("report.PDF") == ".pdf"


def test_get_safe_output_path_adds_masked_prefix(tmp_path: Path) -> None:
    output = Path(get_safe_output_path("C:/docs/보고서.pdf", tmp_path))
    assert output.name == "masked_보고서.pdf"


def test_get_safe_output_path_adds_number_on_collision(tmp_path: Path) -> None:
    (tmp_path / "masked_보고서.pdf").write_text("exists", encoding="utf-8")
    output = Path(get_safe_output_path("C:/docs/보고서.pdf", tmp_path))
    assert output.name == "masked_보고서_2.pdf"


def test_ensure_not_same_path_raises_for_same_path(tmp_path: Path) -> None:
    original = tmp_path / "same.pdf"
    original.write_text("sample", encoding="utf-8")
    with pytest.raises(ValueError, match="원본 파일과 결과 파일 경로가 같습니다"):
        ensure_not_same_path(original, original)


def test_is_writable_directory(tmp_path: Path) -> None:
    assert is_writable_directory(tmp_path) is True


def test_calculate_file_hash_is_stable_for_same_content(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.txt"
    input_path.write_text("same content", encoding="utf-8")

    assert calculate_file_hash(input_path) == calculate_file_hash(input_path)


def test_calculate_file_hash_changes_when_content_changes(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.txt"
    input_path.write_text("before", encoding="utf-8")
    before_hash = calculate_file_hash(input_path)

    input_path.write_text("after", encoding="utf-8")

    assert calculate_file_hash(input_path) != before_hash
