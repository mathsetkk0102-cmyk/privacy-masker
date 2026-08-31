import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from app.screens.save_confirm_screen import SaveConfirmScreen
from core.models import DetectionItem, WorkflowState


def app_instance() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_save_summary_warns_about_unselected_name_candidates(tmp_path: Path) -> None:
    app_instance()
    screen = SaveConfirmScreen()
    state = WorkflowState(
        input_files=[Path("sample.pdf")],
        output_folder=tmp_path,
        detections=[
            DetectionItem(
                id="name-1",
                file_path="sample.pdf",
                file_type="pdf",
                page_or_sheet="page 1",
                location="page 1",
                pii_type="이름",
                original_text="홍길동",
                masked_text="홍**",
                confidence="낮음",
                review_status="확인 필요",
                selected=False,
            )
        ],
    )

    screen.load_summary(state)

    summary = screen.summary_label.text()
    assert "미선택 이름 후보 개수: 1" in summary
    assert "선택하지 않은 이름 후보는 결과 문서에서 마스킹되지 않습니다." in summary
