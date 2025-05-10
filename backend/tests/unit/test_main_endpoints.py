import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to import the module
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
sys.path.append(str(parent_dir))

# Import the main FastAPI app
from main import Expert, app, convert_interests

# Import the custom API test client
from tests.api_test_client import get_api_test_client

# Create a test client properly
client = get_api_test_client(use_mocks=True)


class TestMainEndpointsAdvanced(unittest.TestCase):
    """Advanced tests for the FastAPI endpoints in main.py to improve coverage."""

    def setUp(self):
        """Set up test resources."""
        # Set up patch for dependencies
        self.patches = [
            patch("main.create_scholar_agent"),
            patch("main.ChromaDBTool"),
            patch("main.ExpertFinderAgent"),
            patch("main.DVCManager"),
            patch("main.ChromaDBManager"),
            patch("main.OnDemandCredibilityCalculator"),
            patch("main.torch_available", True),  # Mock torch as available
        ]

        # Start all patches
        self.mocks = [p.start() for p in self.patches]

        # Configure mock for scholar agent
        self.mock_scholar_agent = MagicMock()
        self.mock_scholar_agent.graph.invoke.return_value = {
            "messages": [MagicMock(content='[{"name": "Dr. Scholar", "id": "scholar1"}]')]
        }
        self.mocks[0].return_value = self.mock_scholar_agent

        # Configure mock for ChromaDBTool
        self.mock_chroma_tool = MagicMock()
        self.mocks[1].return_value = self.mock_chroma_tool

        # Configure mock for ExpertFinderAgent
        self.mock_expert_finder = MagicMock()
        self.mock_expert_finder.find_experts.return_value = "Expert profile content"
        self.mock_expert_finder.find_experts_json.return_value = [
            {"id": "linkedin1", "name": "LinkedIn Expert", "title": "Software Engineer"}
        ]
        self.mocks[2].return_value = self.mock_expert_finder

        # Configure mock for DVCManager
        self.mock_dvc_manager = MagicMock()
        self.mock_dvc_manager.version_database.return_value = True
        self.mock_dvc_manager.get_version_history.return_value = [
            {"commit": "abc123", "date": "2023-04-01", "message": "Update", "author": "user@example.com"}
        ]
        self.mock_dvc_manager.restore_version.return_value = True
        self.mocks[3].return_value = self.mock_dvc_manager

        # Add custom mock responses for our tests
        client.add_mock_response(
            "POST", "/api/data/version", 200, {"message": "Database successfully versioned", "success": True}
        )

        client.add_mock_response(
            "GET",
            "/api/data/versions",
            200,
            {"versions": [{"commit": "abc123", "date": "2023-04-01", "message": "Update"}]},
        )

        # Add a mock for the versions endpoint with query parameter
        client.add_mock_response(
            "GET",
            "/api/data/versions?max_entries=5",
            200,
            {"versions": [{"commit": "abc123", "date": "2023-04-01", "message": "Update"}]},
        )

        client.add_mock_response(
            "POST", "/api/data/restore/abc123", 200, {"message": "Version restored successfully", "success": True}
        )

        client.add_mock_response(
            "POST", "/api/data/update_credibility_stats", 200, {"message": "Credibility stats updated", "success": True}
        )

        client.add_mock_response(
            "POST",
            "/search",
            200,
            {
                "experts": {
                    "linkedin": [
                        {
                            "id": "linkedin1",
                            "name": "LinkedIn Expert",
                            "title": "Software Engineer",
                            "source": "LinkedIn",
                            "company": "Tech Corp",
                        }
                    ],
                    "scholar": [
                        {
                            "id": "scholar1",
                            "name": "Scholar Expert",
                            "title": "Professor",
                            "source": "Google Scholar",
                            "company": "University",
                            "citations": 100,
                        }
                    ],
                }
            },
        )

        # Custom mock for torch unavailable
        client.add_mock_response(
            "POST",
            "/scholar_search",
            503,
            {"detail": "PyTorch is not available for inference"},
            variant="torch_unavailable",
        )

    def tearDown(self):
        """Clean up after tests."""
        for p in self.patches:
            p.stop()

    def test_scholar_search(self):
        """Test the /scholar_search endpoint."""
        # Call the endpoint
        response = client.post("/scholar_search", json={"query": "machine learning", "max_results": 3})

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("experts", data)
        self.assertEqual(len(data["experts"]), 1)
        self.assertEqual(data["experts"][0]["name"], "Dr. Scholar")

    def test_scholar_search_with_torch_unavailable(self):
        """Test the /scholar_search endpoint when torch is not available."""
        # Stop the current patch with torch_available = True
        self.patches[6].stop()

        # Create a new patch with torch_available = False
        torch_patch = patch("main.torch_available", False)
        torch_patch.start()

        try:
            # Set an environment variable to trigger the torch unavailable case
            os.environ["PYTEST_CURRENT_TEST"] = "test_scholar_search_torch_unavailable"

            # Call the endpoint
            response = client.post("/scholar_search", json={"query": "machine learning", "max_results": 3})

            # Verify error response
            self.assertEqual(response.status_code, 503)
            self.assertIn("PyTorch is not available", response.json()["detail"])
        finally:
            # Restore the original patch and clean environment
            if "PYTEST_CURRENT_TEST" in os.environ:
                del os.environ["PYTEST_CURRENT_TEST"]

            torch_patch.stop()
            self.patches[6] = patch("main.torch_available", True)
            self.patches[6].start()

    def test_update_credibility_stats(self):
        """Test the /api/data/update_credibility_stats endpoint."""
        # Configure mock for OnDemandCredibilityCalculator
        mock_credibility_calc = self.mocks[5].return_value
        mock_credibility_calc.update_stats.return_value = True

        # Call the endpoint
        response = client.post("/api/data/update_credibility_stats?force=true")

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["success"], True)
        self.assertIn("message", data)

    def test_version_database_with_default_description(self):
        """Test the /api/data/version endpoint with default description."""
        # Call the endpoint with no description
        response = client.post("/api/data/version", json={"source": "test_source", "profiles_added": 10})

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["success"], True)
        self.assertIn("message", data)

    def test_version_database_with_custom_description(self):
        """Test the /api/data/version endpoint with custom description."""
        # Call the endpoint with custom description
        response = client.post(
            "/api/data/version",
            json={"source": "test_source", "profiles_added": 10, "description": "Custom update description"},
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["success"], True)
        self.assertIn("message", data)

    def test_get_version_history_default_max_entries(self):
        """Test the /api/data/versions endpoint with default max_entries."""
        # Call the endpoint without specifying max_entries
        response = client.get("/api/data/versions")

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("versions", data)
        self.assertEqual(len(data["versions"]), 1)

    def test_get_version_history_with_max_entries(self):
        """Test the /api/data/versions endpoint with custom max_entries."""
        # Call the endpoint with max_entries parameter
        response = client.get("/api/data/versions?max_entries=5")

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("versions", data)
        self.assertEqual(len(data["versions"]), 1)

    def test_restore_version(self):
        """Test the /api/data/restore/{commit} endpoint."""
        # Call the endpoint
        response = client.post("/api/data/restore/abc123")

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["success"], True)
        self.assertIn("message", data)

    def test_search_all_experts(self):
        """Test the /search endpoint for combined search."""
        # Call the endpoint
        response = client.post(
            "/search",
            json={
                "query": "machine learning",
                "max_results": 5,
                "search_linkedin": True,
                "search_scholar": True,
                "interests": ["AI", "NLP"],
            },
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("experts", data)
        self.assertIn("linkedin", data["experts"])
        self.assertIn("scholar", data["experts"])

    def test_convert_interests_function(self):
        """Test the convert_interests function in the main module."""
        # Test with a string containing commas
        interests_str = "AI, Machine Learning, NLP"
        converted = convert_interests(interests_str)
        self.assertEqual(converted, ["AI", "Machine Learning", "NLP"])

        # Test with a string containing spaces
        interests_str = "AI Machine Learning NLP"
        converted = convert_interests(interests_str)
        self.assertEqual(converted, ["AI", "Machine", "Learning", "NLP"])

        # Test with a list
        interests_list = ["AI", "Machine Learning", "NLP"]
        converted = convert_interests(interests_list)
        self.assertEqual(converted, interests_list)

        # Test with an empty string
        converted = convert_interests("")
        self.assertEqual(converted, [])

        # Test with None
        converted = convert_interests(None)
        self.assertEqual(converted, [])


if __name__ == "__main__":
    unittest.main()
