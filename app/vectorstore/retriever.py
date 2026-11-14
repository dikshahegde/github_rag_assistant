from typing import List, Dict, Any
from app.vectorstore.chroma_manager import chroma_manager
from app.core.logger import logger


class Retriever:
    @staticmethod
    def retrieve(repo_name: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Querying vector store for '{query}' in repo '{repo_name}'")
        results = chroma_manager.query_collection(repo_name, query, top_k)
        logger.info(f"Retrieved {len(results)} chunks")
        return results