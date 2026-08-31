from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.models import WorkflowState


class SaveConfirmScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        title = QLabel("마스킹 사본 저장")
        title.setObjectName("PageTitle")
        self.summary_label = QLabel("")
        self.summary_label.setObjectName("SummaryLabel")

        back_button = QPushButton("이전으로 돌아가기")
        back_button.setObjectName("SecondaryButton")
        back_button.clicked.connect(self.back_requested.emit)

        save_button = QPushButton("마스킹 사본 저장")
        save_button.setObjectName("PrimaryButton")
        self.save_button = save_button
        save_button.clicked.connect(self.save_requested.emit)

        button_row = QHBoxLayout()
        button_row.addWidget(back_button)
        button_row.addStretch()
        button_row.addWidget(save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(self.summary_label)
        layout.addStretch()
        layout.addLayout(button_row)

    def load_summary(self, state: WorkflowState) -> None:
        selected_count = sum(1 for item in state.detections if item.selected)
        need_review_count = sum(1 for item in state.detections if item.review_status == "확인 필요")
        unselected_name_count = sum(
            1 for item in state.detections if item.pii_type == "이름" and not item.selected
        )
        summary_lines = [
            f"선택한 파일 개수: {len(state.input_files)}",
            f"탐지된 개인정보 후보 개수: {len(state.detections)}",
            f"실제 마스킹할 항목 개수: {selected_count}",
            f"확인 필요 항목 개수: {need_review_count}",
            f"미선택 이름 후보 개수: {unselected_name_count}",
            f"저장 폴더: {state.output_folder}",
            "로그 저장: CSV 로그를 저장합니다.",
        ]
        if unselected_name_count:
            summary_lines.extend(
                [
                    "",
                    "주의: 선택하지 않은 이름 후보는 결과 문서에서 마스킹되지 않습니다.",
                ]
            )
        summary_lines.extend(
            [
                "",
                "원본 파일은 수정하지 않고 마스킹된 사본만 저장합니다.",
                "검토 화면에서 선택한 항목만 마스킹됩니다.",
                "OCR 결과는 누락될 수 있으므로 저장 전 검토가 필요합니다.",
            ]
        )
        self.summary_label.setText("\n".join(summary_lines))

    def set_saving(self, saving: bool) -> None:
        self.save_button.setEnabled(not saving)
        self.save_button.setText("저장 중..." if saving else "마스킹 사본 저장")
