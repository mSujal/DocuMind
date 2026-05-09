import pymupdf4llm
import pytesseract
from pdf2image import convert_from_path

class Extraction:

    @staticmethod
    def _ocr_page(pdf_path, page_num):
        """
        Fallback OCR for a single page using Tesseract.
        """
        images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=300)
        if not images:
            return ""
        return pytesseract.image_to_string(images[0]).strip()

    @staticmethod
    def extract_text(pdf_path):
        """
        Returns list of (page_num, clean_text) tuples, one per oage chunk.
        Fall back to Tesseract OCR for pages with no extractable text.
        """
        page_chunks = pymupdf4llm.to_text(pdf_path, page_chunks=True, show_progress=False)

        results = []
        for chunk in page_chunks:
            page_num = chunk["metadata"]["page_number"]
            text = chunk["text"].strip()

            if len(text) < 50: # likely scanned or image-only 
                text = Extraction._ocr_page(pdf_path, page_num)

            if text:
                results.append((page_num, text))

        return results
