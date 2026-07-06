from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QStackedWidget, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt

from constants import C

# ── Dialog-scoped stylesheet ──────────────────────────────────────────────────
DLG_SS = f"""
    QDialog, QWidget, QStackedWidget {{ background: #FFFFFF; }}
    QLineEdit {{
        font-size: 14px;
        background: #FFFFFF;
        border: 1px solid {C['border']};
        border-radius: 5px;
        padding: 5px 8px;
    }}
    QLineEdit:focus {{ border: 1.5px solid {C['accent']}; }}
    QPushButton#btn_accent {{
        font-size: 15px;
        font-weight: bold;
        background: {C['accent']};
        color: white;
        border-radius: 5px;
        padding: 6px 14px;
    }}
    QPushButton#btn_accent:hover {{ background: {C['accent_dk']}; }}
"""

# ── Widget helpers ────────────────────────────────────────────────────────────

def link_btn(text):
    b = QPushButton(text)
    b.setStyleSheet(
        f"QPushButton{{border:none;background:transparent;color:{C['accent']};"
        "text-decoration:underline;font-size:13px;padding:0;}}"
        f"QPushButton:hover{{color:{C['accent_dk']};}}"
    )
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def field(placeholder, echo=False):
    le = QLineEdit()
    le.setPlaceholderText(placeholder)
    le.setFixedHeight(38)
    if echo:
        le.setEchoMode(QLineEdit.EchoMode.Password)
    return le


def err_label(height=32):
    lbl = QLabel("")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"color:{C['danger']};font-size:13px;background:transparent;")
    lbl.setWordWrap(True)
    lbl.setFixedHeight(height)
    return lbl


def muted(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{C['muted']};font-size:13px;background:transparent;")
    return lbl


def set_msg(label, text, ok=False):
    color = C['accent'] if ok else C['danger']
    label.setStyleSheet(f"color:{color};font-size:13px;background:transparent;")
    label.setText(text)


def accent_btn(label_text, height=40):
    btn = QPushButton(label_text)
    btn.setObjectName("btn_accent")
    btn.setFixedHeight(height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


# ── Page builders ─────────────────────────────────────────────────────────────
# Each builder returns (QWidget, refs_dict).
# Builders construct layouts only — no signal connections.

def build_login_page():
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    user_le = field("아이디")
    pw_le = field("비밀번호", echo=True)
    err = err_label(height=32)
    login_btn = accent_btn("로그인")

    lay.addWidget(user_le)
    lay.addWidget(pw_le)
    lay.addWidget(err)
    lay.addWidget(login_btn)
    lay.addSpacing(10)

    signup_row = QHBoxLayout()
    signup_row.addStretch()
    signup_row.addWidget(muted("계정이 없으신가요?"))
    signup_row.addSpacing(4)
    signup_lnk = link_btn("회원가입")
    signup_row.addWidget(signup_lnk)
    signup_row.addStretch()
    lay.addLayout(signup_row)

    forgot_row = QHBoxLayout()
    forgot_lnk = link_btn("아이디 / 비밀번호 찾기")
    forgot_row.addStretch()
    forgot_row.addWidget(forgot_lnk)
    forgot_row.addStretch()
    lay.addLayout(forgot_row)

    return page, {
        "user_le": user_le, "pw_le": pw_le, "err": err,
        "login_btn": login_btn, "signup_lnk": signup_lnk, "forgot_lnk": forgot_lnk,
    }


def build_signup_page():
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    user_le = field("아이디")
    pw_le = field("비밀번호", echo=True)
    pw2_le = field("비밀번호 확인", echo=True)
    name_le = field("이름")
    bname_le = field("세례명")
    err = err_label(height=32)
    signup_btn = accent_btn("가입하기")

    for w in (user_le, pw_le, pw2_le, name_le, bname_le):
        lay.addWidget(w)
    lay.addWidget(err)
    lay.addWidget(signup_btn)
    lay.addSpacing(10)

    link_row = QHBoxLayout()
    link_row.addStretch()
    link_row.addWidget(muted("이미 계정이 있으신가요?"))
    link_row.addSpacing(4)
    login_lnk = link_btn("로그인")
    link_row.addWidget(login_lnk)
    link_row.addStretch()
    lay.addLayout(link_row)

    return page, {
        "user_le": user_le, "pw_le": pw_le, "pw2_le": pw2_le,
        "name_le": name_le, "bname_le": bname_le, "err": err,
        "signup_btn": signup_btn, "login_lnk": login_lnk,
    }


def build_find_id_page():
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 4, 0, 0)
    lay.setSpacing(8)

    name_le = field("이름")
    bname_le = field("세례명")
    err = err_label(height=32)
    err.setVisible(False)
    btn = accent_btn("아이디 찾기")

    lay.addWidget(name_le)
    lay.addWidget(bname_le)
    lay.addWidget(err)
    lay.addWidget(btn)
    lay.addSpacing(10)

    return page, {"name_le": name_le, "bname_le": bname_le, "err": err, "btn": btn}


def build_reset_pw_page():
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 4, 0, 0)
    lay.setSpacing(8)

    user_le = field("아이디")
    name_le = field("이름")
    bname_le = field("세례명")
    new_le = field("새 비밀번호", echo=True)
    new2_le = field("새 비밀번호 확인", echo=True)
    err = err_label(height=32)
    btn = accent_btn("비밀번호 재설정")

    for w in (user_le, name_le, bname_le, new_le, new2_le):
        lay.addWidget(w)
    lay.addWidget(err)
    lay.addWidget(btn)

    return page, {
        "user_le": user_le, "name_le": name_le, "bname_le": bname_le,
        "new_le": new_le, "new2_le": new2_le, "err": err, "btn": btn,
    }


def build_forgot_page():
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    tab_row = QHBoxLayout()
    tab_id_btn = QPushButton("아이디 찾기")
    tab_pw_btn = QPushButton("비밀번호 재설정")
    for btn in (tab_id_btn, tab_pw_btn):
        btn.setFixedHeight(34)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tab_row.addWidget(btn)
    lay.addLayout(tab_row)

    inner_stack = QStackedWidget()
    fi_page, fi = build_find_id_page()
    rp_page, rp = build_reset_pw_page()
    inner_stack.addWidget(fi_page)
    inner_stack.addWidget(rp_page)
    lay.addWidget(inner_stack)

    lay.addSpacing(4)
    back_row = QHBoxLayout()
    back_lnk = link_btn("로그인으로 돌아가기")
    back_row.addStretch()
    back_row.addWidget(back_lnk)
    back_row.addStretch()
    lay.addLayout(back_row)

    return page, {
        "tab_id_btn": tab_id_btn, "tab_pw_btn": tab_pw_btn,
        "inner_stack": inner_stack, "back_lnk": back_lnk,
        "fi": fi, "rp": rp,
    }
