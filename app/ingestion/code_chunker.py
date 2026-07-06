import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.logger import logger
from app.core.constants import LANGUAGE_MAPPING

# Flag to check tree-sitter availability
TREE_SITTER_AVAILABLE = False
try:
    from tree_sitter_languages import get_parser
    TREE_SITTER_AVAILABLE = True
except Exception as e:
    logger.warning(
        f"Tree-sitter or tree-sitter-languages not available: {e}. "
        "Falling back to regex-based code-aware chunker."
    )


class Chunk:
    def __init__(
        self,
        text: str,
        file_path: str,
        chunk_type: str,
        name: str = "",
        start_line: int = 1,
        end_line: int = 1,
        parent_class: str = ""
    ):
        self.text = text
        self.file_path = file_path
        self.chunk_type = chunk_type  # 'class', 'function', 'method', 'markdown_section', 'module_level'
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.parent_class = parent_class

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "path": self.file_path,
            "chunk_type": self.chunk_type,
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "parent_class": self.parent_class or "N/A"
        }


class CodeChunker:
    @classmethod
    def chunk_file(cls, file_path: Path, content: str) -> List[Chunk]:
        """Dispatches file to the appropriate chunking strategy based on file extension."""
        ext = file_path.suffix.lower()
        rel_path = file_path.name
        
        # If markdown, parse by headers
        if ext == ".md":
            return cls.chunk_markdown(content, str(file_path))

        # Check if extension maps to a supported tree-sitter language
        lang_id = LANGUAGE_MAPPING.get(ext)
        if not lang_id:
            # Fallback to simple line-based chunking for text/other files
            return cls.chunk_lines_simple(content, str(file_path))

        if TREE_SITTER_AVAILABLE:
            try:
                return cls.chunk_with_treesitter(content, str(file_path), lang_id)
            except Exception as e:
                logger.warning(f"Tree-sitter chunking failed for {file_path}: {e}. Trying regex chunking.")
                
        return cls.chunk_with_regex(content, str(file_path), lang_id)

    @classmethod
    def chunk_with_treesitter(cls, content: str, file_path: str, lang_id: str) -> List[Chunk]:
        """Chunks source code using Tree-sitter AST nodes (classes, functions, methods)."""
        parser = get_parser(lang_id)
        bytes_code = bytes(content, "utf8")
        tree = parser.parse(bytes_code)
        
        chunks: List[Chunk] = []
        visited_lines = set()
        lines = content.splitlines()

        # Define node types we care about
        class_types = {"class_definition", "class_declaration"}
        func_types = {
            "function_definition",
            "function_declaration",
            "method_definition",
            "constructor_declaration",
            "method_declaration"
        }

        # First pass: Extract functions and classes
        def traverse(node, current_class: str = ""):
            nonlocal chunks
            node_type = node.type
            
            # Identify class
            name = ""
            is_class = node_type in class_types
            is_func = node_type in func_types
            
            if is_class or is_func:
                # Find name identifier
                for child in node.children:
                    if child.type in ("identifier", "property_identifier", "name"):
                        name = bytes_code[child.start_byte:child.end_byte].decode("utf8", errors="ignore")
                        break
                
                start_l = node.start_point[0] + 1
                end_l = node.end_point[0] + 1
                node_text = bytes_code[node.start_byte:node.end_byte].decode("utf8", errors="ignore")
                
                # Check if it's empty or invalid
                if node_text.strip():
                    chunk_type = "class" if is_class else ("method" if current_class else "function")
                    chunks.append(Chunk(
                        text=node_text,
                        file_path=file_path,
                        chunk_type=chunk_type,
                        name=name,
                        start_line=start_l,
                        end_line=end_l,
                        parent_class=current_class
                    ))
                    
                    # Mark lines as covered so we don't duplicate them in module-level chunks
                    for line_idx in range(start_l, end_l + 1):
                        visited_lines.add(line_idx)
            
            # Recurse children
            next_class = name if is_class else current_class
            for child in node.children:
                traverse(child, next_class)

        traverse(tree.root_node)

        # Second pass: Gather remaining "module-level" code blocks (imports, globals, etc.)
        current_block = []
        block_start = 1
        
        for idx, line in enumerate(lines):
            line_num = idx + 1
            if line_num not in visited_lines:
                if not current_block:
                    block_start = line_num
                current_block.append(line)
            else:
                if current_block:
                    block_text = "\n".join(current_block)
                    if block_text.strip():
                        chunks.append(Chunk(
                            text=block_text,
                            file_path=file_path,
                            chunk_type="module_level",
                            name=f"global_block_{block_start}",
                            start_line=block_start,
                            end_line=line_num - 1
                        ))
                    current_block = []
                    
        if current_block:
            block_text = "\n".join(current_block)
            if block_text.strip():
                chunks.append(Chunk(
                    text=block_text,
                    file_path=file_path,
                    chunk_type="module_level",
                    name=f"global_block_{block_start}",
                    start_line=block_start,
                    end_line=len(lines)
                ))

        # Sort chunks by start_line
        chunks.sort(key=lambda c: c.start_line)
        return chunks

    @classmethod
    def chunk_with_regex(cls, content: str, file_path: str, lang_id: str) -> List[Chunk]:
        """Regex-based fallback that parses files block-by-block based on indented functions/classes."""
        lines = content.splitlines()
        chunks: List[Chunk] = []
        
        # Regex patterns depending on language
        class_regex = None
        func_regex = None
        
        if lang_id == "python":
            class_regex = re.compile(r"^class\s+([a-zA-Z0-9_]+)\b")
            func_regex = re.compile(r"^\s*def\s+([a-zA-Z0-9_]+)\b")
        elif lang_id in ("javascript", "typescript"):
            class_regex = re.compile(r"^(?:export\s+)?class\s+([a-zA-Z0-9_]+)\b")
            func_regex = re.compile(r"^\s*(?:async\s+)?function\s+([a-zA-Z0-9_]+)\b|^\s*(?:export\s+)?const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>|^\s*([a-zA-Z0-9_]+)\s*\(.*?\)\s*\{")
        elif lang_id == "java":
            class_regex = re.compile(r"^(?:public\s+|private\s+)?(?:class|interface)\s+([a-zA-Z0-9_]+)\b")
            func_regex = re.compile(r"^\s*(?:public|private|protected|static|\s) +[\w\<\>\[\]]+ +([a-zA-Z0-9_]+)\s*\(.*?\)\s*\{")

        # Fallback to simple line chunks if regex is not applicable
        if not class_regex or not func_regex:
            return cls.chunk_lines_simple(content, file_path)

        current_chunk_lines = []
        chunk_start = 1
        chunk_name = "module_level"
        chunk_type = "module_level"
        parent_class = ""

        for idx, line in enumerate(lines):
            line_num = idx + 1
            
            # Check for new class
            class_match = class_regex.match(line)
            # Check for new function/method
            func_match = func_regex.match(line)
            
            # Detect indent changes or new declarations to split previous block
            if class_match or func_match:
                if current_chunk_lines:
                    # Save current chunk
                    text = "\n".join(current_chunk_lines)
                    if text.strip():
                        chunks.append(Chunk(
                            text=text,
                            file_path=file_path,
                            chunk_type=chunk_type,
                            name=chunk_name,
                            start_line=chunk_start,
                            end_line=line_num - 1,
                            parent_class=parent_class
                        ))
                
                # Reset for new block
                current_chunk_lines = [line]
                chunk_start = line_num
                
                if class_match:
                    chunk_name = class_match.group(1)
                    chunk_type = "class"
                    parent_class = chunk_name
                else:
                    # func_match
                    groups = [g for g in func_match.groups() if g]
                    chunk_name = groups[0] if groups else "anonymous"
                    # If the function is top-level (no indentation), reset the parent class context
                    if not line.startswith(" ") and not line.startswith("\t"):
                        parent_class = ""
                    chunk_type = "method" if parent_class else "function"
            else:
                current_chunk_lines.append(line)

        # Flush last chunk
        if current_chunk_lines:
            text = "\n".join(current_chunk_lines)
            if text.strip():
                chunks.append(Chunk(
                    text=text,
                    file_path=file_path,
                    chunk_type=chunk_type,
                    name=chunk_name,
                    start_line=chunk_start,
                    end_line=len(lines),
                    parent_class=parent_class
                ))

        return chunks

    @classmethod
    def chunk_markdown(cls, content: str, file_path: str) -> List[Chunk]:
        """Chunks Markdown files using headers (# Header 1, ## Header 2)."""
        lines = content.splitlines()
        chunks: List[Chunk] = []
        
        current_chunk_lines = []
        chunk_start = 1
        chunk_name = "README"
        
        header_regex = re.compile(r"^(#{1,6})\s+(.+)$")
        
        for idx, line in enumerate(lines):
            line_num = idx + 1
            match = header_regex.match(line)
            if match:
                # Flush previous
                if current_chunk_lines:
                    text = "\n".join(current_chunk_lines)
                    if text.strip():
                        chunks.append(Chunk(
                            text=text,
                            file_path=file_path,
                            chunk_type="markdown_section",
                            name=chunk_name,
                            start_line=chunk_start,
                            end_line=line_num - 1
                        ))
                
                current_chunk_lines = [line]
                chunk_start = line_num
                chunk_name = match.group(2).strip()
            else:
                current_chunk_lines.append(line)
                
        # Flush last
        if current_chunk_lines:
            text = "\n".join(current_chunk_lines)
            if text.strip():
                chunks.append(Chunk(
                    text=text,
                    file_path=file_path,
                    chunk_type="markdown_section",
                    name=chunk_name,
                    start_line=chunk_start,
                    end_line=len(lines)
                ))
                
        return chunks

    @classmethod
    def chunk_lines_simple(cls, content: str, file_path: str, chunk_size_lines: int = 40) -> List[Chunk]:
        """Fallback lines-based chunker for simple text files or files with unsupported extensions."""
        lines = content.splitlines()
        chunks: List[Chunk] = []
        
        for i in range(0, len(lines), chunk_size_lines):
            chunk_lines = lines[i : i + chunk_size_lines]
            text = "\n".join(chunk_lines)
            start_l = i + 1
            end_l = min(i + chunk_size_lines, len(lines))
            
            if text.strip():
                chunks.append(Chunk(
                    text=text,
                    file_path=file_path,
                    chunk_type="module_level",
                    name=f"block_{start_l}_{end_l}",
                    start_line=start_l,
                    end_line=end_l
                ))
        return chunks
