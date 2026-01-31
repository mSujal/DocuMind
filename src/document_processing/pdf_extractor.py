"""
Text Extractor
"""

import pymupdf4llm
import config

class Text_Extractor:
    """
    Extracts text from PDF files as Markdown using PyMuPDF4LLM, with improved handling of complex layouts and structure preservation.
    """
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.md_text = pymupdf4llm.to_markdown(pdf_path)

    def print_md(self):
        return self.md_text