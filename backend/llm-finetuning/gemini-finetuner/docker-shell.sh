#!/bin/bash

# Exit immediately on error
set -e

# Source environment variables
source ../env.dev

# Set your Docker image name
export IMAGE_NAME="llm-gemini-finetuner"

# Stop and remove existing container if it exists
docker stop "$IMAGE_NAME" 2>/dev/null || true
docker rm "$IMAGE_NAME" 2>/dev/null || true

# Remove existing image if it exists
docker rmi "$IMAGE_NAME" 2>/dev/null || true

# Build the Docker image (no-cache optional)
docker build --no-cache -t "$IMAGE_NAME" -f Dockerfile .

# Run Container with appropriate paths based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows-specific settings
    echo "Running on Windows..."

    # Get the absolute path to the secrets directory (3 levels up)
    SECRETS_DIR="$(dirname "$(dirname "$(dirname "$(pwd)")")")/secrets"
    BASE_DIR="$(pwd)"

    # Convert Windows paths to /mnt/c/... format for Docker in WSL
    BASE_DIR_WIN=$(echo "$BASE_DIR" | sed 's/\\/\//g' | sed 's/^\([A-Z]\):/\/mnt\/\1/')
    SECRETS_DIR_WIN=$(echo "$SECRETS_DIR" | sed 's/\\/\//g' | sed 's/^\([A-Z]\):/\/mnt\/\1/')

    # Ensure secrets directory exists (Windows host check)
    if [ ! -d "$SECRETS_DIR" ]; then
        echo "Error: Secrets directory not found at $SECRETS_DIR"
        echo "Please ensure the secrets directory exists and contains llm-service-account.json"
        exit 1
    fi

    # Check if service account file exists (Windows host check)
    if [ ! -f "$SECRETS_DIR/llm-service-account.json" ]; then
        echo "Error: Service account file not found at $SECRETS_DIR/llm-service-account.json"
        exit 1
    fi

    echo "Mounting secrets from: $SECRETS_DIR_WIN"
    echo "Mounting base directory from: $BASE_DIR_WIN"

    # Disable Git Bash path rewriting and run the container
    MSYS_NO_PATHCONV=1 docker run --rm --name "$IMAGE_NAME" -ti \
        -v "${BASE_DIR_WIN}:/app" \
        -v "${SECRETS_DIR_WIN}:/secrets:ro" \
        -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/llm-service-account.json \
        -e PYTHONPATH=/app \
        -e GCP_PROJECT="$GCP_PROJECT" \
        -e GCS_BUCKET_NAME="$GCS_BUCKET_NAME" \
        -e GEMINI_MODEL_NAME="$GEMINI_MODEL_NAME" \
        -e GEMINI_MODEL_VERSION="$GEMINI_MODEL_VERSION" \
        -e GEMINI_MODEL_ENDPOINT="$GEMINI_MODEL_ENDPOINT" \
        -e GEMINI_MODEL_REGION="$GEMINI_MODEL_REGION" \
        "$IMAGE_NAME"

else
    # Linux/Unix settings
    echo "Running on Linux/Unix..."

    # Get the absolute path to the secrets directory (3 levels up)
    SECRETS_DIR="$(dirname "$(dirname "$(dirname "$(pwd)")")")/secrets"
    BASE_DIR="$(pwd)"

    # Check secrets directory on Linux side
    if [ ! -d "$SECRETS_DIR" ]; then
        echo "Error: Secrets directory not found at $SECRETS_DIR"
        exit 1
    fi

    if [ ! -f "$SECRETS_DIR/llm-service-account.json" ]; then
        echo "Error: Service account file not found at $SECRETS_DIR/llm-service-account.json"
        exit 1
    fi

    echo "Mounting secrets from: $SECRETS_DIR"
    echo "Mounting base directory from: $BASE_DIR"

    docker run --rm --name "$IMAGE_NAME" -ti \
        -v "${BASE_DIR}:/app" \
        -v "${SECRETS_DIR}:/secrets:ro" \
        -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/llm-service-account.json \
        -e PYTHONPATH=/app \
        -e GCP_PROJECT="$GCP_PROJECT" \
        -e GCS_BUCKET_NAME="$GCS_BUCKET_NAME" \
        -e GEMINI_MODEL_NAME="$GEMINI_MODEL_NAME" \
        -e GEMINI_MODEL_VERSION="$GEMINI_MODEL_VERSION" \
        -e GEMINI_MODEL_ENDPOINT="$GEMINI_MODEL_ENDPOINT" \
        -e GEMINI_MODEL_REGION="$GEMINI_MODEL_REGION" \
        "$IMAGE_NAME"
fi
