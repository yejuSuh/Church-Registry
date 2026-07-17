from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QDialog, QMessageBox,
)
from PyQt6.QtCore import Qt

from constants import C
from ui_helpers import fv, mk_btn, mk_entry, vbox_field, shdr


class PersonPicker(QWidget):
    """Search-or-free-text picker for an "other person" field on a sacrament
    intake form (godparent, sponsor, father, mother). Type a name to search
    existing members; click a match to link its member_id and pre-fill the
    name fields, or just type Korean/English/baptismal name as free text if
    the person isn't a member -- most godparents/parents won't be.

    "Match" means: the staff member typed a name, saw it in the search
    results, and clicked it. There's no automatic/fuzzy matching -- the form
    always keeps the free-text name the applicant wrote, and the FK is only
    set by an explicit human pick.
    """

    def __init__(self, db, title, show_english=True, show_phone=False):
        super().__init__()
        self.db = db
        self.member_id = None

        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(4)
        lay.addWidget(shdr(title))

        search_row = QWidget()
        sl = QHBoxLayout(search_row); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(6)
        self.search_e = mk_entry()
        self.search_e.setPlaceholderText("교인 검색 (이름/세례명) — 없으면 아래에 직접 입력")
        self.clear_btn = mk_btn("연결 해제", "btn_muted")
        self.clear_btn.setFixedWidth(84)
        self.clear_btn.setVisible(False)
        sl.addWidget(self.search_e, 1); sl.addWidget(self.clear_btn)
        lay.addWidget(search_row)

        self.results = QListWidget()
        self.results.setFixedHeight(88)
        self.results.setVisible(False)
        lay.addWidget(self.results)

        self.match_lbl = QLabel("")
        self.match_lbl.setObjectName("mu")
        self.match_lbl.setVisible(False)
        lay.addWidget(self.match_lbl)

        fields_row = QWidget()
        fl = QHBoxLayout(fields_row); fl.setContentsMargins(0, 0, 0, 0); fl.setSpacing(10)
        self.kr_e = mk_entry()
        fl.addWidget(vbox_field("이름 (한글)", self.kr_e, C['card']), 1)
        self.en_e = None
        if show_english:
            self.en_e = mk_entry()
            fl.addWidget(vbox_field("이름 (영문)", self.en_e, C['card']), 1)
        self.bn_e = mk_entry()
        fl.addWidget(vbox_field("세례명", self.bn_e, C['card']), 1)
        self.phone_e = None
        if show_phone:
            self.phone_e = mk_entry()
            fl.addWidget(vbox_field("전화", self.phone_e, C['card']), 1)
        lay.addWidget(fields_row)

        self.search_e.textChanged.connect(self._on_search)
        self.results.itemClicked.connect(self._on_pick)
        self.clear_btn.clicked.connect(self._on_clear)

    def _on_search(self, text):
        text = text.strip()
        if not text or self.member_id:
            self.results.setVisible(False)
            return
        rows = self.db.search_people(text)
        self.results.clear()
        for r in rows:
            label = f"{fv(r, 'display_id')}  {fv(r, 'name')}"
            bn = fv(r, 'baptismal_name')
            if bn:
                label += f" ({bn})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, r)
            self.results.addItem(item)
        self.results.setVisible(bool(rows))

    def _on_pick(self, item):
        r = item.data(Qt.ItemDataRole.UserRole)
        self.member_id = r["member_id"]
        self.kr_e.setText(fv(r, "name"))
        if self.en_e:
            self.en_e.setText(fv(r, "name_english"))
        self.bn_e.setText(fv(r, "baptismal_name"))
        if self.phone_e:
            self.phone_e.setText(fv(r, "phone_cell") or fv(r, "phone_home"))
        self.search_e.blockSignals(True)
        self.search_e.setText(fv(r, "display_id"))
        self.search_e.setReadOnly(True)
        self.search_e.blockSignals(False)
        self.results.setVisible(False)
        self.match_lbl.setText(f"✓ 교적 연결됨: {fv(r, 'display_id')}")
        self.match_lbl.setVisible(True)
        self.clear_btn.setVisible(True)

    def _on_clear(self):
        self.member_id = None
        self.search_e.blockSignals(True)
        self.search_e.clear()
        self.search_e.setReadOnly(False)
        self.search_e.blockSignals(False)
        self.match_lbl.setVisible(False)
        self.clear_btn.setVisible(False)

    def data(self, prefix):
        """Return a dict of {prefix}_member_id / {prefix}_name_korean / etc,
        matching the baptism/confirmation table's column naming convention."""
        d = {
            f"{prefix}_member_id": self.member_id,
            f"{prefix}_name_korean": self.kr_e.text().strip() or None,
            f"{prefix}_baptismal_name": self.bn_e.text().strip() or None,
        }
        if self.en_e:
            d[f"{prefix}_name_english"] = self.en_e.text().strip() or None
        if self.phone_e:
            d[f"{prefix}_phone"] = self.phone_e.text().strip() or None
        return d

    def has_data(self):
        return bool(self.member_id or self.kr_e.text().strip())


class WeddingMatchDialog(QDialog):
    """Small chooser listing existing `wedding` rows that might match the
    applicant's marriage, so the adult confirmation/initiation intake forms
    don't blindly create a duplicate wedding record every time."""

    def __init__(self, parent, db, name, member_id=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("기존 혼인기록 찾기")
        self.resize(420, 320)
        self.setModal(True)
        self.chosen = None

        lay = QVBoxLayout(self); lay.setContentsMargins(12, 12, 12, 12); lay.setSpacing(8)
        lay.addWidget(QLabel(f"'{name}' 와(과) 일치할 수 있는 혼인기록:"))

        self.results = QListWidget()
        rows = db.search_weddings(name=name, member_id=member_id)
        for r in rows:
            label = (
                f"{fv(r,'wedding_no')}  {fv(r,'wedding_date')}"
                f"  {fv(r,'groom_name')} ↔ {fv(r,'bride_name')}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, r)
            self.results.addItem(item)
        if not rows:
            self.results.addItem("일치하는 혼인기록 없음")
        lay.addWidget(self.results, 1)

        bb = QWidget()
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(0, 0, 0, 0); bbl.addStretch()
        cb = mk_btn("취소", "btn_muted")
        ub = mk_btn("이 기록 사용", "btn_accent")
        cb.clicked.connect(self.reject)
        ub.clicked.connect(self._use_selected)
        bbl.addWidget(cb); bbl.addWidget(ub)
        lay.addWidget(bb)

    def _use_selected(self):
        item = self.results.currentItem()
        if not item:
            QMessageBox.warning(self, "선택 필요", "혼인기록을 선택하세요.")
            return
        r = item.data(Qt.ItemDataRole.UserRole)
        if r is None:
            self.reject()
            return
        self.chosen = r
        self.accept()
