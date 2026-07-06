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
        
        # Parse citations from raw response
        # Matches patterns like [src/auth.py:50-90]
        # Regex captures: Group 1 = file, Group 2 = start_line, Group 3 = end_line
        matches = re.findall(r"\[([^:\s]+):(\d+)-(\d+)\]", raw_response)
        
        citations = []
        seen_citations = set()
        for match in matches:
            file_path, start, end = match
            citation_key = f"{file_path}:{start}-{end}"
            if citation_key not in seen_citations:
                seen_citations.add(citation_key)
                
                # Search retrieved chunks to find a snippet of code
                snippet = ""
                for chunk in retrieved_chunks:
                    meta = chunk["metadata"]
                    meta_path = meta.get("path", meta.get("file", ""))
                    if meta_path == file_path:
                        snippet = chunk["text"]
                        break
                        
                citations.append({
                    "file": file_path,
                    "start_line": int(start),
                    "end_line": int(end),
                    "snippet": snippet
                })
                
        return raw_response, citations
