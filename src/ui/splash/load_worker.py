"""
Background worker that initializes the APp while splash screen shows
"""
from PyQt5.QtCore import QThread, pyqtSignal

class LoadWorker(QThread):
    status = pyqtSignal(str) # update taglineLabel
    finished = pyqtSignal(object)

    def run(self):
        self.status.emit("Modules...")
        from src.app import App

        self.status.emit("Tokenizer & Model...")
        instance = App()

        self.status.emit("Ready!")
        self.finished.emit(instance)
