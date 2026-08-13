import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QShortcut, QKeySequence

from core.constants import APP_TITLE, C, DB_PATH
from core.session import session
from ui.ui_helpers import mk_btn
from forms.parishioner_form import ParishionerForm
from ui.detail_panel import DetailPanel
from ui.list_view import ListView
from ui.stats_view import StatsView
from ui.user_mgmt_view import UserMgmtView
from ui.sacrament_entry_view import SacramentEntryView


class MainWindow(QMainWindow):
    """Main application window: sidebar navigation, parishioner list/detail splitter, stats, and user management."""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.logged_out = False   # church_app.py checks this to re-show the login page
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
            ("보스턴 한인 성당",              "font-size:14px;font-weight:bold;color:white;background:transparent;"),
            ("St. Antoine Daveluy Korean Parish", "font-size:9px;color:#8EAFD4;background:transparent;"),
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

        # visible to everyone; the view itself limits non-admins to their own account
        self.nav_users = QPushButton("👤  계정 관리")
        self.nav_users.setObjectName("nav_btn")
        self.nav_users.setCursor(Qt.CursorShape.PointingHandCursor)
        sbl.addWidget(self.nav_users)

        sbl.addSpacing(8)
        rule2 = QWidget(); rule2.setFixedHeight(1)
        rule2.setStyleSheet(f"background:rgba(255,255,255,0.08);")
        sbl.addWidget(rule2)
        sbl.addSpacing(8)

        self.nav_sacrament = QPushButton("✚  성사 추가")
        self.nav_sacrament.setObjectName("nav_btn")
        self.nav_sacrament.setCursor(Qt.CursorShape.PointingHandCursor)
        sbl.addWidget(self.nav_sacrament)

        sbl.addSpacing(12)
        self._count_lbl = QLabel()
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_lbl.setStyleSheet("font-size:11px;color:#8EAFD4;background:transparent;")
        sbl.addWidget(self._count_lbl)

        sbl.addStretch()
        self._user_lbl = QLabel()
        self._user_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._user_lbl.setStyleSheet("font-size:12px;color:#8EAFD4;background:transparent;")
        self._user_lbl.setWordWrap(True)
        sbl.addWidget(self._user_lbl)
        self._refresh_user_lbl()

        self.logout_btn = QPushButton("🚪  로그아웃")
        self.logout_btn.setObjectName("nav_btn")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sbl.addWidget(self.logout_btn)
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

        # index 3 — sacrament entry (independent of selected member)
        self.sacrament_entry_view = SacramentEntryView(db)
        self.stack.addWidget(self.sacrament_entry_view)

        # ── Signals ──────────────────────────────────────────────────────────
        self.nav_list.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.nav_stats.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.nav_users.clicked.connect(lambda: self._open_user_mgmt())
        self.nav_sacrament.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.list_view.add_btn.clicked.connect(self._add)
        self.list_view.row_selected.connect(self.detail_view.load)
        self.detail_view.edit_sig.connect(self._edit)
        self.detail_view.delete_sig.connect(self._delete)
        self.logout_btn.clicked.connect(lambda: self._logout())
        self.user_mgmt_view.session_changed.connect(self._refresh_user_lbl)
        # own account was deactivated/deleted -- the session is no longer
        # valid, so skip the confirmation and go straight back to login
        self.user_mgmt_view.logout_requested.connect(lambda: self._logout(confirm=False))

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

    def _refresh_user_lbl(self):
        self._user_lbl.setText(f"👤 {session.name} ({session.baptism_name})")

    def _logout(self, confirm=True):
        if confirm and QMessageBox.question(
            self, "로그아웃", "로그아웃 하시겠습니까?"
        ) != QMessageBox.StandardButton.Yes:
            return
        session.username = session.name = session.baptism_name = session.user_level = ""
        self.logged_out = True
        self.close()

    def _open_user_mgmt(self):
        self.user_mgmt_view._load()   # refresh data each time
        self.stack.setCurrentIndex(2)

    def _reload(self):
        self.list_view.load()
        # self._refresh_count()

    # def _refresh_count(self):
    #     self._count_lbl.setText(f"활성 교인  {self.db.stats()['active']}명")

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

    def _delete(self, pno):
        msg = f"교적을 삭제하시겠습니까?\n{pno}\n\n이 작업은 되돌릴 수 없습니다."
        if QMessageBox.question(self, "삭제 확인", msg) == QMessageBox.StandardButton.Yes:
            self.db.hard_delete(pno)
            self._reload()
            self.detail_view.show_empty()
