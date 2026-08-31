from pathlib import Path

import pytest

from processors.hwp_processor_stub import HwpProcessorStub


def test_hwp_stub_supports_hwp_extension() -> None:
    assert HwpProcessorStub().supports("sample.hwp") is True


def test_hwp_stub_detect_raises_clear_message() -> None:
    with pytest.raises(ValueError, match="HWPX로 변환 후 처리하세요"):
        HwpProcessorStub().detect(Path("sample.hwp"))


def test_hwp_stub_apply_raises_clear_message(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="HWPX로 변환 후 처리하세요"):
        HwpProcessorStub().apply_masking(Path("sample.hwp"), tmp_path, [])
