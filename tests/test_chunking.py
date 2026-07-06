import pytest
from pathlib import Path
from app.ingestion.code_chunker import CodeChunker

def test_python_regex_chunking():
    # Test fallback regex code chunking on Python code
    python_code = """
class DatabaseManager:
    def __init__(self, url):
        self.url = url
        
    def connect(self):
        return True

def initialize_app():
    return DatabaseManager("sqlite://")
"""
    file_path = Path("test_db.py")
    chunks = CodeChunker.chunk_with_regex(python_code, str(file_path), "python")
    
    # We expect chunks:
    # 1. DatabaseManager class
    # 2. initialize_app function
    assert len(chunks) >= 2
    
    class_chunks = [c for c in chunks if c.chunk_type == "class"]
    assert len(class_chunks) >= 1
    assert class_chunks[0].name == "DatabaseManager"
    
    func_chunks = [c for c in chunks if c.chunk_type == "function"]
    assert len(func_chunks) >= 1
    assert func_chunks[0].name == "initialize_app"

def test_markdown_chunking():
    # Test markdown section chunking
    markdown_content = """# Main Project Title
This is some description.

## Installation
Run npm install.

## Usage
Run npm run dev.
"""
    file_path = Path("README.md")
    chunks = CodeChunker.chunk_markdown(markdown_content, str(file_path))
    
    assert len(chunks) == 3
    assert chunks[0].name == "Main Project Title"
    assert chunks[1].name == "Installation"
    assert chunks[2].name == "Usage"
    assert chunks[0].start_line == 1
    assert chunks[1].start_line == 4
    assert chunks[2].start_line == 7
