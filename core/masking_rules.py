import re


PII_TYPES = {
    "이름",
    "전화번호",
    "이메일",
    "주민등록번호",
    "생년월일",
    "주소",
    "계좌번호",
    "학교명",
}

AUTO_SELECTED_TYPES = {"전화번호", "이메일", "주민등록번호", "생년월일"}
NEEDS_REVIEW_TYPES = {"이름", "주소", "계좌번호", "학교명"}

REVIEW_AUTO_SELECTED = "자동선택"
REVIEW_NEEDS_REVIEW = "확인 필요"
REVIEW_EXCLUDED = "제외"

CONFIDENCE_HIGH = "높음"
CONFIDENCE_MEDIUM = "보통"
CONFIDENCE_LOW = "낮음"


def default_review_status(pii_type: str) -> str:
    if pii_type in AUTO_SELECTED_TYPES:
        return REVIEW_AUTO_SELECTED
    return REVIEW_NEEDS_REVIEW


def default_selected(pii_type: str) -> bool:
    return default_review_status(pii_type) == REVIEW_AUTO_SELECTED


def default_confidence(pii_type: str) -> str:
    if pii_type in {"전화번호", "이메일", "주민등록번호"}:
        return CONFIDENCE_HIGH
    if pii_type in {"생년월일", "계좌번호", "주소", "학교명"}:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_LOW


def mask_phone(value: str) -> str:
    match = re.fullmatch(r"(\d{2,3})([- ]?)(\d{3,4})([- ]?)(\d{4})", value)
    if not match:
        return value
    area, sep1, middle, sep2, last = match.groups()
    separator = sep1 or sep2 or "-"
    return f"{area}{separator}{'*' * len(middle)}{separator}{last}"


def mask_email(value: str) -> str:
    local, at, domain = value.partition("@")
    if not at or not domain:
        return value
    if len(local) <= 1:
        masked_local = "*"
    elif len(local) == 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 1)
    return f"{masked_local}@{domain}"


def mask_rrn(value: str) -> str:
    match = re.fullmatch(r"(\d{6})(-?)(\d{7})", value)
    if not match:
        return value
    _birth, separator, _tail = match.groups()
    return f"{'*' * 6}{separator}{'*' * 7}"


def mask_birthdate(value: str) -> str:
    separated = re.fullmatch(r"(\d{4})([.\-/])(\d{1,2})([.\-/])(\d{1,2})", value)
    if separated:
        year, sep1, _month, sep2, _day = separated.groups()
        return f"{year}{sep1}**{sep2}**"

    compact = re.fullmatch(r"(\d{2})(\d{2})(\d{2})", value)
    if compact:
        return compact.group(1) + "****"

    return value


def mask_account(value: str) -> str:
    if "-" in value:
        parts = value.split("-")
        if len(parts) >= 3 and len(parts[-1]) >= 2:
            return f"{parts[0]}-***-{'*' * max(0, len(parts[-1]) - 2)}{parts[-1][-2:]}"

    digits = re.sub(r"\D", "", value)
    if len(digits) < 8:
        return value
    return f"{digits[:3]}{'*' * (len(digits) - 5)}{digits[-2:]}"


def mask_address(value: str) -> str:
    parts = value.split()
    if len(parts) >= 3:
        return " ".join(parts[:2] + ["***"])
    return value + " ***"


def mask_name(value: str) -> str:
    if len(value) <= 1:
        return "*"
    return value[0] + "*" * (len(value) - 1)


def mask_school(value: str) -> str:
    for suffix in ("초등학교", "중학교", "고등학교", "대학교"):
        if value.endswith(suffix):
            return "***" + suffix
    return "***학교"


def mask_value(pii_type: str, value: str) -> str:
    maskers = {
        "전화번호": mask_phone,
        "이메일": mask_email,
        "주민등록번호": mask_rrn,
        "생년월일": mask_birthdate,
        "계좌번호": mask_account,
        "주소": mask_address,
        "이름": mask_name,
        "학교명": mask_school,
    }
    return maskers.get(pii_type, lambda text: text)(value)
