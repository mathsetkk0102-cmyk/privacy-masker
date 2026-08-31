from PySide6.QtWidgets import QMainWindow, QStatusBar

from app.wizard_controller import WizardController


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("개인정보 마스킹 도구")
        self.resize(1180, 760)
        self.controller = WizardController()
        self.setCentralWidget(self.controller)
        self.credit_status_bar = QStatusBar()
        self.credit_status_bar.setObjectName("CreditStatusBar")
        self.credit_status_bar.showMessage("Made by NFT-H")
        self.setStatusBar(self.credit_status_bar)
