import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import json


# Mark as system test
@pytest.mark.system
def test_end_to_end_search_flow(api_client, monkeypatch, tmp_path):
    """
    Test the full search flow from API to database and back.

    This test:
    1. Mocks ChromaDB and LinkedIn services
    2. Sends a search query through the API
    3. Verifies combined results are returned
    """
    # Set up a test ChromaDB directory
    chroma_dir = tmp_path / "chromadb_test"
    chroma_dir.mkdir(exist_ok=True)

    # Mock data for Google Scholar experts
    scholar_experts = [
        {
            "id": "scholar1",
            "name": "Dr. Scholar",
            "title": "Research Scientist",
            "source": "scholar",
            "company": "University Research",
            "citations": 500,
            "interests": ["AI", "Machine Learning", "Neural Networks"],
            "publications": ["Groundbreaking Research Paper"],
        }
    ]

    # Mock data for LinkedIn experts
    linkedin_experts = [
        {
            "id": "linkedin1",
            "name": "Jane Professional",
            "title": "Senior AI Engineer",
            "source": "linkedin",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "skills": ["Python", "TensorFlow", "Machine Learning"],
            "years_experience": 8,
        }
    ]

    # Create mocks for ChromaDBManager and ExpertFinderAgent
    mock_chromadb = MagicMock()
    mock_chromadb.query.return_value = scholar_experts

    mock_linkedin = MagicMock()
    mock_linkedin.find_experts.return_value = linkedin_experts

    # Patch all the necessary dependencies
    with patch("main.ChromaDBManager", return_value=mock_chromadb), patch(
        "main.ExpertFinderAgent", return_value=mock_linkedin
    ), patch("main.torch_available", True), patch("main.DVCManager"):

        # Test query
        search_query = "artificial intelligence machine learning"

        # Call the combined search endpoint
        response = api_client.post("/search", json={"query": search_query, "max_results": 5})

        # Verify response status and structure
        assert response.status_code == 200
        data = response.json()

        # Check that we have the combined results
        assert "experts" in data
        assert "total" in data
        assert "scholar_count" in data
        assert "linkedin_count" in data

        # Verify we got the combined count
        assert data["total"] == len(scholar_experts) + len(linkedin_experts)
        assert data["scholar_count"] == len(scholar_experts)
        assert data["linkedin_count"] == len(linkedin_experts)

        # Verify experts data is correct
        experts = data["experts"]
        assert len(experts) == 2

        # Check specific expert details from both sources
        scholar_expert = next((e for e in experts if e["source"] == "scholar"), None)
        linkedin_expert = next((e for e in experts if e["source"] == "linkedin"), None)

        assert scholar_expert is not None
        assert linkedin_expert is not None

        assert scholar_expert["name"] == "Dr. Scholar"
        assert scholar_expert["citations"] == 500
        assert "Neural Networks" in scholar_expert["interests"]

        assert linkedin_expert["name"] == "Jane Professional"
        assert linkedin_expert["company"] == "Tech Company"
        assert linkedin_expert["years_experience"] == 8


@pytest.mark.system
def test_version_management_flow(api_client, monkeypatch, tmp_path):
    """
    Test the full version management flow.

    This test:
    1. Mocks DVCManager
    2. Creates a new version
    3. Gets version history
    4. Restores a specific version
    """
    # Mock version history
    version_history = [
        {
            "commit_hash": "abc123",
            "date": "2025-04-01 12:00:00 -0400",
            "message": "Update with 100 profiles from test source",
        },
        {
            "commit_hash": "def456",
            "date": "2025-04-02 12:00:00 -0400",
            "message": "Update with 50 profiles from linkedin",
        },
    ]

    # Create mock for DVCManager
    mock_dvc = MagicMock()
    mock_dvc.version_database.return_value = True
    mock_dvc.get_version_history.return_value = version_history
    mock_dvc.restore_version.return_value = True

    # Patch the necessary dependencies
    with patch("main.DVCManager", return_value=mock_dvc), patch("main.ChromaDBManager"):

        # 1. Create a new version
        create_response = api_client.post(
            "/api/data/version",
            json={"source": "test_system", "profiles_added": 25, "description": "System test version"},
        )

        # Verify create response
        assert create_response.status_code == 200
        assert create_response.json()["message"] == "Database successfully versioned"

        # 2. Get version history
        history_response = api_client.get("/api/data/versions?max_entries=2")

        # Verify history response
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert "versions" in history_data
        assert len(history_data["versions"]) == 2

        # 3. Restore a specific version
        restore_response = api_client.post(f"/api/data/restore/{version_history[0]['commit_hash']}")

        # Verify restore response
        assert restore_response.status_code == 200
        assert "Successfully restored" in restore_response.json()["message"]
        assert version_history[0]["commit_hash"] in restore_response.json()["message"]
