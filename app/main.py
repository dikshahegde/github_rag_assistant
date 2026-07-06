import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.api import health, upload_repo, chat

# Initialize directories at import time
settings.chroma_db_dir
settings.cloned_repos_dir
settings.processed_chunks_dir

app = FastAPI(
    title="GitHub Repository RAG Assistant API",
    description="Backend service for cloning git repositories, performing AST-aware chunking, indexing in ChromaDB, and executing Gemini RAG queries.",
    version="1.0.0"
)

# Enable CORS. Origins are configurable via the ALLOWED_ORIGINS env var so the
# same image can be locked down in production instead of always allowing "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router, prefix="/api/health", tags=["Health Check"])
app.include_router(upload_repo.router, prefix="/api/upload", tags=["Repository Ingestion"])
app.include_router(chat.router, prefix="/api/chat", tags=["RAG Chat"])

@app.on_event("startup")
def startup_event():
    logger.info("Initializing GitHub Repository RAG Assistant API...")
    logger.info(f"Storage path configurations:")
    logger.info(f" - ChromaDB directory: {settings.chroma_db_dir}")
    logger.info(f" - Cloned repositories: {settings.cloned_repos_dir}")
    logger.info(f" - Processed chunk metadata: {settings.processed_chunks_dir}")
    logger.info("Backend service is ready to accept requests.")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
