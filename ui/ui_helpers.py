from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QTextEdit,
    QStyle, QStyleOptionButton,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen

from core.constants import C

# Shared rounded-checkbox look, used by both the list_view export column
# (drawn via QStyledItemDelegate) and StyledCheckBox below (drawn via paintEvent).
CB_SZ = 15   # checkbox size in px
CB_RD = 3    # corner radius


def draw_checkbox(painter, rect, checked: bool):
    """Draw a rounded checkbox centered in rect. Works for delegate paint and widget paintEvent."""
    cx = rect.x() + (rect.width()  - CB_SZ) // 2
    cy = rect.y() + (rect.height() - CB_SZ) // 2
    rf = QRectF(cx, cy, CB_SZ, CB_SZ)

    path = QPainterPath()
    path.addRoundedRect(rf, CB_RD, CB_RD)

    painter.save()
    painter.setRenderHint(painter.RenderHint.Antialiasing)
    if checked:
        painter.fillPath(path, QColor(C['accent']))
        m = 3
        painter.setPen(QPen(QColor('#FFFFFF'), 1.8,
                            Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(cx + m,            cy + CB_SZ // 2,
                         cx + CB_SZ // 2 - 1, cy + CB_SZ - m - 1)
        painter.drawLine(cx + CB_SZ // 2 - 1, cy + CB_SZ - m - 1,
                         cx + CB_SZ - m,   cy + m)
    else:
        painter.fillPath(path, QColor('#FFFFFF'))
        painter.setPen(QPen(QColor(C['border']), 1.2))
        painter.drawPath(path)
    painter.restore()


class StyledCheckBox(QCheckBox):
    """QCheckBox using the same rounded, hand-drawn indicator as the list_view export column."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        opt = QStyleOptionButton()
        self.initStyleOption(opt)

        # Compute both rects from the same unmodified opt.rect first --
        # mutating opt.rect before the second lookup would shift it.
        ind_rect = self.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxIndicator, opt, self
        )
        label_rect = self.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxContents, opt, self
        )

        label_opt = QStyleOptionButton(opt)
        label_opt.rect = label_rect
        self.style().drawControl(QStyle.ControlElement.CE_CheckBoxLabel, label_opt, painter, self)

        draw_checkbox(painter, ind_rect, self.isChecked())
        painter.end()


def fv(row, k):
    try:
        v = row[k]
        return str(v).strip() if v else ""
    except Exception:
        return ""

def mk_btn(text, oid="btn_accent"):
    b = QPushButton(text)
    b.setObjectName(oid)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

def shdr(text):
    lbl = QLabel(text)
    lbl.setObjectName("section_hdr")
    return lbl

def vbox_field(label, widget, bg=None):
    w = QWidget()
    if bg:
        w.setStyleSheet(f"background:{bg};")
    vb = QVBoxLayout(w)
    vb.setContentsMargins(0, 0, 0, 0)
    vb.setSpacing(2)
    lb = QLabel(label)
    lb.setObjectName("fl")
    vb.addWidget(lb)
    vb.addWidget(widget)
    return w

def mk_entry(val=""):
    e = QLineEdit()
    e.setText(str(val).strip() if val else "")
    return e

class _NoScrollComboBox(QComboBox):
    """A QComboBox that only responds to the mouse wheel while it has focus.
    Plain QComboBox changes its selected value on any wheel scroll under the
    cursor -- inside this app's scrollable forms (ParishionerForm, the
    sacrament intake dialogs), that means scrolling past a dropdown silently
    corrupts its value. Click or tab into it first, same as any other field."""

    def wheelEvent(self, event):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

def mk_combo(values, val=""):
    cb = _NoScrollComboBox()
    cb.addItems(values)
    if val:
        i = cb.findText(str(val).strip(), Qt.MatchFlag.MatchContains)
        if i >= 0:
            cb.setCurrentIndex(i)
    return cb

def mk_regno(text):
    """A person's 교적번호 rendered like a stamped ledger plate -- the one
    place this app spends its typographic boldness (see constants.py's
    design-token comment). Everywhere else stays on the plain UI face."""
    lbl = QLabel(text)
    lbl.setObjectName("regno")
    f = lbl.font()
    f.setFamily("Georgia")
    f.setPointSize(12)
    f.setBold(True)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.4)
    lbl.setFont(f)
    return lbl


def mk_check(label, val=""):
    cb = StyledCheckBox(label)
    cb.setChecked(str(val).strip() in ("Y", "1") or val is True or val == 1)
    return cb

def ge(w):
    if isinstance(w, QLineEdit):
        return w.text().strip()
    if isinstance(w, QComboBox):
        return w.currentText().strip()
    if isinstance(w, QTextEdit):
        return w.toPlainText().strip()
    return ""
