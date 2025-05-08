import pytest
import json
from unittest.mock import patch, MagicMock

BASE_URL = "http://localhost:8000"

@pytest.mark.unit
def test_root_endpoint(api_client):
    """Test the root endpoint."""
    with patch('main.ChromaDBManager'):  # Mock ChromaDBManager to avoid initialization
        response = api_client.get("/")
        assert response.status_code == 200
        assert "Welcome to Expert Finder API" in response.json()["message"]
        assert "version" in response.json()
        assert "endpoints" in response.json()

@pytest.mark.unit
def test_health_endpoint(api_client):
    """Test the health check endpoint."""
    with patch('main.ChromaDBManager'):  # Mock ChromaDBManager to avoid initialization
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.unit
def test_search_query_validation(api_client):
    """Test validation for SearchQuery model."""
    with patch('main.ChromaDBManager'):  # Mock ChromaDBManager to avoid initialization
        # Test empty query
        payload = {
            "query": "",  # Empty query should be rejected
            "max_results": 5
        }
        response = api_client.post("/search", json=payload)
        assert response.status_code == 422  # Unprocessable Entity
        
        # Test negative max_results
        payload = {
            "query": "Valid query",
            "max_results": -1  # Negative should be rejected or fixed
        }
        response = api_client.post("/search", json=payload)
        # Depending on implementation, this might return 422 or 200 with a fixed value
        if response.status_code == 200:
            # If implementation fixes the value
            assert response.json()["experts"] is not None
        else:
            # If implementation rejects it
            assert response.status_code == 422

@pytest.mark.unit
def test_search_endpoint_with_mocks(api_client):
    """Test search endpoint with mocked backend services."""
    # Create mock for ChromaDBManager
    mock_chromadb = MagicMock()
    mock_chromadb.query.return_value = [
        {
            "id": "test1",
            "name": "Test Expert",
            "title": "Test Researcher",
            "source": "scholar",
            "citations": 100,
            "interests": ["AI", "Machine Learning"],
            "publications": ["Test paper 1"]
        }
    ]
    
    # Mock the linkedin expert finder too
    mock_linkedin = MagicMock()
    mock_linkedin.find_experts.return_value = []
    
    # Patch the necessary dependencies
    with patch('main.ChromaDBManager', return_value=mock_chromadb), \
         patch('main.ExpertFinderAgent', return_value=mock_linkedin), \
         patch('main.torch_available', True):
        
        # Make the request
        payload = {
            "query": "Machine Learning",
            "max_results": 5
        }
        response = api_client.post("/search", json=payload)
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert "experts" in response_data
        assert isinstance(response_data["experts"], list)
        
        # Verify the mock was called correctly
        mock_chromadb.query.assert_called_once()
        args, kwargs = mock_chromadb.query.call_args
        assert "Machine Learning" in args
        assert kwargs.get("n_results", 0) >= 5

@pytest.mark.unit
def test_version_database_endpoint(api_client):
    """Test the version_database endpoint."""
    # Create mock for DVCManager
    mock_dvc = MagicMock()
    mock_dvc.version_database.return_value = True
    
    # Patch the necessary dependencies
    with patch('main.DVCManager', return_value=mock_dvc), \
         patch('main.ChromaDBManager'):
        
        # Make the request
        payload = {
            "source": "test",
            "profiles_added": 10,
            "description": "Test version"
        }
        response = api_client.post("/api/data/version", json=payload)
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["message"] == "Database successfully versioned"
        
        # Verify the mock was called correctly
        mock_dvc.version_database.assert_called_once()
        args, kwargs = mock_dvc.version_database.call_args
        assert isinstance(args[0], dict)
        assert args[0]["source"] == "test"
        assert args[0]["profiles_added"] == 10

if __name__ == "__main__":
    try:
        test_root_endpoint(api_client)
        test_health_endpoint(api_client)
        test_search_query_validation(api_client)
        test_search_endpoint_with_mocks(api_client)
        test_version_database_endpoint(api_client)
    except Exception as e:
        print("\nError:", str(e))