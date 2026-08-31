import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from app.screens.review_table_screen import ReviewTableScreen
from core.models import DetectionItem


def app_instance() -> QApplication:
    return QApplication.instance() or QApplication([])


def make_item(pii_type: str, selected: bool) -> DetectionItem:
    original_text = "홍길동" if pii_type == "이름" else "010-1234-5678"
    return DetectionItem(
        id=pii_type,
        file_path=str(Path("sample.pdf")),
        file_type="pdf",
        page_or_sheet="page 1",
        location="page 1",
        pii_type=pii_type,
        original_text=original_text,
        masked_text="홍**" if pii_type == "이름" else "010-****-5678",
        confidence="낮음" if pii_type == "이름" else "높음",
        review_status="확인 필요" if pii_type == "이름" else "자동선택",
        selected=selected,
    )


def test_review_table_can_select_name_candidates_only() -> None:
    app_instance()
    screen = ReviewTableScreen()
    name_item = make_item("이름", selected=False)
    phone_item = make_item("전화번호", selected=False)

    screen.load_items([name_item, phone_item])
    screen.set_pii_type_checked("이름", True)

    assert name_item.selected is True
    assert phone_item.selected is False


def test_review_table_can_temporarily_hide_original_text() -> None:
    app_instance()
    screen = ReviewTableScreen()
    name_item = make_item("이름", selected=False)
    screen.load_items([name_item])

    screen.set_original_text_hidden(True)

    assert screen.table.item(0, screen.ORIGINAL_TEXT_COLUMN).text() == "********"
    assert name_item.original_text == "홍길동"

    screen.set_original_text_hidden(False)

    assert screen.table.item(0, screen.ORIGINAL_TEXT_COLUMN).text() == "홍길동"
