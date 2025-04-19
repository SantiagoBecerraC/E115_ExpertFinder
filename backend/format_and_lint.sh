#!/bin/bash

# Exit on error
set -e

# Function to print section headers
print_header() {
    echo "==================================================="
    echo "$1"
    echo "==================================================="
}

# Function to run formatting and linting on a directory
format_and_lint() {
    local dir=$1
    local name=$2
    
    print_header "Processing $name code in $dir"
    
    # Change to the directory
    cd "$dir"
    
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
    
    # Return to the original directory
    cd - > /dev/null
    
    echo "$name formatting and linting complete!"
}

# Main script
print_header "Starting formatting and linting process"

# Process Google Scholar code
format_and_lint "google_scholar" "Google Scholar"

# Process LinkedIn data processing code
format_and_lint "linkedin_data_processing" "LinkedIn Data Processing"

# Process utils code
format_and_lint "utils" "Utils"

# Process agent code
format_and_lint "agent" "Agent"

print_header "All formatting and linting complete!" 