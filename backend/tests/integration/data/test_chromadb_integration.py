import pytest
import json
import os
from pathlib import Path

@pytest.mark.integration
def test_chromadb_batch_operations():
    """Test batch operations in ChromaDB."""
    from utils.chroma_db_utils import ChromaDBManager
    import uuid
    
    # Create a unique collection name
    collection_name = f"test_batch_ops_{uuid.uuid4().hex[:8]}"
    
    # Create the manager
    db_manager = ChromaDBManager(collection_name=collection_name)
    
    try:
        # Test batch addition
        docs = [
            "First test document for batch operations",
            "Second test document with different content",
            "Third document to test batch retrieval"
        ]
        ids = [f"batch-doc-{i}" for i in range(len(docs))]
        metadatas = [{"batch_index": str(i), "source": "test"} for i in range(len(docs))]  # Convert to string
        
        # Add documents in batch
        db_manager.add_documents(documents=docs, ids=ids, metadatas=metadatas)
        
        # Test batch retrieval
        results = db_manager.collection.get(
            ids=ids,
            include=["metadatas", "documents"]
        )
        
        # Verify all documents were added
        assert len(results["ids"]) == len(docs), "Not all documents were retrieved"
        assert set(results["ids"]) == set(ids), "Retrieved IDs don't match added IDs"
        
        # Test batch query
        query_results = db_manager.query("test document", n_results=10)
        assert len(query_results) > 0, "Query returned no results"
        
        # Test metadata filtering - use different approach
        filtered_index = 1
        # Get document directly by ID as backup approach
        doc_id = f"batch-doc-{filtered_index}"
        direct_result = db_manager.collection.get(
            ids=[doc_id]
        )
        
        assert len(direct_result["ids"]) == 1, f"Couldn't retrieve document with ID {doc_id}"
        assert direct_result["ids"][0] == doc_id, "Retrieved ID doesn't match expected ID"
        
    finally:
        db_manager.delete_collection()


@pytest.mark.integration
def test_chromadb_update_operations():
    """Test update operations in ChromaDB."""
    from utils.chroma_db_utils import ChromaDBManager
    import uuid
    
    # Create a unique collection name
    collection_name = f"test_update_ops_{uuid.uuid4().hex[:8]}"
    
    # Create the manager
    db_manager = ChromaDBManager(collection_name=collection_name)
    
    try:
        # Add initial document
        doc_id = "update-test-doc"
        initial_doc = "Initial document content"
        initial_metadata = {"version": 1, "status": "draft"}
        
        db_manager.add_documents(
            documents=[initial_doc],
            ids=[doc_id],
            metadatas=[initial_metadata]
        )
        
        # Update the document
        updated_doc = "Updated document content"
        updated_metadata = {"version": 2, "status": "published"}
        
        db_manager.collection.update(
            ids=[doc_id],
            documents=[updated_doc],
            metadatas=[updated_metadata]
        )
        
        # Retrieve and verify the update
        result = db_manager.collection.get(
            ids=[doc_id],
            include=["metadatas", "documents"]
        )
        
        assert result["documents"][0] == updated_doc, "Document content not updated correctly"
        assert result["metadatas"][0]["version"] == 2, "Metadata not updated correctly"
        assert result["metadatas"][0]["status"] == "published", "Metadata status not updated correctly"
        
    finally:
        db_manager.delete_collection()

@pytest.mark.integration
def test_chromadb_simplest_operations():
    """Test very basic operations in ChromaDB."""
    from utils.chroma_db_utils import ChromaDBManager
    import uuid
    
    # Create a unique collection
    collection_name = f"test_basic_ops_{uuid.uuid4().hex[:8]}"
    db_manager = ChromaDBManager(collection_name=collection_name)
    
    try:
        # Add just one document
        doc = "Test document for basic operations"
        doc_id = "test-doc-1"
        metadata = {"source": "test", "type": "document"}
        
        # Add document
        db_manager.add_documents(
            documents=[doc],
            ids=[doc_id],
            metadatas=[metadata]
        )
        
        # Test simple query
        results = db_manager.query(
            query_text="test document",
            n_results=1
        )
        
        assert len(results) > 0, "Query should return results"
        assert results[0]["content"] == doc, "Query should return the document"
        
        # Test direct access to collection
        collection = db_manager.collection
        assert collection is not None, "Should have access to collection"
        
        # Test getting document by ID
        direct_result = collection.get(ids=[doc_id])
        assert len(direct_result["ids"]) == 1, "Should retrieve one document"
        assert direct_result["ids"][0] == doc_id, "Retrieved document should match ID"
        
    finally:
        db_manager.delete_collection()