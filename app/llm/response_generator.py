import re
from typing import List, Dict, Any, Tuple
from app.llm.gemini_client import GeminiClient
from app.llm.prompts import RAG_SYSTEM_INSTRUCTION, RAG_USER_PROMPT_TEMPLATE

class ResponseGenerator:
    @staticmethod
    def format_chunks(chunks: List[Dict[str, Any]]) -> str:
        """Formats vector store retrieved chunks into a standard structured prompt context block."""
        formatted = []
        for idx, chunk in enumerate(chunks):
            meta = chunk["metadata"]
            file_path = meta.get("path", meta.get("file", "unknown"))
            start = meta.get("start_line", 1)
            end = meta.get("end_line", 1)
            chunk_type = meta.get("chunk_type", "code")
            name = meta.get("name", "")
            
            header = f"--- CHUNK {idx+1} | File: {file_path} (Lines {start}-{end})"
            if name:
                header += f" | {chunk_type.capitalize()}: {name}"
            header += " ---"
            
            formatted_chunk = f"{header}\n{chunk['text']}\n"
            formatted.append(formatted_chunk)
            
        return "\n".join(formatted)

    @classmethod
    def generate_rag_answer(
        cls,
        question: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Formats context, queries Gemini, parses annotations, and maps them to citations."""
        formatted_context = cls.format_chunks(retrieved_chunks)
        prompt = RAG_USER_PROMPT_TEMPLATE.format(
            retrieved_chunks=formatted_context,
            question=question
        )
        
        raw_response = GeminiClient.generate_response(
            prompt=prompt,
            system_instruction=RAG_SYSTEM_INSTRUCTION
        )
        
        citations = []
        seen_citations = set()
        citation_pattern = re.compile(r"\[([^:\s]+):(\d+)-(\d+)\]")

        def validate_citation(match: re.Match) -> str:
            file_path, start_text, end_text = match.groups()
            start, end = int(start_text), int(end_text)
            if start < 1 or end < start:
                return f"{file_path} (lines {start}-{end})"

            for chunk in retrieved_chunks:
                metadata = chunk["metadata"]
                chunk_path = metadata.get("path", metadata.get("file", ""))
                chunk_start = int(metadata.get("start_line", 1))
                chunk_end = int(metadata.get("end_line", chunk_start))
                if (
                    chunk_path == file_path
                    and chunk_start <= start
                    and end <= chunk_end
                ):
                    citation_key = f"{file_path}:{start}-{end}"
                    if citation_key not in seen_citations:
                        seen_citations.add(citation_key)
                        lines = chunk["text"].splitlines()
                        snippet = "\n".join(lines[start - chunk_start : end - chunk_start + 1])
                        citations.append({
                            "file": file_path,
                            "start_line": start,
                            "end_line": end,
                            "snippet": snippet,
                        })
                    return match.group(0)

            return f"{file_path} (lines {start}-{end})"

        validated_response = citation_pattern.sub(validate_citation, raw_response)
        return validated_response, citations
