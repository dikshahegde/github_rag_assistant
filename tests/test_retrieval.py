import pytest
from unittest.mock import MagicMock, patch
from app.vectorstore.chroma_manager import ChromaManager
from app.ingestion.code_chunker import Chunk

@patch("chromadb.PersistentClient")
def test_chroma_manager_collection_creation(mock_client_class):
    # Mock Chroma client and collection
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_client_class.return_value = mock_client

    # Initialize ChromaManager with mocked client
    manager = ChromaManager()
    
    # Assert collection name normalization
    col_name = manager.get_collection_name("My-Awesome-Repo.git")
    assert col_name == "my-awesome-repo_git"
    
    # Get collection
    col = manager.get_collection("My-Awesome-Repo.git")
    mock_client.get_or_create_collection.assert_called_with(
        name="my-awesome-repo_git",
        embedding_function=manager.embedding_function
    )
    assert col == mock_collection

@patch("chromadb.PersistentClient")
@patch("app.ingestion.embedding_generator.EmbeddingGenerator.get_embeddings")
def test_add_chunks(mock_get_embeddings, mock_client_class):
    # Mock embeddings and client
    mock_get_embeddings.return_value = [[0.1] * 384]
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_client_class.return_value = mock_client

    manager = ChromaManager()
    
    # Add a mock chunk
    mock_chunk = Chunk(
        text="def hello(): return 'world'",
        file_path="src/hello.py",
        chunk_type="function",
        name="hello",
        start_line=1,
        end_line=2
    )
    
    manager.add_chunks("test-repo", [mock_chunk])
    
    # Verify collection.add was called
    assert mock_collection.add.called
    args, kwargs = mock_collection.add.call_args
    assert "src_hello_py" in kwargs["ids"][0]
    assert kwargs["documents"][0] == "def hello(): return 'world'"
    assert kwargs["metadatas"][0]["name"] == "hello"
