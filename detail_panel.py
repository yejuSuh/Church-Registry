from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QGridLayout, QTabWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal

from constants import C
from ui_helpers import fv, mk_btn, shdr
from sacraments_tab import SacramentsTab
from move_records_tab import MoveRecordsTab


class DetailPanel(QWidget):
    edit_sig        = pyqtSignal(str)
    delete_sig      = pyqtSignal(str, bool)
    add_sig         = pyqtSignal(str, str)
    perm_delete_sig = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._l = QVBoxLayout(self)
        self._l.setContentsMargins(0, 0, 0, 0)
        self._l.setSpacing(0)
        self._current_tab = 0
        self.show_empty()

    def _clear(self):
        while self._l.count():
            it = self._l.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def show_empty(self):
        self._clear()
        w = QWidget(); w.setObjectName("card")
        l = QVBoxLayout(w)
        lbl = QLabel("← 교적을 선택하세요")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{C['muted']};font-size:15px;")
        l.addWidget(lbl)
        self._l.addWidget(w)

    def load(self, pno):
        p = self.db.get(pno)
        if not p:
            self.show_empty()
            return
        self._clear()

        v = lambda k: fv(p, k) or "—"
        is_del = v("delete_flag") == "Y"

        hdr = QWidget(); hdr.setObjectName("detail_hdr"); hdr.setFixedHeight(68)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 8, 16, 8)
        name_txt = f"{v('name')}  ({v('baptism_nm')})" if v("baptism_nm") != "—" else v("name")
        nl = QLabel(name_txt)
        nl.setStyleSheet("font-size:17px;font-weight:bold;")
        sl = QLabel(f"교적번호: {v('parishioner_no')}  |  관계: {v('relation')}  |  세대주: {v('host_nm')}")
        sl.setStyleSheet("color:#BDD7EE;font-size:10px;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;color:white;font-size:14px;"
            "border:none;border-radius:4px;padding:0;}"
            "QPushButton:hover{background:rgba(255,255,255,0.2);}"
        )
        close_btn.clicked.connect(self.show_empty)
        info_col = QVBoxLayout(); info_col.addWidget(nl); info_col.addWidget(sl)
        hl.addLayout(info_col); hl.addStretch(); hl.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop)
        self._l.addWidget(hdr)

        bb = QWidget(); bb.setObjectName("detail_btnbar"); bb.setFixedHeight(46)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(8, 6, 8, 6); bbl.setSpacing(6)
        eb     = mk_btn("✏️  수정", "btn_accent")
        ab     = mk_btn("👤+  가족 추가", "btn_success")
        db_btn = mk_btn("♻️  복원" if is_del else "🗑  삭제",
                        "btn_accent" if is_del else "btn_danger")
        eb.clicked.connect(lambda: self.edit_sig.emit(pno))
        ab.clicked.connect(lambda: self.add_sig.emit(v("host_nm"), pno))
        db_btn.clicked.connect(lambda: self.delete_sig.emit(pno, is_del))
        bbl.addWidget(eb); bbl.addWidget(ab); bbl.addWidget(db_btn)
        if is_del:
            pd_btn = mk_btn("🗑  영구 삭제", "btn_danger")
            pd_btn.clicked.connect(lambda: self.perm_delete_sig.emit(pno))
            bbl.addWidget(pd_btn)
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
        r2("교적번호", v("parishioner_no"), "세례명",    v("baptism_nm"))
        r2("세대주",   v("host_nm"),        "관계",      v("relation"))
        r2("생년월일", v("personal_no")[:6] if v("personal_no") != "—" else "—", "축일", v("baptism_day"))
        r2("등록일",   v("registion_date"), "이전 교구", v("pre_parish_nm"))

        flags = []
        if v("etemal") == "Y":          flags.append("✅ 영원한 교적")
        if v("money_duty_flag") == "Y": flags.append("💰 교무금")
        if v("lazy_flag") == "Y":       flags.append("😴 냉담자")
        if v("alone_flag") == "Y":      flags.append("🏠 독거")
        if v("delete_flag") == "Y":     flags.append("🗑 삭제됨")
        if flags:
            fl = QLabel("  ".join(flags)); fl.setObjectName("mu")
            grid.addWidget(fl, r, 0, 1, 4); r += 1

        sh("📞  연락처")
        r2("집 전화",   v("tel_home"),   "휴대폰",  v("tel_hp"))
        r2("직장 전화", v("tel_office"), "주소",    v("address"))
        r2("상세 주소", v("address_no"))

        sh("✝  세례 정보")
        r2("세례일",    v("baptism_date"),      "세례번호",  v("baptism_no"))
        r2("세례 교구", v("baptism_parish_nm"), "세례 성당", v("baptism_church"))

        sh("🕊  견진 정보")
        r2("견진일", v("sacrament_date"), "견진 교구", v("sacrament_parish_nm"))

        if v("office_nm") != "—" or v("job_kind") != "—":
            sh("💼  직장")
            r2("직장명", v("office_nm"), "직종", v("job_kind"))

        if v("personal_memo") != "—":
            sh("📝  메모")
            ml = QLabel(v("personal_memo")); ml.setObjectName("fv"); ml.setWordWrap(True)
            grid.addWidget(ml, r, 0, 1, 4); r += 1

        members = self.db.household(v("host_nm"), exclude=pno)
        if members:
            sh(f"👨‍👩‍👧  같은 세대 ({len(members)}명)")
            tbl = QTableWidget(len(members), 4)
            tbl.setHorizontalHeaderLabels(["이름", "세례명", "관계", "교적번호"])
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.horizontalHeader().setStyleSheet(
                "QHeaderView::section{"
                f"background:transparent;color:{C['muted']};"
                "font-size:11px;font-weight:normal;"
                "border:none;border-bottom:1px solid #D0D8E4;padding:2px 6px;}"
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
                for j, key in enumerate(["name", "baptism_nm", "relation", "parishioner_no"]):
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
