from fastapi import APIRouter, HTTPException
from app.models.request_models import RepoUploadRequest
from app.models.response_models import RepoUploadResponse
from app.services.repository_service import RepositoryService
from app.core.logger import logger
from app.core.config import settings
from app.vectorstore.chroma_manager import chroma_manager
from typing import List, Dict, Any
import os
router = APIRouter()

@router.post("", response_model=RepoUploadResponse)
def upload_repository(payload: RepoUploadRequest):
    """Clones a remote repository, parses supported files, chunks them, and generates an architectural summary."""
    try:
        logger.info(f"Starting ingestion process for repository URL: {payload.url}")
        result = RepositoryService.process_repository(
            repo_url=payload.url,
            force_clone=payload.force_clone
        )
        return RepoUploadResponse(
            repo_name=result["repo_name"],
            message=f"Repository '{result['repo_name']}' loaded and indexed successfully.",
            parsed_files_count=result["parsed_files_count"],
            chunks_count=result["chunks_count"],
            summary=result["summary"],
            files=result["files"]
        )
    except Exception as e:
        logger.error(f"Error processing repository: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clone and index repository. Error details: {str(e)}"
        )

@router.get("", response_model=List[Dict[str, Any]])
def list_repositories():
    """Lists all previously ingested repositories and summaries from cache."""
    try:
        return RepositoryService.get_cloned_repositories()
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{repo_name}/files/{file_path:path}")
def get_file_content(repo_name: str, file_path: str):
    """Returns the raw content of a specific code or documentation file."""
    try:
        content = RepositoryService.get_file_content(repo_name, file_path)
        return {"content": content}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error reading file '{file_path}' in repo '{repo_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{repo_name}")
def delete_repository(repo_name: str):
    """Deletes a repository's cloned files, metadata, chat history, and vector store."""
    import shutil
    import stat

    def force_remove_readonly(func, path, exc_info):
        """Handle read-only files on Windows by chmod before retrying."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    # Delete metadata file
    meta_path = settings.processed_chunks_dir / f"{repo_name}_meta.json"
    if meta_path.exists():
        meta_path.unlink()

    # Delete chat history file
    chat_path = settings.processed_chunks_dir / f"{repo_name}_chat.json"
    if chat_path.exists():
        chat_path.unlink()

    # Delete cloned repo folder (including read-only .git files on Windows)
    repo_path = settings.cloned_repos_dir / repo_name
    if repo_path.exists():
        shutil.rmtree(repo_path, onexc=force_remove_readonly)

    # Delete vector store collection
    try:
        chroma_manager.delete_collection(repo_name)
    except Exception as e:
        logger.warning(f"Could not delete chroma collection for {repo_name}: {e}")

    logger.info(f"Deleted repository '{repo_name}' and all associated data.")
    return {"status": "deleted", "repo_name": repo_name}