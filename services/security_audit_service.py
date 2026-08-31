from pathlib import Path

SENSITIVE_LOG_KEYS = {"original_text", "masked_text", "pii_text", "detected_text"}


def assert_no_plaintext_in_log_row(row: dict) -> None:
    forbidden = SENSITIVE_LOG_KEYS.intersection(row.keys())
    if forbidden:
        raise ValueError(f"로그 row에 개인정보 원문 가능 컬럼이 포함되어 있습니다: {', '.join(sorted(forbidden))}")


def sanitize_log_row(row: dict, allowed_columns: list[str]) -> dict:
    clean_row = {column: row.get(column, "") for column in allowed_columns}
    assert_no_plaintext_in_log_row(clean_row)
    return clean_row


def check_output_path_safety(original_file_path: str, output_file_path: str) -> None:
    if Path(original_file_path).resolve() == Path(output_file_path).resolve():
        raise ValueError("원본 파일과 결과 파일 경로가 같습니다. 다른 저장 폴더를 선택하세요.")


def check_no_external_network_usage_note() -> str:
    return "이 앱은 외부 서버, 외부 API, 클라우드 저장소로 문서를 전송하지 않는 로컬 처리 구조를 사용합니다."


def summarize_security_policy() -> list[str]:
    return [
        "원본 파일 덮어쓰기 금지",
        "로그에 개인정보 원문 저장 금지",
        "외부 서버 전송 금지",
        "사용자가 선택한 항목만 마스킹",
        "OCR 결과 검토 필요",
        "HWP 미지원 안내",
    ]
