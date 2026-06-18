from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtCore import Qt

from constants import C
from session import session


class LoginDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("로그인")
        self.resize(400, 300)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 36, 48, 36)
        outer.setSpacing(0)

        title = QLabel("교적 관리 시스템")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size:20px;font-weight:bold;color:{C['sidebar']};"
            "background:transparent;margin-bottom:6px;"
        )
        sub = QLabel("보스톤 한인 천주교")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"font-size:11px;color:{C['muted']};background:transparent;")
        outer.addWidget(title)
        outer.addWidget(sub)
        outer.addSpacing(28)

        self._user_le = QLineEdit()
        self._user_le.setPlaceholderText("아이디")
        self._user_le.setFixedHeight(36)
        outer.addWidget(self._user_le)
        outer.addSpacing(8)

        self._pw_le = QLineEdit()
        self._pw_le.setPlaceholderText("비밀번호")
        self._pw_le.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_le.setFixedHeight(36)
        self._pw_le.returnPressed.connect(self._login)
        outer.addWidget(self._pw_le)
        outer.addSpacing(6)

        self._err_lbl = QLabel("")
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err_lbl.setStyleSheet(
            f"color:{C['danger']};font-size:11px;background:transparent;"
        )
        outer.addWidget(self._err_lbl)
        outer.addSpacing(10)

        login_btn = QPushButton("로그인")
        login_btn.setObjectName("btn_accent")
        login_btn.setFixedHeight(38)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self._login)
        outer.addWidget(login_btn)

    def _login(self):
        username = self._user_le.text().strip()
        password = self._pw_le.text()
        if not username or not password:
            self._err_lbl.setText("아이디와 비밀번호를 입력하세요.")
            return
        user = self.db.verify_login(username, password)
        if user is None:
            self._err_lbl.setText("아이디 또는 비밀번호가 올바르지 않습니다.")
            self._pw_le.clear()
            return
        self.db.update_last_login(username)
        session.username   = user["username"]
        session.name       = user["name"]
        session.user_level = user["user_level"]
        self.accept()
