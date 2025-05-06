# Expert Finder Testing Implementation Guide

This document outlines the comprehensive testing strategy and implementation steps for the Expert Finder project.

## 0. Current State Assessment (May 2025)

### Existing Testing Infrastructure
- Directory layout already follows the structure proposed in this document (unit / integration / system / fixtures)
- Unit tests exist for many utility modules (`chroma_db_utils`, Scholar / LinkedIn data processing, etc.)
- A few integration tests exist (DVC ChromaDB)
- No real system-level tests yet (`backend/tests/system` only has `__init__.py`)
- GitHub Actions workflow directory is empty – tests are **not** wired into CI
- No coverage config (`.coveragerc`) or HTML/Codecov upload
- Existing FastAPI endpoint tests (`test_api.py`) call a running server via `requests` rather than using `fastapi.testclient`
- Some key modules basically untested:
  - `main.py` endpoint logic & Pydantic validators
  - `DVCManager.version_database / restore_version / get_version_history` (needs `subprocess` / git mocks)
  - `OnDemandCredibilityCalculator` and anything inside `linkedin_data_processing`
- No automatic lint step (flake8 / isort) or code-format check in CI
- No fixtures for ChromaDB / DVC isolation across tests
- Tests do not use `pytest` markers (`unit`, `integration`, `system`) for filtering

### Gaps vs. Project Requirements
| Requirement | Gap / Issue |
|-------------|-------------|
| ≥70% line coverage, doc listing uncovered parts | Coverage job missing, actual % unknown, no report |
| Unit / Integration / System tests in CI | System tests not in place |
| Linting on every push / PR | Not configured |
| GitHub Actions should run Docker builds for each container | Build step missing |
| Integration tests must hit exposed API | Need `pytest` HTTP client tests |
| K8s "health-check" probe must be exercised in tests | Only `/health` endpoint exists; not tested |

## 1. Testing Framework Setup

### PyTest Configuration
```bash
# Install additional testing dependencies
pip install pytest pytest-cov pytest-mock httpx pytest-asyncio
```

Create/update `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
filterwarnings =
    ignore::DeprecationWarning
    ignore::UserWarning
markers =
    unit: Unit tests
    integration: Integration tests
    system: System tests
    dvc: Data version control tests
    slow: Tests that take a long time to run
```

## 2. Testing Structure

Create the following directory structure:
```
backend/
├── tests/
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_dvc_utils.py
│   │   ├── test_chroma_db_utils.py
│   │   ├── test_linkedin_finder.py
│   │   └── test_api.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_dvc_integration.py
│   │   ├── test_chromadb_dvc_integration.py
│   │   └── test_api_integration.py
│   ├── system/
│   │   ├── __init__.py
│   │   ├── test_search_flow.py
│   │   └── test_version_management.py
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── test_data/
│   │   │   ├── sample_experts.json
│   │   │   └── sample_queries.json
│   │   └── mock_services/
│   │       ├── mock_chromadb.py
│   │       └── mock_dvc.py
│   └── conftest.py
├── docs/
│   ├── testing/
│   │   ├── testing_readme.md
│   │   └── testing_todo.md
│   └── coverage/
│       └── coverage_reports/
├── scripts/
│   ├── run_tests.sh
│   └── format_and_lint.sh
├── .github/
│   └── workflows/
│       └── test.yml
├── .coveragerc
└── pytest.ini
```

### Directory Structure Explanation

