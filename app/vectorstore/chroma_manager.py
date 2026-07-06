import json
import math
import os
from pathlib import Path
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logger import logger
from app.ingestion.code_chunker import Chunk


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class ChromaManager:
    def __init__(self):
        self.store_dir = settings.chroma_db_dir
        logger.info(f"Initializing JSON vector store at {self.store_dir}")

    def _get_store_path(self, repo_name: str) -> Path:
        safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in repo_name)
        return self.store_dir / f"{safe.lower()}.json"

    def delete_collection(self, repo_name: str):
        path = self._get_store_path(repo_name)
        if path.exists():
            path.unlink()
            logger.info(f"Deleted vector store for '{repo_name}'")
        else:
            logger.warning(f"No vector store found for '{repo_name}'")

    def add_chunks(self, repo_name: str, chunks: List[Chunk]):
        if not chunks:
            logger.warning("No chunks to index")
            return

        from app.ingestion.embedding_generator import EmbeddingGenerator

        path = self._get_store_path(repo_name)

        # Load existing records if any
        records = []
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                records = json.load(f)

        existing_ids = {r["id"] for r in records}

        documents = [c.text for c in chunks]
        metadatas = [c.to_dict() for c in chunks]
        ids = []
        for idx, c in enumerate(chunks):
            safe_file = c.file_path.replace("/", "_").replace(".", "_")
            ids.append(f"{safe_file}_{c.start_line}_{c.end_line}_{idx}")

        batch_size = 50
        new_records = []
        for i in range(0, len(chunks), batch_size):
            end_idx = min(i + batch_size, len(chunks))
            logger.info(f"Embedding batch {i}-{end_idx}")
            batch_texts = documents[i:end_idx]
            embeddings = EmbeddingGenerator.get_embeddings(batch_texts)
            for j, emb in enumerate(embeddings):
                record_id = ids[i + j]
                new_records.append({
                    "id": record_id,
                    "text": batch_texts[j],
                    "metadata": metadatas[i + j],
                    "embedding": emb
                })
            logger.info(f"Batch {i}-{end_idx} embedded successfully")

        # Upsert: replace existing ids, append new ones
        records_by_id = {r["id"]: r for r in records}
        for r in new_records:
            records_by_id[r["id"]] = r
        final_records = list(records_by_id.values())

        with open(path, "w", encoding="utf-8") as f:
            json.dump(final_records, f)

        logger.info(f"Indexed {len(new_records)} chunks for '{repo_name}'. Total: {len(final_records)}")

    def query_collection(self, repo_name: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        from app.ingestion.embedding_generator import EmbeddingGenerator

        path = self._get_store_path(repo_name)
        if not path.exists():
            logger.warning(f"No vector store found for '{repo_name}'")
            return []

        with open(path, "r", encoding="utf-8") as f:
            records = json.load(f)

        if not records:
            return []

        query_emb = EmbeddingGenerator.get_embeddings([query])[0]

        scored = []
        for r in records:
            sim = cosine_similarity(query_emb, r["embedding"])
            scored.append((sim, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        return [
            {
                "id": r["id"],
                "text": r["text"],
                "metadata": r["metadata"],
                "distance": 1.0 - sim
            }
            for sim, r in top
        ]


chroma_manager = ChromaManager()