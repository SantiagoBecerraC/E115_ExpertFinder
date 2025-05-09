# Expert Finder Testing Development Plan

This document outlines the comprehensive testing strategy for the Expert Finder project, focusing on real data and implementations.

## System Overview

The Expert Finder system consists of six key stages:

1. **Data Collection**: Gathering data from LinkedIn and Google Scholar sources
2. **Data Processing**: Processing raw data into a structured format
3. **Data Vectorization**: Converting processed data into vector embeddings
4. **Database Storage**: Storing vectorized data in ChromaDB
5. **Version Control** (Optional): Versioning the data using DVC
6. **Query & Response**: Using LLM to query the database and return results to the frontend

## Testing Approach

Our testing strategy is organized into three layers:

- **Unit Tests**: Testing individual components in isolation
- **Integration Tests**: Testing interactions between components
- **System Tests**: Testing end-to-end workflows

All tests will use real data and implementations wherever possible, not mock objects or shortcuts.

## Directory Structure

```
backend/
├── tests/
│   ├── unit/               # Unit tests for individual components
│   ├── integration/        # Tests for component interactions
│   ├── system/             # End-to-end system tests
│   ├── fixtures/           # Test data and helper functions
│   │   ├── test_data/
│   │   │   ├── linkedin/   # LinkedIn test data (pre/post processing)
│   │   │   └── scholar/    # Google Scholar test data (pre/post processing)
│   │   └── conftest.py     # Shared pytest fixtures
```

## Test Implementation Plan

### Priority Order for Testing

Based on code analysis and current coverage levels (15% initially), we've identified the following testing priorities to reach our 70% coverage target:

#### Priority 1: Core Utilities (High Impact)

1. **utils/chroma_db_utils.py** (325 lines) - Used throughout the app
   - Test initialization with various configurations
   - Test collection management (create, reset, delete)
   - Test document operations (add, query, count)
   - Test error handling and edge cases

2. **utils/dvc_utils.py** (201 lines) - Used for versioning
   - Test initialization and repo setup
   - Test version operations (create, list, restore)
   - Test error handling for common DVC issues

#### Priority 2: LinkedIn Processing (Largest Modules)

3. **linkedin_data_processing/process_linkedin_profiles.py** (1,032 lines)
   - Use test data: `backend/tests/fixtures/test_data/linkedinProfiles_beforeProcessing/profile_0.json`
   - Test extraction of profile fields
   - Test profile cleaning and normalization
   - Test special case handling

4. **linkedin_data_processing/expert_finder_linkedin.py** (766 lines) 
   - Test core functionality except search function
   - Test profile scoring and ranking
   - Test expert identification logic

#### Priority 3: Vectorization (Search Interface)

5. **google_scholar/scholar_data_vectorization.py** (306 lines)
   - Use test data: `backend/tests/fixtures/test_data/Google_Scholar_Data_semiglutide_20250414_231353.json`
   - Test document preparation
   - Test embedding generation
   - Test ChromaDB integration

6. **linkedin_data_processing/linkedin_vectorizer.py** (476 lines)
   - Use test data: `backend/tests/fixtures/test_data/ACoAAA-n0MQBGjQ97rW5iLkYlYSolGR_7vSvoXE_processed.json`
   - Test vectorization of LinkedIn profiles
   - Test metadata extraction
   - Test embedding quality checks

### 1. Data Processing Tests

#### Unit Tests

**LinkedIn Data Processing**

```python
# test_linkedin_profile_processor.py

def test_extract_profile_data():
    """Test extraction of relevant data from a raw LinkedIn profile."""
    # Load real raw LinkedIn profile from fixtures
    # Call extract_profile_data function
    # Verify structure and key fields

def test_create_profile_text():
    """Test creating text representation of a profile for embedding."""
    # Load real processed LinkedIn profile
    # Call create_profile_text function
    # Verify that text includes important profile information
```

**Google Scholar Processing**

```python
# test_scholar_data_processor.py

def test_process_scholar_data():
    """Test processing scholar data from a real file."""
    # Load real Google Scholar data file
    # Call process_scholar_data function
    # Verify structure and key fields

def test_prepare_chroma_data():
    """Test preparing data for ChromaDB format."""
    # Use real processed scholar data
    # Call prepare_chroma_data function
    # Verify that data is formatted correctly for ChromaDB
```

### 2. Vectorization Tests

#### Unit Tests

**LinkedIn Vectorization**

```python
# test_linkedin_vectorizer.py

def test_create_profile_embeddings():
    """Test creating embeddings from LinkedIn profile text."""
    # Load real processed LinkedIn profile
    # Call function to create embeddings
    # Verify embedding structure and dimensions

def test_add_profiles_to_chroma():
    """Test adding LinkedIn profiles to ChromaDB."""
    # Create temporary ChromaDB
    # Use real LinkedIn profiles
    # Call add_profiles_to_chroma function
    # Verify profiles were added correctly
```

**Google Scholar Vectorization**

```python
# test_scholar_data_vectorization.py

def test_prepare_documents_for_chromadb():
    """Test preparing documents for ChromaDB using real author data."""
    # Load real author data
    # Call prepare_documents_for_chromadb function
    # Verify document structure is correct for ChromaDB

def test_load_to_chromadb():
    """Test loading documents to a real ChromaDB instance."""
    # Create temporary ChromaDB
    # Prepare real documents
    # Load to ChromaDB
    # Verify documents were added correctly
```

