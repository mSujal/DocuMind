"""
Run the pipeline to save mcq from the provided pdf and specified number of questions
"""
import argparse
from time import time
import os

import config
from src.doc_processing.late_chunking import LateChunking
from src.doc_processing.ragpipeline import RAGPipeline
from src.doc_processing.vector_store import VectorStore
from src.doc_processing.text_extraction import Extraction
from src.doc_processing.mcq_store import MCQStore

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
api_key = os.getenv("GROQ_API_KEY")

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "chroma_db"

class Headless():
    def __init__(self, ragpipeline):
        self.current_pdf = None
        self.rag_pipeline = ragpipeline
        self.pages = None 

    def load_pdf(self, pdf_path): 
        self.current_pdf = pdf_path
        print(f"[Headess] PDF set to: {[pdf_path]}")

    def extract(self):
        print("\n\n[Headless] Extraction Started...")
        self.pages = Extraction.extract_text(self.current_pdf)
        print(f"[Headless] Extraction done - {len(self.pages)} pages")

    
    def index(self):
        print("\n\n[Headless] Indexing started...")
        self.rag_pipeline.index(self.pages, self.current_pdf)
        print("[Headless Indexing done]")

    def generate_mcq(self, topic="all topic", num_questions=5, save_json=False, output_dir="mcq_output"):
        print(f"[Headless] Generating {num_questions} MCQS on: {topic if topic != 'any topic' else 'General topics from PDF'}")
        result = self.rag_pipeline.query_mcq(
            question=topic, 
            num_questions=num_questions,
            save_json=save_json,
            output_dir=output_dir
        )
        print(f"[Headless] Generated {num_questions} MCQS on {topic if topic != 'any topic' else 'General topics from PDF'}\n\t Stored in mcq_output directory")
        return result
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Headless MCQ Generator")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--topic", help="Topic to generate MCQ about")
    parser.add_argument("--num", type=int, default=5, help="Number of MCQS to generate. Default 5")
    parser.add_argument("--save", action="store_true", help="Save output as JSON")
    parser.add_argument("--output-dir", default="mcq_output", help="Output directory for storing MCQs")
    args = parser.parse_args()

    lc = LateChunking(
        model_name=config.MODEL,
        tokenizer_name=config.TOKENIZER
    )
    vs = VectorStore()
    ms = MCQStore()
    rag = RAGPipeline(
        late_chunking=lc,
        api_key=api_key,
        vector_store=vs,
        mcq_store=ms
    )
    
    headless = Headless(ragpipeline=rag)
    headless.load_pdf(args.pdf)

    if not vs.is_indexed(args.pdf):
        headless.extract()


    headless.index()
    result = headless.generate_mcq(
        topic=args.topic or "all_topics",
        num_questions=args.num, 
        save_json=args.save,
        output_dir=args.output_dir
    )
    
