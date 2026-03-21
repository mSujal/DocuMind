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
    def __init__(self, late_chunking, api_key, vector_store, top_k=config.TOP_K):
        self.lc = late_chunking
        self.client = Groq(api_key=api_key)
        self.top_k = top_k
        self.vector_store = vector_store
        self.chunk_embeddings = None

    def index(self, pages, pdf_path):
        self.pdf_path = pdf_path
        corpus = "\n\n".join(text for _, text in pages) 

        # load from database instead of re-embedding
        if self.vector_store.is_indexed(pdf_path):
            self.lc.chunks, self.chunk_embeddings, self.lc.chunk_pages = self.vector_store.load(pdf_path)
        else: # embed using latechunking 
            self.chunk_embeddings = self.lc.run(pages)
            self.vector_store.store(pdf_path, self.lc.chunks, self.chunk_embeddings, self.lc.chunk_pages)
    

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
            
            if not isinstance(chunk_emb, torch.Tensor):
                chunk_emb = torch.tensor(chunk_emb, dtype=torch.float32).to(self.lc.device)
        
            score = F.cosine_similarity(
                query_embedding.unsqueeze(0),
                chunk_emb.unsqueeze(0)
            )
            similarities.append((score.item(), i))

        similarities.sort(reverse=True)
        top_chunks = similarities[:self.top_k]

        retrieved = [(self.lc.chunks[i], self.lc.chunk_pages[i]) for (_, i) in top_chunks]

        return retrieved

    def query_qna(self, question):
        """
        Q&A prompt: answer the question strictly from retrieved context.
        """
        retrieved_chunks = self._retrieve(question)
        context = '\n\n'.join(f"[Page {page}] {chunk}" for chunk, page in retrieved_chunks)

        prompt = f"""
        You are a helpful assistant. Answer the question based strictly on the context provided below.
        Each context chunk is prefixed with its page number like [Page N].
        Always cite the page number(s) you used at the end of your answer like: 
        (Source Page: [5]) and in case of multi page (Source Page: [4][5]  ...)
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
        context = '\n\n'.join(f"[Page {page}] {chunk}" for chunk, page in retrieved_chunks)

        prompt = f"""
        You are a helpful assistant. Based only on the context provided below, generate 5 multiple choice questions, each with exactly 4 options (A, B, C, D) and never should options be more than 4 and in explanation also mention difficulty with star icon.
        Each context chunk is prefixed with its page number like [Page N].
        At the end of each explanation cite the page like: 
        (Source Page: [5]) and in case of multi page (Source Page: [4][5]  ...)

        Context: {context}

        Topic to generate MCQ about: {question}

        Format your response exactly like this:
        Question: <question here> 
        A) <option>          
        B) <option>
        C) <option>           
        D) <option>
        Correct Answer: <letter>
        Explanation: [Easy/Medium/Hard] <brief explanation based on context>
        """

        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
