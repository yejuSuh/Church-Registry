from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QGridLayout, QScrollArea, QFrame, QLabel, QMessageBox, QTabWidget,
)
from PyQt6.QtCore import Qt, QDate

from core.constants import C
from ui.ui_helpers import fv, mk_btn, mk_entry, mk_date, mk_combo, mk_check, vbox_field, shdr, ge
from forms.person_picker import PersonPicker, WeddingMatchDialog


# ── Shared building blocks ───────────────────────────────────────────────────

def member_summary(member):
    """Read-only one-liner identifying the member a sacrament is being added
    to. The member's own data (names, birth date, address, ...) already lives
    on the registration record, so intake forms don't ask for it again."""
    w = QWidget()
    lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(4)
    lay.addWidget(shdr("👤  신청자"))
    parts = [fv(member, "display_id"), fv(member, "name")]
    bn = fv(member, "baptismal_name")
    if bn:
        parts[-1] += f" ({bn})"
    sex = {'M': '남', 'F': '여'}.get(fv(member, "sex"), "")
    for extra in (sex, fv(member, "birth_date")):
        if extra:
            parts.append(extra)
    lbl = QLabel("  ·  ".join(p for p in parts if p))
    lbl.setObjectName("fv")
    lay.addWidget(lbl)
    return w


class ParentBlock(QWidget):
    """Father/mother field group: a PersonPicker (name + phone) plus that
    parent's own baptism info (date/diocese/parish) -- same column shape on
    both `baptism` and `confirmation`."""

    def __init__(self, db, title, required=()):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        self.picker = PersonPicker(db, title, show_english=True, show_phone=True,
                                   required=required)
        lay.addWidget(self.picker)

        row = QWidget()
        rl = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(10)
        self.bdate_e = mk_date(); rl.addWidget(vbox_field("세례일", self.bdate_e, C['card']), 1)
        self.dioc_e = mk_entry(); rl.addWidget(vbox_field("세례 교구", self.dioc_e, C['card']), 1)
        self.par_e = mk_entry(); rl.addWidget(vbox_field("세례 성당", self.par_e, C['card']), 1)
        lay.addWidget(row)

    def data(self, prefix):
        d = self.picker.data(prefix)
        d[f"{prefix}_baptism_date"] = ge(self.bdate_e) or None
        d[f"{prefix}_baptism_diocese"] = self.dioc_e.text().strip() or None
        d[f"{prefix}_baptism_parish"] = self.par_e.text().strip() or None
        return d

    def name_korean(self):
        return self.picker.kr_e.text().strip()

    def member_id(self):
        return self.picker.member_id


class PriorBaptismBlock(QWidget):
    """Editable baptism block — pre-fills from the first existing record when present.

    Either path (existing or new) shows the same fully-editable grid. On save:
    - existing record → update changed fields in DB
    - no record → create a new baptism row (skipped if date is blank)
    """

    def __init__(self, records):
        super().__init__()
        self.has_existing = bool(records)
        self._rec_id = records[0]["id"] if records else None
        rec = records[0] if records else None

        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        lay.addWidget(shdr("✝  세례성사"))

        g = QGridLayout(); g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(3): g.setColumnStretch(col, 1)

        def _cell(label, key, row, col, span=1, star=False, kind="text"):
            lbl_txt = f"{label} *" if star and not self.has_existing else label
            val = fv(rec, key) if rec else ""
            e = mk_date(val) if kind == "date" else mk_entry(val)
            g.addWidget(vbox_field(lbl_txt, e, C['card']), row, col, 1, span)
            return e

        self.date_e     = _cell("세례일자",        "date",                0, 0, star=True, kind="date")
        self.dioc_e     = _cell("세례교구",        "diocese",             0, 1)
        self.par_e      = _cell("세례본당",        "parish",              0, 2)
        self.off_e      = _cell("집전자",          "officiant_name",      1, 0)
        self.off_bn_e   = _cell("집전자 세례명",   "officiant_name_bapt", 1, 1)
        self.gp_ko_e    = _cell("대부/대모",       "godparent_name_ko",   2, 0)
        self.gp_bn_e    = _cell("대부/대모 세례명", "godparent_name_bapt", 2, 1)
        self.gp_en_e    = _cell("대부/대모 영문명", "godparent_name_en",   2, 2)
        lay.addLayout(g)

    def _field_data(self):
        return dict(
            date=ge(self.date_e) or None,
            diocese=self.dioc_e.text().strip() or None,
            parish=self.par_e.text().strip() or None,
            officiant_name=self.off_e.text().strip() or None,
            officiant_name_bapt=self.off_bn_e.text().strip() or None,
            godparent_name_ko=self.gp_ko_e.text().strip() or None,
            godparent_name_bapt=self.gp_bn_e.text().strip() or None,
            godparent_name_en=self.gp_en_e.text().strip() or None,
        )

    def maybe_create(self, db, member_id):
        data = self._field_data()
        if self.has_existing:
            db.update_sacrament_record("baptism", "id", self._rec_id,
                                       {k: v for k, v in data.items()})
        else:
            if not data["date"]:
                return
            data["member_id"] = member_id
            db.create_baptism(data)


