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
            None, "ERROR",
            f"데이터베이스 파일을 찾을 수 없습니다.\n{DB_PATH}\n해당 경로에 파일이 존재하는지 확인하세요.",
        )
        sys.exit(1)

    db = DB(DB_PATH)

    # Login → main window loop: logging out closes the main window and brings
    # the login/signup page back up instead of quitting the app.
    while True:
        login = LoginDialog(db)
        if login.exec() != LoginDialog.DialogCode.Accepted:
            break

        win = MainWindow(db)
        win.show()
        app.exec()
        if not win.logged_out:
            break
    sys.exit(0)
