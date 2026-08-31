from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from services.ocr_service import describe_ocr_status


class DetectionProgressScreen(QWidget):
    back_requested = Signal()
    detection_finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        title = QLabel("개인정보 탐지")
        title.setObjectName("PageTitle")
        subtitle = QLabel("PDF, XLSX, DOCX, HWPX 파일은 실제 문서에서 개인정보 후보를 탐지합니다. 스캔 PDF는 Tesseract OCR 설치가 필요합니다.")
        subtitle.setObjectName("MutedText")
        self.ocr_label = QLabel(describe_ocr_status())
        self.ocr_label.setObjectName("WarningText")
        self.status_list = QListWidget()

        back_button = QPushButton("이전")
        back_button.setObjectName("SecondaryButton")
        back_button.clicked.connect(self.back_requested.emit)

        sample_button = QPushButton("분석 결과 보기")
        sample_button.setObjectName("PrimaryButton")
        sample_button.clicked.connect(self.detection_finished.emit)

        button_row = QHBoxLayout()
        button_row.addWidget(back_button)
        button_row.addStretch()
        button_row.addWidget(sample_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.ocr_label)
        layout.addWidget(self.status_list, 1)
        layout.addLayout(button_row)

    def start_demo_detection(self, files: list[Path]) -> None:
        self.status_list.clear()
        if not files:
            self.status_list.addItem("선택 파일 없음 | 샘플 데이터로 검토 화면을 표시할 수 있습니다.")
            return
        for file in files:
            self.status_list.addItem(f"{file.name} | 대기 | PDF/XLSX/DOCX/HWPX는 실제 분석, HWP는 실패 항목으로 표시")
