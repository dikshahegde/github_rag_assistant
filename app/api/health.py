from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("")
def health_check():
    """Simple API check reporting service health status and API Key configuration status."""
    return {
        "status": "healthy",
        "gemini_key_configured": bool(settings.GEMINI_API_KEY.strip())
    }
