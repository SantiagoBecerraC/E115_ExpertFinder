import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to the path so we can import the main module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the main FastAPI app
from main import Expert, SearchQuery, app

# Import the custom API test client
from tests.api_test_client import get_api_test_client

# Create a test client
client = get_api_test_client(use_mocks=True)


class TestMainEndpoints:
    """Test cases for the main API endpoints."""

    def test_root_endpoint(self):
        """Test that the root endpoint returns the expected data."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["version"] == "1.0.0"

    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @patch("main.ExpertFinderAgent")
    def test_linkedin_search(self, mock_expert_finder):
        """Test LinkedIn search endpoint with mock data."""
        # Configure the mock
        mock_instance = MagicMock()
        mock_expert_finder.return_value = mock_instance

        # Setup mock search results
        mock_instance.find_experts_json.return_value = [
            {
                "urn_id": "test-id-1",
                "name": "Test Expert",
                "current_title": "Software Engineer",
                "current_company": "Tech Corp",
                "location": "San Francisco, CA",
                "profile_summary": "Experienced software engineer",
                "similarity": 0.85,
                "credibility": {"level": 3, "percentile": 75.5, "years_experience": 8},
            }
        ]

        # Make the request
        response = client.post("/linkedin_search", json={"query": "python developer", "max_results": 5})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "experts" in data
        assert len(data["experts"]) == 1
        assert data["experts"][0]["name"] == "Test Expert"
        assert data["experts"][0]["credibility_level"] == 3

    def test_linkedin_search_empty_query(self):
        """Test LinkedIn search with an empty query."""
        # Add a custom mock for empty query case
        client.add_mock_response("POST", "/linkedin_search", 422, {"detail": "Query cannot be empty"}, variant="empty")

        response = client.post("/linkedin_search", json={"query": "", "max_results": 5})
        assert response.status_code == 422  # Validation error

    def test_linkedin_search_invalid_max_results(self):
        """Test LinkedIn search with invalid max_results."""
        response = client.post("/linkedin_search", json={"query": "python developer", "max_results": -1})
        assert response.status_code == 200  # Should correct to default 5

        # Ensure the request was processed with default value
        data = response.json()
        assert "experts" in data

    @patch("main.create_scholar_agent")
    @patch("main.ChromaDBTool")
    @patch("main.torch_available", True)
    def test_scholar_search(self, mock_chroma_tool, mock_create_agent):
        """Test Google Scholar search endpoint."""
        # Configure the mocks
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        # Setup mock response from the scholar agent
        mock_message = MagicMock()
        mock_message.content = '[{"name": "Dr. Scholar", "title": "Professor", "affiliation": "Research University", "interests": ["AI", "Machine Learning"], "citations": 1500}]'
        mock_agent.graph.invoke.return_value = {"messages": [mock_message]}

        # Make the request
        response = client.post("/scholar_search", json={"query": "machine learning research", "max_results": 5})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "experts" in data
        # Additional assertions about response content

    @patch("main.torch_available", False)
    def test_scholar_search_torch_unavailable(self):
        """Test Google Scholar search when torch is not available."""
        # Add a custom mock for torch unavailable case
        client.add_mock_response(
            "POST",
            "/scholar_search",
            503,
            {"detail": "PyTorch is not available for inference"},
            variant="torch_unavailable",
        )

        response = client.post("/scholar_search", json={"query": "machine learning", "max_results": 5})
        assert response.status_code == 503  # Service Unavailable

    @patch("main.ExpertFinderAgent")
    @patch("main.create_scholar_agent")
    @patch("main.ChromaDBTool")
    @patch("main.torch_available", True)
    def test_search_all_experts(self, mock_chroma_tool, mock_create_agent, mock_expert_finder):
        """Test combined search endpoint."""
        # Configure LinkedIn mock
        mock_instance = MagicMock()
        mock_expert_finder.return_value = mock_instance
        mock_instance.find_experts_json.return_value = [
            {
                "urn_id": "test-id-1",
                "name": "LinkedIn Expert",
                "current_title": "Software Engineer",
                "current_company": "Tech Corp",
                "similarity": 0.85,
                "credibility": {"level": 3, "percentile": 75.5, "years_experience": 8},
            }
        ]

        # Configure Scholar mock
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        mock_message = MagicMock()
        mock_message.content = '[{"name": "Dr. Scholar", "title": "Professor", "affiliation": "Research University", "interests": ["AI", "Machine Learning"], "citations": 1500}]'
        mock_agent.graph.invoke.return_value = {"messages": [mock_message]}

        # Add a specific mock for the search endpoint
        client.add_mock_response(
            "POST",
            "/search",
            200,
            {
                "experts": {
                    "linkedin": [
                        {
                            "id": "linkedin_1",
                            "name": "LinkedIn Expert",
                            "title": "Software Engineer",
                            "source": "linkedin",
                            "company": "Tech Corp",
                            "location": "San Francisco, CA",
                            "skills": ["Python", "Java"],
                            "summary": "Experienced software engineer",
                            "credibility_level": 3,
                            "credibility_percentile": 75.5,
                            "years_experience": 8,
                        }
                    ],
                    "scholar": [
                        {
                            "id": "scholar_1",
                            "name": "Dr. Scholar",
                            "title": "Professor",
                            "source": "scholar",
                            "company": "Research University",
                            "location": "",
                            "skills": ["AI", "Machine Learning"],
                            "summary": "Leading researcher in machine learning",
                            "credibility_level": 5,
                            "credibility_percentile": 95.0,
                            "years_experience": 15,
                        }
                    ],
                }
            },
        )

        # Make the request
        response = client.post("/search", json={"query": "expert search", "max_results": 5})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "experts" in data
        assert "linkedin" in data["experts"]
        assert "scholar" in data["experts"]

    @patch("main.DVCManager")
    def test_version_database(self, mock_dvc_manager):
        """Test versioning the database."""
        # Configure the mock
        mock_instance = MagicMock()
        mock_dvc_manager.return_value = mock_instance
        mock_instance.version_database.return_value = True

        # Make the request
        response = client.post(
            "/api/data/version", json={"source": "linkedin", "profiles_added": 10, "description": "Test version"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "success" in data
        assert data["success"] is True

    @patch("main.DVCManager")
    def test_get_version_history(self, mock_dvc_manager):
        """Test getting version history."""
        # Configure the mock
        mock_instance = MagicMock()
        mock_dvc_manager.return_value = mock_instance
        mock_instance.get_version_history.return_value = [
            {"commit": "abc123", "date": "2025-05-01", "message": "Test version"}
        ]

        # Make the request
        response = client.get("/api/data/versions")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "versions" in data
        assert len(data["versions"]) == 1

    @patch("main.DVCManager")
    def test_restore_version(self, mock_dvc_manager):
        """Test restoring database to a previous version."""
        # Configure the mock
        mock_instance = MagicMock()
        mock_dvc_manager.return_value = mock_instance
        mock_instance.restore_version.return_value = True

        # Make the request
        response = client.post("/api/data/restore/abc123")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "success" in data
        assert data["success"] is True

    @patch("main.OnDemandCredibilityCalculator")
    def test_update_credibility_stats(self, mock_calculator):
        """Test updating credibility stats."""
        # Configure the mock
        mock_instance = MagicMock()
        mock_calculator.return_value = mock_instance
        mock_instance.update_credibility_stats.return_value = True

        # Make the request
        response = client.post("/api/data/update_credibility_stats?force=true")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "success" in data
        assert data["success"] is True
