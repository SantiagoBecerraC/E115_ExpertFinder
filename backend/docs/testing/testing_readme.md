# Expert Finder Testing Plan & Progress

## Run Comprehensive Tests

```bash
# Run this command from the backend directory to get comprehensive coverage metrics:
EF_TEST_MODE=1 pytest --cov=. --cov-report=term-missing
```

## Overview

This document tracks the current testing status and future test development plan for the Expert Finder project. The testing strategy is organized into three levels:

1. **Unit Tests**: Testing individual components in isolation (with mocking)
2. **Integration Tests**: Testing how components work together
3. **System Tests**: Testing complete workflows from end to end

---

## Current Test Coverage

_Comprehensive test run on May 9, 2025:_

| Module                   | Coverage | Status            | Priority   |
|--------------------------|----------|-------------------|------------|
| Overall                  | 48%      | ⚠️ Needs improvement | -          |
| DVC Utils                | 96%      | ✅ Excellent       | Low        |
| CLI Commands             | 90%      | ✅ Excellent       | Low        |
| ChromaDB Utils           | 80%      | ✅ Good            | Low        |
| Scholar Data Vectorization| 77%     | ✅ Good            | Low        |
| LinkedIn Vectorizer      | 72%      | ✅ Good            | Low        |
| Dynamic Credibility      | 71%      | ✅ Good            | Low        |
| Credibility System       | 54%      | ⚠️ Moderate        | Medium     |
| Process LinkedIn Profiles| 43%      | ⚠️ Needs improvement | High     |
| Scholar Data Processor   | 45%      | ⚠️ Needs improvement | Medium   |
| Credibility Stats        | 25%      | ⚠️ Poor            | High       |
| ExpertFinderAgent        | 33%      | ⚠️ Needs improvement | High     |
| Main API Endpoints       | 0%       | ❌ Missing         | Critical   |
| Test ChromaDB            | 10%      | ❌ Poor            | Low        |

---

## Unit Testing Tasks

### High Priority
- **Main API Endpoints**
  - Test all API endpoints with mock backends
  - Test input validation and error handling
  - Test response structure and pagination
  - Test authentication and authorization flows

- **Credibility Stats**
  - Test statistics calculation and aggregation
  - Test stats file management
  - Test data validation and normalization
  - Test stats update workflows

- **ExpertFinderAgent**
  - Test reranking functionality with Vertex AI (mocked)
  - Test credential management
  - Test error handling for API rate limits and network failures
  - Test fallback strategies when Vertex AI is unavailable

- **Process LinkedIn Profiles**
  - Test profile parsing and extraction
  - Test field normalization
  - Test the experience scoring algorithm
  - Test education level classification
  - Test the handling of incomplete profiles

### Medium Priority
- **Dynamic Credibility**
  - Test credibility score calculation
  - Test statistics generation
  - Test the OnDemandCredibilityCalculator class
  - Test educational institution recognition
  - Test company recognition and categorization

- **ChromaDB Utils**
  - Test collection management features
  - Test metadata filtering functionality
  - Test handling of large document batches
  - Test persistence and cross-session availability

### Low Priority
- **Schema Validation**
  - Test validation of input data formats
  - Test handling of malformed data
  - Test normalization of inconsistent field names

---

## Integration Testing Tasks

### High Priority
- **LinkedIn Processing Pipeline**
  - Test the end-to-end flow from raw profiles to vectorized data
  - Test with a realistic dataset (10-20 profiles)
  - Test incremental processing (new profiles only)
  - Verify ChromaDB integration with real in-memory instance

- **API Endpoint Tests**
  - Test all search endpoints with real data
  - Test versioning workflows with DVC
  - Test error handling and rate limiting
  - Test authentication mechanisms

### Medium Priority
- **Combined Data Source**
  - Test searching across both LinkedIn and Google Scholar data
  - Test merging of results from multiple sources
  - Test relevance scoring with mixed data types

- **Credibility System Integration**
  - Test credibility score impact on search ranking
  - Test updates to credibility metrics
  - Test performance with large numbers of profiles

---

## System Testing Tasks

### High Priority
- **End-to-End Search Workflows**
  - Test complete search process from query to ranked results
  - Test with various query types (specific skills, general areas, experience levels)
  - Test performance with large result sets

- **Database Versioning and Rollback**
  - Test creating versions with meaningful metadata
  - Test rolling back to previous versions
  - Test behavior when restoring missing data

### Medium Priority
- **Performance Tests**
  - Test search latency with various database sizes
  - Test processing pipeline throughput
  - Test concurrent API usage

- **Error Recovery**
  - Test system behavior during network failures
  - Test recovery from interrupted operations
  - Test data consistency after failures

---

## Implementation Approach

- **Phase 1: Complete Unit Tests (2 weeks)**
  - Focus on LinkedIn modules with 0% coverage
  - Improve ExpertFinderAgent coverage to at least 70%
  - Create test fixtures with realistic test data

- **Phase 2: Integration Tests (1 week)**
  - Implement tests for LinkedIn processing pipeline
  - Create API endpoint tests with mocked backends
  - Set up system for integration test isolation

- **Phase 3: System Tests (1 week)**
  - Create end-to-end workflow tests
  - Implement performance benchmarks
  - Test error recovery scenarios

---

## Testing Guidelines

- **Isolate External Dependencies**: Use strategic mocking for all external APIs, databases, and file systems
- **Test Edge Cases**: Include tests for error conditions, empty results, and boundary values
- **Use Realistic Test Data**: Base test fixtures on actual production data formats
- **Verify Behavior, Not Implementation**: Focus on testing the contract/interface of components

---

## Directory Structure

```
backend/
├── tests/
│   ├── unit/        # Tests for individual components
│   ├── integration/ # Tests for component interactions
│   ├── system/      # End-to-end tests
│   ├── fixtures/    # Shared test data and mocks
│   └── conftest.py  # Shared pytest fixtures
```

---

## Mocking Strategy

- **External API Mocking**: Google Scholar API, ChromaDB, and other external services are mocked to return predefined responses.
- **File System Operations**: File reads/writes are mocked using `mock_open` or use temporary directories.
- **API Endpoint Testing**: `MockTestClient` replaces FastAPI's TestClient for unit tests, while integration tests use the real FastAPI TestClient.

---

## Running Tests

### Prerequisites

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock httpx pytest-asyncio
```

### Running Tests Manually

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
pytest
pytest tests/unit/test_dvc_utils.py
pytest --cov=. --cov-report=html
```

---

## CI/CD Integration

- Tests are automatically run on GitHub Actions:
  - On every push to main and develop branches
  - On every pull request to main and develop branches
- The CI pipeline includes:
  1. Linting with flake8
  2. Running all test levels
  3. Generating and uploading coverage reports

---

## API and Data Flow

- **Google Scholar Data Flow**: Download → Process → Vectorize → Store (see code for function relationships)
- **API Endpoint Architecture**: Client → FastAPI Endpoints → ChromaDB/DVC Integration

---

## Module-Specific Testing Approaches

- Each module (e.g., ChromaDB utils, DVC utils, LinkedIn processing, Google Scholar processing) has dedicated tests for:
  - Initialization and setup
  - Core functionality
  - Error handling and edge cases
  - Integration with other modules

---

## Next Steps

- Continue to expand integration and system tests
- Ensure coverage for all critical modules and workflows
- Keep this documentation up to date as the testing framework evolves