from pathlib import Path
import zipfile

from core.logger import CsvAuditLogger
from processors.hwpx_processor import HwpxProcessor


SECTION_XML = """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <body>
    <p>홍길동 학생은 니코초등학교에 재학 중입니다.</p>
    <p>연락처는 010-1234-5678이고 이메일은 teacher@school.kr입니다.</p>
    <p>주민등록번호는 900101-1234567입니다.</p>
    <p>주소는 서울특별시 강남구 역삼동입니다.</p>
  </body>
</root>
"""


def create_sample_hwpx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("mimetype", "application/hwp+zip")
        package.writestr("Contents/section0.xml", SECTION_XML)
        package.writestr("Contents/header.xml", "<root><meta>header</meta></root>")


def read_section(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as package:
        return package.read("Contents/section0.xml").decode("utf-8")


def test_hwpx_supports_zip_package(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.hwpx"
    create_sample_hwpx(input_path)

    assert HwpxProcessor().supports(input_path) is True


def test_hwpx_detects_pii_with_xml_location_and_metadata(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.hwpx"
    create_sample_hwpx(input_path)

    items = HwpxProcessor().detect(input_path)
    types = {item.pii_type for item in items}

    assert {"이름", "전화번호", "이메일", "주민등록번호", "주소", "학교명"}.issubset(types)
    assert all(item.location.startswith("Contents/section0.xml::") for item in items)
    assert all(item.metadata.get("xml_path") == "Contents/section0.xml" for item in items)

    by_type = {item.pii_type: item for item in items}
    assert by_type["전화번호"].review_status == "자동선택"
    assert by_type["이메일"].review_status == "자동선택"
    assert by_type["이름"].review_status == "확인 필요"
    assert by_type["주소"].review_status == "확인 필요"
    assert by_type["학교명"].review_status == "확인 필요"


def test_hwpx_apply_masking_only_selected_items_and_keeps_original(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.hwpx"
    output_dir = tmp_path / "out"
    create_sample_hwpx(input_path)

    processor = HwpxProcessor()
    items = processor.detect(input_path)
    for item in items:
        item.selected = item.pii_type == "전화번호"

    output_path = Path(processor.apply_masking(input_path, output_dir, items))

    assert output_path.exists()
    assert output_path.name == "masked_sample.hwpx"
    assert "010-1234-5678" in read_section(input_path)
    assert "010-****-5678" in read_section(output_path)
    assert "teacher@school.kr" in read_section(output_path)


def test_hwpx_uses_user_edited_masked_text(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.hwpx"
    output_dir = tmp_path / "out"
    create_sample_hwpx(input_path)

    processor = HwpxProcessor()
    items = processor.detect(input_path)
    for item in items:
        item.selected = item.original_text == "teacher@school.kr"
        if item.selected:
            item.masked_text = "직접수정@example.com"

    output_path = Path(processor.apply_masking(input_path, output_dir, items))

    assert "직접수정@example.com" in read_section(output_path)


def test_hwpx_log_does_not_store_pii_text(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.hwpx"
    create_sample_hwpx(input_path)

    items = HwpxProcessor().detect(input_path)
    log_path = CsvAuditLogger(tmp_path).write_run_log([input_path], items)
    log_text = log_path.read_text(encoding="utf-8-sig")

    assert "010-1234-5678" not in log_text
    assert "teacher@school.kr" not in log_text
    assert "홍길동" not in log_text
