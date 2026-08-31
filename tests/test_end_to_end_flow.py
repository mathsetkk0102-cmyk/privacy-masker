from pathlib import Path
import re
import zipfile

import pytest

openpyxl = pytest.importorskip("openpyxl")
docx = pytest.importorskip("docx")
fitz = pytest.importorskip("fitz")

from core.file_utils import calculate_file_hash
from services.export_service import ExportService


SENSITIVE_SAMPLES = [
    "010-1234-5678",
    "teacher@school.kr",
    "900101-1234567",
    "1990.01.01",
    "123-456-789012",
]


def create_e2e_xlsx(path: Path) -> None:
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Sheet1"
    worksheet["A1"] = "홍길동 / 010-1234-5678 / teacher@school.kr"
    worksheet["A2"] = "900101-1234567"
    worksheet["A3"] = "서울특별시 강남구 역삼동"
    worksheet["A4"] = "123-456-789012"
    worksheet["A5"] = "니코초등학교"
    workbook.save(path)


def create_e2e_docx(path: Path) -> None:
    document = docx.Document()
    document.add_paragraph("홍길동 연락처는 010-1234-5678이고 이메일은 teacher@school.kr입니다.")
    table = document.add_table(rows=3, cols=1)
    table.cell(0, 0).text = "900101-1234567"
    table.cell(1, 0).text = "서울특별시 강남구 역삼동"
    table.cell(2, 0).text = "니코초등학교"
    document.save(path)


def create_e2e_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Hong Gil Dong")
    page.insert_text((72, 100), "010-1234-5678")
    page.insert_text((72, 128), "teacher@school.kr")
    page.insert_text((72, 156), "900101-1234567")
    document.save(str(path))
    document.close()


def create_e2e_hwpx(path: Path) -> None:
    section_xml = """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <body>
    <p>홍길동 연락처는 010-1234-5678이고 이메일은 teacher@school.kr입니다.</p>
    <p>주민등록번호는 900101-1234567입니다.</p>
    <p>주소는 서울특별시 강남구 역삼동입니다.</p>
    <p>학교명은 니코초등학교입니다.</p>
  </body>
</root>
"""
    with zipfile.ZipFile(path, "w") as package:
        package.writestr("mimetype", "application/hwp+zip")
        package.writestr("Contents/section0.xml", section_xml)


def read_xlsx_text(path: Path) -> str:
    workbook = openpyxl.load_workbook(path, data_only=False)
    values: list[str] = []
    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    values.append(cell.value)
    return "\n".join(values)


def read_docx_text(path: Path) -> str:
    document = docx.Document(path)
    values = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                values.extend(paragraph.text for paragraph in cell.paragraphs)
    return "\n".join(values)


def read_pdf_text(path: Path) -> str:
    with fitz.open(path) as document:
        return "\n".join(page.get_text("text") for page in document)


def read_hwpx_text(path: Path) -> str:
    with zipfile.ZipFile(path, "r") as package:
        return package.read("Contents/section0.xml").decode("utf-8")


def should_select_for_e2e(original_text: str) -> bool:
    return bool(
        re.fullmatch(r"010-\d{4}-\d{4}", original_text)
        or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", original_text)
        or re.fullmatch(r"\d{6}-\d{7}", original_text)
    )


def test_end_to_end_export_preserves_originals_and_safe_log(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    input_files = [
        input_dir / "sample.xlsx",
        input_dir / "sample.docx",
        input_dir / "sample.pdf",
        input_dir / "sample.hwpx",
        input_dir / "unsupported.txt",
    ]
    create_e2e_xlsx(input_files[0])
    create_e2e_docx(input_files[1])
    create_e2e_pdf(input_files[2])
    create_e2e_hwpx(input_files[3])
    input_files[4].write_text("010-1234-5678", encoding="utf-8")

    before_hashes = {path: calculate_file_hash(path) for path in input_files}
    service = ExportService()
    detections = []
    detection_failures: dict[Path, str] = {}

    for path in input_files:
        try:
            file_items = service.detect_file(path)
        except Exception as exc:
            detection_failures[path] = str(exc)
            continue
        for item in file_items:
            item.selected = should_select_for_e2e(item.original_text)
            if item.selected and item.original_text == "teacher@school.kr":
                item.masked_text = "edited@example.com"
        detections.extend(file_items)

    assert input_files[4] in detection_failures
    assert any(item.selected for item in detections)

    result = service.export_files(input_files, output_dir, detections)

    assert result.success_count == 4
    assert result.fail_count == 1
    assert result.log_file_path
    assert Path(result.log_file_path).exists()
    assert all(calculate_file_hash(path) == before_hashes[path] for path in input_files)

    successful_outputs = {
        Path(item.original_file_path).suffix.lower(): Path(item.output_file_path)
        for item in result.results
        if item.success
    }
    assert read_xlsx_text(successful_outputs[".xlsx"]).count("010-****-5678") >= 1
    assert "edited@example.com" in read_docx_text(successful_outputs[".docx"])
    assert "010-1234-5678" not in read_pdf_text(successful_outputs[".pdf"])
    assert "010-****-5678" in read_hwpx_text(successful_outputs[".hwpx"])

    log_text = Path(result.log_file_path).read_text(encoding="utf-8-sig")
    forbidden_values = SENSITIVE_SAMPLES + ["010-****-5678", "edited@example.com"]
    for value in forbidden_values:
        assert value not in log_text

    failed = [item for item in result.results if not item.success]
    assert len(failed) == 1
    assert failed[0].original_file_name == "unsupported.txt"
