#!/bin/bash

# Exit on error
set -e

echo "Formatting and linting Google Scholar code..."

# Install required packages if not already installed
pip install black flake8 isort

# Format code with Black
echo "Formatting code with Black..."
black .

# Sort imports with isort
echo "Sorting imports with isort..."
isort .

# Lint code with Flake8
echo "Linting code with Flake8..."
flake8 .

echo "Formatting and linting complete!" 