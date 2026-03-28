"""
Splash screen widget loaded from splash.ui
"""
import os
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from src.ui.splash.load_worker import LoadWorker 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_PATH = os.path.join(BASE_DIR, "..", "..", "..", "assets", "splash.ui")

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        loadUi(UI_PATH, self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        self.move (
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2, 
        )

    def start_loading(self):
        self.worker = LoadWorker()
        self.worker.status.connect(self._on_status)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_status(self, message):
        self.taglineLabel.setText(message)

    def _on_finished(self, late_chunking, vector_store, rag_pipeline):
        from src.app import App
        self.app_instance = App(late_chunking, vector_store, rag_pipeline)
        self.close()
        self.app_instance.show()
