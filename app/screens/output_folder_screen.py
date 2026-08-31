from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from services.validation_service import validate_output_folder


class OutputFolderScreen(QWidget):
    back_requested = Signal()
    next_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.output_folder = ""

        self.title = QLabel("저장 폴더 선택")
        self.title.setObjectName("PageTitle")
        self.subtitle = QLabel("마스킹된 사본과 CSV 로그를 저장할 폴더를 선택하세요.")
        self.subtitle.setObjectName("MutedText")
        self.file_count_label = QLabel("선택한 파일: 0개")
        self.path_label = QLabel("저장 폴더가 선택되지 않았습니다.")
        self.path_label.setObjectName("PathLabel")

        pick_button = QPushButton("저장 폴더 선택")
        pick_button.setObjectName("PrimaryButton")
        pick_button.clicked.connect(self.pick_folder)

        back_button = QPushButton("이전")
        back_button.setObjectName("SecondaryButton")
        back_button.clicked.connect(self.back_requested.emit)

        next_button = QPushButton("다음")
        next_button.setObjectName("PrimaryButton")
        next_button.clicked.connect(self.emit_next)

        button_row = QHBoxLayout()
        button_row.addWidget(back_button)
        button_row.addStretch()
        button_row.addWidget(pick_button)
        button_row.addWidget(next_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.setSpacing(18)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.file_count_label)
        layout.addWidget(self.path_label)
        layout.addStretch()
        layout.addLayout(button_row)

    def set_file_count(self, count: int) -> None:
        self.file_count_label.setText(f"선택한 파일: {count}개")

    def pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "저장 폴더 선택")
        if folder:
            self.output_folder = folder
            self.path_label.setText(folder)

    def emit_next(self) -> None:
        if not self.output_folder:
            self.path_label.setText("저장 폴더를 선택하세요.")
            return
        is_valid, message = validate_output_folder(self.output_folder)
        if not is_valid:
            self.path_label.setText(message)
            return
        self.next_requested.emit(self.output_folder)

    def reset(self) -> None:
        self.output_folder = ""
        self.path_label.setText("저장 폴더가 선택되지 않았습니다.")
