from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from core.file_utils import open_folder_in_explorer
from core.models import BatchProcessingResult


class ResultScreen(QWidget):
    restart_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.output_dir = ""

        title = QLabel("처리 결과 확인")
        title.setObjectName("PageTitle")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setObjectName("SummaryLabel")

        open_folder_button = QPushButton("저장 폴더 열기")
        open_folder_button.setObjectName("SecondaryButton")
        open_folder_button.clicked.connect(self.open_output_folder)
        self.open_folder_button = open_folder_button

        restart_button = QPushButton("새 파일 처리")
        restart_button.setObjectName("PrimaryButton")
        restart_button.clicked.connect(self.restart_requested.emit)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(open_folder_button)
        button_row.addWidget(restart_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(self.result_text, 1)
        layout.addLayout(button_row)

    def load_result(self, result: BatchProcessingResult) -> None:
        self.output_dir = result.output_dir
        self.open_folder_button.setEnabled(bool(self.output_dir))

        lines = [
            "상태: 성공" if result.success else "상태: 일부 실패 또는 확인 필요",
            f"전체 처리 파일 수: {result.total_count}",
            f"성공한 파일 수: {result.success_count}",
            f"실패한 파일 수: {result.fail_count}",
            f"저장 폴더: {result.output_dir}",
            f"로그 파일: {result.log_file_path or '로그 저장 실패 또는 미실행'}",
        ]
        if result.log_error_message:
            lines.extend(["", "로그/분석 메시지:", result.log_error_message])

        success_results = [item for item in result.results if item.success]
        failed_results = [item for item in result.results if not item.success]

        if success_results:
            lines.extend(["", "성공 파일 목록:"])
            for item in success_results:
                lines.append(
                    f"- {item.original_file_name} -> {item.output_file_name} | {item.file_type} | 마스킹 {item.selected_count}건"
                )

        if failed_results:
            lines.extend(["", "실패 파일 목록:"])
            for item in failed_results:
                lines.append(f"- {item.original_file_name} | {item.file_type} | {item.error_message}")

        self.result_text.setPlainText("\n".join(lines))

    def open_output_folder(self) -> None:
        try:
            open_folder_in_explorer(self.output_dir)
        except Exception as exc:
            self.result_text.append(f"\n저장 폴더를 열 수 없습니다. 폴더가 이동되었는지 확인하세요. ({exc})")
