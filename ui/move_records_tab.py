from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QGridLayout,
)

from core.constants import C
from ui.ui_helpers import fv, mk_btn, shdr
from forms.sacrament_forms import MoveInForm, MoveOutForm


class MoveRecordsTab(QWidget):
    def __init__(self, db, pno):
        super().__init__()
        self.db = db; self.pno = pno
        self._name = ""
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(self._scroll, 1)
        self._load()

    def reload(self):
        self._load()

    def _load(self):
        p = self.db.get(self.pno)
        self._name = fv(p, "name") if p else ""

        body = QWidget(); body.setObjectName("card")
        lay = QVBoxLayout(body); lay.setContentsMargins(12, 8, 12, 16); lay.setSpacing(10)
        self._build_movein(lay)
        self._build_moveout(lay)
        lay.addStretch()
        self._scroll.setWidget(body)

    def _open(self, cls):
        cls(self, self.db, self.pno, self._name, on_save=self.reload).exec()

    def _build_movein(self, lay):
        hdr = QWidget()
        hl = QHBoxLayout(hdr); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(6)
        hl.addWidget(shdr("📥  전입 기록")); hl.addStretch()
        btn = mk_btn("+ 추가", "btn_success")
        btn.setFixedHeight(26); btn.setFixedWidth(68)
        btn.clicked.connect(lambda: self._open(MoveInForm))
        hl.addWidget(btn)
        lay.addWidget(hdr)

        records = self.db.get_movein_records(self.pno)
        if not records:
            lbl = QLabel("  기록 없음"); lbl.setObjectName("mu"); lay.addWidget(lbl)
            return
        for rec in records:
            pairs = [
                ("전입일",    fv(rec, "date")),
                ("이전 교구", fv(rec, "former_diocese")),
                ("이전 성당", fv(rec, "former_parish")),
            ]
            lay.addWidget(self._record_card(pairs))

    def _build_moveout(self, lay):
        hdr = QWidget()
        hl = QHBoxLayout(hdr); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(6)
        hl.addWidget(shdr("📤  전출 기록")); hl.addStretch()
        btn = mk_btn("+ 추가", "btn_success")
        btn.setFixedHeight(26); btn.setFixedWidth(68)
        btn.clicked.connect(lambda: self._open(MoveOutForm))
        hl.addWidget(btn)
        lay.addWidget(hdr)

        records = self.db.get_moveout_records(self.pno)
        if not records:
            lbl = QLabel("  기록 없음"); lbl.setObjectName("mu"); lay.addWidget(lbl)
            return
        for rec in records:
            pairs = [
                ("전출일",  fv(rec, "date")),
                ("새 교구", fv(rec, "dest_diocese")),
                ("새 성당", fv(rec, "dest_parish")),
            ]
            lay.addWidget(self._record_card(pairs))

    def _record_card(self, pairs):
        pairs = [(l, v) for l, v in pairs if v and v not in ("—", "")]
        card = QWidget()
        card.setStyleSheet(f"background:{C['header']};border-radius:4px;")
        g = QGridLayout(card); g.setContentsMargins(10, 6, 10, 6)
        g.setHorizontalSpacing(12); g.setVerticalSpacing(3)
        g.setColumnStretch(1, 2); g.setColumnStretch(3, 2)
        row, col = 0, 0
        for lbl_txt, val_txt in pairs:
            lw = QLabel(lbl_txt); lw.setObjectName("fl")
            vw = QLabel(val_txt); vw.setObjectName("fv"); vw.setWordWrap(True)
            g.addWidget(lw, row, col * 2); g.addWidget(vw, row, col * 2 + 1)
            col += 1
            if col >= 2: col = 0; row += 1
        return card
