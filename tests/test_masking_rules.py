from core.masking_rules import default_review_status, mask_value


def test_phone_masking() -> None:
    assert mask_value("전화번호", "010-1234-5678") == "010-****-5678"
    assert mask_value("전화번호", "02-123-4567") == "02-***-4567"


def test_email_masking() -> None:
    assert mask_value("이메일", "teacher@school.kr") == "t******@school.kr"
    assert mask_value("이메일", "ab@test.com") == "a*@test.com"


def test_resident_number_masking() -> None:
    assert mask_value("주민등록번호", "900101-1234567") == "******-*******"
    assert mask_value("주민등록번호", "9001011234567") == "*************"


def test_birthdate_masking() -> None:
    assert mask_value("생년월일", "1990.01.01") == "1990.**.**"
    assert mask_value("생년월일", "1990-01-01") == "1990-**-**"
    assert mask_value("생년월일", "900101") == "90****"


def test_account_masking() -> None:
    assert mask_value("계좌번호", "123-456-789012") == "123-***-****12"
    assert mask_value("계좌번호", "110123456789") == "110*******89"


def test_name_masking() -> None:
    assert mask_value("이름", "홍길동") == "홍**"
    assert mask_value("이름", "김철") == "김*"
    assert mask_value("이름", "남궁민수") == "남***"


def test_school_masking() -> None:
    assert mask_value("학교명", "니코초등학교") == "***초등학교"
    assert mask_value("학교명", "한국중학교") == "***중학교"
    assert mask_value("학교명", "서울고등학교") == "***고등학교"
    assert mask_value("학교명", "코딩대학교") == "***대학교"


def test_ambiguous_items_need_review() -> None:
    assert default_review_status("주소") == "확인 필요"
    assert default_review_status("계좌번호") == "확인 필요"
    assert default_review_status("학교명") == "확인 필요"
