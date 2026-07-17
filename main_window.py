import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QShortcut, QKeySequence

from constants import APP_TITLE, C, DB_PATH
from session import session
from ui_helpers import mk_btn
from parishioner_form import ParishionerForm
from detail_panel import DetailPanel
from list_view import ListView
from stats_view import StatsView
from user_mgmt_view import UserMgmtView


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle(APP_TITLE)
        self.resize(1300, 820)
        self.setMinimumSize(960, 600)

        root = QWidget(); self.setCentralWidget(root)
        rl = QHBoxLayout(root); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sb = QWidget(); sb.setObjectName("sidebar"); sb.setFixedWidth(196)
        sbl = QVBoxLayout(sb); sbl.setContentsMargins(8, 16, 8, 12); sbl.setSpacing(4)
        for txt, style in [
            ("✝",                     "font-size:28px;color:white;background:transparent;"),
            ("교적 관리",              "font-size:14px;font-weight:bold;color:white;background:transparent;"),
            ("Boston Korean Catholic", "font-size:9px;color:#8EAFD4;background:transparent;"),
        ]:
            l = QLabel(txt)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setStyleSheet(style)
            sbl.addWidget(l)

        # a single quiet flourish under the wordmark -- a seal-ink rule,
        # like the gilt line under a ledger's spine title
        rule = QWidget(); rule.setFixedHeight(2)
        rule.setStyleSheet(f"background:{C['accent']};border-radius:1px;")
        rule_row = QHBoxLayout(); rule_row.setContentsMargins(48, 8, 48, 0)
        rule_row.addWidget(rule)
        sbl.addLayout(rule_row)
        sbl.addSpacing(14)

        self.nav_list  = QPushButton("👥  교적 목록")
        self.nav_stats = QPushButton("📊  현황 통계")
        for nb in [self.nav_list, self.nav_stats]:
            nb.setObjectName("nav_btn")
            nb.setCursor(Qt.CursorShape.PointingHandCursor)
            sbl.addWidget(nb)

        # admin-only nav
        self.nav_users = None
        if session.user_level == "admin":
            self.nav_users = QPushButton("👤  계정 관리")
            self.nav_users.setObjectName("nav_btn")
            self.nav_users.setCursor(Qt.CursorShape.PointingHandCursor)
            sbl.addWidget(self.nav_users)

        sbl.addSpacing(12)
        self._count_lbl = QLabel()
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_lbl.setStyleSheet("font-size:11px;color:#8EAFD4;background:transparent;")
        sbl.addWidget(self._count_lbl)

        sbl.addStretch()
        user_lbl = QLabel(f"👤 {session.name} ({session.baptism_name})")
        user_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_lbl.setStyleSheet("font-size:12px;color:#8EAFD4;background:transparent;")
        user_lbl.setWordWrap(True)
        sbl.addWidget(user_lbl)
        # sbl.addSpacing(2)
        # db_lbl = QLabel(os.path.basename(DB_PATH))
        # db_lbl.setStyleSheet("font-size:8px;color:#5A7FA8;background:transparent;")
        # db_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # db_lbl.setWordWrap(True)
        # sbl.addWidget(db_lbl)
        rl.addWidget(sb)

        # ── Main stack ───────────────────────────────────────────────────────
        self.stack = QStackedWidget(); rl.addWidget(self.stack, 1)

        # index 0 — parishioner list + detail
        self.list_view   = ListView(db)
        self.detail_view = DetailPanel(db)
        sp = QSplitter(Qt.Orientation.Horizontal)
        sp.addWidget(self.list_view); sp.addWidget(self.detail_view)
        sp.setSizes([620, 380]); sp.setHandleWidth(1)
        lp = QWidget()
        lpl = QVBoxLayout(lp); lpl.setContentsMargins(0, 0, 0, 0); lpl.setSpacing(0)
        lpl.addWidget(sp)
        self.stack.addWidget(lp)

        # index 1 — stats
        self.stats_view = StatsView(db)
        self.stack.addWidget(self.stats_view)

        # index 2 — user management (always in stack; nav only visible to admins)
        self.user_mgmt_view = UserMgmtView(db)
        self.stack.addWidget(self.user_mgmt_view)

        # ── Signals ──────────────────────────────────────────────────────────
        self.nav_list.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.nav_stats.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        if self.nav_users:
            self.nav_users.clicked.connect(lambda: self._open_user_mgmt())
        self.list_view.add_btn.clicked.connect(self._add)
        self.list_view.row_selected.connect(self.detail_view.load)
        self.detail_view.edit_sig.connect(self._edit)
        self.detail_view.delete_sig.connect(self._delete)
        self.detail_view.add_sig.connect(self._add_member)

        # ── Keyboard shortcuts ────────────────────────────────────────────────
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._add)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._focus_search)
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self.list_view.export_btn.click)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._clear_search)

        settings = QSettings("BostonKoreanCatholic", "ChurchRegistry")
        geom = settings.value("window/geometry")
        if geom:
            self.restoreGeometry(geom)

        self._reload()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _open_user_mgmt(self):
        if session.user_level != "admin":
            return
        self.user_mgmt_view._load()   # refresh data each time
        self.stack.setCurrentIndex(2)

    def _reload(self):
        self.list_view.load()
        self._refresh_count()

    def _refresh_count(self):
        self._count_lbl.setText(f"활성 교인  {self.db.stats()['active']}명")

    def _focus_search(self):
        self.stack.setCurrentIndex(0)
        self.list_view.q_le.setFocus()

    def _clear_search(self):
        self.stack.setCurrentIndex(0)
        self.list_view.q_le.clear()

    def closeEvent(self, event):
        QSettings("BostonKoreanCatholic", "ChurchRegistry").setValue(
            "window/geometry", self.saveGeometry())
        super().closeEvent(event)

    # ── CRUD actions ──────────────────────────────────────────────────────────

    def _add(self):
        ParishionerForm(self, self.db, on_save=self._reload).exec()

    def _edit(self, pno):
        def refresh():
            self._reload()
            self.detail_view.load(pno)
        ParishionerForm(self, self.db, pno=pno, on_save=refresh).exec()

    def _add_member(self, host, ref_pno):
        area = ref_pno.split("-")[0] if "-" in ref_pno else "00112"
        def refresh():
            self._reload()
            self.detail_view.load(ref_pno)
        ParishionerForm(self, self.db, prefill_host=host, prefill_area=area, on_save=refresh).exec()

    def _delete(self, pno):
        msg = f"교적을 삭제하시겠습니까?\n{pno}\n\n이 작업은 되돌릴 수 없습니다."
        if QMessageBox.question(self, "삭제 확인", msg) == QMessageBox.StandardButton.Yes:
            self.db.hard_delete(pno)
            self._reload()
            self.detail_view.show_empty()
