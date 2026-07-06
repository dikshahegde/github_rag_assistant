from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class RepoUploadRequest(BaseModel):
    url: str = Field(..., description="The git URL of the GitHub repository (HTTPS format)")
    force_clone: Optional[bool] = Field(default=False, description="Whether to clone and overwrite existing directory")

class ChatQueryRequest(BaseModel):
    repo_name: str = Field(..., description="Name of the repository to query")
    query: str = Field(..., description="Question about the repository")
    top_k: Optional[int] = Field(default=5, description="Number of source chunks to retrieve")
