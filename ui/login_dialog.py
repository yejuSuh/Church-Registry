from PyQt6.QtWidgets import QDialog, QLabel, QStackedWidget, QVBoxLayout
from PyQt6.QtCore import Qt

from core.constants import C, FONT_LEDGER, BTN_RADIUS
from core.session import session
from ui.login_view import (
    DLG_SS, set_msg,
    build_login_page, build_signup_page, build_forgot_page,
)


class LoginDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("로그인")
        self.setModal(True)
        self.setFixedWidth(400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setStyleSheet(DLG_SS)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 28, 40, 24)
        outer.setSpacing(0)

        title = QLabel("교적 관리 시스템")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-family:{FONT_LEDGER};font-size:23px;font-weight:bold;"
            f"color:{C['sidebar']};background:transparent;"
        )
        sub = QLabel("보스톤 한인 천주교")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"font-size:11px;color:{C['muted']};background:transparent;")
        outer.addWidget(title)
        outer.addWidget(sub)
        outer.addSpacing(22)

        self._stack = QStackedWidget()
        outer.addWidget(self._stack)

        self._setup_login_page()
        self._setup_signup_page()
        self._setup_forgot_page()

        # Derive the dialog's fixed height from each page's actual content
        # instead of hand-guessed pixel constants, which drift out of sync
        # whenever a page's fields change (that's what left a large blank
        # gap above the reset-password button). QStackedWidget.sizeHint()
        # reports the max across ALL of its pages, not just the current
        # one, so we algebraically strip that contribution out rather than
        # trying to hand-measure every row and spacing ourselves.
        m = outer.contentsMargins()
        self._header_h = (
            self.sizeHint().height() - m.top() - m.bottom() - self._stack.sizeHint().height()
        )
        self._forgot_chrome_h = (
            self._forgot_page.sizeHint().height() - self._forgot_inner.sizeHint().height()
        )

        self._show_login()

    def _current_content_height(self):
        top = self._stack.currentWidget()
        if top is self._forgot_page:
            leaf = self._forgot_inner.currentWidget()
            return self._forgot_chrome_h + leaf.sizeHint().height()
        return top.sizeHint().height()

    def _sync_height(self):
        if not hasattr(self, "_header_h"):
            return  # still inside __init__, building pages -- nothing to sync yet
        m = self.layout().contentsMargins()
        total = m.top() + m.bottom() + self._header_h + self._current_content_height()
        self.setFixedHeight(total)

    # ── Page setup (build + wire signals) ────────────────────────────────────

    def _setup_login_page(self):
        page, w = build_login_page()
        self._user_le   = w["user_le"]
        self._pw_le     = w["pw_le"]
        self._login_err = w["err"]
        self._user_le.returnPressed.connect(self._login)
        self._pw_le.returnPressed.connect(self._login)
        w["login_btn"].clicked.connect(self._login)
        w["signup_lnk"].clicked.connect(self._show_signup)
        w["forgot_lnk"].clicked.connect(self._show_forgot)
        self._stack.addWidget(page)

    def _setup_signup_page(self):
        page, w = build_signup_page()
        self._su_user_le  = w["user_le"]
        self._su_pw_le    = w["pw_le"]
        self._su_pw2_le   = w["pw2_le"]
        self._su_name_le  = w["name_le"]
        self._su_bname_le = w["bname_le"]
        self._signup_err  = w["err"]
        for le in (self._su_user_le, self._su_pw_le, self._su_pw2_le,
                   self._su_name_le, self._su_bname_le):
            le.returnPressed.connect(self._signup)
        w["signup_btn"].clicked.connect(self._signup)
        w["login_lnk"].clicked.connect(self._show_login)
        self._stack.addWidget(page)

    def _setup_forgot_page(self):
        page, w = build_forgot_page()
        self._tab_id_btn   = w["tab_id_btn"]
        self._tab_pw_btn   = w["tab_pw_btn"]
        self._forgot_inner = w["inner_stack"]
        fi, rp             = w["fi"], w["rp"]

        self._fi_name_le  = fi["name_le"]
        self._fi_bname_le = fi["bname_le"]
        self._fi_err      = fi["err"]
        for le in (self._fi_name_le, self._fi_bname_le):
            le.returnPressed.connect(self._forgot_find_id)
        fi["btn"].clicked.connect(self._forgot_find_id)

        self._rp_user_le  = rp["user_le"]
        self._rp_name_le  = rp["name_le"]
        self._rp_bname_le = rp["bname_le"]
        self._rp_new_le   = rp["new_le"]
        self._rp_new2_le  = rp["new2_le"]
        self._rp_err      = rp["err"]
        for le in (self._rp_user_le, self._rp_name_le, self._rp_bname_le,
                   self._rp_new_le, self._rp_new2_le):
            le.returnPressed.connect(self._forgot_reset_pw)
        rp["btn"].clicked.connect(self._forgot_reset_pw)

        self._tab_id_btn.clicked.connect(lambda: self._switch_forgot_tab(0))
        self._tab_pw_btn.clicked.connect(lambda: self._switch_forgot_tab(1))
        w["back_lnk"].clicked.connect(self._show_login)
        self._forgot_page = page
        self._stack.addWidget(page)
        self._switch_forgot_tab(0)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show_login(self):
        self._stack.setCurrentIndex(0)
        self._login_err.setText("")
        self._login_err.setVisible(False)
        self._sync_height()

    def _show_signup(self):
        self._stack.setCurrentIndex(1)
        self._signup_err.setText("")
        self._signup_err.setVisible(False)
        self._sync_height()

    def _show_forgot(self):
        self._stack.setCurrentIndex(2)
        self._switch_forgot_tab(0)

    def _switch_forgot_tab(self, idx):
        self._forgot_inner.setCurrentIndex(idx)
        # Same visual language as btn_accent / btn_muted elsewhere in the app
        # (solid fill for the active choice, quiet outline for the inactive
        # one) -- these two buttons can't just use those object names since
        # which one is "active" changes at runtime, but they should still
        # look like they belong to the same button system.
        active = (
            f"QPushButton{{background:{C['accent']};color:#fff;font-weight:bold;"
            f"border:1px solid transparent;border-radius:{BTN_RADIUS};"
            "font-size:13px;padding:0;}}"
        )
        inactive = (
            f"QPushButton{{background:transparent;color:{C['muted']};"
            f"border:1px solid {C['border']};border-radius:{BTN_RADIUS};"
            "font-size:13px;padding:0;}}"
            f"QPushButton:hover{{background:{C['header']};color:{C['text']};}}"
        )
        self._tab_id_btn.setStyleSheet(active if idx == 0 else inactive)
        self._tab_pw_btn.setStyleSheet(active if idx == 1 else inactive)
        self._fi_err.setText("")
        self._fi_err.setVisible(False)
        self._rp_err.setText("")
        self._rp_err.setVisible(False)
        self._sync_height()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _login(self):
        username = self._user_le.text().strip()
        password = self._pw_le.text()
        if not username or not password:
            set_msg(self._login_err, "아이디와 비밀번호를 입력하세요.")
            self._sync_height()
            return
        user = self.db.verify_login(username, password)
        if user is None:
            set_msg(self._login_err, "아이디 또는 비밀번호가 올바르지 않습니다.")
            self._pw_le.clear()
            self._sync_height()
            return
        if not user["is_active"]:
            set_msg(self._login_err, "비활성화된 계정입니다. 관리자에게 문의하세요.")
            self._sync_height()
            return
        self._complete_login(user)

    def _signup(self):
        username  = self._su_user_le.text().strip()
        password  = self._su_pw_le.text()
        password2 = self._su_pw2_le.text()
        name      = self._su_name_le.text().strip()
        bname     = self._su_bname_le.text().strip()
        if not all([username, password, password2, name, bname]):
            set_msg(self._signup_err, "모든 필드를 입력하세요.")
            self._sync_height()
            return
        if password != password2:
            set_msg(self._signup_err, "비밀번호가 일치하지 않습니다.")
            self._sync_height()
            return
        if self.db.username_exists(username):
            set_msg(self._signup_err, "아이디가 이미 사용중입니다.")
            self._sync_height()
            return
        try:
            self.db.create_user(username, password, name, bname, "staff")
            self._complete_login(self.db.get_user(username))
        except Exception as e:
            set_msg(self._signup_err, str(e))
            self._sync_height()

    def _forgot_find_id(self):
        name  = self._fi_name_le.text().strip()
        bname = self._fi_bname_le.text().strip()
        if not name or not bname:
            set_msg(self._fi_err, "이름과 세례명을 입력하세요.")
        else:
            rows = self.db.find_username_by_name(name, bname)
            if not rows:
                set_msg(self._fi_err, "일치하는 계정을 찾을 수 없습니다.")
            else:
                set_msg(self._fi_err, "아이디: " + ", ".join(r["username"] for r in rows), ok=True)
        self._sync_height()

    def _forgot_reset_pw(self):
        username = self._rp_user_le.text().strip()
        name     = self._rp_name_le.text().strip()
        bname    = self._rp_bname_le.text().strip()
        new_pw   = self._rp_new_le.text()
        new_pw2  = self._rp_new2_le.text()
        if not all([username, name, bname, new_pw, new_pw2]):
            set_msg(self._rp_err, "모든 필드를 입력하세요.")
            self._sync_height()
            return
        if new_pw != new_pw2:
            set_msg(self._rp_err, "비밀번호가 일치하지 않습니다.")
            self._sync_height()
            return
        if not self.db.reset_password_by_identity(username, name, bname, new_pw):
            set_msg(self._rp_err, "입력한 정보가 올바르지 않습니다.")
        else:
            set_msg(self._rp_err, "비밀번호가 재설정되었습니다.", ok=True)
            self._rp_new_le.clear()
            self._rp_new2_le.clear()
        self._sync_height()

    def _complete_login(self, user):
        session.username     = user["username"]
        session.name         = user["name"]
        session.baptism_name = user["baptism_name"]
        session.user_level   = user["user_level"]
        self.accept()
