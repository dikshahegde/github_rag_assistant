from pathlib import Path
from typing import List, Optional
from app.core.logger import logger
from app.ingestion.code_chunker import CodeChunker, Chunk
from app.core.constants import SUPPORTED_EXTENSIONS

class FileParser:
    @staticmethod
    def read_file_safe(file_path: Path) -> Optional[str]:
        """Safely reads file contents, falling back to latin-1 if UTF-8 fails."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                logger.debug(f"UTF-8 decode failed for {file_path}. Trying latin-1.")
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path} with latin-1: {e}")
                return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    @classmethod
    def parse_file(cls, file_path: Path, repo_path: Path) -> List[Chunk]:
        """Reads a file and parses it into Chunks using the CodeChunker."""
        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return []

        content = cls.read_file_safe(file_path)
        if content is None:
            return []

        # Get relative path for metadata
        try:
            relative_path = file_path.relative_to(repo_path)
        except ValueError:
            relative_path = file_path

        # Standardize path separators to forward slash for consistency in UI and vector DB
        rel_path_str = str(relative_path).replace("\\", "/")
        
        chunks = CodeChunker.chunk_file(file_path, content)
        
        # Override file_path to be the relative path
        for chunk in chunks:
            chunk.file_path = rel_path_str
            
        return chunks
