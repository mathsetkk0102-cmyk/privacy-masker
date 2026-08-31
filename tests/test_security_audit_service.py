from pathlib import Path

import pytest

from services.security_audit_service import (
    assert_no_plaintext_in_log_row,
    check_no_external_network_usage_note,
    check_output_path_safety,
    summarize_security_policy,
)


def test_log_row_rejects_original_text_key() -> None:
    with pytest.raises(ValueError):
        assert_no_plaintext_in_log_row({"original_text": "010-1234-5678"})


def test_log_row_rejects_masked_text_key() -> None:
    with pytest.raises(ValueError):
        assert_no_plaintext_in_log_row({"masked_text": "010-****-5678"})


def test_output_path_safety_rejects_same_path(tmp_path: Path) -> None:
    path = tmp_path / "same.pdf"
    path.write_text("sample", encoding="utf-8")
    with pytest.raises(ValueError):
        check_output_path_safety(str(path), str(path))


def test_security_policy_summary() -> None:
    policies = summarize_security_policy()
    assert "원본 파일 덮어쓰기 금지" in policies
    assert "외부 서버 전송 금지" in policies
    assert "외부 서버" in check_no_external_network_usage_note()
