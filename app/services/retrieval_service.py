from typing import List, Dict, Any
from app.vectorstore.retriever import Retriever

class RetrievalService:
    @staticmethod
    def retrieve_context(repo_name: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves semantic chunks for RAG queries."""
        return Retriever.retrieve(repo_name, query, top_k=top_k)
