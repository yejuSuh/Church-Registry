import sys, os
from PyQt6.QtWidgets import QApplication, QMessageBox

from core.constants import DB_PATH, SS
from core.database import DB
from ui.views import LoginDialog, MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(SS)

    if not os.path.exists(DB_PATH):
        QMessageBox.critical(
            None, "오류",
            f"데이터베이스 파일을 찾을 수 없습니다:\n{DB_PATH}\n\nparish.db 를 같은 폴더에 놓아주세요.",
        )
        sys.exit(1)

    db = DB(DB_PATH)

    login = LoginDialog(db)
    if login.exec() != LoginDialog.DialogCode.Accepted:
        sys.exit(0)

    win = MainWindow(db)
    win.show()
    sys.exit(app.exec())
