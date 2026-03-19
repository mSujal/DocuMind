"""
ChromaDB vector store
"""
from dis import haslocal
import hashlib
from unittest import expectedFailure, result
import chromadb
from chromadb.config import Settings
import config
 
class VectorStore:
    def __init__(self, persist_dir = config.PERSIST_DIR):
        """
        Args:
            persist_dir: folder where chromadb stores data ie embeddings
        """
        self.client = chromadb.PersistentClient(
            path = persist_dir,
            settings = Settings(anonymized_telemetry=False)
        )

    def _pdf_id(self, pdf_path):
        """
        Convert pdf path into stable collection name 
        """
        digest = hashlib.md5(pdf_path.encode()).hexdigest()[:8]
        stem = "".join(c if c.isalnum() else "-" for c in pdf_path)[-40:]
        return f"{digest}-{stem}"[:63]

    def _get_or_create_collection(self, pdf_path):
        name = self._pdf_id(pdf_path)
        return self.client.get_or_create_collection(
                name = name,
                metadata = {"pdf_path": pdf_path},
                embedding_function = None 
        )

    def is_indexed(self, pdf_path):
        """Return true if the pdf has already been embedded adn stored"""
        name = self._pdf_id(pdf_path)
        existing = [c.name for c in self.client.list_collections()]
        if name not in existing:
            return False
        col = self.client.get_collection(name=name, embedding_function=None)
        return col.count() > 0

    def store(self, pdf_path, chunks, embeddings, chunk_pages):
        """
        Persists chunks and their embeddings for pdf 

        Args:
            pdf_path : path used as collction key
            chunks : chunks from LateChunking.chunks
            embeddings: embeddings from LateChunking.chunk_embeddings
        """
        col = self._get_or_create_collection(pdf_path)

        # tensor => python list for storing in chromadb
        embeddings_list = [e.cpu().float().tolist() for e in embeddings]
        ids = [f"chunk-{i}" for i in range(len(chunks))]
        metadatas = [{"chunk_index": i, "page": chunk_pages[i]} for i in range(len(chunks))]

        # upsert for re-indexing the same pdf is safe
        col.upsert(
            ids = ids,
            documents=chunks,
            embeddings=embeddings_list,
            metadatas=metadatas,
        )
        print(f"[VectorStore] stored {len(chunks)} chunks for '{pdf_path}'")

    def load(self, pdf_path):
        """
        Load stored chunks and embeddings for pdfs

        Return:
            (chunks, embeddings) where embeddings are python list
        """
        col = self._get_or_create_collection(pdf_path)
        result = col.get(include=["documents", "embeddings", "metadatas"])
        pages = [m["page"] for m in result["metadatas"]]

        chunks = result["documents"]
        embeddings = result["embeddings"]
        print(f"[VectorStore] Loaded {len(chunks)} chunks for '{pdf_path}'")
        return chunks, embeddings, pages

    def query(self, pdf_path, query_embedding, top_k):
        """
        If we want chromadb to handle similarity search natively.

        Args:
            query_embedding: python list
            top_k : number of result

        Returns:
            list of matching chunk texts
        """
        col = self._get_or_create_collection(pdf_path)
        results = col.query(
                query_embedding = [query_embedding],
                n_results = top_k,
                include=["documents"]
        )
        return results["documents"][0]

    def delete(self, pdf_path):
        """Remove all stored data for pdf for re-indexing"""
        name = self._pdf_id(pdf_path)
        try:
            self.client.delete_collection(name)
            print(f"[VectorStore] Deleted collection for '{pdf_path}'")
        except Exception:
            pass

