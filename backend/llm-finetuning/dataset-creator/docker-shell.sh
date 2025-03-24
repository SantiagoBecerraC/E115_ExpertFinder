#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Read the settings file
source ../env.dev

export IMAGE_NAME="llm-dataset-creator"

# Stop and remove existing container if it exists
docker stop "$IMAGE_NAME" 2>/dev/null || true
docker rm "$IMAGE_NAME" 2>/dev/null || true

# Remove existing image if it exists
docker rmi "$IMAGE_NAME" 2>/dev/null || true

# Build the image based on the Dockerfile
docker build --no-cache -t "$IMAGE_NAME" -f Dockerfile .

# Run Container with appropriate entrypoint based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows-specific settings
    echo "Running on Windows..."
    
    # Get the absolute path to the secrets directory (three levels up from dataset-creator)
    SECRETS_DIR="$(dirname "$(dirname "$(dirname "$(pwd)")")")/secrets"
    BASE_DIR="$(pwd)"
    
    # Convert Windows paths to Unix format for Docker
    # For WSL2, use /mnt/c/... format
    BASE_DIR_WIN=$(echo "$BASE_DIR" | sed 's/\\/\//g' | sed 's/^\([A-Z]\):/\/mnt\/\1/')
    SECRETS_DIR_WIN=$(echo "$SECRETS_DIR" | sed 's/\\/\//g' | sed 's/^\([A-Z]\):/\/mnt\/\1/')
    
    # Ensure secrets directory exists (Windows host check)
    if [ ! -d "$SECRETS_DIR" ]; then
        echo "Error: Secrets directory not found at $SECRETS_DIR"
        echo "Please ensure the secrets directory exists and contains llm-service-account.json"
        echo "Expected location: $SECRETS_DIR"
        exit 1
    fi
    
    # Check if service account file exists (Windows host check)
    if [ ! -f "$SECRETS_DIR/llm-service-account.json" ]; then
        echo "Error: Service account file not found at $SECRETS_DIR/llm-service-account.json"
        echo "Please ensure the service account file exists in the secrets directory"
        echo "Expected location: $SECRETS_DIR/llm-service-account.json"
        exit 1
    fi
    
    echo "Mounting secrets from: $SECRETS_DIR_WIN"
    echo "Mounting base directory from: $BASE_DIR_WIN"
    
    # Run the container with proper paths and environment
    MSYS_NO_PATHCONV=1 docker run --rm --name "$IMAGE_NAME" -ti \
        -v "${BASE_DIR_WIN}:/app" \
        -v "${SECRETS_DIR_WIN}:/secrets" \
        -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/llm-service-account.json \
        -e GCP_PROJECT="$GCP_PROJECT" \
        -e GCS_BUCKET_NAME="$GCS_BUCKET_NAME" \
        -e PYTHONPATH=/app \
        "$IMAGE_NAME"
else
    # Linux/Unix settings
    echo "Running on Linux/Unix..."
    
    # Get the absolute path to the secrets directory (three levels up from dataset-creator)
    SECRETS_DIR="$(dirname "$(dirname "$(dirname "$(pwd)")")")/secrets"
    BASE_DIR="$(pwd)"
    
    echo "Mounting secrets from: $SECRETS_DIR"
    echo "Mounting base directory from: $BASE_DIR"
    
    # Run the container with proper paths and environment
    docker run --rm --name "$IMAGE_NAME" -ti \
        -v "${BASE_DIR}:/app" \
        -v "${SECRETS_DIR}:/secrets" \
        -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/llm-service-account.json \
        -e GCP_PROJECT="$GCP_PROJECT" \
        -e GCS_BUCKET_NAME="$GCS_BUCKET_NAME" \
        -e PYTHONPATH=/app \
        "$IMAGE_NAME"
fi
