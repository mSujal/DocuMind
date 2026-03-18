"""Initalization of the application"""

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAction
from src.ui.main_window import MainWindow
from src.doc_processing.late_chunking import LateChunking
from src.doc_processing.ragpipeline import RAGPipeline
from src.doc_processing.vector_store import VectorStore
from src.workers.indexing_worker import IndexingWorker
import os
import config

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
api_key = os.getenv("GROQ_API_KEY")

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "chroma_db"


class App(QMainWindow):
    """
    Main Application class  

    Sets up the main windows, manage the application state and coordinate the ui compoments and loads the model

    Attributes:
        main_winodw (MainWindoe) : central widget containig the ui
        current_pdf (str): path to currently opned pdf
    """

    def __init__(self):
        """Initalization of applicaition main window and load the model"""
        super().__init__()
        self.current_pdf = None
        self._worker = None
        
        self.late_chunking = LateChunking(
            model_name=config.MODEL,
            tokenizer_name=config.TOKENIZER
        )

        self.vector_store = VectorStore(persist_dir=str(DB_PATH))

        self.rag_pipeline = RAGPipeline(
            late_chunking=self.late_chunking,
            api_key=api_key,
            vector_store=self.vector_store
        )

        self.main_window = MainWindow()
        self.setCentralWidget(self.main_window)

        self.main_window.pdf_opened.connect(self._on_pdf_opened)
        self.update_title()
        self.setGeometry(100, 100, 800, 600)

    def open_pdf(self, pdf_path):
        """
        Open pdf file and update window title dynamically 
        
        Args: 
            pdf_path (str): path to pdf file
        """
        self.main_window.load_pdf(pdf_path)

    def _on_pdf_opened(self, pdf_path):
        """
        Called whenever pdf is loaded in mainwindow.

        Triggered by MainWindow.pdf_opened signal
        Cancels any in-progress indexing and starts a fresh worker.

        Args:
            pdf_path (str): path to newly loaded pdf
        """
        self.current_pdf = pdf_path
        self.update_title()

        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()

        self._worker = IndexingWorker(self.rag_pipeline, pdf_path)
        self._worker.started_extraction.connect(self._on_extraction_started)
        self._worker.started_indexing.connect(self._on_indexing_started)
        self._worker.finished.connect(self._on_indexing_finished)
        self._worker.error.connect(self._on_indexing_error)
        self._worker.start()

    def _on_extraction_started(self):
        self.main_window.set_pipeline_status("Extracting text...")

    def _on_indexing_started(self):
        if self.vector_store.is_indexed(self.current_pdf):
            self.main_window.set_pipeline_status("Loading embeddings from store...")
        else:
            self.main_window.set_pipeline_status("Building embeddings...")

    def _on_indexing_finished(self):
        self.main_window.set_pipeline_status("Ready")

    def _on_indexing_error(self, message: str):
        self.main_window.set_pipeline_status(f"Error: {message}")

    def update_title(self):
        """Update window title based on opened pdf"""
        if self.current_pdf:
            filename = os.path.basename(self.current_pdf)
            self.setWindowTitle(f"{filename} - DocuMind")
        else:
            self.setWindowTitle("DocuMind")
