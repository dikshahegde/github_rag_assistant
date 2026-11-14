from fastapi import APIRouter, HTTPException
from app.models.request_models import ChatQueryRequest
from app.models.response_models import ChatResponse
from app.services.rag_service import RAGService
from app.core.logger import logger
from app.core.paths import chat_history_path
import json
from typing import List, Dict, Any

router = APIRouter()

@router.post("", response_model=ChatResponse)
def query_repository(payload: ChatQueryRequest):
    """Processes a user question about a repository using retriever-guided generation."""
    try:
        logger.info(f"RAG query request for '{payload.repo_name}'")
        result = RAGService.answer_query(
            repo_name=payload.repo_name,
            query=payload.query,
            top_k=payload.top_k
        )
        return ChatResponse(
            answer=result["answer"],
            citations=result["citations"],
            retrieved_chunks=result["retrieved_chunks"]
        )
    except Exception as e:
        logger.error(f"Error executing chat query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while answering your query: {str(e)}"
        )


@router.get("/{repo_name}/history")
def get_chat_history(repo_name: str):
    """Load saved chat history for a repo."""
    try:
        chat_path = chat_history_path(repo_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not chat_path.exists():
        return []
    try:
        with open(chat_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error loading chat history for {repo_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load chat history.")


@router.post("/{repo_name}/history")
def save_chat_history(repo_name: str, messages: List[Dict[str, Any]]):
    """Save chat history for a repo."""
    try:
        chat_path = chat_history_path(repo_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        chat_path.parent.mkdir(parents=True, exist_ok=True)
        with open(chat_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
        return {"status": "saved"}
    except (OSError, TypeError, ValueError) as e:
        logger.error(f"Error saving chat history for {repo_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save chat history: {str(e)}"
        )