from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RepoUploadResponse(BaseModel):
    repo_name: str
    message: str
    parsed_files_count: int
    chunks_count: int
    summary: str
    files: List[str]

class Citation(BaseModel):
    file: str
    start_line: int
    end_line: int
    snippet: str

class ChunkResponse(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]
    distance: float

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    retrieved_chunks: List[ChunkResponse]
