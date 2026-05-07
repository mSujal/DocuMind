"""Main entry point for the application"""
import os
import platform
import sys
import config
from PyQt5.QtWidgets import QApplication, QSplashScreen
from src.ui.splash.splash_screen import SplashScreen

if __name__ == "__main__":
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    app.processEvents() 
    splash.start_loading()
    sys.exit(app.exec_())


