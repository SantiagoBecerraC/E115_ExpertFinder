import pytest
from pathlib import Path
import chromadb
from chromadb.config import Settings

@pytest.mark.unit
def test_chromadb_initialization(temp_chroma_dir):
    """Test ChromaDB initialization with temporary directory."""
    client = chromadb.Client(Settings(
        persist_directory=str(temp_chroma_dir),
        anonymized_telemetry=False
    ))
    
    # Test collection creation
    collection = client.create_collection("test_collection")
    assert collection is not None
    
    # Test document addition
    collection.add(
        documents=["This is a test document"],
        metadatas=[{"source": "test"}],
        ids=["test1"]
    )
    
    # Test query
    results = collection.query(
        query_texts=["test document"],
        n_results=1
    )
    assert len(results["documents"][0]) == 1
    assert results["documents"][0][0] == "This is a test document"

@pytest.mark.unit
def test_chromadb_persistence(temp_chroma_dir):
    """Test ChromaDB data persistence."""
    # First client instance
    client1 = chromadb.Client(Settings(
        persist_directory=str(temp_chroma_dir),
        anonymized_telemetry=False
    ))
    collection = client1.create_collection("persistence_test")
    collection.add(
        documents=["Persistent document"],
        ids=["persist1"]
    )
    
    # Second client instance
    client2 = chromadb.Client(Settings(
        persist_directory=str(temp_chroma_dir),
        anonymized_telemetry=False
    ))
    collection = client2.get_collection("persistence_test")
    results = collection.query(
        query_texts=["Persistent"],
        n_results=1
    )
    assert len(results["documents"][0]) == 1
    assert results["documents"][0][0] == "Persistent document" 