import os
import platform
import subprocess
import tempfile

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal

from constants import C
from ui_helpers import mk_btn


class PrinterDiscoveryThread(QThread):
    finished = pyqtSignal(list)   # list of (display_label, printer_id, is_network)

    def run(self):
        printers = []
        system = platform.system()
        try:
            if system in ('Darwin', 'Linux'):
                result = subprocess.run(
                    ['lpstat', '-v'], capture_output=True, text=True, timeout=8
                )
                for line in result.stdout.splitlines():
                    if line.startswith('device for '):
                        rest = line[len('device for '):]
                        if ':' in rest:
                            name, uri = rest.split(':', 1)
                            name = name.strip(); uri = uri.strip()
                            is_net = not uri.startswith('usb://')
                            label = f"{name}  ({'네트워크' if is_net else 'USB'})"
                            printers.append((label, name, is_net))
            elif system == 'Windows':
                result = subprocess.run(
                    ['wmic', 'printer', 'get', 'Name,PortName', '/format:csv'],
                    capture_output=True, text=True, timeout=8
                )
                for line in result.stdout.splitlines()[2:]:
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        name = parts[1].strip(); port = parts[2].strip()
                        if name:
                            is_net = any(port.upper().startswith(p) for p in ('IP_', '\\\\'))
                            label = f"{name}  ({'네트워크' if is_net else 'USB/로컬'})"
                            printers.append((label, name, is_net))
        except Exception:
            pass
        self.finished.emit(printers)


class PrinterSearchDialog(QDialog):
    def __init__(self, parent, pdf_path):
        super().__init__(parent)
        self._pdf_path = pdf_path
        self._thread   = None
        self.setWindowTitle("프린터 선택")
        self.setModal(True)
        self.resize(460, 340)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        self._status = QLabel("프린터 검색 중...")
        self._status.setObjectName("fv")
        lay.addWidget(self._status)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        lay.addWidget(self._list)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        self._refresh_btn = mk_btn("새로고침", "btn_muted")
        self._refresh_btn.clicked.connect(self._start_search)
        self._print_btn = mk_btn("인쇄", "btn_accent")
        self._print_btn.clicked.connect(self._do_print)
        self._print_btn.setEnabled(False)
        cancel = mk_btn("취소", "btn_muted")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._print_btn)
        btn_row.addWidget(cancel)
        lay.addLayout(btn_row)

        self._list.currentItemChanged.connect(
            lambda cur, _: self._print_btn.setEnabled(cur is not None)
        )
        QTimer.singleShot(0, self._start_search)

    def _start_search(self):
        self._status.setText("프린터 검색 중...")
        self._list.clear()
        self._print_btn.setEnabled(False)
        self._refresh_btn.setEnabled(False)

        self._thread = PrinterDiscoveryThread(self)
        self._thread.finished.connect(self._on_found)
        self._thread.start()

    def _on_found(self, printers):
        self._refresh_btn.setEnabled(True)
        if printers:
            net_count = sum(1 for _, _, n in printers if n)
            self._status.setText(f"{len(printers)}개 프린터 발견  (네트워크: {net_count}개)")
            for label, printer_id, _ in printers:
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, printer_id)
                self._list.addItem(item)
        else:
            self._status.setText("프린터를 찾을 수 없습니다.")

    def _do_print(self):
        item = self._list.currentItem()
        if not item:
            return
        printer_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            system = platform.system()
            if system in ('Darwin', 'Linux'):
                subprocess.run(['lp', '-d', printer_id, self._pdf_path], check=True)
            elif system == 'Windows':
                subprocess.run(
                    ['powershell', '-Command',
                     f'Start-Process -FilePath "{self._pdf_path}" -Verb Print -Wait'],
                    check=True
                )
            else:
                QMessageBox.warning(self, "미지원", "이 운영체제는 지원되지 않습니다.")
                return
            QMessageBox.information(self, "인쇄", f"'{printer_id}'(으)로 인쇄 요청을 보냈습니다.")
            self.accept()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "오류", f"인쇄 실패:\n{e}")


