# Expert Finder Testing Documentation

## Testing Strategy

The Expert Finder application uses a comprehensive testing approach with three levels of tests:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing how components work together
3. **System Tests**: Testing complete workflows from end to end

## Test Coverage

The project aims for at least 70% code coverage. Current coverage metrics:
- Overall: XX%
- DVC Utils: XX%
- ChromaDB Utils: XX%
- API Endpoints: XX%

Modules with limited coverage:
- [List any modules that don't meet the coverage threshold]

## Test Tools

- **PyTest**: Main testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking library
- **httpx**: HTTP client for API testing
- **pytest-asyncio**: For testing async code

## Running Tests

### Prerequisites

1. Set up your Python environment with required dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov pytest-mock httpx pytest-asyncio
   ```

2. Set up any required environment variables for testing:
   ```bash
   export OPENAI_API_KEY=your_test_api_key
   ```

### Running Tests Manually

Use the test runner script:

```bash
# Run all tests
./run_tests.sh

# Run only unit tests
./run_tests.sh --unit

# Run integration tests
./run_tests.sh --integration

# Run system tests
./run_tests.sh --system

# Run tests with coverage
./run_tests.sh --coverage

# Run specific DVC tests
./run_tests.sh --dvc
```

Or use pytest directly:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_dvc_utils.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### CI/CD Integration

Tests are automatically run on GitHub Actions:
- On every push to main and develop branches
- On every pull request to main and develop branches

The CI pipeline includes:
1. Linting with flake8
2. Running all test levels
3. Generating and uploading coverage reports

## Adding New Tests

When adding new features, follow these guidelines for test creation:

1. Create unit tests for each new function or class
2. Create integration tests for interactions between components
3. Update system tests if user workflows are affected
4. Run coverage report to ensure new code is properly tested

## Mocking External Services

For tests that interact with external services (OpenAI, ChromaDB, DVC), use mocking:

```python
# Example of mocking ChromaDB
@patch('chromadb.PersistentClient')
def test_function(mock_client):
    mock_client.return_value.get_collection.return_value = MagicMock()
    # Test code here
```
```

### 8. Improving the Existing Tests

Let's enhance the existing test files:

```python
# Update backend/test_dvc_integration.py with more comprehensive tests
import os
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from utils.chroma_db_utils import ChromaDBManager
from utils.dvc_utils import DVCManager

# More extensive test cases...
```

### 9. K8s Environment Testing Strategy

For Kubernetes environment testing:

1. Create mock deployments for local testing
2. Set up environment variables for switching between local/K8s testing

```python
# Example of K8s-aware test fixture
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
```

## Summary and Next Steps

1. **Immediate Tasks**:
   - Create the test directory structure
   - Implement unit tests for key components (DVC, ChromaDB)
   - Set up the GitHub Actions workflow
   - Create the testing documentation

2. **Medium-term Tasks**:
   - Implement integration tests between components
   - Build system tests for end-to-end workflows
   - Increase test coverage to meet the 70% requirement

3. **Collaboration with Team**:
   - Work with the K8s teammate to ensure tests can run in the deployment environment
   - Coordinate with the CI/CD teammate to ensure tests are integrated into the pipeline

4. **Continuous Improvement**:
   - Regularly review and update tests as the application evolves
   - Monitor test coverage and address gaps
   - Add performance tests for critical operations

This comprehensive testing strategy will help you satisfy the project requirements while ensuring the Expert Finder application remains robust and reliable through future development.