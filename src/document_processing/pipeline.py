from src.document_processing.processors import Text_Extractor, Chunker

def run_pipeline(pdf_path):
    extractor = Text_Extractor(pdf_path=pdf_path)
    chunker = Chunker

    md_Text = extractor.process()
    chunks = chunk.process(md_Text)

    print(chunks)