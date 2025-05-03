#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Debug information
echo "docker-shell.sh started"
echo "Arguments: $@"
echo "First argument: $1"

# Set variables
export BASE_DIR=$(pwd)
export PERSISTENT_DIR=$(pwd)/../../chromadb/
export SECRETS_DIR=$(pwd)/../../secrets
export DATA_DIR=$(pwd)/../google-scholar-data/
export GCP_PROJECT="expertfinder-452203" # CHANGE TO YOUR PROJECT ID
export GOOGLE_APPLICATION_CREDENTIALS=$SECRETS_DIR/"expertfinder.json"
export IMAGE_NAME="expert-finder-backend"

# Load environment variables from .env file if it exists
if [ -f "$SECRETS_DIR/.env" ]; then
    # Read each line from .env file
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments and empty lines
        [[ $line =~ ^#.*$ ]] && continue
        [[ -z $line ]] && continue
        
        # Export valid environment variables
        if [[ $line =~ ^[A-Za-z_][A-Za-z0-9_]*=.*$ ]]; then
            export "$line"
        fi
    done < "$SECRETS_DIR/.env"
else
    echo "Warning: .env file not found at $SECRETS_DIR/.env"
fi

# Create the network if we don't have it yet
docker network inspect expert-finder-network >/dev/null 2>&1 || docker network create expert-finder-network

# Build the image based on the Dockerfile
docker build -t $IMAGE_NAME -f Dockerfile .

# Function to run tests
run_tests() {
    echo "run_tests function called"
    echo "Running tests..."
    echo "Current directory: $(pwd)"
    echo "Base directory: $BASE_DIR"
    echo "Running pytest with arguments: $@"
    
    # Run the container with pytest directly, overriding the ENTRYPOINT
    docker run --rm --name $IMAGE_NAME-test \
        --entrypoint="" \
        -v "$BASE_DIR":/app \
        -v "$SECRETS_DIR":/secrets \
        -v "$PERSISTENT_DIR":/persistent \
        -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
        -e GCP_PROJECT=$GCP_PROJECT \
        $IMAGE_NAME \
        bash -c "cd /app && python -m pytest $@"
    
    # Check the exit code
    if [ $? -ne 0 ]; then
        echo "Tests failed with exit code $?"
    else
        echo "Tests completed successfully"
    fi
}

# Function to run formatting and linting
run_format_and_lint() {
    echo "run_format_and_lint function called"
    echo "Running formatting and linting..."
    echo "Current directory: $(pwd)"
    echo "Base directory: $BASE_DIR"
    
    # Run the container with format_and_lint.sh, overriding the ENTRYPOINT
    docker run --rm --name $IMAGE_NAME-format \
        --entrypoint="" \
        -v "$BASE_DIR":/app \
        -v "$SECRETS_DIR":/secrets \
        -v "$PERSISTENT_DIR":/persistent \
        -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
        -e GCP_PROJECT=$GCP_PROJECT \
        $IMAGE_NAME \
        bash -c "cd /app && chmod +x format_and_lint.sh && ./format_and_lint.sh"
    
    # Check the exit code
    if [ $? -ne 0 ]; then
        echo "Formatting and linting failed with exit code $?"
    else
        echo "Formatting and linting completed successfully"
    fi
}

# Check if the first argument is "test"
echo "Checking if first argument is 'test': $1"
if [ "$1" == "test" ]; then
    echo "First argument is 'test', running tests"
    # Shift the first argument and pass the rest to pytest
    shift
    run_tests $@
# Check if the first argument is "format"
elif [ "$1" == "format" ]; then
    echo "First argument is 'format', running formatting and linting"
    run_format_and_lint
else
    echo "First argument is not 'test' or 'format', running containers"
    # Run All Containers
    docker compose run --rm --service-ports $IMAGE_NAME
fi

# Run Container
# docker run --rm --name $IMAGE_NAME -ti \
#     -v "$BASE_DIR":/app \
#     -v "$SECRETS_DIR":/secrets \
#     -v "$PERSISTENT_DIR":/persistent \
#     -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
#     -e GCP_PROJECT=$GCP_PROJECT \
#     $IMAGE_NAME


#