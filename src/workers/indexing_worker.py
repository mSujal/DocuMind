"""
Background worker for PDF text extraction and RAG pipeline indexing.
Runs in a separate QThread to keep the UI responsive.
"""

from PyQt5.QtCore import QThread, pyqtSignal
from src.doc_processing.text_extraction import Extraction


class IndexingWorker(QThread):
    """
    Worker thread that runs:
        1. Extraction.extract_text()   — PDF -> cleaned corpus
        2. rag_pipeline.index()        — corpus -> chunk embeddings

    Signals:
        started_extraction  : extraction phase has begun
        started_indexing    : embedding/indexing phase has begun
        finished            : indexing complete
        error (str)         : fault in process 
    """

    started_extraction = pyqtSignal()
    started_indexing = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, rag_pipeline, pdf_path):
        super().__init__()
        self.rag_pipeline = rag_pipeline
        self.pdf_path = pdf_path

    def run(self):
        """
        Entry point 
        Called automatically by QThread.start().
        """
        try:
            # Phase 1: text extraction
            self.started_extraction.emit()
            corpus = Extraction.extract_text(self.pdf_path)

            # Phase 2: chunking + embedding 
            self.started_indexing.emit()
            self.rag_pipeline.index(corpus, pdf_path=self.pdf_path)

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))
