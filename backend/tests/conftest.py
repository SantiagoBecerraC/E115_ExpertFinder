import os
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "fixtures" / "test_data"

@pytest.fixture
def mock_services_dir():
    """Return the path to the mock services directory."""
    return Path(__file__).parent / "fixtures" / "mock_services"

@pytest.fixture
def k8s_environment():
    """Set up a test environment that simulates K8s deployment."""
    original_env = os.environ.copy()
    
    # Set environment variables that would be present in K8s
    os.environ["KUBERNETES_SERVICE_HOST"] = "127.0.0.1"
    os.environ["KUBERNETES_SERVICE_PORT"] = "8443"
    os.environ["CHROMA_DB_HOST"] = "chroma-service"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def temp_chroma_dir(tmp_path):
    """Create a temporary directory for ChromaDB testing."""
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    return chroma_dir

@pytest.fixture
def temp_dvc_dir(tmp_path):
    """Create a temporary directory for DVC testing."""
    dvc_dir = tmp_path / "dvc"
    dvc_dir.mkdir()
    return dvc_dir 