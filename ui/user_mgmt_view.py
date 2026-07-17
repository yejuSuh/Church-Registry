from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QGridLayout, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.constants import C
from core.session import session
from ui.ui_helpers import mk_btn, mk_combo, vbox_field


class UserFormDialog(QDialog):
    def __init__(self, parent, db, user=None, on_save=None):
        super().__init__(parent)
        self.db = db
        self.user = user       # None → add mode, dict → edit mode
        self.on_save = on_save
        is_edit = user is not None

        self.setWindowTitle("계정 수정" if is_edit else "계정 추가")
        self.setModal(True)
        self.resize(420, 300)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        g = QGridLayout()
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(8)

        self._user_le = QLineEdit(user["username"] if is_edit else "")
        if is_edit:
            self._user_le.setReadOnly(True)
            self._user_le.setStyleSheet(f"background:{C['header']};color:{C['muted']};")
        g.addWidget(vbox_field("아이디", self._user_le), 0, 0, 1, 2)

        self._pw_le = QLineEdit()
        self._pw_le.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_le.setPlaceholderText("변경 시에만 입력" if is_edit else "")
        g.addWidget(vbox_field("비밀번호" + (" (선택)" if is_edit else ""), self._pw_le), 1, 0)

        self._pw2_le = QLineEdit()
        self._pw2_le.setEchoMode(QLineEdit.EchoMode.Password)
        g.addWidget(vbox_field("비밀번호 확인", self._pw2_le), 1, 1)

        self._name_le = QLineEdit(user["name"] if is_edit else "")
        g.addWidget(vbox_field("이름", self._name_le), 2, 0)

        self._bname_le = QLineEdit(user["baptism_name"] if is_edit else "")
        g.addWidget(vbox_field("세례명", self._bname_le), 2, 1)

        self._level_cb = mk_combo(["staff", "admin"], user["user_level"] if is_edit else "staff")
        if session.user_level != "admin":
            # non-admins only ever edit their own account and must not be
            # able to promote themselves
            self._level_cb.setEnabled(False)
        g.addWidget(vbox_field("권한", self._level_cb), 3, 0)

        lay.addLayout(g)

        self._err = QLabel("")
        self._err.setStyleSheet(f"color:{C['danger']};font-size:11px;background:transparent;")
        lay.addWidget(self._err)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel = mk_btn("취소", "btn_muted")
        save   = mk_btn("저장", "btn_accent")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

    def _save(self):
        username = self._user_le.text().strip()
        password = self._pw_le.text()
        password2 = self._pw2_le.text()
        name  = self._name_le.text().strip()
        bname = self._bname_le.text().strip()
        level = self._level_cb.currentText()
        is_edit = self.user is not None

        if not is_edit and not username:
            self._err.setText("아이디를 입력하세요."); return
        if not name:
            self._err.setText("이름을 입력하세요."); return
        if not bname:
            self._err.setText("세례명을 입력하세요."); return
        if not is_edit and not password:
            self._err.setText("비밀번호를 입력하세요."); return
        if password and password != password2:
            self._err.setText("비밀번호가 일치하지 않습니다."); return
        if not is_edit and self.db.username_exists(username):
            self._err.setText("아이디가 이미 사용중입니다."); return

        try:
            if is_edit:
                self.db.update_user(self.user["username"], name, bname, level, password or None)
            else:
                self.db.create_user(username, password, name, bname, level)
            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            self._err.setText(str(e))


