import json
import os
from typing import List, Dict

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

_CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "source_corpus.json")


def _chunk_text(text: str, chunk_size: int, overlap: int = 50) -> List[str]:
    """Split text into fixed-size token-approximate chunks with overlap.
    Uses word count as proxy for token count (~1 word ≈ 1.3 tokens).
    """
    words = text.split()
    word_chunk = max(1, int(chunk_size / 1.3))
    word_overlap = max(0, int(overlap / 1.3))
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + word_chunk, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += word_chunk - word_overlap
    return chunks


class DocumentStore:
    """
    In-memory ChromaDB vector store backed by data/source_corpus.json.
    Documents are split into fixed-size chunks; retrieved_ids are mapped
    back to parent doc_id so they match expected_retrieval_ids in golden_set.

    chunk_size: approximate token size per chunk (500 for V1, 200 for V2)
    """

    def __init__(
        self,
        corpus_path: str = _CORPUS_PATH,
        chunk_size: int = 500,
        collection_name: str = "rag_corpus",
    ):
        self.chunk_size = chunk_size
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
        # chunk_id → parent doc_id mapping
        self._chunk_to_doc: Dict[str, str] = {}
        self._load_corpus(corpus_path)

    def _load_corpus(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            docs = json.load(f)

        chunk_ids, chunk_texts, chunk_metas = [], [], []
        for doc in docs:
            doc_id = doc["doc_id"]
            chunks = _chunk_text(doc["text"], self.chunk_size)
            for i, chunk in enumerate(chunks):
                cid = f"{doc_id}_c{i}"
                self._chunk_to_doc[cid] = doc_id
                chunk_ids.append(cid)
                chunk_texts.append(chunk)
                chunk_metas.append({"doc_id": doc_id, "chunk_index": i, "title": doc["title"]})

        existing = set(self._collection.get(ids=chunk_ids)["ids"])
        new = [(i, t, m) for i, t, m in zip(chunk_ids, chunk_texts, chunk_metas) if i not in existing]
        if new:
            ids_, texts_, metas_ = zip(*new)
            self._collection.add(ids=list(ids_), documents=list(texts_), metadatas=list(metas_))

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Return top_k results, deduped by parent doc_id.
        Each result: {doc_id, content, score, title, chunk_id}
        """
        # Fetch more candidates to account for dedup
        n = min(top_k * 3, self._collection.count())
        results = self._collection.query(
            query_texts=[query],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )

        seen_doc_ids = set()
        output = []
        for cid, text, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            doc_id = self._chunk_to_doc.get(cid, meta.get("doc_id", cid))
            if doc_id in seen_doc_ids:
                continue
            seen_doc_ids.add(doc_id)
            output.append({
                "doc_id": doc_id,
                "chunk_id": cid,
                "content": text,
                "score": round(1.0 - dist, 4),
                "title": meta.get("title", ""),
            })
            if len(output) >= top_k:
                break
        return output


if __name__ == "__main__":
    print("=== chunk_size=500 (V1) ===")
    store_v1 = DocumentStore(chunk_size=500)
    for h in store_v1.retrieve("What is HNSW indexing?", top_k=3):
        print(f"  [{h['doc_id']}] chunk={h['chunk_id']}  score={h['score']:.3f} — {h['title'][:50]}")

    print("\n=== chunk_size=200 (V2) ===")
    store_v2 = DocumentStore(chunk_size=200)
    for h in store_v2.retrieve("What is HNSW indexing?", top_k=3):
        print(f"  [{h['doc_id']}] chunk={h['chunk_id']}  score={h['score']:.3f} — {h['title'][:50]}")
