"""Main entry point for the application"""
import os
import platform

# suppress the cuda for dll error in windows
if platform.system() == "Windows":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

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


# """Main entry point for the application"""
# import os
# import platform
#
# # suppress the cuda for dll error in windows
# if platform.system() == "Windows":
#     os.environ["CUDA_VISIBLE_DEVICES"] = ""
#
# import sys
# import config
# from PyQt5.QtWidgets import QApplication, QSplashScreen
# from src.ui.splash.splash_screen import SplashScreen
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#
#     splash = SplashScreen()
#     splash.show()
#     app.processEvents()
#     splash.start_loading()
#     sys.exit(app.exec_())
#     #
#     # splash_pix = QPixmap(400, 200)
#     # splash_pix.fill(QColor(config.BG_PRIMARY))
#     # splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
#     # splash.showMessage(
#     #     "DocuMind  —  Loading model...",
#     #     Qt.AlignCenter,
#     #     QColor(config.TEXT_PRIMARY)
#     # )
#     # splash.show()
#     # app.processEvents() 
#     #
#     # from src.app import App  
#     # window = App()
#     # window.show()
#     # splash.finish(window)
#     #
#     # sys.exit(app.exec_())
