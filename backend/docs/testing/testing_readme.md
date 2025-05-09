# Expert Finder Testing Documentation

## Run Comprehensive Tests

```bash
# Run this command from the backend directory to get comprehensive coverage metrics:
EF_TEST_MODE=1 pytest --cov=. --cov-report=term-missing
```

## Testing Strategy

The Expert Finder application uses a comprehensive testing approach with three levels of tests:

1. **Unit Tests**: Testing individual components in isolation
   - Mock external dependencies (ChromaDB, GCP, Vertex AI, etc.)
   - Test functionality, not implementation details
   - Cover success paths and error handling
   - Use realistic test data fixtures

2. **Integration Tests**: Testing how components work together
   - Test interaction between components with minimal mocking
   - Use in-memory databases where possible
   - Verify data flow across component boundaries

3. **System Tests**: Testing complete workflows from end to end
   - Test full workflows as experienced by end users
   - Verify performance metrics and load handling
   - Test error recovery and resilience

This testing strategy is designed to meet the project's required deliverables:
- Achieve at least 70% code coverage 
- Implement integration tests across the exposed API
- Create a comprehensive testing framework for the RAG pipeline
- Document testing gaps and future improvements

## Test Coverage

The project aims for at least 70% code coverage. A comprehensive test run on May 9, 2025 shows the following accurate coverage metrics:

| Module | Coverage | Status | Priority |
|---|---|---|---|
| Overall | 48% | ⚠️ Needs improvement | - |
| DVC Utils | 96% | ✅ Excellent | Low |
| CLI Commands | 90% | ✅ Excellent | Low |
| ChromaDB Utils | 80% | ✅ Good | Low |
| Scholar Data Vectorization | 77% | ✅ Good | Low |
| LinkedIn Vectorizer | 72% | ✅ Good | Low |
| Dynamic Credibility | 71% | ✅ Good | Low |
| Credibility System | 54% | ⚠️ Moderate | Medium |
| Process LinkedIn Profiles | 43% | ⚠️ Needs improvement | High |
| Scholar Data Processor | 45% | ⚠️ Needs improvement | Medium |
| Credibility Stats | 25% | ⚠️ Poor | High |
| ExpertFinderAgent | 33% | ⚠️ Needs improvement | High |
| Main API Endpoints | 0% | ❌ Missing | Critical |
| Test ChromaDB | 10% | ❌ Poor | Low |

### Recent Improvements:

1. **CLI Module (linkedin_data_processing/cli.py)**
   - Increased coverage from 0% to 90%
   - Implemented tests for all command-line functions
   - Verified error handling and boundary conditions

2. **ExpertFinderAgent (linkedin_data_processing/expert_finder_linkedin.py)**
   - Increased coverage from 7% to 33% 
   - Added tests for core functionality like expert search and response generation
   - Implemented mocks for Vertex AI and ChromaDB integrations

3. **Several other modules have better coverage than previously reported**
   - LinkedIn Vectorizer: 72% (previously reported as 0%)
   - Dynamic Credibility: 71% (previously reported as 0%)
   - ChromaDB Utils: 80% (previously reported as 49%)
   - Process LinkedIn Profiles: 43% (previously reported as 0%)

## Test Tools

- **PyTest**: Main testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking library
- **httpx**: HTTP client for API testing
- **pytest-asyncio**: For testing async code

## Implementation Phases

The testing implementation has been divided into multiple phases:

### Phase 1: Basic Setup and Assessment

Phase 1 focused on establishing the testing infrastructure:

1. **Directory Structure**: Created a hierarchical testing structure:
   ```
   backend/
   ├── tests/
   │   ├── unit/        # Tests for individual components
   │   ├── integration/ # Tests for component interactions
   │   ├── system/      # End-to-end tests
   │   ├── fixtures/    # Shared test data and mocks
   │   └── conftest.py  # Shared pytest fixtures
   ```

2. **Pytest Configuration**: Set up pytest configuration in `pytest.ini` with:
   - Test discovery paths and patterns
   - Custom markers (unit, integration, system, dvc, slow)
   - Coverage settings specific to target modules

