# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the ExpertFinder project.

## Overview

We have the following workflows:

1. **pytest.yml** - Runs unit tests with coverage reporting
2. **ci.yml** - Full CI pipeline with linting, unit tests, and integration tests

## Workflow Details

### pytest.yml

This workflow focuses on running unit tests and generating coverage reports. It:

- Runs on PRs to main and develop branches and direct pushes
- Uses micromamba to set up the Python environment
- Runs all unit tests with code coverage
- Fails if coverage is below 60% (aiming for 70% eventually)
- Generates a coverage badge

### ci.yml

This is a more comprehensive workflow that:

- Runs code formatting and linting checks
- Runs all unit tests with coverage reporting
- Runs integration tests that don't require complicated fixtures
- Combines coverage reports into a single report
- Updates README with coverage badge

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