1. **tests/**
   - `unit/`: Contains all unit tests for individual components
   - `integration/`: Contains tests for component interactions
   - `system/`: Contains end-to-end system tests
   - `fixtures/`: Contains test data and mock services
   - `conftest.py`: Shared pytest fixtures and configurations

2. **docs/testing/**
   - Contains all testing-related documentation
   - `testing_readme.md`: General testing documentation
   - `testing_todo.md`: Testing implementation guide

3. **scripts/**
   - Contains utility scripts for testing
   - `run_tests.sh`: Test runner script
   - `format_and_lint.sh`: Code formatting and linting

4. **.github/workflows/**
   - Contains CI/CD workflow configurations
   - `test.yml`: GitHub Actions test workflow

5. **Configuration Files**
   - `.coveragerc`: Coverage configuration
   - `pytest.ini`: PyTest configuration

### File Organization Rules

1. **Test Files**
   - All test files should be prefixed with `test_`
   - Test files should be placed in the appropriate test type directory
   - Each test file should have a corresponding `__init__.py`

2. **Test Data**
   - All test data should be placed in `tests/fixtures/test_data/`
   - Mock services should be placed in `tests/fixtures/mock_services/`

3. **Documentation**
   - All testing documentation should be placed in `docs/testing/`
   - Coverage reports should be placed in `docs/coverage/coverage_reports/`

4. **Scripts**
   - All utility scripts should be placed in `scripts/`
   - Scripts should be executable and documented

## 3. Test Types Implementation

### Unit Tests Implementation

1. **DVCManager Tests** (`tests/unit/test_dvc_utils.py`):
   - Test initialization
   - Test version_database
   - Test restore_version
   - Test get_version_history
   - Test error handling

2. **ChromaDBManager Tests** (`tests/unit/test_chroma_db_utils.py`):
   - Test initialization
   - Test query functionality
   - Test add_documents
   - Test add_documents_with_version
   - Test collection management

### Integration Tests Implementation

1. **ChromaDB-DVC Integration** (`tests/integration/test_chromadb_dvc_integration.py`):
   - Test document addition with versioning
   - Test version restoration
   - Test version history retrieval
   - Test error handling in integration

2. **API Integration** (`tests/integration/test_api_integration.py`):
   - Test version_database endpoint
   - Test get_version_history endpoint
   - Test restore_version endpoint
   - Test error responses

### System Tests Implementation

1. **Search Flow** (`tests/system/test_search_flow.py`):
   - Test end-to-end search functionality
   - Test expert profile retrieval
   - Test result formatting
   - Test error handling

## 4. Test Coverage Configuration

Create `.coveragerc`:
```ini
[run]
source = .
omit = 
    venv/*
    */tests/*
    */migrations/*
    */site-packages/*
    */dist-packages/*
    */__pycache__/*
    */.eggs/*
    
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError
```

## 5. GitHub Actions CI Implementation

Create `.github/workflows/test.yml`:
```yaml
name: Run Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install pytest pytest-cov pytest-mock httpx pytest-asyncio
        
    - name: Lint with flake8
      run: |
        pip install flake8
        cd backend
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        
    - name: Run unit tests
      run: |
        cd backend
        pytest tests/unit/ -v --cov=.
        
    - name: Run integration tests
      run: |
        cd backend
        pytest tests/integration/ -v --cov=. --cov-append
        
    - name: Run system tests
      run: |
        cd backend
        pytest tests/system/ -v --cov=. --cov-append
        
    - name: Generate coverage report
      run: |
        cd backend
        pytest --cov=. --cov-report=xml
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        fail_ci_if_error: true
```

## 6. Test Runner Script

Create `backend/run_tests.sh`:
```bash
#!/bin/bash

# Parse command line arguments
TYPE="all"
COVERAGE=false

for arg in "$@"
do
    case $arg in
        --unit)
        TYPE="unit"
        shift
        ;;
        --integration)
        TYPE="integration"
        shift
        ;;
        --system)
        TYPE="system"
        shift
        ;;
        --dvc)
        TYPE="dvc"
        shift
        ;;
        --coverage)
        COVERAGE=true
        shift
        ;;
    esac
done

# Base command
CMD="python -m pytest"

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    CMD="$CMD --cov=. --cov-report=term --cov-report=html"
fi

# Run specific test type
case $TYPE in
    unit)
    echo "Running unit tests..."
    $CMD tests/unit/ -v
    ;;
    integration)
    echo "Running integration tests..."
    $CMD tests/integration/ -v
    ;;
    system)
    echo "Running system tests..."
    $CMD tests/system/ -v
    ;;
    dvc)
    echo "Running DVC tests..."
    $CMD -m dvc -v
    ;;
    all)
    echo "Running all tests..."
    $CMD -v
    ;;
esac

# If coverage was generated, show the report location
if [ "$COVERAGE" = true ]; then
    echo "Coverage report generated in htmlcov/index.html"
fi
```

Make it executable:
```bash
chmod +x backend/run_tests.sh
```

## 7. K8s Environment Testing Strategy

For Kubernetes environment testing:

1. Create mock deployments for local testing
2. Set up environment variables for switching between local/K8s testing

Example K8s-aware test fixture:
```python
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

## 8. Implementation Timeline

### Phase 1: Basic Setup and Assessment (Week 1)
- Set up testing directory structure
- Configure PyTest
- Create `.coveragerc` to configure coverage settings
- Measure current coverage (`pytest --cov=backend --cov-report=term-missing`)
- Document uncovered modules and functions
- Add PyTest markers (`@pytest.mark.unit`, etc.) to existing tests
- Update the `run_tests.sh` script to filter on markers

### Phase 2: API Testing Improvement & Unit Test Expansion (Week 2)
- Convert `test_api.py` to use `fastapi.testclient` instead of `requests`
- Add tests for the `/health` endpoint
- Implement missing unit tests for:
  - `utils.dvc_utils` (mock `subprocess.run`)
  - `main.SearchQuery` validators (edge cases)
  - `linkedin_data_processing` vectorizer logic
- Create shared fixtures for:
  - Temporary ChromaDB directory
  - Temporary DVC repository
  - FastAPI test client

### Phase 3: Integration & System Tests (Week 3)
- Create `tests/system/test_end_to_end.py` with tests that:
  - Spin up `TestClient`
  - Push a sample document to ChromaDB
  - Call `/search` endpoints
  - Assert combined results from different sources
- Implement K8s-aware fixture for environment variable switching
- Test scaling scenarios with multiple concurrent requests

### Phase 4: CI/CD Pipeline Implementation (Week 4)
- Create `.github/workflows/ci.yml` with:
  - Linting step (flake8 / isort)
  - Unit & integration tests
  - Coverage gate (fail if < 70%)
  - Docker build verification
- Add Codecov upload step
- Configure deployment to Kubernetes on successful merge to main

### Phase 5: Integration with Kubernetes (Week 5)
- Implement system tests that run in a Kubernetes environment
- Test auto-scaling capabilities
- Verify liveness and readiness probes
- Automate deployment validation
- Achieve 70% overall coverage

## 9. Collaboration Points

### With K8s Team
- Coordinate on environment variables
- Share test deployment configurations
- Align on scaling test scenarios

### With CI/CD Team
- Integrate test results into pipeline
- Set up automated deployment triggers
- Configure coverage reporting

## 10. Quality Metrics

### Coverage Goals
- Overall code coverage: ≥70%
- Critical path coverage: ≥90%
- DVC operations coverage: ≥80%
- API endpoints coverage: ≥85%

### Performance Metrics
- Test execution time: <5 minutes
- CI pipeline time: <15 minutes
- Test reliability: >99%

## 11. Maintenance Plan

### Regular Tasks
- Weekly coverage report review
- Monthly test suite optimization
- Quarterly performance benchmark
- Bi-annual test strategy review

### Documentation Updates
- Update test documentation monthly
- Review and update test cases quarterly
- Maintain test coverage dashboard
- Document new test patterns

## 12. Risk Management

### Identified Risks
1. Flaky tests in CI environment
2. Coverage gaps in critical paths
3. Performance degradation with test growth
4. Integration test complexity

### Mitigation Strategies
1. Implement retry mechanisms for flaky tests
2. Regular coverage analysis and gap filling
3. Test suite optimization and parallelization
4. Modular test design and clear documentation