import os
import shutil
import re
from pathlib import Path
from git import Repo
from app.core.config import settings
from app.core.logger import logger
from app.core.constants import IGNORE_PATTERNS


class GitHubLoader:
    @staticmethod
    def get_repo_name_from_url(url: str) -> str:
        clean_url = url.rstrip("/")
        match = re.search(r"/([^/]+?)(?:\.git)?$", clean_url)
        if match:
            return match.group(1)
        return "temp_repo"

    @classmethod
    def clone_repository(cls, url: str, force_clone: bool = False) -> Path:
        repo_name = cls.get_repo_name_from_url(url)
        target_path = settings.cloned_repos_dir / repo_name

        if target_path.exists():
            if force_clone:
                logger.info(f"Removing existing directory at {target_path} for force clone.")
                try:
                    def make_writable(func, path, exc_info):
                        import stat
                        if not os.access(path, os.W_OK):
                            os.chmod(path, stat.S_IWRITE)
                            func(path)
                        else:
                            raise exc_info[1]
                    shutil.rmtree(target_path, onerror=make_writable)
                except Exception as e:
                    logger.warning(f"Error removing {target_path}: {e}")
                    shutil.rmtree(target_path, ignore_errors=True)
            else:
                logger.info(f"Repository already exists at {target_path}. Skipping clone.")
                return target_path

        logger.info(f"Cloning repository from {url} to {target_path}...")
        try:
            Repo.clone_from(url, target_path, depth=1)
            logger.info("Clone completed successfully.")
            return target_path
        except Exception as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)
            raise e

    @staticmethod
    def should_ignore(path: Path, root_path: Path) -> bool:
        try:
            relative_path = path.relative_to(root_path)
            for part in relative_path.parts:
                if part in IGNORE_PATTERNS:
                    return True
        except ValueError:
            return True
        return False

    @classmethod
    def get_repo_files(cls, repo_path: Path) -> list:
        logger.info(f"Scanning repository: {repo_path}")
        files_list = []

        for root, dirs, files in os.walk(repo_path):
            current_dir = Path(root)

            # Prune ignored directories in-place so os.walk doesn't recurse into them
            dirs[:] = [
                d for d in dirs
                if not cls.should_ignore(current_dir / d, repo_path)
            ]

            # Skip if current directory itself should be ignored
            if cls.should_ignore(current_dir, repo_path):
                continue

            for file in files:
                file_path = current_dir / file
                if not cls.should_ignore(file_path, repo_path):
                    files_list.append(file_path)
                    logger.debug(f"Including file: {file_path}")

        logger.info(f"Found {len(files_list)} total files.")
        for f in files_list:
            logger.info(f)
        return files_list