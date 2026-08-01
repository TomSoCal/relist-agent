import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from database import init_db
from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.main_window import MainWindow

def main():
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Apply dark theme (dark mode only)
    theme_file = os.path.join(os.path.dirname(__file__), "themes", "dark_theme.qss")
    if os.path.exists(theme_file):
        with open(theme_file, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    # Initialize database
    init_db()

    # Create and show main window
    # (eBay OAuth setup prompts in Settings tab if needed)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
