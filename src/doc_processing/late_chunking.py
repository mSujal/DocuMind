"""
Latechunking implementation
"""
from transformers import AutoTokenizer, AutoModel
import torch

class LateChunking():
    def __init__(self, model_name, tokenizer_name):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.model = AutoModel.from_pretrained(model_name)

    def _chunk(self, corpus):
        """
        Recursive text splitting chunking 

        Args: 
            corpus: extracted text from pdf file
        """
        pass

    def _tokenize(self, corpus):
        """
        Tokenize the chunks

        Args: 
            corpus: extracted text from pdf file
        """
        self.tokens = self.tokenizer(
            corpus,
            return_tensors="pt",
            return_offsets_mapping=True
        )

    def _find_token_boundries(self, corpus):
        """
        Find the token boundries and map the character to the boundries
        """
        self.chunk_boundaries = []
        current_pos = 0
        for chunk in self.chunks:
            start_char = corpus.find(chunk, current_pos)
            end_char = start_char + len(chunk)
            self.chunk_boundaries.append((start_char, end_char))
            current_pos = end_char

        offset_mapping = self.tokens["offset_mapping"][0]
        self.token_boundaries = []
        for (chunk_start, chunk_end) in self.chunk_boundaries:
            token_start = None
            token_end = None
            for i, (tok_start, tok_end) in enumerate(offset_mapping):
                if tok_start == 0 and tok_end == 0: # skip special tokens
                    continue
                if tok_start >= chunk_start and token_start is None:
                    token_start = i
                if tok_end <= chunk_end:
                    token_end = i
            self.token_boundaries.append((token_start, token_end))


        def _embed(self):
            """
            Embed the chunks 
            """
            with torch.no_grad(): # dont keep track of gradients
                output = self.model(
                    input_ids = self.tokens["input_ids"],
                    attention_mask = self.tokens["attention_mask"]
                )
            all_token_embeddings = outputs.last_hidden_state[0]
            self.chunk_embeddings = []
            for (token_start, token_end) in self.token_boundaries:
                chunk_token_embeddings = all_token_embeddings[token_start:token_end+1]
                chunk_embedding = chunk_token_embeddings.mean(dim=0)
                self.chunk_embeddings.append(chunk_embedding)

            return self.chunk_embeddings

        def run(self, corpus):
            """
            Pipeline function to be called

            Returns:
                chunk_embeddings : vector embedding for chunks
            """
            self._chunk(corpus)
            self._tokenize(corpus)
            self._find_token_boundaries(corpus)
            chunk_embeddings = self._embed()
            
            return chunk_embeddings