class UserMgmtView(QWidget):
    _COLS    = ["아이디", "이름", "세례명", "권한", "상태", "마지막 로그인", "작업"]
    _COL_W   = [120, 100, 100, 70, 65, 150]   # last col stretches

    session_changed  = pyqtSignal()   # own name/baptism_name edited
    logout_requested = pyqtSignal()   # own account deactivated or deleted

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        tb = QWidget(); tb.setObjectName("toolbar"); tb.setFixedHeight(52)
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(14, 8, 14, 8)
        title = QLabel("계정 관리")
        title.setStyleSheet(
            f"font-size:15px;font-weight:bold;color:{C['text']};background:transparent;"
        )
        tbl.addWidget(title); tbl.addStretch()
        if session.user_level == "admin":
            add_btn = mk_btn("+ 계정 추가", "btn_accent")
            add_btn.clicked.connect(self._add)
            tbl.addWidget(add_btn)
        lay.addWidget(tb)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self._COLS))
        self._table.setHorizontalHeaderLabels(self._COLS)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)
        for i, w in enumerate(self._COL_W):
            self._table.setColumnWidth(i, w)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        lay.addWidget(self._table, 1)

        self._load()

    def _load(self):
        users = self.db.list_users()
        self._table.setRowCount(len(users))
        for i, u in enumerate(users):
            self._table.setRowHeight(i, 36)
            active = bool(u["is_active"])
            cells = [
                u["username"],
                u["name"],
                u["baptism_name"],
                "관리자" if u["user_level"] == "admin" else "일반",
                "활성" if active else "비활성",
                u["last_login"] or "—",
            ]
            for j, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if not active:
                    item.setForeground(QColor("#AAAAAA"))
                self._table.setItem(i, j, item)

            self._table.setCellWidget(i, 6, self._action_cell(dict(u)))

    def _action_cell(self, u):
        cell = QWidget()
        # non-admins may only act on their own account -- other rows get an
        # empty cell so the buttons aren't even visible
        if session.user_level != "admin" and u["username"] != session.username:
            return cell

        hl = QHBoxLayout(cell)
        hl.setContentsMargins(4, 2, 4, 2)
        hl.setSpacing(4)

        active = bool(u["is_active"])

        edit_btn = mk_btn("수정", "btn_muted")
        edit_btn.setFixedHeight(26)
        edit_btn.clicked.connect(lambda: self._edit(u))

        toggle_btn = mk_btn(
            "비활성화" if active else "활성화",
            "btn_muted" if active else "btn_success",
        )
        toggle_btn.setFixedHeight(26)
        toggle_btn.clicked.connect(lambda: self._toggle(u["username"], active))

        del_btn = mk_btn("삭제", "btn_danger")
        del_btn.setFixedHeight(26)
        del_btn.clicked.connect(lambda: self._delete(u["username"]))

        hl.addWidget(edit_btn)
        hl.addWidget(toggle_btn)
        hl.addWidget(del_btn)
        hl.addStretch()
        return cell

    # ── Actions ──────────────────────────────────────────────────────────────

    def _add(self):
        UserFormDialog(self, self.db, on_save=self._load).exec()

    def _edit(self, user):
        def done():
            self._load()
            if user["username"] == session.username:
                u = self.db.get_user(session.username)
                session.name         = u["name"]
                session.baptism_name = u["baptism_name"]
                self.session_changed.emit()
        UserFormDialog(self, self.db, user=user, on_save=done).exec()

    def _toggle(self, username, currently_active):
        is_self = username == session.username
        if currently_active:
            if is_self and QMessageBox.question(
                self, "계정 비활성화",
                "본인 계정을 비활성화하면 로그아웃되며 다시 로그인할 수 없습니다.\n계속하시겠습니까?",
            ) != QMessageBox.StandardButton.Yes:
                return
            self.db.deactivate_user(username)
            if is_self:
                self.logout_requested.emit()
                return
        else:
            self.db.activate_user(username)
        self._load()

    def _delete(self, username):
        is_self = username == session.username
        msg = (
            "본인 계정을 영구 삭제하시겠습니까?\n삭제 후 즉시 로그아웃됩니다."
            if is_self else f"'{username}' 계정을 영구 삭제하시겠습니까?"
        )
        if QMessageBox.question(self, "계정 삭제", msg) != QMessageBox.StandardButton.Yes:
            return
        if not self.db.delete_user(username):
            QMessageBox.warning(self, "삭제 불가", "마지막 관리자 계정은 삭제할 수 없습니다.")
            return
        if is_self:
            self.logout_requested.emit()
            return
        self._load()
