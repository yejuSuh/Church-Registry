from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QPushButton, QLineEdit,
)
from PyQt6.QtCore import Qt

from constants import C
from session import session


def _link_btn(text):
    b = QPushButton(text)
    b.setStyleSheet(
        f"QPushButton{{border:none;background:transparent;color:{C['accent']};"
        "text-decoration:underline;font-size:11px;padding:0;}}"
        f"QPushButton:hover{{color:{C['accent_dk']};}}"
    )
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class LoginDialog(QDialog):
    _LOGIN_H  = 318
    _SIGNUP_H = 450

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("로그인")
        self.setModal(True)
        self.setFixedWidth(400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 28, 40, 24)
        outer.setSpacing(0)

        # ── Header (shared) ──────────────────────────────────────────────────
        title = QLabel("교적 관리 시스템")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size:20px;font-weight:bold;color:{C['sidebar']};background:transparent;"
        )
        sub = QLabel("보스톤 한인 천주교")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"font-size:11px;color:{C['muted']};background:transparent;")
        outer.addWidget(title)
        outer.addWidget(sub)
        outer.addSpacing(22)

        # ── Mode stack ───────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        outer.addWidget(self._stack)

        self._stack.addWidget(self._build_login_page())
        self._stack.addWidget(self._build_signup_page())

        self._show_login()

    # ── Page builders ────────────────────────────────────────────────────────

    def _build_login_page(self):
        page = QStackedWidget.__new__(QStackedWidget)   # use plain QDialog child widget
        from PyQt6.QtWidgets import QWidget
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._user_le = QLineEdit(); self._user_le.setPlaceholderText("아이디")
        self._user_le.setFixedHeight(36)
        lay.addWidget(self._user_le)

        self._pw_le = QLineEdit(); self._pw_le.setPlaceholderText("비밀번호")
        self._pw_le.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_le.setFixedHeight(36)
        self._pw_le.returnPressed.connect(self._login)
        lay.addWidget(self._pw_le)

        self._login_err = QLabel("")
        self._login_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._login_err.setStyleSheet(
            f"color:{C['danger']};font-size:11px;background:transparent;"
        )
        self._login_err.setWordWrap(True)
        self._login_err.setFixedHeight(30)
        lay.addWidget(self._login_err)

        login_btn = QPushButton("로그인")
        login_btn.setObjectName("btn_accent")
        login_btn.setFixedHeight(38)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self._login)
        lay.addWidget(login_btn)

        lay.addSpacing(10)
        link_row = QHBoxLayout()
        lbl = QLabel("계정이 없으신가요?")
        lbl.setStyleSheet(f"color:{C['muted']};font-size:11px;background:transparent;")
        lnk = _link_btn("회원가입")
        lnk.clicked.connect(self._show_signup)
        link_row.addStretch(); link_row.addWidget(lbl)
        link_row.addSpacing(4); link_row.addWidget(lnk); link_row.addStretch()
        lay.addLayout(link_row)

        return page

    def _build_signup_page(self):
        from PyQt6.QtWidgets import QWidget
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        def field(placeholder, echo=False):
            le = QLineEdit(); le.setPlaceholderText(placeholder); le.setFixedHeight(36)
            if echo:
                le.setEchoMode(QLineEdit.EchoMode.Password)
            lay.addWidget(le)
            return le

        self._su_user_le  = field("아이디")
        self._su_pw_le    = field("비밀번호", echo=True)
        self._su_pw2_le   = field("비밀번호 확인", echo=True)
        self._su_name_le  = field("이름")
        self._su_bname_le = field("세례명")
        self._su_pw2_le.returnPressed.connect(self._signup)

        self._signup_err = QLabel("")
        self._signup_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._signup_err.setStyleSheet(
            f"color:{C['danger']};font-size:11px;background:transparent;"
        )
        self._signup_err.setWordWrap(True)
        self._signup_err.setFixedHeight(30)
        lay.addWidget(self._signup_err)

        signup_btn = QPushButton("가입하기")
        signup_btn.setObjectName("btn_accent")
        signup_btn.setFixedHeight(38)
        signup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        signup_btn.clicked.connect(self._signup)
        lay.addWidget(signup_btn)

        lay.addSpacing(10)
        link_row = QHBoxLayout()
        lbl = QLabel("이미 계정이 있으신가요?")
        lbl.setStyleSheet(f"color:{C['muted']};font-size:11px;background:transparent;")
        lnk = _link_btn("로그인")
        lnk.clicked.connect(self._show_login)
        link_row.addStretch(); link_row.addWidget(lbl)
        link_row.addSpacing(4); link_row.addWidget(lnk); link_row.addStretch()
        lay.addLayout(link_row)

        return page

    # ── Mode switch ──────────────────────────────────────────────────────────

    def _show_login(self):
        self._stack.setCurrentIndex(0)
        self._login_err.setText("")
        self.setFixedHeight(self._LOGIN_H)

    def _show_signup(self):
        self._stack.setCurrentIndex(1)
        self._signup_err.setText("")
        self.setFixedHeight(self._SIGNUP_H)

    # ── Actions ──────────────────────────────────────────────────────────────

    def _login(self):
        username = self._user_le.text().strip()
        password = self._pw_le.text()
        if not username or not password:
            self._login_err.setText("아이디와 비밀번호를 입력하세요.")
            return
        user = self.db.verify_login(username, password)
        if user is None:
            self._login_err.setText("아이디 또는 비밀번호가 올바르지 않습니다.")
            self._pw_le.clear()
            return
        if not user["is_active"]:
            self._login_err.setText("비활성화된 계정입니다. 관리자에게 문의하세요.")
            return
        self._complete_login(user)

    def _signup(self):
        username = self._su_user_le.text().strip()
        password = self._su_pw_le.text()
        password2 = self._su_pw2_le.text()
        name      = self._su_name_le.text().strip()
        bname     = self._su_bname_le.text().strip()

        if not all([username, password, password2, name, bname]):
            self._signup_err.setText("모든 필드를 입력하세요.")
            return
        if password != password2:
            self._signup_err.setText("비밀번호가 일치하지 않습니다.")
            return
        if self.db.username_exists(username):
            self._signup_err.setText("아이디가 이미 사용중입니다.")
            return
        try:
            self.db.create_user(username, password, name, bname, "staff")
            user = self.db.get_user(username)
            self._complete_login(user)
        except Exception as e:
            self._signup_err.setText(str(e))

    def _complete_login(self, user):
        self.db.update_last_login(user["username"])
        session.username     = user["username"]
        session.name         = user["name"]
        session.baptism_name = user["baptism_name"]
        session.user_level   = user["user_level"]
        self.accept()
