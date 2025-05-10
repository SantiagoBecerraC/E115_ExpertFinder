# Expert Finder Testing Plan

## Run Comprehensive Tests

```bash
# Run this command from the backend directory to get comprehensive coverage metrics:
export GCP_PROJECT=dummy
export EF_TEST_MODE=1
export PYTHONPATH=.
pytest --cov=. --cov-report=term-missing
```

```
# unit test:
GCP_PROJECT=dummy EF_TEST_MODE=1 PYTHONPATH=. pytest tests/integration/ -m integration -v
# system test
GCP_PROJECT=dummy EF_TEST_MODE=1 PYTHONPATH=. pytest tests/system/ -m system -v
```

## Overview

This document outlines the current testing status and future test development plan for the Expert Finder project. The testing strategy is organized into three levels:

1. **Unit Tests**: Testing individual components in isolation with mocking
2. **Integration Tests**: Testing how components work together
3. **System Tests**: Testing complete workflows from end to end

## Current Test Coverage

Comprehensive test run on May 9, 2025 shows the following coverage metrics:

| Module | Coverage | Status | Priority |
|---|---|---|---|
| DVC Utils | 96% | ✅ Excellent | Low |
| CLI Commands | 90% | ✅ Excellent | Low |
| ChromaDB Utils | 78% | ✅ Good | Low |
| Scholar Data Vectorization | 76% | ✅ Good | Low |
| LinkedIn Vectorizer | 72% | ✅ Good | Low |
| Dynamic Credibility | 71% | ✅ Good | Low |
| Credibility System | 54% | ⚠️ Moderate | Medium |
| Scholar Data Processor | 45% | ⚠️ Needs improvement | Medium |
| Process LinkedIn Profiles | 43% | ⚠️ Needs improvement | High |
| ExpertFinderAgent | 33% | ⚠️ Needs improvement | High |
| Credibility Stats | 25% | ❌ Poor | High |
| Main API Endpoints | 0% | ❌ Missing | Critical |

**Overall Coverage**: 48% (Target: 70%)

## Known Test Issues

### ChromaDB Initialization Errors

Several tests fail with `RuntimeError: Failed to initialize ChromaDB: '_type'` error. Investigation shows this is likely due to ChromaDB API version compatibility issues:

1. **Root Cause**: In ChromaDB v0.6.3, `client.list_collections()` returns `CollectionName` objects (not plain strings)

```python
# Current code (works in production but fails in tests):
collection_names = self.client.list_collections()
if self.collection_name in collection_names:  # Type mismatch here
```

2. **Potential Solutions**:
   - Extract string names: `collection_names = [str(c) for c in client.list_collections()]`
   - Skip the failing tests in CI with `@pytest.mark.skip` until fixed
   - Pin ChromaDB version in requirements to a compatible version

3. **Impact**: This affects 10 tests across ChromaDB-related functionality

Do not fix this issue until confirming which approach preserves production behavior!

## Unit Testing Tasks

### High Priority
1. **Main API Endpoints Tests**
   - Test all API endpoints with mock backends
   - Test input validation and error handling
   - Test response structure and pagination
   - Test authentication and authorization flows

2. **Credibility Stats Tests**
   - Test statistics calculation and aggregation
   - Test stats file management
   - Test data validation and normalization
   - Test stats update workflows

3. **ExpertFinderAgent Tests**
   - Test reranking functionality with Vertex AI (mocked)
   - Test credential management
   - Test error handling for API rate limits and network failures
   - Test fallback strategies when Vertex AI is unavailable

4. **Process LinkedIn Profiles Tests**
   - Test profile parsing and extraction
   - Test field normalization
   - Test the experience scoring algorithm
   - Test education level classification
   - Test the handling of incomplete profiles

### Medium Priority
1. **Dynamic Credibility Tests**
   - Test credibility score calculation
   - Test statistics generation
   - Test the OnDemandCredibilityCalculator class
   - Test educational institution recognition
   - Test company recognition and categorization

2. **Improve ChromaDB Utils Tests**
   - Test collection management features
   - Test metadata filtering functionality
   - Test handling of large document batches
   - Test persistence and cross-session availability

### Low Priority
1. **Schema Validation Tests**
   - Test validation of input data formats
   - Test handling of malformed data
   - Test normalization of inconsistent field names

## Integration Testing Tasks

### High Priority
1. **LinkedIn Processing Pipeline**
   - Test the end-to-end flow from raw profiles to vectorized data
   - Test with a realistic dataset (10-20 profiles)
   - Test incremental processing (new profiles only)
   - Verify ChromaDB integration with real in-memory instance
   
2. **API Endpoint Tests**
   - Test all search endpoints with real data
   - Test versioning workflows with DVC
   - Test error handling and rate limiting
   - Test authentication mechanisms

### Medium Priority
1. **Combined Data Source Tests**
   - Test searching across both LinkedIn and Google Scholar data
   - Test merging of results from multiple sources
   - Test relevance scoring with mixed data types

2. **Credibility System Integration**
   - Test credibility score impact on search ranking
   - Test updates to credibility metrics
   - Test performance with large numbers of profiles

## System Testing Tasks

### High Priority
1. **End-to-End Search Workflows**
   - Test complete search process from query to ranked results
   - Test with various query types (specific skills, general areas, experience levels)
   - Test performance with large result sets

2. **Database Versioning and Rollback**
   - Test creating versions with meaningful metadata
   - Test rolling back to previous versions
   - Test behavior when restoring missing data

### Medium Priority
1. **Performance Tests**
   - Test search latency with various database sizes
   - Test processing pipeline throughput
   - Test concurrent API usage

2. **Error Recovery**
   - Test system behavior during network failures
   - Test recovery from interrupted operations
   - Test data consistency after failures

## Implementation Approach

### Phase 1: Complete Unit Tests (2 weeks)
- Focus on LinkedIn modules with 0% coverage
- Improve ExpertFinderAgent coverage to at least 70%
- Create test fixtures with realistic test data

### Phase 2: Integration Tests (1 week)
- Implement tests for LinkedIn processing pipeline
- Create API endpoint tests with mocked backends
- Set up system for integration test isolation

### Phase 3: System Tests (1 week)
- Create end-to-end workflow tests
- Implement performance benchmarks
- Test error recovery scenarios

## Testing Guidelines

### Unit Testing Best Practices
- **Isolate External Dependencies**: Use strategic mocking for all external APIs, databases, and file systems
- **Test Edge Cases**: Include tests for error conditions, empty results, and boundary values
- **Use Realistic Test Data**: Base test fixtures on actual production data formats
- **Verify Behavior, Not Implementation**: Focus on testing the contract/interface of components

### Integration Testing Approach
- Use in-memory databases where possible
- Create temporary, isolated environments for each test
- Implement cleanup to ensure tests don't affect each other
- Use environment variables to control real vs. mocked services