3. **Coverage Configuration**: Created `.coveragerc` to:
   - Define source directories to analyze
   - Specify paths to exclude (tests, site-packages, etc.)
   - Configure reporting options

4. **Test Isolation Fixtures**: Implemented fixtures in `conftest.py` for:
   - Temporary directories for ChromaDB and DVC testing
   - Environment variable management
   - Mock API clients for external services

### Phase 2: API Testing and Unit Test Expansion

Phase 2 built upon the framework to implement comprehensive tests:

1. **Google Scholar Module Tests**: Created specialized tests for:
   - `test_download_scholar_data.py`: Testing the API interaction, data extraction, and saving mechanisms
   - `test_scholar_data_processor.py`: Testing the processing of raw scholar data
   - `test_scholar_data_vectorization.py`: Testing preparation of data for ChromaDB

2. **Hybrid API Testing Framework**: We use two complementary approaches for API testing:

   **A. MockTestClient for Unit Tests**:
   - Implemented in `conftest.py` as a custom `MockTestClient`
   - Works around FastAPI/Starlette version compatibility issues
   - Simulates API endpoints without requiring a running server
   - Provides standardized response structures for various endpoints
   - Isolates tests from environmental dependencies (PyTorch, Cohere, etc.)
   - Used in `test_api.py` for stable, dependency-free testing

   **B. FastAPI TestClient for Integration Tests**:
   - Set up in `conftest.py` as the `fastapi_test_client` fixture
   - Provides real testing of the actual FastAPI application code
   - Properly mocks backend dependencies (ChromaDB, DVC, etc.)
   - Compatible with the CI/CD pipeline requirements
   - Used in `test_api_testclient.py` for integration-focused testing
   - Requires more environment setup but provides higher fidelity

3. **API Endpoint Testing Coverage**: Our API tests verify:
   - Input validation and error handling
   - Response structure validation
   - Different search endpoints and sources
   - Database versioning operations
   - End-to-end workflow integration

## API and Method Connections

### Google Scholar Data Flow

1. **Download → Process → Vectorize → Store** Pipeline:

   ```
   download_scholar_data.py                scholar_data_processor.py              scholar_data_vectorization.py
   ┌────────────────────┐                ┌────────────────────────┐             ┌─────────────────────────────┐
   │                    │                │                        │             │                             │
   │ extract_data() ────┼───JSON Data───►│ process_scholar_data() ├─────┐      │                             │
   │                    │                │                        │      │      │                             │
   │ save_to_json() ────┼───────────────►│ prepare_chroma_data()  │      ├─────► load_google_scholar_data()  │
   │                    │                │                        │      │      │                             │
   └────────────────────┘                └────────────────────────┘      │      │ prepare_documents_for_     │
                                                                         └─────► chromadb()                  │
                                                                                │                             │
                                                                                │ load_to_chromadb()          │
                                                                                │                             │
                                                                                └─────────────────────────────┘
                                                                                           │
                                                                                           ▼
                                                                                   ChromaDB Storage
   ```

2. **Function Relationships**:

   - `extract_data()`: Queries Google Scholar API with given parameters, extracts article data, author information, and citations.
   - `save_to_json()`: Stores extracted data as JSON files for later processing.
   - `process_scholar_data()`: Reads JSON files, transforms data into author-centric structure where each author has a collection of their articles.
   - `prepare_chroma_data()`: Converts processed data into ChromaDB-ready format with metadata, document content, and IDs.
   - `load_google_scholar_data()`: Loads all processed JSON files from data directory.
   - `prepare_documents_for_chromadb()`: Creates content documents for each author and their publications with metadata.
   - `load_to_chromadb()`: Uploads documents to ChromaDB for vector search.

3. **Testing Approach**:

   - **Mock Data Flow**: Tests provide mock input data at each step
   - **Function Isolation**: Each function is tested separately with controlled inputs
   - **Output Validation**: Verify structure, content, and transformations
   - **Error Handling**: Test edge cases like empty data, missing fields, and malformed inputs

### API Endpoint Architecture