# ── Dialog scaffolding ───────────────────────────────────────────────────────

class _IntakeDialog(QDialog):
    """Base class for full sacrament intake dialogs; provides shared grid helpers."""

    def __init__(self, parent, db, pno, name, title, size, on_save=None):
        super().__init__(parent)
        self.db = db; self.pno = pno; self.on_save = on_save
        self.member = db.get(pno)
        self.setWindowTitle(title)
        self.resize(*size)
        self.setModal(True)

        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(); body.setObjectName("card")
        scroll.setWidget(body)
        self.grid = QGridLayout(body)
        self.grid.setContentsMargins(16, 12, 16, 12)
        self.grid.setHorizontalSpacing(16); self.grid.setVerticalSpacing(10)
        for col in range(4):
            self.grid.setColumnStretch(col, 1)
        outer.addWidget(scroll, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8); bbl.addStretch()
        cbtn = mk_btn("취소", "btn_muted"); sbtn = mk_btn("💾  저장", "btn_accent")
        cbtn.clicked.connect(self.reject); sbtn.clicked.connect(self._save)
        bbl.addWidget(cbtn); bbl.addWidget(sbtn)
        outer.addWidget(bb)

    def add(self, lbl, w, r, c, span=1):
        self.grid.addWidget(vbox_field(lbl, w, C['card']), r, c, 1, span)
        return w

    def hdr(self, text, r):
        self.grid.addWidget(shdr(text), r, 0, 1, 4)

    def _link_parents(self, father: ParentBlock, mother: ParentBlock):
        # When a matched parent is found, join the child into that parent's
        # household automatically rather than requiring a manual follow-up.
        father_mid = father.member_id()
        mother_mid = mother.member_id()
        if not (father_mid or mother_mid):
            return
        relation = {'M': '자', 'F': '녀'}.get(fv(self.member, "sex"), '자녀')
        parent_mid = father_mid or mother_mid
        self.db.link_child_to_parent(self.pno, parent_mid, relation)


