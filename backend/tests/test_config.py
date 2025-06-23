"""
Test configuration for connecting to real services.

This module provides configuration for tests to connect to real services 
running in Docker or Kubernetes, with fallback to mocks when services are unavailable.
"""

import os
import socket
from pathlib import Path


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


# Detect if we're running in Kubernetes
IN_KUBERNETES = os.environ.get("KUBERNETES_SERVICE_HOST") is not None

# ChromaDB connection configuration
if IN_KUBERNETES:
    CHROMA_HOST = os.environ.get("CHROMA_DB_HOST", "chroma-service")
    CHROMA_PORT = int(os.environ.get("CHROMA_DB_PORT", "8000"))
else:
    CHROMA_HOST = os.environ.get("CHROMA_DB_HOST", "localhost")
    CHROMA_PORT = int(os.environ.get("CHROMA_DB_PORT", "8000"))

# Check if ChromaDB is available
CHROMA_AVAILABLE = is_service_reachable(CHROMA_HOST, CHROMA_PORT)

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "fixtures" / "test_data"

# Force real service usage (override automatic detection)
USE_REAL_SERVICES = os.environ.get("USE_REAL_SERVICES", "False").lower() in ["true", "1", "yes"]

# API Keys for external services
# These are set for tests only - never use these in production code
OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY",
    "your-key-here",
)
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "your-key-here")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "your-key-here")

# Search engine constants
GOOGLE_NEWS = "google_news"
GOOGLE = "google"

# Test settings
SKIP_SLOW_TESTS = os.environ.get("SKIP_SLOW_TESTS", "False").lower() in ["true", "1", "yes"]
SKIP_INTEGRATION_TESTS = (
    os.environ.get("SKIP_INTEGRATION_TESTS", "False").lower() in ["true", "1", "yes"] and not USE_REAL_SERVICES
)
