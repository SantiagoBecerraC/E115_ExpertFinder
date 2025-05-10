"""
Integration test for ChromaDB using real data and connections.

This test will use the real ChromaDB instance if available (running docker),
otherwise it falls back to the mock implementation.
"""

import pytest
import os
import uuid
import time
from pathlib import Path

from google_scholar.scholar_data_processor import process_scholar_data, prepare_chroma_data
from google_scholar.scholar_data_vectorization import load_to_chromadb
from utils.chroma_db_utils import ChromaDBManager


@pytest.mark.integration
def test_load_real_scholar_data_to_chromadb(real_scholar_data_file, chroma_client, use_real_services):
    """Test loading real Google Scholar data to ChromaDB.

    This test processes real Google Scholar data and loads it into either:
    - A real ChromaDB instance (if Docker is running)
    - An in-memory ChromaDB instance (if no Docker)
    """
    # Skip this test if it's running in CI without real services
    if os.environ.get("CI") and not use_real_services:
        pytest.skip("Skipping integration test in CI without real services")

    # Process the real data file
    authors_data = process_scholar_data(real_scholar_data_file)
    assert len(authors_data) > 0, "No author data found in the real data file"

    # Create a unique collection name for each test run
    # This prevents conflicts with previous test runs
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    file_name = Path(real_scholar_data_file).stem
    collection_name = f"test_collection_{file_name}_{unique_id}_{timestamp}"

    # Extract query from filename for better context
    query = "test query"
    file_path_str = str(real_scholar_data_file)
    if "semiglutide" in file_path_str:
        query = "semiglutide"
    elif "artificial" in file_path_str:
        query = "artificial intelligence"

    # Prepare data for ChromaDB
    chroma_data = prepare_chroma_data(authors_data, query=query)

    # Initialize ChromaDB manager with unique collection name
    print(f"Using unique collection name: {collection_name}")
    db_manager = ChromaDBManager(collection_name=collection_name)

    # For testing purposes, let's use a temporary collection
    # This avoids interfering with any existing data
    print(f"\nCreated test collection: {collection_name}")

    # In a real integration test, we'd use the actual DB
    # db_manager.client would be auto-initialized to connect to the real ChromaDB

    # Load data into ChromaDB
    authors_count = len(chroma_data["authors"])
    articles_count = len(chroma_data["articles"])
    all_docs = chroma_data["authors"] + chroma_data["articles"]

    # Instead of handling duplicates manually, use the existing load_to_chromadb function
    # which already handles duplicate IDs properly
    try:
        # Use the application's existing function to load documents into ChromaDB
        # This function already has built-in handling for duplicate IDs
        load_to_chromadb(all_docs, db_manager)
        print(f"Successfully loaded documents using load_to_chromadb function")

        # Verify the data was loaded
        collection_count = db_manager.collection.count()
        assert collection_count == len(all_docs), f"Expected {len(all_docs)} documents, got {collection_count}"

        # Run a simple query to verify the collection works
        results = db_manager.collection.query(query_texts=[query], n_results=min(5, collection_count))

        # Verify results
        assert len(results["documents"][0]) > 0, "Query returned no documents"

        print(f"\nSuccessfully loaded and queried {authors_count} authors and {articles_count} articles")
        print(f"First result: {results['documents'][0][0][:100]}...")

    finally:
        # Clean up - delete the collection if using real ChromaDB
        if use_real_services:
            try:
                chroma_client.delete_collection(collection_name)
                print(f"Cleaned up test collection: {collection_name}")
            except Exception as e:
                print(f"Warning: Failed to clean up collection: {e}")
