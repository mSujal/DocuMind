from src.document_processing.processors import Text_Extractor, Chunker

class ProcessingPipeline():

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def run_pipeline(self):
        extractor = Text_Extractor(pdf_path=self.pdf_path)
        chunker = Chunker()

        md_Text = extractor.process()
        chunks = chunker.process(md_Text)
        
        # print(chunks) 
        return chunks
