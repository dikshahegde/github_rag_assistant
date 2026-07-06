import os
import json
from pathlib import Path
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logger import logger
from app.ingestion.github_loader import GitHubLoader
from app.ingestion.file_parser import FileParser
from app.vectorstore.chroma_manager import chroma_manager
from app.llm.gemini_client import GeminiClient
from app.llm.prompts import SUMMARY_SYSTEM_INSTRUCTION, SUMMARY_USER_PROMPT_TEMPLATE

class RepositoryService:
        
    @classmethod
    def process_repository(cls, repo_url: str, force_clone: bool = False) -> Dict[str, Any]:
        repo_name = GitHubLoader.get_repo_name_from_url(repo_url)
        repo_path = GitHubLoader.clone_repository(repo_url, force_clone=force_clone)

        if force_clone:
            chroma_manager.delete_collection(repo_name)

        all_files = GitHubLoader.get_repo_files(repo_path)
        logger.info(f"Found {len(all_files)} total files in {repo_name}.")

        # Parse only supported files for RAG indexing
        all_chunks = []
        parsed_files = []

        for file_path in all_files:
            file_chunks = FileParser.parse_file(file_path, repo_path)

            if file_chunks:
                all_chunks.extend(file_chunks)

                rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                parsed_files.append(rel_path)

        # Build full file list for sidebar (all files, not just parsed ones)
        all_file_paths = []

        for file_path in all_files:
            rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
            all_file_paths.append(rel_path)

        logger.info(
            f"Generated {len(all_chunks)} chunks from {len(parsed_files)} source files."
        )

        try:
            logger.info("Starting vector indexing")
            chroma_manager.add_chunks(repo_name, all_chunks)
            logger.info("Vector indexing complete")

        except Exception as e:
            logger.exception("Vector indexing failed")
            raise

        summary_path = repo_path / "rag_summary.md"
        summary_text = ""

        if summary_path.exists() and not force_clone:
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_text = f.read()

            logger.info("Loaded existing repository summary from disk.")

        else:
            summary_text = cls.generate_summary(repo_name, all_chunks)

            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary_text)

            logger.info("Generated and saved new repository summary.")

        # Save metadata with both all_files and parsed_files
        meta_path = settings.processed_chunks_dir / f"{repo_name}_meta.json"

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "repo_name": repo_name,
                    "repo_url": repo_url,
                    "parsed_files": parsed_files,
                    "all_files": all_file_paths,  # ← save all files
                },
                f,
                indent=2,
            )

        return {
            "repo_name": repo_name,
            "parsed_files_count": len(parsed_files),
            "chunks_count": len(all_chunks),
            "summary": summary_text,
            "files": all_file_paths,  # ← return all files to frontend
        }

    @classmethod
    def generate_summary(cls, repo_name: str, chunks: List[Any]) -> str:
        """Generates architectural overview using class and function outlines."""
        outlines = []
        
        # Extract function/class outlines to feed LLM (avoids overwhelming context window)
        for chunk in chunks:
            if chunk.chunk_type in ("class", "function", "method"):
                parent_info = f" (in Class {chunk.parent_class})" if chunk.parent_class else ""
                outlines.append(
                    f"- {chunk.file_path}: {chunk.chunk_type.capitalize()} '{chunk.name}'{parent_info} (Lines {chunk.start_line}-{chunk.end_line})"
                )
                
        # Limit outline length if codebase is massive
        limited_outlines = outlines[:150]
        outlines_str = "\n".join(limited_outlines)
        if len(outlines) > 150:
            outlines_str += f"\n- ... [and {len(outlines) - 150} more declarations]"

        prompt = SUMMARY_USER_PROMPT_TEMPLATE.format(file_outlines=outlines_str)
        try:
            return GeminiClient.generate_response(
                prompt=prompt,
                system_instruction=SUMMARY_SYSTEM_INSTRUCTION
            )
        except Exception as e:
            logger.error(f"Failed to generate repository summary: {e}")
            return f"# {repo_name}\nFailed to generate summary automatically. RAG features are still available."

    @staticmethod
    def get_cloned_repositories() -> List[Dict[str, Any]]:
        repos = []
        meta_dir = settings.processed_chunks_dir
        if not meta_dir.exists():
            return []

        for file in meta_dir.glob("*_meta.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                repo_name = data["repo_name"]
                summary_path = settings.cloned_repos_dir / repo_name / "rag_summary.md"
                summary = ""
                if summary_path.exists():
                    with open(summary_path, "r", encoding="utf-8") as sf:
                        summary = sf.read()
                data["summary"] = summary
                # Use all_files if available, fall back to parsed_files
                data["files"] = data.get("all_files", data.get("parsed_files", []))
                repos.append(data)
            except Exception as e:
                logger.error(f"Error reading metadata file {file}: {e}")
        return repos

    @staticmethod
    def get_file_content(repo_name: str, file_path: str) -> str:
        """Retrieves raw content of a file in the repository."""
        full_path = settings.cloned_repos_dir / repo_name / file_path
        # Prevent Directory Traversal attacks
        try:
            resolved_path = full_path.resolve()
            cloned_repos_resolved = settings.cloned_repos_dir.resolve()
            if not str(resolved_path).startswith(str(cloned_repos_resolved)):
                raise ValueError("Unauthorized path access.")
        except Exception as e:
            logger.error(f"Security validation failed for path {file_path}: {e}")
            raise ValueError("Invalid file path.")

        if not full_path.exists():
            raise FileNotFoundError(f"File {file_path} not found in repository.")
            
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(full_path, "r", encoding="latin-1") as f:
                return f.read()
