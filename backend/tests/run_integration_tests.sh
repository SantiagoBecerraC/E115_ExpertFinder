#!/bin/bash
# run_integration_tests.sh - Script to run integration tests for the Expert Finder project

set -e  # Exit immediately if a command exits with a non-zero status

# Color configuration for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running integration tests (excluding DVC)...${NC}"

# Run the tests
# -v: verbose
# -m integration: only run tests marked with @pytest.mark.integration
# --cov=..: measure coverage for parent directory code
# --cov-report=term: print the coverage report to the terminal

# From tests directory, run integration tests in the integration subdirectory
pytest -v -m integration integration/ --cov=.. --cov-report=term

# Check the exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All integration tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Integration tests failed!${NC}"
    exit 1
fi