class ConfirmationIntakeForm(_IntakeDialog):
    """Full 견진성사 신청서: applicant info, prior baptism, sponsor, and adult/youth tabs."""
    """Unified 견진성사 신청서: common required blocks (applicant, baptism
    info, sponsor, rite info) plus a 성인/청소년 tab for the type-specific
    fields. Replaces the separate adult/RCIA/youth forms."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "견진성사 신청서", (720, 800), on_save)
        r = 0
        self.grid.addWidget(member_summary(self.member), r, 0, 1, 4); r += 1

        self.prior_baptism = PriorBaptismBlock(records=db.get_baptism_records(pno))
        self.grid.addWidget(self.prior_baptism, r, 0, 1, 4); r += 1

        self.sponsor = PersonPicker(db, "🕊  대부모", show_english=True, show_phone=False,
                                    required=("kr", "en", "bn"))
        self.grid.addWidget(self.sponsor, r, 0, 1, 4); r += 1

        self.hdr("🕊  견진 정보", r); r += 1
        self.date_e  = self.add("성사 예정일 *", mk_date(), r, 0)
        self.off_e   = self.add("집전사제/(대)주교 *",         mk_entry(), r, 1, 2)
        self.cname_e = self.add("견진명",                      mk_entry(), r, 3); r += 1

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_adult_tab(), "성인")
        self.tabs.addTab(self._build_youth_tab(), "청소년")
        self.grid.addWidget(self.tabs, r, 0, 1, 4); r += 1
        self.grid.setRowStretch(r, 1)

    # ── Tab builders ─────────────────────────────────────────────────────────

    def _build_adult_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 10, 8, 10); lay.setSpacing(10)

        mrow = QWidget()
        ml = QHBoxLayout(mrow); ml.setContentsMargins(0, 0, 0, 0); ml.setSpacing(10)
        self.marital_cb = mk_combo(
            ['미혼', '초혼', '재혼', '이혼', '사별'], fv(self.member, "marital_status")
        )
        ml.addWidget(vbox_field("혼인상태 *", self.marital_cb, C['card']), 1)
        ml.addStretch(3)
        lay.addWidget(mrow)

        self.spouse_group = QWidget()
        sl = QVBoxLayout(self.spouse_group); sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(6)
        self.spouse = PersonPicker(self.db, "💍  배우자", show_english=True, show_phone=False,
                                   required=("kr", "en", "bn"))
        sl.addWidget(self.spouse)

        wrow = QWidget()
        wl = QHBoxLayout(wrow); wl.setContentsMargins(0, 0, 0, 0); wl.setSpacing(10)
        self.wtype_cb = mk_combo(["성사혼", "관면혼", "단순유효화혼", "바오로특전혼", "근본유효화혼", "기타"])
        wl.addWidget(vbox_field("혼인 형태 *", self.wtype_cb, C['card']), 1)
        self.wdate_e = mk_date()
        wl.addWidget(vbox_field("혼인날짜 *", self.wdate_e, C['card']), 1)
        self.woff_e = mk_entry()
        wl.addWidget(vbox_field("예식 집전자 *", self.woff_e, C['card']), 1)
        sl.addWidget(wrow)

        wrow_other = QWidget()
        wl_other = QHBoxLayout(wrow_other); wl_other.setContentsMargins(0, 0, 0, 0)
        self.wtype_other_e = mk_entry(); self.wtype_other_e.setPlaceholderText("혼인 형태를 직접 입력하세요")
        wl_other.addWidget(vbox_field("형태 직접입력", self.wtype_other_e, C['card']), 1)
        wrow_other.setVisible(False)
        self.wtype_cb.currentTextChanged.connect(lambda t: wrow_other.setVisible(t == "기타"))
        sl.addWidget(wrow_other)

        wrow2 = QWidget()
        wl2 = QHBoxLayout(wrow2); wl2.setContentsMargins(0, 0, 0, 0); wl2.setSpacing(10)
        find_btn = mk_btn("🔍 기존 혼인기록 찾기", "btn_muted")
        find_btn.clicked.connect(self._find_wedding)
        wl2.addWidget(find_btn, 1)
        sl.addWidget(wrow2)

        lay.addWidget(self.spouse_group)
        lay.addStretch()
        self._matched_wedding_no = None

        self.marital_cb.currentTextChanged.connect(lambda _: self._on_marital_change())
        self._on_marital_change()
        return w

    def _build_youth_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(8, 10, 8, 10); lay.setSpacing(10)
        self.father = ParentBlock(self.db, "👨  아버지", required=("kr", "en", "phone"))
        self.mother = ParentBlock(self.db, "👩  어머니", required=("kr", "en", "phone"))
        self.married_cb = mk_check("부모가 혼인성사(성당)로 결혼함")
        lay.addWidget(self.father)
        lay.addWidget(self.mother)
        lay.addWidget(self.married_cb)
        lay.addStretch()
        return w

    # ── Adult tab helpers ────────────────────────────────────────────────────

    def _on_marital_change(self):
        show = ge(self.marital_cb) in ("초혼", "재혼")
        self.spouse_group.setVisible(show)

    def _find_wedding(self):
        spouse_name = self.spouse.kr_e.text().strip()
        dlg = WeddingMatchDialog(self, self.db, spouse_name, member_id=self.pno)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.chosen:
            r = dlg.chosen
            self._matched_wedding_no = r["wedding_no"]
            d = QDate.fromString(fv(r, "date"), "MM/dd/yyyy")
            if d.isValid():
                self.wdate_e.setDate(d)
            idx = self.wtype_cb.findText(fv(r, "wedding_type"), Qt.MatchFlag.MatchContains)
            if idx >= 0:
                self.wtype_cb.setCurrentIndex(idx)
            if fv(r, "wedding_type") == "기타":
                self.wtype_other_e.setText(fv(r, "type_other") or "")
            self.woff_e.setText(fv(r, "officiant_name"))

    def _resolve_wedding(self, marital_status):
        """Creates a new `wedding` row if the applicant is married and no
        existing wedding record was matched. Returns the wedding_no or None."""
        if marital_status not in ("초혼", "재혼"):
            return None
        if self._matched_wedding_no:
            return self._matched_wedding_no
        spouse_name = self.spouse.kr_e.text().strip()
        if not spouse_name:
            return None
        is_groom = fv(self.member, "sex") == 'M'
        wtype = ge(self.wtype_cb) or None
        wdata = dict(
            date=ge(self.wdate_e) or None,
            wedding_type=wtype,
            officiant_name=ge(self.woff_e) or None,
        )
        if wtype == "기타":
            wdata["type_other"] = ge(self.wtype_other_e) or None
        applicant_kr = fv(self.member, "name") or None
        applicant_bn = fv(self.member, "baptismal_name") or None
        spouse_bn = self.spouse.bn_e.text().strip() or None
        if is_groom:
            wdata.update(
                groom_id=self.pno, groom_name=applicant_kr,
                groom_name_bapt=applicant_bn,
                bride_id=self.spouse.member_id, bride_name=spouse_name,
                bride_name_bapt=spouse_bn,
            )
        else:
            wdata.update(
                bride_id=self.pno, bride_name=applicant_kr,
                bride_name_bapt=applicant_bn,
                groom_id=self.spouse.member_id, groom_name=spouse_name,
                groom_name_bapt=spouse_bn,
            )
        self.db.create_wedding_record(wdata)
        return wno

    # ── Save ─────────────────────────────────────────────────────────────────

    def _save(self):
        try:
            is_adult = self.tabs.currentIndex() == 0

            checks = [
                (self.date_e,      "성사 예정일을 입력하세요."),
                (self.off_e,       "집전사제/(대)주교를 입력하세요."),
                (self.sponsor.kr_e, "대부모 한글 이름을 입력하세요."),
                (self.sponsor.en_e, "대부모 영문 이름을 입력하세요."),
                (self.sponsor.bn_e, "대부모 세례명을 입력하세요."),
            ]
            if not self.prior_baptism.has_existing:
                checks += [
                    (self.prior_baptism.date_e, "세례일자를 입력하세요."),
                    (self.prior_baptism.dioc_e, "세례교구를 입력하세요."),
                    (self.prior_baptism.par_e,  "세례본당을 입력하세요."),
                ]
            if is_adult:
                if ge(self.marital_cb) in ("초혼", "재혼"):
                    checks += [
                        (self.spouse.kr_e, "배우자 한글 이름을 입력하세요."),
                        (self.spouse.en_e, "배우자 영문 이름을 입력하세요."),
                        (self.spouse.bn_e, "배우자 세례명을 입력하세요."),
                        (self.wdate_e,     "혼인날짜를 입력하세요."),
                        (self.woff_e,      "예식 집전자를 입력하세요."),
                    ]
            else:
                checks += [
                    (self.father.picker.kr_e,    "아버지 한글 이름을 입력하세요."),
                    (self.father.picker.en_e,    "아버지 영문 이름을 입력하세요."),
                    (self.father.picker.phone_e, "아버지 전화번호를 입력하세요."),
                    (self.mother.picker.kr_e,    "어머니 한글 이름을 입력하세요."),
                    (self.mother.picker.en_e,    "어머니 영문 이름을 입력하세요."),
                    (self.mother.picker.phone_e, "어머니 전화번호를 입력하세요."),
                ]
            for widget, msg in checks:
                if not widget.text().strip():
                    QMessageBox.warning(self, "오류", msg)
                    widget.setFocus()
                    return

            self.prior_baptism.maybe_create(self.db, self.pno)

            data = dict(
                member_id=self.pno,
                is_adp=1,
                date=ge(self.date_e),
                officiant_name=ge(self.off_e),
                confirmation_name=ge(self.cname_e) or None,
            )
            data.update(self.sponsor.data("godparent"))

            if is_adult:
                self._resolve_wedding(ge(self.marital_cb))
            else:
                self._link_parents(self.father, self.mother)

            self.db.create_confirmation_record(data)

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


# ── Form 3: 유아세례 및 첫영성체 신청서 — Infant Baptism & First Communion ───

class InfantBaptismForm(_IntakeDialog):
    """Infant baptism + optional first communion intake form; links parents to household."""
    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "유아세례 및 첫영성체 신청서", (720, 780), on_save)
        r = 0
        self.grid.addWidget(member_summary(self.member), r, 0, 1, 4); r += 1

        self.hdr("✝  세례 정보", r); r += 1
        self.date_e   = self.add("세례일 (예정/실시)", mk_date(), r, 0, 2)
        self.off_e    = self.add("집전자/부제",        mk_entry(), r, 2)
        self.off_bn_e = self.add("집전자 세례명",      mk_entry(), r, 3); r += 1
        self.bname_e  = self.add("세례명", mk_entry(fv(self.member, "baptismal_name")), r, 0); r += 1

        self.father = ParentBlock(db, "👨  아버지")
        self.grid.addWidget(self.father, r, 0, 1, 4); r += 1
        self.mother = ParentBlock(db, "👩  어머니")
        self.grid.addWidget(self.mother, r, 0, 1, 4); r += 1

        self.married_cb = mk_check("부모가 혼인성사(성당)로 결혼함")
        self.grid.addWidget(self.married_cb, r, 0, 1, 4); r += 1

        self.godparent = PersonPicker(db, "🕊  대부/대모", show_english=True, show_phone=False)
        self.grid.addWidget(self.godparent, r, 0, 1, 4); r += 1

        self.comm_cb = mk_check("첫영성체 신청")
        self.grid.addWidget(self.comm_cb, r, 0, 1, 4); r += 1

        self.comm_group = QWidget()
        cl = QHBoxLayout(self.comm_group); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(10)
        self.comm_date_e = mk_date()
        cl.addWidget(vbox_field("첫영성체일 (예정/실시)", self.comm_date_e, C['card']), 1)
        self.comm_cb.toggled.connect(self.comm_group.setVisible)
        self.comm_group.setVisible(False)
        self.grid.addWidget(self.comm_group, r, 0, 1, 4); r += 1

        self.grid.setRowStretch(r, 1)

    def _save(self):
        try:
            bname = ge(self.bname_e) or None
            if bname:
                self.db.update(self.pno, {"baptismal_name": bname})
            data = dict(
                member_id=self.pno,
                is_adp=1,
                date=ge(self.date_e) or None,
                officiant_name=ge(self.off_e) or None,
                officiant_name_bapt=ge(self.off_bn_e) or None,
            )
            data.update(self.godparent.data("godparent"))
            self.db.create_baptism(data)

            if self.comm_cb.isChecked():
                self.db.create_communion_record(dict(
                    member_id=self.pno,
                    is_adp=1,
                    date=ge(self.comm_date_e) or None,
                ))

            self._link_parents(self.father, self.mother)

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))


# ── Form 4: 첫영성체 신청서 — First Communion ────────────────────────────────

class FirstCommunionForm(_IntakeDialog):
    """첫영성체 신청서: shows member info (incl. address/birth date), prior baptism,
    parent blocks, and communion-specific fields (date, officiant)."""

    def __init__(self, parent, db, pno, name, on_save=None):
        super().__init__(parent, db, pno, name, "첫영성체 신청서", (720, 800), on_save)
        r = 0

        # ── 신청자 (member detail incl. birth date & address) ─────────────────
        self.grid.addWidget(self._member_detail_block(), r, 0, 1, 4); r += 1

        # ── 세례 정보 ─────────────────────────────────────────────────────────
        self.prior_baptism = PriorBaptismBlock(records=db.get_baptism_records(pno))
        self.grid.addWidget(self.prior_baptism, r, 0, 1, 4); r += 1

        # ── 부모 정보 ─────────────────────────────────────────────────────────
        self.father = ParentBlock(db, "👨  아버지")
        self.grid.addWidget(self.father, r, 0, 1, 4); r += 1
        self.mother = ParentBlock(db, "👩  어머니")
        self.grid.addWidget(self.mother, r, 0, 1, 4); r += 1

        # ── 첫영성체 정보 ─────────────────────────────────────────────────────
        self.hdr("🍞  첫영성체 정보", r); r += 1
        self.date_e   = self.add("성사 예정일", mk_date(), r, 0, 2)
        self.off_e    = self.add("집전자",      mk_entry(), r, 2)
        self.off_bn_e = self.add("집전자 세례명", mk_entry(), r, 3); r += 1

        self.grid.setRowStretch(r, 1)

    def _member_detail_block(self):
        """Member info block — pre-filled and editable; changes are saved back to the member record."""
        w = QWidget()
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        lay.addWidget(shdr("👤  신청자"))

        g = QGridLayout(); g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(16); g.setVerticalSpacing(6)
        for col in range(4): g.setColumnStretch(col, 1)

        m = self.member

        def _cell(label, key, row, col, span=1):
            e = mk_entry(fv(m, key))
            g.addWidget(vbox_field(label, e, C['card']), row, col, 1, span)
            return e

        self._m_name_e  = _cell("이름",     "name",           0, 0)
        self._m_bname_e = _cell("세례명",   "baptismal_name", 0, 1)
        self._m_birth_e = _cell("생년월일", "birth_date",     0, 2)
        # 교적번호 is immutable — keep it read-only
        reg_e = mk_entry(fv(m, "display_id")); reg_e.setReadOnly(True)
        reg_e.setStyleSheet(f"background:{C['header']};color:{C['text']};")
        g.addWidget(vbox_field("교적번호", reg_e, C['card']), 0, 3)
        self._m_addr_e  = _cell("주소",     "address",        1, 0, 4)
        lay.addLayout(g)
        return w

    def _save(self):
        if not ge(self.date_e):
            QMessageBox.warning(self, "오류", "성사 예정일을 입력하세요.")
            return
        if not self.prior_baptism.has_existing and not self.prior_baptism.date_e.text().strip():
            QMessageBox.warning(self, "오류", "세례일자를 입력하세요.")
            return
        try:
            # Write back any member info edits
            self.db.update(self.pno, dict(
                name=ge(self._m_name_e),
                baptismal_name=ge(self._m_bname_e) or None,
                birth_date=ge(self._m_birth_e) or None,
                address=ge(self._m_addr_e) or None,
            ))
            self.prior_baptism.maybe_create(self.db, self.pno)
            self.db.create_communion_record(dict(
                member_id=self.pno,
                is_adp=1,
                date=ge(self.date_e) or None,
                officiant_name=ge(self.off_e) or None,
                officiant_name_bapt=ge(self.off_bn_e) or None,
            ))
            self._link_parents(self.father, self.mother)
            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
