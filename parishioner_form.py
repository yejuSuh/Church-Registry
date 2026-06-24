from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QComboBox, QCheckBox, QTextEdit,
    QScrollArea, QFrame, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt

from constants import C, AREA_DISP, AREA_MAP, RELATIONS
from ui_helpers import fv, mk_btn, shdr, vbox_field, mk_entry, mk_combo, mk_check, ge


class ParishionerForm(QDialog):
    def __init__(self, parent, db, pno=None, on_save=None, prefill_host="", prefill_area=""):
        super().__init__(parent)
        self.db = db
        self.pno = pno
        self.on_save = on_save
        self.setWindowTitle("교적 추가" if not pno else "교적 수정")
        self.resize(700, 480)
        self.setModal(True)

        existing = db.get(pno) if pno else None
        ev = lambda k: fv(existing, k) if existing else ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        body.setObjectName("card")
        scroll.setWidget(body)
        grid = QGridLayout(body)
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        for col in range(4):
            grid.setColumnStretch(col, 1)
        outer.addWidget(scroll, 1)

        r = 0

        def add(label, widget, row, col, span=1):
            grid.addWidget(vbox_field(label, widget, C['card']), row, col, 1, span)
            return widget

        grid.addWidget(shdr("📋  기본 정보"), r, 0, 1, 4); r += 1

        # area_cb → district name; no_le shows member_id
        if existing:
            member_id = ev("member_id")
            cur_area = next((d for d in AREA_DISP if d.startswith(member_id[:5])), AREA_DISP[-1])
        elif prefill_area:
            cur_area = next((d for d in AREA_DISP if d.startswith(prefill_area)), AREA_DISP[-1])
        else:
            cur_area = AREA_DISP[-1]

        self.area_cb = mk_combo(AREA_DISP, cur_area)
        self.no_le = QLineEdit(ev("member_id") if existing else "")
        self.no_le.setReadOnly(True)
        self.no_le.setStyleSheet(f"background:{C['header']};color:{C['muted']};")
        grid.addWidget(vbox_field("구역 *", self.area_cb, C['card']), r, 0, 1, 2)
        grid.addWidget(vbox_field("교적번호 (자동 생성)", self.no_le, C['card']), r, 2, 1, 2); r += 1

        self.name_e  = add("이름 *",       mk_entry(ev("name")),                                               r, 0)
        self.bname_e = add("세례명",        mk_entry(ev("baptismal_name")),                                     r, 1)
        self.host_e  = add("세대주 이름 *", mk_entry(ev("head_of_household") if existing else prefill_host),   r, 2)
        self.rel_cb  = add("관계 *",        mk_combo(RELATIONS, ev("relation") if existing else "본인"),        r, 3); r += 1

        grid.addWidget(shdr("💰  교무금"), r, 0, 1, 4); r += 1
        dues_val = ev("dues_paying") or "N"
        self.dues_cb      = mk_check("교무금 납부", dues_val)
        fw = QWidget(); fw.setObjectName("card")
        fl = QHBoxLayout(fw); fl.setContentsMargins(4, 2, 4, 2)
        fl.addWidget(self.dues_cb); fl.addStretch()
        grid.addWidget(fw, r, 0, 1, 4); r += 1

        self.dues_amt_e  = add("월 교무금",  mk_entry(ev("monthly_dues")),  r, 0)
        self.dues_st_e   = add("시작일",     mk_entry(ev("dues_start")),    r, 1)
        self.dues_last_e = add("최근 납부",  mk_entry(ev("dues_last_paid")), r, 2); r += 1

        grid.addWidget(shdr("📝  메모"), r, 0, 1, 4); r += 1
        self.notes_te = QTextEdit()
        self.notes_te.setFixedHeight(80)
        self.notes_te.setPlainText(ev("notes"))
        grid.addWidget(vbox_field("메모", self.notes_te, C['card']), r, 0, 1, 4); r += 1
        grid.setRowStretch(r, 1)

        bb = QWidget(); bb.setObjectName("card"); bb.setFixedHeight(54)
        bbl = QHBoxLayout(bb); bbl.setContentsMargins(12, 8, 12, 8)
        bbl.addStretch()
        cancel_b = mk_btn("취소", "btn_muted")
        save_b   = mk_btn("💾  저장", "btn_accent")
        cancel_b.clicked.connect(self.reject)
        save_b.clicked.connect(self._save)
        bbl.addWidget(cancel_b); bbl.addWidget(save_b)
        outer.addWidget(bb)

    def _save(self):
        name = ge(self.name_e)
        host = ge(self.host_e)
        if not name:
            QMessageBox.warning(self, "오류", "이름을 입력하세요.")
            return
        if not host:
            QMessageBox.warning(self, "오류", "세대주 이름을 입력하세요.")
            return

        area_text = ge(self.area_cb)
        area_parts = area_text.split(None, 1)
        area_code    = area_parts[0]
        district_name = area_parts[1].strip() if len(area_parts) > 1 else area_text

        pno = self.pno if self.pno else self.db.next_no(area_code)
        data = dict(
            member_id=pno,
            name=name,
            head_of_household=host,
            relation=ge(self.rel_cb),
            baptismal_name=ge(self.bname_e),
            district=district_name,
            dues_paying="Y" if self.dues_cb.isChecked() else "N",
            monthly_dues=ge(self.dues_amt_e) or None,
            dues_start=ge(self.dues_st_e),
            dues_last_paid=ge(self.dues_last_e),
            notes=ge(self.notes_te),
        )
        try:
            if self.pno:
                del data["member_id"]
                self.db.update(self.pno, data)
            else:
                self.db.create(data)
            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
