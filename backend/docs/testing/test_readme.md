# Expert Finder Testing Guide

This document provides detailed guidance on testing the Expert Finder application, including how to run tests, common issues, and solutions.

## Running Tests

### Basic Test Command

```bash
# From the backend directory:
python -m pytest tests/unit/ --cov=. --cov-config=../.coveragerc --cov-report=term-missing
```

### Activating the Environment

```bash
# If using micromamba:
eval "$(micromamba shell hook -s zsh)" && micromamba activate py311

# Then run tests:
python -m pytest tests/unit/ --cov=. --cov-config=../.coveragerc --cov-report=term-missing
```

### Running Specific Test Files or Classes

```bash
# Run a specific test file:
python -m pytest tests/unit/test_expert_finder_linkedin.py

# Run a specific test class:
python -m pytest tests/unit/test_linkedin_process_profiles.py::TestLinkedInProfileProcessing

# Run a specific test method:
python -m pytest tests/unit/test_expert_finder_linkedin.py::TestExpertFinderAgent::test_parse_query
```

## Code Formatting Requirements

The CI pipeline enforces strict code formatting rules. Always run these tools before pushing:

### Install Formatting Tools

```bash
pip install black==24.3.0 isort==5.13.2
```

### Automatic Code Formatting

```bash
# Format code with Black:
black --line-length 120 .

# Sort imports with isort:
isort --profile black --line-length 120 .
```

### Checking Formatting Without Making Changes

```bash
# Check code formatting without changing files:
black --check --line-length 120 .

# Check import sorting without changing files:
isort --check-only --profile black --line-length 120 .
```

## Common Testing Issues and Solutions

### 1. Dependency Conflicts

**Issue**: Dependency resolution errors with fastapi and chromadb:

```
The conflict is caused by:
    The user requested fastapi==0.103.1
    chromadb 1.0.8 depends on fastapi==0.115.9
```

**Solution**: Update requirements-test.txt to use the compatible version:

```bash
# Edit requirements-test.txt to use:
fastapi==0.115.9  # Instead of fastapi==0.103.1
```

### 2. Code Formatting Errors

**Issue**: CI pipeline fails with code formatting errors:

```
would reformat /home/runner/work/E115_ExpertFinder/E115_ExpertFinder/backend/utils/dvc_utils.py
Error: Process completed with exit code 1.
```

**Solution**: Run Black to format your code before pushing:

```bash
black --line-length 120 .
```

### 3. Import Sorting Errors

**Issue**: CI pipeline fails with import sorting errors:

```
ERROR: backend/main.py Imports are incorrectly sorted and/or formatted.
```

**Solution**: Run isort to fix import ordering:

```bash
isort --profile black --line-length 120 .
```

### 4. Missing Package Configuration

**Issue**: CI pipeline fails with package installation error:

```
ERROR: file:///home/runner/work/E115_ExpertFinder/E115_ExpertFinder/backend does not appear to be a Python project: neither 'setup.py' nor 'pyproject.toml' found.
```

**Solution**: Ensure there's a setup.py file in the backend directory:

```python
# backend/setup.py
from setuptools import setup, find_packages

setup(
    name="expert-finder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Dependencies are already in requirements-test.txt
    ],
    python_requires=">=3.11",
    description="Expert Finder backend for searching and discovering experts",
    author="Expert Finder Team",
)
```

This file allows pip to install the backend code as a package with `pip install -e .` command.

### 5. Module Import Errors

**Issue**: Import errors due to incorrect module structure:

```
AttributeError: module 'agent' has no attribute 'scholar_agent'
```

**Solution**: Ensure Python modules have proper `__init__.py` files:

```bash
# Create an __init__.py file in the agent directory:
touch agent/__init__.py

# If the error persists, check for correct import paths in your code
```

### 6. Mock Function Issues

**Issue**: Tests fail with unexpected mock function calls or arguments.

**Solution**: Check the implementation of the mocked function and ensure your test is correctly patching it:

```python
# Example of proper patching:
@patch('linkedin_data_processing.process_linkedin_profiles.initialize_gcp_client')
def test_function(self, mock_init_gcp):
    # Configure the mock:
    mock_init_gcp.return_value = mock_gcp_client
    
    # Call the function being tested
    result = process_profiles_and_upload_to_gcp("/tmp/test_profiles")
    
    # Assert the mock was called correctly
    mock_init_gcp.assert_called_once()
```

### 7. Test Coverage Issues

**Issue**: Test coverage is below the required threshold.

**Solution**: Analyze the coverage report to identify uncovered lines and add tests:

```bash
# Generate detailed HTML coverage report:
python -m pytest tests/unit/ --cov=. --cov-config=../.coveragerc --cov-report=html:reports/coverage-report

# Then open reports/coverage-report/index.html in a browser to see detailed line-by-line coverage
```

## Tips for Effective Testing

1. **Follow the AAA Pattern**: Arrange, Act, Assert
   - Arrange: Set up test data and mocks
   - Act: Call the function being tested
   - Assert: Verify the expected behavior

2. **Test Edge Cases**: Don't just test happy paths
   - Test with empty or invalid inputs
   - Test error handling
   - Test boundary conditions

3. **Use Realistic Test Data**: Create fixtures that resemble real data
   - The project includes sample data in tests/fixtures/test_data/

4. **Mock External Dependencies**: Avoid actual API calls or database operations
   - Use the @patch decorator to mock external functions
   - Configure mock return values to test different scenarios

5. **Keep Tests Independent**: Each test should be able to run on its own
   - Don't create dependencies between tests
   - Reset mocks and fixtures between tests

## Troubleshooting GitHub Actions CI Failures

When the GitHub Actions CI pipeline fails, follow these steps to troubleshoot:

1. **Check the workflow logs**: Click on the failing workflow to see detailed logs

2. **Identify the failing step**: Look for red ❌ icons to find the exact step that failed

3. **Read the error message**: Most failures will have clear error messages, such as:
   - "would reformat [file]" for Black formatting issues
   - "ERROR: [file] Imports are incorrectly sorted" for isort issues
   - "Coverage is below 60%" for coverage issues

4. **Reproduce locally**: Run the same command locally to see if you can reproduce the error:
   ```bash
   # For Black formatting errors:
   black --check --line-length 120 .
   
   # For isort errors:
   isort --check-only --profile black --line-length 120 .
   
   # For test failures:
   python -m pytest tests/unit/ --cov=. --cov-config=../.coveragerc --cov-report=term-missing
   ```

5. **Fix the issue**: Apply the appropriate fix based on the error type:
   - For formatting issues: Run the formatter tools
   - For test failures: Debug and fix the failing test
   - For coverage issues: Add more tests to increase coverage

6. **Commit and push**: Make a new commit with your fixes and push to trigger the CI pipeline again 