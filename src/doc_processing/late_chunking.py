"""
Late chunking implementation
"""
import os
import platform

from transformers import AutoTokenizer, AutoModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
import torch
import config

class LateChunking():
    def __init__(self, model_name, tokenizer_name, chunk_size=512, chunk_overlap=50):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)

        # Use GPU if available else CPU 
        self.device = config.DEVICE
        self.model = self.model.to(self.device)
        self.model.eval() 

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
            is_separator_regex=False
        )

        self.chunks = []

    def _chunk(self, corpus):
        """
        Recursive character-level text splitting using LangChain.
        Tries separators in order: paragraphs → lines → sentences → words → characters.

        Args:
            corpus: extracted text from pdf file
        """
        self.chunks = self.splitter.split_text(corpus)

    def _tokenize(self, corpus):
        """
        Tokenize the full corpus (not individual chunks) for late chunking.

        Args:
            corpus: extracted text from pdf file
        """
        prefixed_corpus = "search_document: " + corpus

        self.tokens = self.tokenizer(
            prefixed_corpus,
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=8192  
        )
       
        self._offset_mapping = self.tokens.pop("offset_mapping")
        self.tokens = {k: v.to(self.device) for k, v in self.tokens.items()}

    def _find_token_boundaries(self, corpus):
        """
        Map each text chunk's character span to token indices in the full corpus.
        """
        self.chunk_boundaries = []
        current_pos = 0
        for chunk in self.chunks:
            start_char = corpus.find(chunk, current_pos)
            if start_char == -1:
                start_char = corpus.find(chunk)
            end_char = start_char + len(chunk)
            self.chunk_boundaries.append((start_char, end_char))
            current_pos = end_char

        offset_mapping = self._offset_mapping[0]
        self.token_boundaries = []
        for (chunk_start, chunk_end) in self.chunk_boundaries:
            token_start = None
            token_end = None
            for i, (tok_start, tok_end) in enumerate(offset_mapping):
                tok_start = tok_start.item()
                tok_end = tok_end.item()
                if tok_start == 0 and tok_end == 0:  # skip special tokens
                    continue
                if tok_start >= chunk_start and token_start is None:
                    token_start = i
                if tok_end <= chunk_end:
                    token_end = i
           
            if token_start is None or token_end is None:
                token_start = token_start or 1
                token_end = token_end or token_start
            self.token_boundaries.append((token_start, token_end))

    def _embed(self):
        """
        Run the full corpus through the model, then mean-pool each chunk's
        token embeddings — this is the core of late chunking.
        """
        with torch.no_grad():
            outputs = self.model(
                input_ids=self.tokens["input_ids"],
                attention_mask=self.tokens["attention_mask"]
            )
        all_token_embeddings = outputs.last_hidden_state[0] 
        self.chunk_embeddings = []
        for (token_start, token_end) in self.token_boundaries:
            chunk_token_embeddings = all_token_embeddings[token_start:token_end + 1]
            chunk_embedding = chunk_token_embeddings.mean(dim=0)
            self.chunk_embeddings.append(chunk_embedding)

        print(self.chunk_embeddings)
        return self.chunk_embeddings

    def run(self, corpus):
        """
        Full late-chunking pipeline.

        Returns:
            chunk_embeddings: list of embedding tensors, one per chunk
        """
        self._chunk(corpus)
        self._tokenize(corpus)
        self._find_token_boundaries(corpus)
        chunk_embeddings = self._embed()

        return chunk_embeddings
