import re
from pathlib import Path

from app.core.config import settings

_REPO_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def validate_repo_name(repo_name: str) -> str:
    if not _REPO_NAME_PATTERN.fullmatch(repo_name) or repo_name in {".", ".."}:
        raise ValueError("Invalid repository name.")
    return repo_name


def repository_path(repo_name: str) -> Path:
    name = validate_repo_name(repo_name)
    root = settings.cloned_repos_dir.resolve()
    path = root / name
    resolved_path = path.resolve()
    if path.is_symlink() or not resolved_path.is_relative_to(root):
        raise ValueError("Invalid repository name.")
    return path


def chat_history_path(repo_name: str) -> Path:
    name = validate_repo_name(repo_name)
    root = settings.processed_chunks_dir.resolve()
    path = root / f"{name}_chat.json"
    resolved_path = path.resolve()
    if path.is_symlink() or not resolved_path.is_relative_to(root):
        raise ValueError("Invalid repository name.")
    return path
