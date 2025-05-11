# Expert Finder Testing Documentation

## Overview

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

## Test Directory Structure

```
backend/
├── tests/
│   ├── unit/               # Unit tests for individual components
│   │   └── utils/          # Tests for utility modules
│   ├── integration/        # Tests for component interactions
│   │   ├── api/            # API integration tests
│   │   └── data/           # Data processing integration tests
│   ├── system/             # Future end-to-end system tests
│   ├── fixtures/           # Test data and helper functions
│   │   └── test_data/      # Test data files
│   │       ├── linkedinProfiles_beforeProcessing/ # LinkedIn test data
│   │       └── expert-finder-bucket-1/            # Test bucket data
│   │           └── google_scholar/                # Google Scholar test data
│   ├── conftest.py         # Shared pytest fixtures
│   ├── api_test_client.py  # API testing utilities
│   ├── run_integration_tests.sh # Script to run integration tests
│   ├── start_test_environment.sh # Script to set up test environment
│   └── test_config.py      # Test configuration
```


## Running Tests

### Basic Test Commands

```bash
# Run unit tests with coverage reporting
python -m pytest tests/unit/ --cov=. --cov-config=../.coveragerc --cov-report=term-missing

# Run integration tests
python -m pytest tests/integration/ -m integration -v

# Run system tests
python -m pytest tests/system/ -m system -v
```

### Environment Variables

When running tests, set these environment variables:

```bash
export GCP_PROJECT=dummy
export EF_TEST_MODE=1
export PYTHONPATH=.
```

### Running Specific Tests

```bash
# Run a specific test file
python -m pytest tests/unit/test_expert_finder_linkedin.py

# Run a specific test class
python -m pytest tests/unit/test_linkedin_process_profiles.py::TestLinkedInProfileProcessing

# Run a specific test method
python -m pytest tests/unit/test_expert_finder_linkedin.py::TestExpertFinderAgent::test_parse_query
```

## Current Test Coverage

Based on the latest test run, the current coverage is approximately 64% across all modules:

