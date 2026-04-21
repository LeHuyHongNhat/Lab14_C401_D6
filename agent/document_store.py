import json
import os
from typing import List, Dict

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

_CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "source_corpus.json")


class DocumentStore:
    """
    In-memory ChromaDB vector store backed by data/source_corpus.json.
    Uses OpenAI text-embedding-3-small — no local model download required.
    doc_id values match expected_retrieval_ids in golden_set.jsonl.
    """

    def __init__(self, corpus_path: str = _CORPUS_PATH, collection_name: str = "rag_corpus"):
        self._client = chromadb.Client()  # in-memory
        self._ef = OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small",
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._load_corpus(corpus_path)

    def _load_corpus(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            docs = json.load(f)

        ids = [d["doc_id"] for d in docs]
        texts = [d["text"] for d in docs]
        metadatas = [{"title": d["title"], "doc_id": d["doc_id"]} for d in docs]

        existing = set(self._collection.get(ids=ids)["ids"])
        new_docs = [(i, t, m) for i, t, m in zip(ids, texts, metadatas) if i not in existing]
        if new_docs:
            new_ids, new_texts, new_metas = zip(*new_docs)
            self._collection.add(ids=list(new_ids), documents=list(new_texts), metadatas=list(new_metas))

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Return top_k results as list of {doc_id, content, score, title}."""
        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        output = []
        for doc_id, text, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({
                "doc_id": doc_id,
                "content": text,
                "score": round(1.0 - dist, 4),  # cosine distance → similarity
                "title": meta.get("title", ""),
            })
        return output


if __name__ == "__main__":
    store = DocumentStore()
    hits = store.retrieve("What is HNSW indexing?", top_k=3)
    for h in hits:
        print(f"[{h['doc_id']}] score={h['score']:.3f} — {h['title']}")
