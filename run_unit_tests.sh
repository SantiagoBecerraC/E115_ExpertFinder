#!/bin/bash

# Set required environment variables
export GCP_PROJECT=dummy
export EF_TEST_MODE=1
export PYTHONPATH=.

# Clear previous coverage data
python -m coverage erase

# Run only unit tests with coverage measurement
python -m pytest -m unit --cov=. --cov-report=term-missing --cov-report=html:reports/coverage-report -v

# Show coverage summary
echo -e "\n======== COVERAGE SUMMARY ========\n"
python -m coverage report -m 