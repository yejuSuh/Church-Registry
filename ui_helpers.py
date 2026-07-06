from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QTextEdit,
)
from PyQt6.QtCore import Qt

from constants import C


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

def mk_combo(values, val=""):
    cb = QComboBox()
    cb.addItems(values)
    if val:
        i = cb.findText(str(val).strip(), Qt.MatchFlag.MatchContains)
        if i >= 0:
            cb.setCurrentIndex(i)
    return cb

def mk_check(label, val=""):
    cb = QCheckBox(label)
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
