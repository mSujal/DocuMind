"""
ChromaDB store for MCQ question embeddings + option fingerprints.
Used by RAGPipeline to deduplicate generated MCQs across sessions.
"""
import hashlib
import chromadb
from chromadb.config import Settings
import config


class MCQStore:
    def __init__(self, persist_dir=config.PERSIST_DIR):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

    def _collection_name(self, pdf_path):
        digest = hashlib.md5(pdf_path.encode()).hexdigest()[:8]
        stem = "".join(c if c.isalnum() else "-" for c in pdf_path)[-40:]
        return f"mcq-{digest}-{stem}"[:63]

    def _get_or_create_collection(self, pdf_path):
        return self.client.get_or_create_collection(
            name=self._collection_name(pdf_path),
            metadata={"pdf_path": pdf_path},
            embedding_function=None
        )

    def option_fingerprint(self, options, correct_answer):
        """Hash of sorted options + correct answer to catch same-choices duplicates."""
        raw = correct_answer + "|" + "|".join(f"{k}:{v}" for k, v in sorted(options.items()))
        return hashlib.md5(raw.encode()).hexdigest()

    def get_stored_embeddings(self, pdf_path):
        """
        Returns (embeddings, fingerprints) for all stored MCQ questions for this PDF.
        embeddings  : list of list[float]
        fingerprints: set of str
        """
        col = self._get_or_create_collection(pdf_path)
        if col.count() == 0:
            return [], set()

        result = col.get(include=["embeddings", "metadatas"])
        embeddings   = result["embeddings"]
        fingerprints = {m["option_fingerprint"] for m in result["metadatas"]}
        return embeddings, fingerprints

    def store(self, pdf_path, questions):
        """
        Persist a list of deduplicated MCQ dicts (must have 'embedding' key).
        """
        col = self._get_or_create_collection(pdf_path)
        existing_count = col.count()

        ids, embeddings, documents, metadatas = [], [], [], []
        for i, q in enumerate(questions):
            ids.append(f"mcq-{existing_count + i}")
            embeddings.append(q["embedding"])
            documents.append(q["question"])
            metadatas.append({
                "option_fingerprint": self.option_fingerprint(q["options"], q["correct_answer"])
            })

        col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        print(f"[MCQStore] stored {len(questions)} new question(s) for '{pdf_path}'")