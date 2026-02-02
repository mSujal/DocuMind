"""
Modules for document processing

1. Text extactor
2. Chunking
3. Embedder 
4. Chromastore
"""

import pymupdf4llm
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import config

class Text_Extractor:
    """
    Extracts text from PDF files as Markdown using PyMuPDF4LLM, with improved handling of complex layouts and structure preservation.
    """
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def process(self):
        self.md_text = pymupdf4llm.to_markdown(self.pdf_path).replace("**", "")
        return self.md_text

    def get_mdtext(self):
        return self.md_text


class Chunker:
    """
    Chunk the extracted markdown file based on headers and subheaders in markdown text
    """
    def __init__(self):
        self.headers = [
            ("#", "header"),
            ("##", "subheader"),
            ("###", "subsubheader"),
        ]

    def process(self, md_text):
        md_splitter = MarkdownHeaderTextSplitter(self.headers)
        docs = md_splitter.split_text(md_text)

        chunk_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80
        )

        self.chunked_doc = chunk_splitter.split_documents(docs)
        return self.chunked_doc

    def get_chunks(self):
        return self.chunked_doc