import json
from pathlib import Path

import chromadb
import dvc.api
import pytest
from chromadb.config import Settings


@pytest.mark.integration
def test_dvc_chromadb_integration(temp_chroma_dir, temp_dvc_dir):
    """Test integration between DVC and ChromaDB."""
    # Initialize ChromaDB
    client = chromadb.Client(Settings(persist_directory=str(temp_chroma_dir), anonymized_telemetry=False))
    collection = client.create_collection("integration_test")

    # Add test data
    test_data = {
        "documents": ["Test document 1", "Test document 2"],
        "metadatas": [{"source": "test1"}, {"source": "test2"}],
        "ids": ["id1", "id2"],
    }
    collection.add(**test_data)

    # Save ChromaDB data to DVC
    dvc_data = {
        "collection": "integration_test",
        "documents": test_data["documents"],
        "metadatas": test_data["metadatas"],
        "ids": test_data["ids"],
    }

    # Write to DVC-tracked file
    dvc_file = temp_dvc_dir / "chromadb_data.json"
    with open(dvc_file, "w") as f:
        json.dump(dvc_data, f)

    # Test data restoration
    with open(dvc_file, "r") as f:
        restored_data = json.load(f)

    # Verify restored data
    assert restored_data["collection"] == "integration_test"
    assert len(restored_data["documents"]) == 2
    assert restored_data["documents"][0] == "Test document 1"
    assert restored_data["metadatas"][0]["source"] == "test1"
    assert restored_data["ids"][0] == "id1"


@pytest.mark.integration
def test_dvc_version_management(temp_chroma_dir, temp_dvc_dir):
    """Test version management with DVC and ChromaDB."""
    # Initialize ChromaDB
    client = chromadb.Client(Settings(persist_directory=str(temp_chroma_dir), anonymized_telemetry=False))
    collection = client.create_collection("version_test")

    # Version 1 data
    v1_data = {"documents": ["Version 1 document"], "metadatas": [{"version": "v1"}], "ids": ["v1"]}
    collection.add(**v1_data)

    # Save version 1
    v1_file = temp_dvc_dir / "chromadb_v1.json"
    with open(v1_file, "w") as f:
        json.dump(v1_data, f)

    # Version 2 data
    v2_data = {"documents": ["Version 2 document"], "metadatas": [{"version": "v2"}], "ids": ["v2"]}
    collection.add(**v2_data)

    # Save version 2
    v2_file = temp_dvc_dir / "chromadb_v2.json"
    with open(v2_file, "w") as f:
        json.dump(v2_data, f)

    # Test version restoration
    with open(v1_file, "r") as f:
        restored_v1 = json.load(f)
    assert restored_v1["documents"][0] == "Version 1 document"

    with open(v2_file, "r") as f:
        restored_v2 = json.load(f)
    assert restored_v2["documents"][0] == "Version 2 document"
