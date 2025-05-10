# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the ExpertFinder project.

## Overview

We have the following workflows:

1. **ci.yml** - Code quality checks (black, flake8, import checks)
2. **unit-tests.yml** - Unit tests with mocking and pytest
3. **integration-tests.yml** - Integration tests requiring Docker/DB (future)
4. **system-tests.yml** - End-to-end user flow tests (future)

## Workflow Details

### ci.yml

This workflow focuses on code quality and style:

- Runs on PRs to main and develop branches and direct pushes
- Performs code formatting checks with black
- Runs flake8 for code style and quality
- Checks import statements for proper organization
- Fails if any code quality checks fail

### unit-tests.yml

This workflow handles unit testing:

- Runs on PRs to main and develop branches and direct pushes
- Uses micromamba to set up the Python environment
- Runs all unit tests with code coverage
- Uses mocking for external dependencies
- Fails if coverage is below 60% (aiming for 70% eventually)
- Generates a coverage badge

### integration-tests.yml (Future)

This workflow will handle integration testing:

- Will run tests requiring Docker containers
- Will include database integration tests
- Will be set up when needed for more complex testing scenarios

### system-tests.yml (Future)

This workflow will handle end-to-end testing:

- Will test complete user flows
- Will verify system behavior in production-like environment
- Will be implemented when the system is more mature

## Dependency Management

For consistent dependency management across development and CI environments, we use:

- **requirements-test.txt** - Contains all testing dependencies with pinned versions
- Python 3.11 environment with micromamba
- All dependencies are explicitly specified with exact versions for reproducibility

If you need to add or update dependencies:

1. Update the `backend/requirements-test.txt` file
2. Run `pip freeze > all_dependencies.txt` locally to capture all transitive dependencies
3. Review the differences and update the requirements file as needed

## Coverage Requirements

- We're aiming for 70% code coverage for the project
- Current focus areas for improving coverage:
  - `expert_finder_linkedin.py` (currently at ~59%)
  - `process_linkedin_profiles.py` (currently at ~63%)

## Setup for Coverage Badges

To set up the coverage badges:

1. Create a new GitHub Gist at https://gist.github.com/
2. Update the `gistID` in the workflows with your Gist ID
3. Create a GitHub Personal Access Token with `gist` scope
4. Add this token as a repository secret called `GIST_SECRET`

## Running Tests Locally

To run the same tests locally:

```bash
# Activate your environment
micromamba activate py311

# Install test dependencies
pip install -r backend/requirements-test.txt

# Run unit tests with coverage
python -m pytest tests/unit/ --cov=backend --cov-report=term-missing --ignore=backend/linkedin_raw_data/test_get_profles.py --ignore=llm-finetuning/dataset-creator/test_model.py
```

## Troubleshooting

Common issues:

- Missing dependencies: Make sure to install all required packages
- Path issues: Set PYTHONPATH to include the backend directory
- Integration test failures: Some tests may require GCP credentials or special setup
- Package conflicts: If you encounter dependency conflicts, try creating a fresh environment 