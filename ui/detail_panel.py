from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QGridLayout, QTabWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.constants import C, BTN_RADIUS
from ui.ui_helpers import fv, mk_btn, shdr, mk_regno
from ui.sacraments_tab import SacramentsTab
from ui.move_records_tab import MoveRecordsTab
from forms.household_dialog import HouseholdDialog


class DetailPanel(QWidget):
    """Right-hand panel showing a single member's info, sacraments, move records, family, and household tabs."""

    edit_sig   = pyqtSignal(str)
    delete_sig = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._l = QVBoxLayout(self)
        self._l.setContentsMargins(0, 0, 0, 0)
        self._l.setSpacing(0)
        self._current_tab = 0
        self._pno = None
        self.show_empty()

    def _clear(self):
        while self._l.count():
            it = self._l.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def show_empty(self):
        self._pno = None
        self._clear()
        w = QWidget(); w.setObjectName("card")
        l = QVBoxLayout(w)
        lbl = QLabel("← 교적을 선택하세요")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{C['muted']};font-size:15px;")
        l.addWidget(lbl)
        self._l.addWidget(w)

    def _open_household(self, pno):
        HouseholdDialog(self, self.db, pno, on_change=None).exec()
        self.load(pno)

    def load(self, pno):
        p = self.db.get(pno)
        if not p:
            self.show_empty()
            return
        self._pno = pno
        self._clear()

        v = lambda k: fv(p, k) or "—"
        is_inactive = bool(p["is_inactive"])

        hdr = QWidget(); hdr.setObjectName("detail_hdr"); hdr.setFixedHeight(68)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 8, 16, 8)
        bname = v("baptismal_name")
        name_en = v("name_english")  # alias from _MEMBER_SELECT
        name_txt = v("name")
        if name_en != "—":
            name_txt += f"  {name_en}"
        if bname != "—":
            name_txt += f"  ({bname})"
        nl = QLabel(name_txt)
        nl.setStyleSheet("font-size:17px;font-weight:bold;")
        meta_row = QHBoxLayout(); meta_row.setContentsMargins(0, 2, 0, 0); meta_row.setSpacing(8)
        meta_row.addWidget(mk_regno(v('display_id')))
        meta_txt = QLabel(f"관계: {v('relation')}  |  세대주: {v('head_of_household')}")
        meta_txt.setStyleSheet("color:#BDD7EE;font-size:10px;background:transparent;")
        meta_row.addWidget(meta_txt); meta_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;color:white;font-size:14px;"
            f"border:none;border-radius:{BTN_RADIUS};padding:0;}}"
            "QPushButton:hover{background:rgba(255,255,255,0.2);}"
        )
        close_btn.clicked.connect(self.show_empty)
        info_col = QVBoxLayout(); info_col.addWidget(nl); info_col.addLayout(meta_row)
        hl.addLayout(info_col); hl.addStretch(); hl.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop)
        self._l.addWidget(hdr)

        bb = QWidget(); bb.setObjectName("detail_btnbar"); bb.setFixedHeight(46)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(8, 6, 8, 6); bbl.setSpacing(6)
        eb     = mk_btn("✏️  수정", "btn_accent")
        ab     = mk_btn("🏠  세대 관리", "btn_success")
        db_btn = mk_btn("🗑  삭제", "btn_danger")
        eb.clicked.connect(lambda: self.edit_sig.emit(pno))
        ab.clicked.connect(lambda: self._open_household(pno))
        db_btn.clicked.connect(lambda: self.delete_sig.emit(pno))
        bbl.addWidget(eb); bbl.addWidget(ab); bbl.addWidget(db_btn)
        bbl.addStretch()
        self._l.addWidget(bb)

        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(); body.setObjectName("card")
        grid = QGridLayout(body)
        grid.setContentsMargins(12, 8, 12, 16)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        sc.setWidget(body)

        r = 0

        def sh(t):
            nonlocal r
            grid.addWidget(shdr(t), r, 0, 1, 4); r += 1

        def r2(l1, v1, l2="", v2=""):
            nonlocal r
            lw = QLabel(l1); lw.setObjectName("fl")
            vw = QLabel(v1); vw.setObjectName("fv"); vw.setWordWrap(True)
            grid.addWidget(lw, r, 0); grid.addWidget(vw, r, 1)
            if l2:
                lw2 = QLabel(l2); lw2.setObjectName("fl")
                vw2 = QLabel(v2); vw2.setObjectName("fv"); vw2.setWordWrap(True)
                grid.addWidget(lw2, r, 2); grid.addWidget(vw2, r, 3)
            r += 1

        sh("📋  기본 정보")
        r2("교적번호", v("display_id"),         "세례명",  v("baptismal_name"))
        r2("세대주",   v("head_of_household"), "관계",    v("relation"))
        r2("구역",     v("district"),           "성별",    {"M": "남", "F": "여"}.get(fv(p, "sex"), "—"))
        r2("생년월일", v("birth_date"))
        r2("주소",     v("address"),            "우편번호", v("postal_code"))
        r2("전화",     v("phone"),              "이메일",  v("email"))
        r2("직업",     v("occupation"))

        # flags = []
        # if is_inactive:                    flags.append("😴 냉담자")
        # if v("dues_paying") == "1":        flags.append("💰 교무금")
        # if flags:
        #     fl = QLabel("  ".join(flags)); fl.setObjectName("mu")
        #     grid.addWidget(fl, r, 0, 1, 4); r += 1

        sh("💰  교무금")
        dues_label = "납부" if v("dues_paying") == "1" else "미납"
        r2("납부 여부", dues_label, "월 교무금", v("monthly_dues"))
        r2("시작일",    v("dues_start"),  "최근 납부", v("dues_last_paid"))

        if v("notes") != "—":
            sh("📝  메모")
            ml = QLabel(v("notes")); ml.setObjectName("fv"); ml.setWordWrap(True)
            grid.addWidget(ml, r, 0, 1, 4); r += 1

        members = self.db.household(p["household_id"], exclude=pno)
        if members:
            sh(f"👨‍👩‍👧  세대구성원")
            tbl = QTableWidget(len(members), 4)
            tbl.setHorizontalHeaderLabels(["이름", "세례명", "관계", "교적번호"])
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.horizontalHeader().setStyleSheet(
                "QHeaderView::section{"
                f"background:transparent;color:{C['muted']};"
                "font-size:11px;font-weight:normal;"
                f"border:none;border-bottom:1px solid {C['border']};padding:2px 6px;}}"
            )
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tbl.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            row_h = 24
            hdr_h = tbl.horizontalHeader().sizeHint().height()
            tbl.verticalHeader().setDefaultSectionSize(row_h)
            tbl.setFixedHeight(hdr_h + len(members) * row_h + 2)
            for i, m in enumerate(members):
                for j, key in enumerate(["name", "baptismal_name", "relation", "display_id"]):
                    tbl.setItem(i, j, QTableWidgetItem(str(m[key] or "").strip()))
            grid.addWidget(tbl, r, 0, 1, 4); r += 1

        grid.setRowStretch(r, 1)

        tabs = QTabWidget()
        tabs.addTab(sc, "기본 정보")
        tabs.addTab(SacramentsTab(self.db, pno), "성사 기록")
        tabs.addTab(MoveRecordsTab(self.db, pno), "이동 기록")
        tabs.setCurrentIndex(self._current_tab)
        tabs.currentChanged.connect(lambda i: setattr(self, '_current_tab', i))
        self._l.addWidget(tabs, 1)
