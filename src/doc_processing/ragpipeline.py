"""
Main RAG pipeline handling retrieval to query
"""
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
        Embed the query using same tokenizer model

        Returns: query embeddings vectors
        """
        tokens = self.lc.tokenizer(
            query, 
            return_tensors="pt", 
            return_offsets_mapping=False
        )

        with torch.no_grad(): # not keeping track of gradient
            outputs = self.lc.model(
                input_ids = tokens["input_ids"],
                attention_mask = tokens["attention_mask"]
            )
        query_embedding = outputs.last_hidden_state[0].mean(dim=0)
        
        return query_embedding

    def _retrieve(self, query):
        """
        Retrieve top 5 chunks based on similarity search
        """
        query_embedding = self._embed_query(query)
        similarities = []

        for i, chunk_emb in enumerate(self.chunk_embeddings):
            score = F.cosine_similarity(
                query_embedding.unsqueeze(0),
                chunk_emb.unsequeeze(0)
            )
            similarities.append((score.item(), i))

        similarities.sort(reverse=True)
        top_chunks = similarities[:self.top_k]

        retrieved = [self.lc.chunks[i] for (_, i) in top_chunks]

        return retrieved

    def query_qna(self, question):
        """
        Prompt for question answering

        Args:
            question: user input question to be passed to the LLM

        Function:
            retrieve chunks and create context, using the the context and question make prompt and call LLM for response
        """
        retrieved_chunks = self._retrieve(question)
        context = '\n\n'.join(retrieved_chunks)

        prompt = f"""
        You are a helpful assistant. Answer the question based strictly based on the context provided below.
        Context: {context}
        Question: {question}
        Answer:
        """

        response = self.client.chat.completions.create(
            model = config.LLM_MODEL,
            messages=[{"role":"user", "content":prompt}]
        )
        return response.choices[0].message.content

    def query_mcq(self, question):
        retrieved_chunks = self._retrieve(question)
        context = '\n\n'.join(retrieved_chunks)

        prompt = f"""
        You are a helpful assistant. Based only on context provided below, generate a multiple choice question with 4 options with (A, B, C, D) and indicate the correct answer.

        Context: {context}

        Topic to generate MCQ about: {question}

        Format your response exactly like this:
        Question: <question here>
        A) <option>           B) <option>
        c) <option>           D) <option>
        Correct Answer: <letter>
        Explanation: <brief explanation based on context>
        """

        response = self.client.chat.completions.create(
            model = config.LLM_MODEL,
            messages = [{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content