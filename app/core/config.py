import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GEMINI_API_KEY: str = Field(default="")
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="info")

    # Comma-separated list of allowed CORS origins (e.g. "https://app.example.com,https://example.com")
    # Defaults to "*" to preserve the original local-development behavior.
    ALLOWED_ORIGINS: str = Field(default="*")

    @property
    def allowed_origins_list(self) -> list:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    CHROMA_DB_PATH: str = Field(default="data/chroma_db")
    CLONED_REPOS_PATH: str = Field(default="data/repositories/cloned_repos")
    PROCESSED_CHUNKS_PATH: str = Field(default="data/processed_chunks")

    @property
    def chroma_db_dir(self) -> Path:
        path = Path(self.CHROMA_DB_PATH)
        if not path.is_absolute():
            path = self.BASE_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cloned_repos_dir(self) -> Path:
        path = Path(self.CLONED_REPOS_PATH)
        if not path.is_absolute():
            path = self.BASE_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def processed_chunks_dir(self) -> Path:
        path = Path(self.PROCESSED_CHUNKS_PATH)
        if not path.is_absolute():
            path = self.BASE_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

settings = Settings()