class ExportDialog(QDialog):
    HEADERS = ["교적번호", "이름", "세례명", "관계", "세대주", "구역"]
    FIELDS  = ["member_id", "name", "baptismal_name", "relation", "head_of_household", "district"]
    COL_W   = [110, 80, 80, 55, 90, 160]   # landscape A4 ≈ 762 pts usable

    def __init__(self, parent, rows):
        super().__init__(parent)
        self.rows = rows
        self.setWindowTitle("내보내기")
        self.resize(340, 120)
        self.setModal(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        info = QLabel(f"선택된 교적 {len(rows)}명을 출력합니다.")
        info.setObjectName("fv")
        lay.addWidget(info)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        pdf_btn   = mk_btn("PDF 저장",   "btn_accent")
        print_btn = mk_btn("프린터 인쇄", "btn_muted")
        cancel    = mk_btn("취소",        "btn_muted")
        pdf_btn.clicked.connect(self._export_pdf)
        print_btn.clicked.connect(self._print_pdf)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(pdf_btn)
        btn_row.addWidget(print_btn)
        btn_row.addWidget(cancel)
        lay.addLayout(btn_row)

    def _values(self):
        return [[str(r[f] or "").strip() for f in self.FIELDS] for r in self.rows]

    @staticmethod
    def _korean_font():
        candidates = {
            'Darwin':  [
                '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
                '/Library/Fonts/AppleGothic.ttf',
                '/System/Library/Fonts/AppleSDGothicNeo.ttc',
            ],
            'Windows': [
                'C:/Windows/Fonts/malgun.ttf',
                'C:/Windows/Fonts/gulim.ttc',
            ],
        }
        for path in candidates.get(platform.system(), []):
            if os.path.exists(path):
                return path
        return None

    def _build_pdf(self, path):
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        font_name = "Helvetica"
        font_path = self._korean_font()
        if font_path:
            try:
                pdfmetrics.registerFont(TTFont("Korean", font_path))
                font_name = "Korean"
            except Exception:
                pass

        doc = SimpleDocTemplate(
            path, pagesize=landscape(A4),
            leftMargin=40, rightMargin=40, topMargin=30, bottomMargin=30,
        )
        title_style = ParagraphStyle(
            "t", fontName=font_name, fontSize=13,
            textColor=colors.HexColor("#2D4A6A"), spaceAfter=6,
        )
        elements = [
            Paragraph("보스톤 한인 천주교  |  교적 목록", title_style),
            Spacer(1, 4),
        ]
        data = [self.HEADERS] + self._values()
        cmds = [
            ("FONTNAME",      (0, 0), (-1, -1), font_name),
            ("FONTSIZE",      (0, 0), (-1,  0), 9),
            ("FONTSIZE",      (0, 1), (-1, -1), 8),
            ("BACKGROUND",    (0, 0), (-1,  0), colors.HexColor("#2D4A6A")),
            ("TEXTCOLOR",     (0, 0), (-1,  0), colors.white),
            ("ALIGN",         (0, 0), (-1,  0), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D8E4")),
        ]
        for i in range(1, len(data)):
            bg = colors.HexColor("#F8FAFC") if i % 2 == 0 else colors.white
            cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
        tbl = Table(data, colWidths=self.COL_W, repeatRows=1)
        tbl.setStyle(TableStyle(cmds))
        elements.append(tbl)
        doc.build(elements)

    def _export_pdf(self):
        try:
            from reportlab.platypus import SimpleDocTemplate  # noqa: import check
        except ImportError:
            QMessageBox.critical(self, "오류",
                "reportlab이 설치되지 않았습니다.\n터미널에서 실행하세요: pip install reportlab")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "PDF로 저장", "교적목록.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self._build_pdf(path)
            QMessageBox.information(self, "완료", f"저장 완료:\n{path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _print_pdf(self):
        try:
            from reportlab.platypus import SimpleDocTemplate  # noqa: import check
        except ImportError:
            QMessageBox.critical(self, "오류",
                "reportlab이 설치되지 않았습니다.\n터미널에서 실행하세요: pip install reportlab")
            return

        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            self._build_pdf(tmp.name)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"PDF 생성 실패:\n{e}")
            return

        PrinterSearchDialog(self, tmp.name).exec()
