from typing import Dict, Any, List
from app.services.retrieval_service import RetrievalService
from app.llm.response_generator import ResponseGenerator
from app.core.logger import logger

class RAGService:
    @staticmethod
    def answer_query(repo_name: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieves matching code chunks, asks Gemini to generate an answer, and extracts citations."""
        logger.info(f"RAG query: '{query}' in repo: '{repo_name}'")
        
        # 1. Retrieve context
        chunks = RetrievalService.retrieve_context(repo_name, query, top_k=top_k)
        
        if not chunks:
            return {
                "answer": "No relevant files or documentation chunks were found in the database. "
                          "Please ensure the repository contains files with supported extensions (.py, .js, .ts, .md, .java).",
                "citations": [],
                "retrieved_chunks": []
            }
            
        # 2. Ask LLM to generate answer
        answer, citations = ResponseGenerator.generate_rag_answer(query, chunks)
        
        return {
            "answer": answer,
            "citations": citations,
            "retrieved_chunks": chunks
        }
