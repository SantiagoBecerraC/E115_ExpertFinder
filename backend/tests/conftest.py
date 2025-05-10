import os
import shutil
import socket
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def is_service_reachable(host, port, timeout=0.5):
    """Check if a service is reachable at the given host and port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False


@pytest.fixture
def test_data_dir():
    """Fixture providing a temporary directory for test data."""
    # Create a temporary directory for test data
    temp_dir = tempfile.mkdtemp()

    yield temp_dir

    # Clean up after the test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def test_profiles_dir(test_data_dir):
    """Fixture providing a directory for test LinkedIn profiles."""
    profiles_dir = os.path.join(test_data_dir, "profiles")
    os.makedirs(profiles_dir, exist_ok=True)

    yield profiles_dir


@pytest.fixture
def processed_profiles_dir(test_data_dir):
    """Fixture providing a directory for processed LinkedIn profiles."""
    processed_dir = os.path.join(test_data_dir, "processed_profiles")
    os.makedirs(processed_dir, exist_ok=True)

    yield processed_dir


@pytest.fixture
def fixture_profiles_dir():
    """Fixture providing the path to the fixture profile data."""
    return os.path.join(Path(__file__).parent, "fixtures", "test_data", "profiles")


@pytest.fixture
def fixture_processed_profiles_dir():
    """Fixture providing the path to the fixture processed profile data."""
    return os.path.join(Path(__file__).parent, "fixtures", "test_data", "processed_profiles")


@pytest.fixture
def mock_storage_client():
    """Fixture providing a mock GCS client for testing."""
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_client.bucket.return_value = mock_bucket

    # Set up mocks for blob operations
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    # When download_to_filename is called, create the file
    def download_side_effect(filename):
        with open(filename, "w") as f:
            f.write('{"test": "data"}')

    mock_blob.download_to_filename.side_effect = download_side_effect

    return mock_client


@pytest.fixture
def test_profile_content():
    """Fixture providing content for a test LinkedIn profile."""
    return {
        "profileId": "test-profile-123",
        "firstName": "Test",
        "lastName": "User",
        "headline": "Software Engineer at Test Company",
        "summary": "Experienced software engineer with expertise in Python, Java, and cloud technologies.",
        "industryName": "Software Development",
        "locationName": "San Francisco Bay Area",
        "experience": [
            {
                "companyName": "Test Company",
                "title": "Senior Software Engineer",
                "description": "Developing backend services using Python and AWS.",
                "startDate": {"year": 2020, "month": 1},
                "endDate": None,
                "locationName": "San Francisco, CA",
            },
            {
                "companyName": "Previous Company",
                "title": "Software Engineer",
                "description": "Worked on frontend applications using React and TypeScript.",
                "startDate": {"year": 2018, "month": 3},
                "endDate": {"year": 2019, "month": 12},
                "locationName": "San Francisco, CA",
            },
        ],
        "education": [
            {
                "schoolName": "Test University",
                "degreeName": "Master of Science",
                "fieldOfStudy": "Computer Science",
                "startDate": {"year": 2016},
                "endDate": {"year": 2018},
            },
            {
                "schoolName": "Test College",
                "degreeName": "Bachelor of Science",
                "fieldOfStudy": "Computer Engineering",
                "startDate": {"year": 2012},
                "endDate": {"year": 2016},
            },
        ],
        "skills": [
            {"name": "Python"},
            {"name": "Java"},
            {"name": "JavaScript"},
            {"name": "AWS"},
            {"name": "Docker"},
            {"name": "Machine Learning"},
        ],
    }


@pytest.fixture
def fastapi_test_client():
    """
    Return a FastAPI TestClient for real integration testing.

    This fixture creates a compatible test client that works around FastAPI/Starlette
    version issues while still allowing API testing.
    """
    from .api_test_client import get_api_test_client

    # Check if a local server is running for real testing
    use_real_server = os.environ.get("USE_REAL_API", "").lower() in ["true", "1", "yes"]
    base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

    if use_real_server:
        # Return client that sends real requests to running server
        if is_service_reachable(base_url.replace("http://", "").split(":")[0], int(base_url.split(":")[-1])):
            print("Using real API server at", base_url)
            return get_api_test_client(use_mocks=False, base_url=base_url)

    # Return mock client when server is not available or not requested
    print("Using mock API client")
    return get_api_test_client(use_mocks=True)


@pytest.fixture
def api_client():
    """
    Return a mock API client for testing endpoints.

    This fixture creates a mock client that returns predefined responses for endpoints
    without actually making HTTP requests. This allows tests to run quickly and in isolation.
    """
    from .api_test_client import get_api_test_client

    client = get_api_test_client(use_mocks=True)

    # Add predefined mock responses

    # Health endpoint
    client.add_mock_response("GET", "/health", 200, {"status": "healthy"})

    # Root endpoint
    client.add_mock_response("GET", "/", 200, {"message": "Expert Finder API is running"})

    # Search endpoint - basic result
    client.add_mock_response(
        "POST",
        "/search",
        200,
        {
            "results": [
                {
                    "name": "Test Expert",
                    "title": "Data Scientist",
                    "company": "Test Corp",
                    "summary": "Expert in machine learning with 10+ years of experience",
                    "skills": ["Python", "Machine Learning", "AI"],
                    "credibility_score": 9.0,
                }
            ],
            "total": 1,
        },
        "normal",
    )

    # Search endpoint - empty query error
    client.add_mock_response("POST", "/search", 400, {"detail": "Query parameter is required"}, "empty")

    # Search endpoint - negative max results error
    client.add_mock_response("POST", "/search", 400, {"detail": "max_results must be a positive number"}, "negative")

    # Version endpoints
    client.add_mock_response("POST", "/api/data/version", 200, {"message": "Database successfully versioned"})

    client.add_mock_response(
        "GET",
        "/api/data/version/history",
        200,
        {"versions": [{"commit_hash": "abc123", "date": "2025-04-01", "message": "Test version"}]},
    )

    client.add_mock_response("POST", "/api/data/version/restore", 200, {"message": "Version restored successfully"})

    # Add mock responses for Google Scholar endpoints
    client.add_mock_response(
        "POST",
        "/scholar_search",
        200,
        {
            "experts": [
                {
                    "id": "scholar_1",
                    "name": "Dr. Scholar Test",
                    "title": "Professor of AI",
                    "source": "scholar",
                    "interests": ["Machine Learning", "Deep Learning"],
                    "citations": 1500,
                    "publications": ["Test Publication 1", "Test Publication 2"],
                }
            ],
            "total": 1,
            "source": "scholar",
        },
    )

    # Add mock responses for LinkedIn endpoints
    client.add_mock_response(
        "POST",
        "/linkedin_search",
        200,
        {
            "experts": [
                {
                    "id": "linkedin_1",
                    "name": "LinkedIn Test",
                    "title": "Software Engineer",
                    "source": "linkedin",
                    "company": "Test Company",
                    "skills": ["Python", "Machine Learning", "Data Science"],
                    "years_experience": 5,
                }
            ],
            "total": 1,
            "source": "linkedin",
        },
    )

    with patch("utils.chroma_db_utils.ChromaDBManager") as mock_mgr:
        # ensure any instantiation returns a MagicMock to avoid real DB
        mock_mgr.return_value = MagicMock()
        yield client


@pytest.fixture
def mock_chroma_client():
    """Fixture providing a mock ChromaDB client for testing."""
    with patch("utils.chroma_db_utils.chromadb.PersistentClient") as mock_client:
        # Set up mock collection
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": ["test-doc-1"],
            "documents": ["Test document content"],
            "metadatas": [{"author": "Test Author", "source": "test"}],
            "distances": [0.1],
        }

        # Set up mock client to return the mock collection
        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        yield mock_client_instance


@pytest.fixture
def mock_dvc_manager():
    """Fixture providing a mock DVCManager for testing."""
    mock_dvc = MagicMock()

    # Setup common DVC operations
    mock_dvc.version_database.return_value = True
    mock_dvc.get_version_history.return_value = [
        {"commit_hash": "abc123", "date": "2025-04-01 12:00:00 -0400", "message": "Test version 1"},
        {"commit_hash": "def456", "date": "2025-04-02 12:00:00 -0400", "message": "Test version 2"},
    ]
    mock_dvc.restore_version.return_value = True
    mock_dvc.push_database.return_value = True

    with patch("utils.dvc_utils.DVCManager", return_value=mock_dvc):
        yield mock_dvc

@pytest.fixture
def test_scholar_content():
    """Fixture providing content for a test Google Scholar profile."""
    return {
        "scholar_id": "test-scholar-123",
        "name": "Dr. Test Scholar",
        "affiliations": ["Test University", "Research Institute"],
        "interests": ["Machine Learning", "Artificial Intelligence", "Natural Language Processing"],
        "citations": 1250,
        "h_index": 25,
        "i10_index": 45,
        "publications": [
            {
                "title": "Advances in Test-Driven Machine Learning",
                "year": 2023,
                "authors": ["Test Scholar", "Coauthor One", "Coauthor Two"],
                "publication": "Journal of Test Research",
                "citations": 150
            },
            {
                "title": "Understanding AI in Academic Testing",
                "year": 2021,
                "authors": ["Test Scholar", "Coauthor Three"],
                "publication": "Conference on Artificial Intelligence",
                "citations": 320
            }
        ],
        "co_authors": [
            {"name": "Coauthor One", "scholar_id": "co-1"},
            {"name": "Coauthor Two", "scholar_id": "co-2"},
            {"name": "Coauthor Three", "scholar_id": "co-3"}
        ],
        "url": "https://scholar.example.com/test-scholar-123"
    }


@pytest.fixture
def test_chroma_dir(test_data_dir):
    """Fixture providing a directory for ChromaDB tests."""
    chroma_dir = os.path.join(test_data_dir, "chromadb_test")
    os.makedirs(chroma_dir, exist_ok=True)
    
    yield chroma_dir
    
    # Clean up directory after test
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)