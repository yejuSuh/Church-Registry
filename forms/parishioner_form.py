from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QComboBox, QTextEdit,
    QScrollArea, QFrame, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt

from core.constants import C, AREA_DISP
from ui.ui_helpers import fv, mk_btn, shdr, vbox_field, mk_entry, mk_combo, ge


class ParishionerForm(QDialog):
    def __init__(self, parent, db, pno=None, on_save=None, prefill_host="", prefill_area=""):
        super().__init__(parent)
        self.db = db
        self.pno = pno
        self.on_save = on_save
        self.setWindowTitle("교적 추가" if not pno else "교적 수정")
        self.resize(700, 560)
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

        # area_cb picks the reg_area code (구역 name is derived from it);
        # no_le shows formatted reg_area-reg_code
        if existing:
            cur_area = next((d for d in AREA_DISP if d.startswith(ev("reg_area"))), AREA_DISP[-1])
        elif prefill_area:
            cur_area = next((d for d in AREA_DISP if d.startswith(prefill_area)), AREA_DISP[-1])
        else:
            cur_area = AREA_DISP[-1]

        self.area_cb = mk_combo(AREA_DISP, cur_area)
        if existing:
            # 구역 is part of the registration number (reg_area); changing it
            # would mean renumbering, which edit doesn't support
            self.area_cb.setEnabled(False)
        self.no_le = QLineEdit(ev("display_id") if existing else "")
        self.no_le.setReadOnly(True)
        self.no_le.setStyleSheet(f"background:{C['header']};color:{C['muted']};")
        grid.addWidget(vbox_field("구역 *", self.area_cb, C['card']), r, 0, 1, 2)
        grid.addWidget(vbox_field("교적번호 (자동 생성)", self.no_le, C['card']), r, 2, 1, 2); r += 1

        self.name_kr_e = add("이름 (한글) *", mk_entry(ev("name")),           r, 0)
        self.name_en_e = add("이름 (영문) *", mk_entry(ev("name_english")),   r, 1)
        self.bname_e   = add("세례명 *",      mk_entry(ev("baptismal_name")), r, 2)
        sex_disp = {'M': '남', 'F': '여'}.get(ev("sex"), '')
        self.sex_cb    = add("성별 *",        mk_combo(['', '남', '여'], sex_disp), r, 3); r += 1

        self.birth_e = mk_entry(ev("birth_date"))
        self.birth_e.setPlaceholderText("YYYY/MM/DD")
        grid.addWidget(vbox_field("생년월일 *", self.birth_e, C['card']), r, 0, 1, 2); r += 1

        self.addr_e   = add("주소 *", mk_entry(ev("address")), r, 0, 3)
        self.postal_e = add("우편번호", mk_entry(ev("postal_code")), r, 3); r += 1

        self.phone_e = add("전화",   mk_entry(ev("phone")),      r, 0)
        self.email_e = add("이메일", mk_entry(ev("email")),      r, 1)
        self.occ_e   = add("직업",   mk_entry(ev("occupation")), r, 2); r += 1

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
        required = [
            (self.name_kr_e, "한글 이름을 입력하세요."),
            (self.name_en_e, "영문 이름을 입력하세요."),
            (self.bname_e,   "세례명을 입력하세요."),
            (self.sex_cb,    "성별을 선택하세요."),
            (self.birth_e,   "생년월일을 입력하세요."),
            (self.addr_e,    "주소를 입력하세요."),
        ]
        for widget, msg in required:
            if not ge(widget):
                QMessageBox.warning(self, "오류", msg)
                widget.setFocus()
                return

        area_code = ge(self.area_cb).split(None, 1)[0]
        pno = self.pno if self.pno else self.db.next_no(area_code)
        sex_db = {'남': 'M', '여': 'F'}.get(ge(self.sex_cb)) or None
        data = dict(
            member_id=pno,
            name=ge(self.name_kr_e),
            name_english=ge(self.name_en_e),
            baptismal_name=ge(self.bname_e),
            birth_date=ge(self.birth_e),
            sex=sex_db,
            address=ge(self.addr_e),
            postal_code=ge(self.postal_e) or None,
            phone=ge(self.phone_e) or None,
            email=ge(self.email_e) or None,
            occupation=ge(self.occ_e) or None,
            notes=ge(self.notes_te),
        )
        self._last_created_mid = None
        try:
            if self.pno:
                del data["member_id"]
                self.db.update(self.pno, data)
            else:
                self._last_created_mid = self.db.create(data)
            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
