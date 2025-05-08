import pytest
import tempfile
from pathlib import Path
import chromadb
from chromadb.config import Settings
import uuid
import os
from unittest.mock import patch, MagicMock

# Import here to check implementation, but mock in tests
from utils.chroma_db_utils import ChromaDBManager

@pytest.mark.unit
def test_chromadb_initialization(monkeypatch, tmp_path):
    """Test ChromaDB initialization with temporary directory."""
    # Create a unique path for this test
    test_db_path = tmp_path / "chromadb_test"
    test_db_path.mkdir(exist_ok=True)
    
    # Create a unique collection name
    collection_name = f"test_init_{uuid.uuid4().hex[:8]}"
    
    # Setup mocks
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.create_collection.return_value = mock_collection
    
    # Patch the necessary parts of ChromaDBManager
    with patch('chromadb.PersistentClient', return_value=mock_client), \
         patch.object(ChromaDBManager, '_find_project_root', return_value=tmp_path):
        
        # Create the manager with our test collection
        db_manager = ChromaDBManager(collection_name=collection_name)
        
        # Check initialization
        assert db_manager.client is not None
        assert db_manager.collection is not None
        assert db_manager.collection_name == collection_name
        
        # Verify create_collection was called with right name
        mock_client.create_collection.assert_called_once()
        args, kwargs = mock_client.create_collection.call_args
        assert kwargs['name'] == collection_name

@pytest.mark.unit
def test_chromadb_add_documents(monkeypatch, tmp_path):
    """Test adding documents to ChromaDB."""
    # Create a unique collection name
    collection_name = f"test_add_{uuid.uuid4().hex[:8]}"
    
    # Test documents
    docs = ["This is a test document"]
    ids = ["test1"]
    metadata = [{"source": "unit_test"}]
    
    # Setup mocks
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.create_collection.return_value = mock_collection
    
    # Patch the necessary parts
    with patch('chromadb.PersistentClient', return_value=mock_client), \
         patch.object(ChromaDBManager, '_find_project_root', return_value=tmp_path):
        
        # Create the manager
        db_manager = ChromaDBManager(collection_name=collection_name)
        
        # Add documents
        db_manager.add_documents(docs, ids, metadata)
        
        # Verify add was called with right args
        mock_collection.add.assert_called_once()
        args, kwargs = mock_collection.add.call_args
        assert kwargs['documents'] == docs
        assert kwargs['ids'] == ids
        assert kwargs['metadatas'] == metadata

@pytest.mark.unit
def test_chromadb_query(monkeypatch, tmp_path):
    """Test querying ChromaDB."""
    # Create a unique collection name
    collection_name = f"test_query_{uuid.uuid4().hex[:8]}"
    
    # Setup mocks
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.create_collection.return_value = mock_collection
    
    # Set up the return value for query
    mock_query_result = {
        "ids": [["test1"]],
        "documents": [["This is a test document"]],
        "metadatas": [[{"source": "unit_test", "citations": 10}]],
        "distances": [[0.1]]
    }
    mock_collection.query.return_value = mock_query_result
    
    # Patch the necessary parts
    with patch('chromadb.PersistentClient', return_value=mock_client), \
         patch.object(ChromaDBManager, '_find_project_root', return_value=tmp_path):
        
        # Create the manager
        db_manager = ChromaDBManager(collection_name=collection_name)
        
        # Perform query
        results = db_manager.query("test query", n_results=1)
        
        # Verify query was called
        mock_collection.query.assert_called_once()
        
        # Verify results are processed correctly
        assert isinstance(results, list)
        assert len(results) == 1
        assert "source" in results[0]
        assert results[0]["source"] == "unit_test"
        assert results[0]["citations"] == 10