### 3. ChromaDB Storage Tests

#### Unit Tests

```python
# test_chroma_db_utils.py

def test_chroma_manager_initialization():
    """Test ChromaDBManager initialization."""
    # Create ChromaDBManager with real settings
    # Verify connection and collection setup

def test_add_documents():
    """Test adding documents to ChromaDB."""
    # Create real documents based on test data
    # Add to ChromaDB
    # Verify documents were added correctly

def test_query_collection():
    """Test querying ChromaDB collection."""
    # Add test documents to collection
    # Perform different types of queries
    # Verify query results
```

### 4. DVC Version Control Tests

#### Unit Tests

```python
# test_dvc_utils.py

def test_initialize_dvc():
    """Test initializing DVC in a test directory."""
    # Create temp directory
    # Initialize DVC
    # Verify DVC initialization

def test_version_database():
    """Test versioning database changes."""
    # Create temp directory with DVC
    # Create test files
    # Version with DVC
    # Verify commit created

def test_restore_version():
    """Test restoring a previous version."""
    # Create temp directory with DVC
    # Create and version multiple file changes
    # Restore to a previous version
    # Verify files match expected state
```

### 5. LLM Query Tests

#### Unit Tests

```python
# test_expert_finder_agent.py

def test_search_profiles():
    """Test searching for profiles with semantic search."""
    # Set up test ChromaDB with real profiles
    # Perform search with test query
    # Verify search results format and relevance

def test_generate_response():
    """Test generating a response from search results."""
    # Create sample search results from real data
    # Generate response
    # Verify response structure and content
```

### 6. API and Integration Tests

#### Integration Tests

```python
# test_api.py

def test_search_endpoint():
    """Test the search endpoint with TestClient."""
    # Create TestClient with app
    # Send search request
    # Verify response structure and status code

def test_linkedin_search_endpoint():
    """Test LinkedIn-specific search."""
    # Create TestClient with app
    # Send LinkedIn search request
    # Verify response structure and source field

def test_scholar_search_endpoint():
    """Test Scholar-specific search."""
    # Create TestClient with app
    # Send Scholar search request
    # Verify response structure and source field
```

### 7. System Tests (End-to-End)

#### System Tests

```python
# test_search_flow.py

def test_end_to_end_search():
    """Test the complete search flow from query to response."""
    # Set up test environment with real data
    # Send search request
    # Verify complete pipeline execution
    # Check response quality

def test_combined_sources_search():
    """Test searching from multiple sources."""
    # Set up test environment with LinkedIn and Scholar data
    # Send search request that should match both sources
    # Verify results contain items from both sources
    # Check combined response quality
```

## Test Fixtures

```python
# conftest.py

@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def temp_dvc_dir():
    """Create a temporary directory for DVC testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git and DVC in the temp directory
        subprocess.run(["git", "init"], cwd=tmpdir, check=True)
        subprocess.run(["dvc", "init"], cwd=tmpdir, check=True)
        yield tmpdir

@pytest.fixture
def linkedin_profile_fixture():
    """Load a real LinkedIn profile for testing."""
    fixture_path = Path(__file__).parent / "test_data" / "linkedin" / "sample_profile_processed.json"
    with open(fixture_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def scholar_data_fixture():
    """Load real Google Scholar data for testing."""
    fixture_path = Path(__file__).parent / "test_data" / "scholar" / "sample_scholar_processed.json"
    with open(fixture_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def fastapi_test_client():
    """Create a TestClient for FastAPI testing."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
```

## Testing Principles

1. **Use Real Data**: All tests should use real data from fixtures where possible.
2. **No Mocking Core Logic**: Avoid mocking core application logic; test the real implementation.
3. **Isolate External Dependencies**: Only mock external dependencies like API calls or remote services.
4. **Test Complete Workflows**: Ensure end-to-end testing of key user flows.
5. **Maintain Test Data Quality**: Keep test fixtures up-to-date with production data structure.

## Known Issues and Limitations

- Testing download functionality will be handled later.
- Current Google Scholar module test coverage (54%) has the following gaps that need to be addressed:
  - Main functions (`main()`) in both `scholar_data_processor.py` and `scholar_data_vectorization.py` aren't being tested
  - Error handling code paths aren't covered
  - `load_google_scholar_data()` function in vectorization.py isn't tested
  - Some conditional branches in processing logic aren't exercised by current tests

## Implementation Strategy

### Phase 1: Foundation Tests
- Set up testing directory structure
- Create basic fixtures with real test data
- Implement basic unit tests for core components

### Phase 2: Core Component Tests
- Implement comprehensive unit tests for data processing
- Implement comprehensive unit tests for vectorization
- Create ChromaDB tests with real data

### Phase 3: Integration and System Tests
- Implement integration tests between components
- Develop system tests for end-to-end workflows
- Test real LLM queries against test database

## Coverage Targets

- Overall test coverage: ≥70%
- Critical paths coverage: ≥85%
- Each component should have dedicated tests

## Dependencies

- pytest
- pytest-cov
- httpx (for TestClient)
- tempfile (for temporary directories)
- ChromaDB (for real database tests)
- DVC (for version control tests)
