"""Implemntation for pdf renderer"""

from pathlib import Path
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

class PDF_viewer(QWebEngineView):
    """Basic chromium pdf renderer (temporary thing)"""
    def __init__(self, pdf_path, parent=None):
        super().__init__()
        self.pdf_path = pdf_path
        
        self.settings().setAttribute(
            QWebEngineSettings.PluginsEnabled, True
        )
        self.settings().setAttribute(
            QWebEngineSettings.PdfViewerEnabled, True
        )

        self.load(QUrl.fromLocalFile(str(pdf_path)))
