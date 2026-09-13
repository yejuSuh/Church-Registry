import sys, os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QSettings

from core.constants import DB_PATH, FONT_SIZE_DEFAULT, make_stylesheet
from core.database import DB
from ui.views import LoginDialog, MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    saved_size = int(QSettings("BostonKoreanCatholic", "ChurchRegistry").value(
        "ui/font_size", FONT_SIZE_DEFAULT))
    app.setStyleSheet(make_stylesheet(saved_size))

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