![Unit Test Coverage](https://raw.githubusercontent.com/SantiagoBecerraC/E115_ExpertFinder/test-new/images/unitTestCoverage.png)

| Module | Stmts | Miss | Cover | Missing |
|--------|-------|------|-------|---------|
| Overall | 2398 | 859 | 64% | - |
| agent/scholar_agent.py | 398 | 141 | 65% | 133-136, 161-164, 277-292, 365-405, 426-428, 517-518, 533-579, 583-697, 707 |
| google_scholar/scholar_data_processor.py | 115 | 74 | 36% | 18-20, 30-114, 130, 147-188, 225-281 |
| linkedin_data_processing/cli.py | 142 | 14 | 90% | 43, 73, 75, 77, 79, 81, 130-131, 173, 246, 248, 250, 252, 254 |
| linkedin_data_processing/credibility_stats.py | 107 | 5 | 95% | 119, 126, 189, 194, 232 |
| linkedin_data_processing/credibility_system.py | 76 | 1 | 99% | 59 |
| linkedin_data_processing/dynamic_credibility.py | 56 | 16 | 71% | 40, 63-65, 68-70, 123-135, 154 |
| linkedin_data_processing/expert_finder_linkedin.py | 333 | 116 | 65% | 10-12, 61-63, 71-72, 81-83, 86-94, 103-105, 114-119, 125, 306, 310-316, 343, 347, 379-381, 396-398, 417-418, 455-458, 479, 509, 527-528, 576, 595, 636, 652-691, 698-750 |
| linkedin_data_processing/linkedin_vectorizer.py | 218 | 61 | 72% | 103-109, 113-119, 139-141, 179-183, 192-201, 225-226, 241, 264-265, 289-290, 294-299, 324-328, 342, 410-412, 423-438 |
| linkedin_data_processing/process_linkedin_profiles.py | 458 | 215 | 53% | 16-18, 65-67, 103-104, 108-110, 128-130, 153-436, 462, 493-494, 571-572, 577-579, 600-604, 632-633, 656-658, 672, 703-704, 711-713, 720, 743, 748, 752, 778-784, 788-794, 818-823, 854-856, 895-907, 922-947 |
| main.py | 218 | 133 | 39% | 13, 24, 27, 73, 87-89, 94-96, 128, 146, 156-284, 289-330, 336-356, 365-382, 390-397, 405-416, 427-436 |
| utils/chroma_db_utils.py | 152 | 40 | 74% | 86, 137-138, 176-178, 186-188, 202, 204, 206, 211-212, 219, 236-237, 246-256, 260-265, 305-318 |
| utils/dvc_utils.py | 85 | 3 | 96% | 50, 131, 134 |

Four tests are currently skipped with pytest.mark.skip:
- TestLinkedInProfileExtraction.test_extract_profile_data
- TestLinkedInProfileExtraction.test_create_profile_text
- TestLinkedInProfileExtraction.test_extract_profile_fields
- TestProfileText.test_create_profile_text_complete


## Unit Tests

The project includes comprehensive unit tests for individual components. Here's a breakdown of the major components being tested:

### LinkedIn Data Processing

Tests for processing raw LinkedIn profiles to structured data:

- **extract_profile_data**: Tests the extraction of relevant data from raw LinkedIn profiles
- **create_profile_text**: Tests the creation of text representations of profiles for embedding
- **process_profiles_and_upload_to_gcp**: Tests the profile processing pipeline
- **get_credibility_distribution**: Tests credibility statistics calculation

### Google Scholar Processing

Tests for processing Google Scholar data:

- **process_scholar_data**: Tests extracting relevant data from Google Scholar API responses
- **prepare_chroma_data**: Tests preparing data for ChromaDB storage
- **search_profiles_demo**: Tests the semantic search functionality

### Credibility System

Tests for the expert credibility scoring system:

- **dynamic_credibility**: Tests the on-demand credibility calculation
- **credibility_stats**: Tests the statistical calculations for credibility scores
- **credibility_system**: Tests the overall credibility evaluation system

### ChromaDB and DVC Utilities

- **setup_chroma_db**: Tests ChromaDB initialization and collection management
- **get_profiles_in_chroma**: Tests retrieving profiles from ChromaDB
- **initialize_dvc**: Tests DVC repository initialization
- **version_database**: Tests creating versioned snapshots of the database

## Integration Tests

The integration tests verify that components work together correctly:

### Directory Structure

The integration tests are organized in the following directories:

```
backend/tests/integration/
├── data/                       # Tests for data processing components
│   ├── test_chromadb_integration.py
│   ├── test_linkedin_integration.py
│   ├── test_process_linkedin_profiles_integration.py
│   └── test_scholar_integration.py
└── api/                        # Tests for API functionality
    └── test_api_integration.py
```

### Integration Test Coverage

Based on our test runs, the integration tests provide the following coverage:


![Integration Test Coverage](https://raw.githubusercontent.com/SantiagoBecerraC/E115_ExpertFinder/test-new/images/IntegrationTestCoverage.jpg)

Several key integration tests were implemented to verify component interactions:

1. **ChromaDB Integration**: Tests batch operations, updates, and basic CRUD functionality
2. **LinkedIn Processing**: Tests profile extraction, vectorization, credibility scoring
3. **API Integration**: Tests search endpoints and versioning

### Running Integration Tests

Integration tests can be run with the pytest mark parameter:

```bash
# Run all integration tests
python -m pytest tests/integration/ -m integration -v

# Run a specific integration test file
python -m pytest tests/integration/data/test_chromadb_integration.py -v

# Run a specific test
python -m pytest tests/integration/data/test_linkedin_integration.py::test_linkedin_profile_processing -v
```

The integration tests use test fixtures defined in `tests/fixtures/conftest.py` to set up test environments and provide test data.

## System Tests

**Note: System tests are planned for future implementation**

The system tests will verify end-to-end functionality when implemented. Due to time constraints, system-level testing has been deferred to a future development phase. The current focus is on reaching the 70% test coverage target through unit and integration tests.

When implemented, system tests will cover:

### Search Workflow Tests

Tests the complete search process:

1. **Query Processing**: Processes search queries from users
2. **Semantic Search**: Performs semantic search across multiple data sources
3. **Relevance Scoring**: Ranks results by relevance and credibility
4. **Response Generation**: Creates natural language responses with expert recommendations

### Database Management Tests

Tests database versioning and management:

1. **Version Creation**: Creates database versions with DVC
2. **Version Restoration**: Restores database to previous versions
3. **Incremental Updates**: Tests adding new data to existing database

## Known Issues and Future Improvements

### Current Issues

1. **ChromaDB Initialization**: Tests involving ChromaDB initialization sometimes fail due to version compatibility issues
2. **Google Cloud**: Some tests depend on GCP services and require mocking
3. **Coverage Gaps**: Coverage for process_linkedin_profiles.py and main.py needs improvement

### Future Improvements

1. **Increase API Testing**: Add more tests for API endpoints
2. **Improve Error Handling Coverage**: Add tests for error conditions and recovery
3. **Performance Testing**: Add tests for performance under load
4. **Reduce External Dependencies**: Improve isolation for tests using external services

## Testing Tools

- **PyTest**: Main testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking library
- **pytest-asyncio**: For testing async code

## Code Formatting Requirements

The CI pipeline enforces strict code formatting. Always run these before pushing:

```bash
# Format code with Black:
black --line-length 120 .

# Sort imports with isort:
isort --profile black --line-length 120 .
``` 