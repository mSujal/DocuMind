"""
Background worker that initializes the APP while splash screen shows
"""
from PyQt5.QtCore import QThread, pyqtSignal

import time 

class LoadWorker(QThread):
    status = pyqtSignal(str) # update taglineLabel in splash.ui
    finished = pyqtSignal(object, object, object)

    def run(self):
        from pathlib import Path 
        from dotenv import load_dotenv
        import os 
        import config 

        load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")
        api_key = os.getenv("GROQ_API_KEY")
        PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
        DB_PATH = PROJECT_ROOT / "chroma_db"

        self.status.emit("Loading tokenizer...")
        from src.doc_processing.late_chunking import LateChunking 

        self.status.emit("Loading model weights...")
        late_chunking = LateChunking(
            model_name=config.MODEL,
            tokenizer_name=config.TOKENIZER 
        )

        self.status.emit("Connecting to vector store...")
        from src.doc_processing.vector_store import VectorStore 
        vector_store = VectorStore(persist_dir=str(DB_PATH))

        self.status.emit("Initializing the RAG pipeline")
        from src.doc_processing.ragpipeline import RAGPipeline 
        rag_pipeline = RAGPipeline(
            late_chunking=late_chunking,
            api_key=api_key,
            vector_store=vector_store
        )

        self.status.emit("Ready!")
        time.sleep(1)
        self.finished.emit(late_chunking, vector_store, rag_pipeline)
