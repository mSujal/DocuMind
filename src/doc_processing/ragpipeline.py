"""
Main RAG pipeline handling retrieval to query
"""
import os
import platform

# suppress the cuda for dll error in windows
if platform.system() == "Windows":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch
import torch.nn.functional as F
from groq import Groq
import config


class RAGPipeline():
    def __init__(self, late_chunking, api_key, top_k=config.TOP_K):
        self.lc = late_chunking
        self.client = Groq(api_key=api_key)
        self.top_k = top_k
        self.chunk_embeddings = None

    def index(self, corpus):
        self.corpus = corpus
        self.chunk_embeddings = self.lc.run(corpus)

    def _embed_query(self, query):
        """
        Embed the query using the same tokenizer/model as late chunking.

        Returns: query embedding tensor
        """
        
        prefixed_query = "search_query: " + query

        tokens = self.lc.tokenizer(
            prefixed_query,
            return_tensors="pt",
            return_offsets_mapping=False,
            truncation=True,
            max_length=8192
        )
        tokens = {k: v.to(self.lc.device) for k, v in tokens.items()}

        with torch.no_grad():
            outputs = self.lc.model(
                input_ids=tokens["input_ids"],
                attention_mask=tokens["attention_mask"]
            )
        query_embedding = outputs.last_hidden_state[0].mean(dim=0)

        return query_embedding

    def _retrieve(self, query):
        """
        Retrieve top-k chunks by cosine similarity.
        """
        query_embedding = self._embed_query(query)
        similarities = []

        for i, chunk_emb in enumerate(self.chunk_embeddings):
            score = F.cosine_similarity(
                query_embedding.unsqueeze(0),
                chunk_emb.unsqueeze(0)
            )
            similarities.append((score.item(), i))

        similarities.sort(reverse=True)
        top_chunks = similarities[:self.top_k]

        retrieved = [self.lc.chunks[i] for (_, i) in top_chunks]

        return retrieved

    def query_qna(self, question):
        """
        Q&A prompt: answer the question strictly from retrieved context.
        """
        retrieved_chunks = self._retrieve(question)
        context = '\n\n'.join(retrieved_chunks)

        prompt = f"""
        You are a helpful assistant. Answer the question based strictly on the context provided below.
        Context: {context}
        Question: {question}
        Answer:
        """

        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def query_mcq(self, question):
        """
        MCQ prompt: generate a multiple choice question from retrieved context.
        """
        retrieved_chunks = self._retrieve(question)
        context = '\n\n'.join(retrieved_chunks)

        prompt = f"""
        You are a helpful assistant. Based only on context provided below, generate a multiple choice question with 4 options (A, B, C, D) and indicate the correct answer.

        Context: {context}

        Topic to generate MCQ about: {question}

        Format your response exactly like this:
        Question: <question here>
        A) <option>           B) <option>
        C) <option>           D) <option>
        Correct Answer: <letter>
        Explanation: <brief explanation based on context>
        """

        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
