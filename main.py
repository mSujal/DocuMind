"""Main entry point for the application"""

import sys
from PyQt5.QtWidgets import QApplication
from src.app import App

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())