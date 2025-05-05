# Expert Finder Testing Implementation Guide

This document outlines the comprehensive testing strategy and implementation steps for the Expert Finder project.

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
│   │   ├── test_dvc_utils.py
│   │   ├── test_chroma_db_utils.py
│   │   └── ... (other unit tests)
│   ├── integration/
│   │   ├── test_api_integration.py
│   │   ├── test_chromadb_dvc_integration.py
│   │   └── ... (other integration tests)
│   └── system/
│       ├── test_search_flow.py
│       ├── test_version_management.py
│       └── ... (other system tests)
├── conftest.py  (shared fixtures)
└── ... (existing files)
```

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

### Phase 1: Basic Setup (Week 1)
- [ ] Set up testing directory structure
- [ ] Configure PyTest and coverage
- [ ] Create test runner script
- [ ] Set up GitHub Actions workflow

### Phase 2: Unit Tests (Week 2)
- [ ] Implement DVCManager unit tests
- [ ] Implement ChromaDBManager unit tests
- [ ] Implement API endpoint unit tests
- [ ] Achieve 70% coverage for unit tests

### Phase 3: Integration Tests (Week 3)
- [ ] Implement ChromaDB-DVC integration tests
- [ ] Implement API integration tests
- [ ] Test error handling and edge cases
- [ ] Achieve 70% coverage for integration tests

### Phase 4: System Tests (Week 4)
- [ ] Implement end-to-end search flow tests
- [ ] Implement version management tests
- [ ] Test K8s deployment scenarios
- [ ] Achieve 70% overall coverage

### Phase 5: CI/CD Integration (Week 5)
- [ ] Integrate tests with GitHub Actions
- [ ] Set up coverage reporting
- [ ] Configure automated deployment
- [ ] Document testing procedures

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