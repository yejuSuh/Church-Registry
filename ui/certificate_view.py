from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class CertificateView(QWidget):
    """Placeholder for the certificate printing feature (미구현)."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(12)

        icon = QLabel("🖨")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size:52px;background:transparent;")
        lay.addWidget(icon)

        title = QLabel("증명서 출력")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:20px;font-weight:bold;background:transparent;")
        lay.addWidget(title)

        desc = QLabel(
            "세례 · 견진 · 첫영성체 · 혼인 증명서 및 교적 등본 출력 기능이\n"
            "추후 이 화면에 구현될 예정입니다."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setObjectName("mu")
        desc.setWordWrap(True)
        lay.addWidget(desc)
