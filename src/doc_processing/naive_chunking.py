from transformers import AutoTokenizer, AutoModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
import torch
import os
import config


class NaiveChunking:
    """
    Baseline chunker: splits text then embeds each chunk independently.

    Intentionally mirrors LateChunking's interface (same attributes and run()
    signature) so it drops straight into RAGPipeline without any changes there.

    The only real difference from LateChunking is that each chunk is tokenized
    and embedded on its own — no full-document context window, no token
    boundary alignment. This is the classic "chunk -> embed" approach.
    """

    def __init__(
        self,
        model_name,
        tokenizer_name,
        chunk_size=384,
        chunk_overlap=50,
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)

        self.device = config.DEVICE
        self.model = self.model.to(self.device)
        self.model.eval()
        torch.set_num_threads(os.cpu_count())

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
            is_separator_regex=False,
        )

        # public attrs that RAGPipeline reads directly
        self.chunks           = []
        self.chunk_pages      = []
        self.chunk_embeddings = []

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _chunk(self, pages):
        self.chunks      = []
        self.chunk_pages = []
        for page_num, text in pages:
            splits = self.splitter.split_text(text)
            self.chunks.extend(splits)
            self.chunk_pages.extend([page_num] * len(splits))

    def _embed_chunk(self, text: str) -> torch.Tensor:
        """Embed a single chunk independently with no surrounding context."""
        prefixed = "search_document: " + text
        tokens = self.tokenizer(
            prefixed,
            return_tensors="pt",
            truncation=True,
            max_length=512,         # standard per-chunk limit
            add_special_tokens=True,
        )
        tokens = {k: v.to(self.device) for k, v in tokens.items()}
        with torch.inference_mode():
            outputs = self.model(**tokens)
        # mean-pool over token dimension -> (hidden_size,)
        return outputs.last_hidden_state[0].mean(dim=0)

    # ------------------------------------------------------------------
    # public API  (same signature as LateChunking.run())
    # ------------------------------------------------------------------

    def run(self, pages):
        """
        Chunk pages and embed each chunk independently.

        Args:
            pages: list of (page_num, text) tuples from Extraction.extract_text()

        Returns:
            list of torch.Tensor, one per chunk
        """
        self._chunk(pages)
        print(f"[NaiveChunking] {len(self.chunks)} chunks from {len(pages)} pages")

        self.chunk_embeddings = []
        for i, chunk in enumerate(self.chunks):
            emb = self._embed_chunk(chunk)
            self.chunk_embeddings.append(emb)
            if (i + 1) % 50 == 0 or (i + 1) == len(self.chunks):
                print(f"[NaiveChunking] embedded {i+1}/{len(self.chunks)} chunks", end="\r")

        print()
        print(f"[NaiveChunking] done -- {len(self.chunk_embeddings)} embeddings")
        return self.chunk_embeddings
