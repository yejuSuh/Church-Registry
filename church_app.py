import sys, os
from PyQt6.QtWidgets import QApplication, QMessageBox

from constants import DB_PATH, SS, SQLITE_FILES
from database import DB
from views import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(SS)
    if len(SQLITE_FILES) > 1:
        file_list = "\n".join(f"  • {f}" for f in SQLITE_FILES)
        QMessageBox.warning(
            None, "데이터베이스 파일 여러 개 감지",
            f"폴더에 SQLite 파일이 여러 개 있습니다:\n\n{file_list}\n\n"
            f"첫 번째 파일을 사용합니다: {SQLITE_FILES[0]}",
        )
    if not os.path.exists(DB_PATH):
        QMessageBox.critical(
            None, "오류",
            f"데이터베이스 파일을 찾을 수 없습니다:\n{DB_PATH}\n\nchurch_registry.sqlite 를 같은 폴더에 놓아주세요.",
        )
        sys.exit(1)
    win = MainWindow(DB(DB_PATH))
    win.show()
    sys.exit(app.exec())
