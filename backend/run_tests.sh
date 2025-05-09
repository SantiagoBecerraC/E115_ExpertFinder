#!/bin/bash

# Parse command line arguments
TYPE="all"
COVERAGE=false
VERBOSE=false

for arg in "$@"
do
    case $arg in
        --unit)
        TYPE="unit"
        shift
        ;;
        --integration)
        TYPE="integration"
        shift
        ;;
        --system)
        TYPE="system"
        shift
        ;;
        --dvc)
        TYPE="dvc"
        shift
        ;;
        --coverage)
        COVERAGE=true
        shift
        ;;
        --verbose|-v)
        VERBOSE=true
        shift
        ;;
        *)
        # Unknown option
        shift
        ;;
    esac
done

# Base command
CMD="pipenv run python -m pytest"

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    CMD="$CMD --cov=. --cov-report=term-missing --cov-report=html:docs/coverage/html_report"
fi

# Add verbose flag if requested
if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
fi

# Run specific test type
case $TYPE in
    unit)
    echo "Running unit tests..."
    $CMD -m unit
    ;;
    integration)
    echo "Running integration tests..."
    $CMD -m integration
    ;;
    system)
    echo "Running system tests..."
    $CMD -m system
    ;;
    dvc)
    echo "Running DVC tests..."
    $CMD -m dvc
    ;;
    all)
    echo "Running all tests..."
    $CMD
    ;;
esac

# If coverage was generated, show the report location
if [ "$COVERAGE" = true ]; then
    echo "Coverage report generated in docs/coverage/html_report/index.html"
fi