1. **Search Workflow**:

   ```
   ┌─────────────┐         ┌───────────────┐         ┌──────────────────────┐
   │             │ Request │               │ Query   │                      │
   │ Client ─────┼────────►│ FastAPI       ├────────►│ ChromaDB / DVC       │
   │             │         │ Endpoints     │         │ Integration          │
   │             │◄────────┼───────────────┼◄────────┤                      │
   └─────────────┘ Response│               │ Results │                      │
                           └───────────────┘         └──────────────────────┘
   ```

2. **API Endpoint Functions**:

   - `search_all_experts()`: Main search endpoint combining results from all sources
   - `search_scholar_experts()`: Searches only Google Scholar data
   - `search_linkedin_experts()`: Searches only LinkedIn data
   - `version_database()`: Creates a DVC version of the current database state
   - `get_version_history()`: Retrieves history of database versions
   - `restore_version()`: Restores the database to a specific version
   - `update_credibility_stats()`: Updates expert credibility statistics

3. **Model Validation**:

   - `SearchQuery`: Validates search parameters (query string, max_results)
   - `Expert`: Defines the structure of expert data returned from searches
   - `VersionInfo`: Specifies metadata for database versioning operations

4. **Testing Strategy**:

   - **Mock Client**: `MockTestClient` provides simulated API responses
   - **Input Validation**: Tests various input combinations to verify validation
   - **Response Structure**: Ensures responses follow expected format
   - **Edge Cases**: Tests boundary conditions and error handling

### ChromaDB and DVC Utilities

1. **ChromaDBManager**:

   - Manages connections to ChromaDB
   - Provides methods for adding, querying, and deleting documents
   - Handles collections and embeddings

2. **DVCManager**:

   - Interfaces with DVC for versioning ChromaDB data
   - Tracks version history
   - Provides restore functionality for reverting to previous states

3. **Testing Approach**:

   - Mock ChromaDB client responses
   - Patch subprocess calls for DVC operations
   - Verify correct parameter passing and command construction
   - Test error handling and edge cases

## Mocking Strategy

The testing framework employs strategic mocking to isolate components:

1. **External API Mocking**:
   - Google Scholar API calls are mocked to return predefined responses
   - ChromaDB client operations are simulated

2. **File System Operations**:
   - File reads/writes are mocked using `mock_open`
   - Temporary directories are used for actual file operations

3. **API Endpoint Testing**:
   - `MockTestClient` replaces FastAPI's TestClient
   - Provides predefined responses for each endpoint
   - Supports dynamic response based on input parameters

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

### API Testing Options

```bash
# Run the MockTestClient API tests (unit tests)
pytest tests/unit/test_api.py

# Run the FastAPI TestClient API tests (integration tests)
# Note: These require additional dependencies like PyTorch and Cohere
pytest tests/unit/test_api_testclient.py

# To run a specific test from the TestClient tests
pytest tests/unit/test_api_testclient.py::test_root_endpoint

# Environment setup for integration tests
export USE_REAL_SERVICES=false  # Use in-memory mocks for ChromaDB, etc.
```

#### API Testing Environment Dependencies

Integration tests with FastAPI's TestClient require additional setup:

```bash
# Install API dependencies for integration tests
pip install cohere torch langchain

# Or use Conda/Micromamba
micromamba install -c conda-forge cohere-python pytorch langchain
```

### CI/CD Integration

Tests are automatically run on GitHub Actions:
- On every push to main and develop branches
- On every pull request to main and develop branches

The CI pipeline includes:
1. Linting with flake8
2. Running all test levels
3. Generating and uploading coverage reports

## Next Steps

The testing framework is now ready for Phase 3 implementation:

1. **Integration Tests**: Develop tests for component interactions:
   - ChromaDB and DVC integration
   - Search pipeline from query to results
   - Version management workflow

2. **System Tests**: Create end-to-end tests:
   - Complete user workflows
   - API connectivity with frontend
   - Data flow through entire system

3. **CI/CD Integration**:
   - Configure GitHub Actions workflow
   - Implement coverage gate (fail if < 70%)
   - Set up reporting and notifications