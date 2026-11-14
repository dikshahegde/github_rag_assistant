from pydantic import BaseModel, Field, field_validator
from app.core.paths import validate_repo_name

class RepoUploadRequest(BaseModel):
    url: str = Field(..., min_length=1, description="The git URL of the GitHub repository (HTTPS format)")
    force_clone: bool = Field(default=False, description="Whether to clone and overwrite existing directory")

    @field_validator("url")
    @classmethod
    def trim_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Repository URL cannot be empty.")
        return value

class ChatQueryRequest(BaseModel):
    repo_name: str = Field(..., min_length=1, description="Name of the repository to query")
    query: str = Field(..., min_length=1, description="Question about the repository")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of source chunks to retrieve")

    @field_validator("repo_name")
    @classmethod
    def validate_repository_name(cls, value: str) -> str:
        return validate_repo_name(value)

    @field_validator("query")
    @classmethod
    def trim_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query cannot be empty.")
        return value
