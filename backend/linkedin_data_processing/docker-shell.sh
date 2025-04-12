#!/bin/bash

# Simple docker-shell.sh for LinkedIn Data Processing

# Configuration
IMAGE_NAME="linkedin-expert-finder-rag"

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Ask for credentials path
echo "Please enter the path to your GCP credentials file:"
echo "(Default: $(pwd)/../../../secrets/expertfinder-452203-3c0b81d81d3d.json)"
read -p "> " CREDENTIALS_PATH

# Use default path if none provided
if [ -z "$CREDENTIALS_PATH" ]; then
    CREDENTIALS_PATH="$(pwd)/../../../secrets/expertfinder-452203-3c0b81d81d3d.json"
fi

# Check if credentials file exists
if [ ! -f "$CREDENTIALS_PATH" ]; then
    echo "Error: Credentials file not found at $CREDENTIALS_PATH"
    exit 1
fi

# Run the container with mounted credentials
echo "Running Docker container with credentials from: $CREDENTIALS_PATH"
docker run -it \
    -v "$CREDENTIALS_PATH:/app/secrets.json" \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/process_linkedin_profiles.py:/app/process_linkedin_profiles.py" \
    -v "$(pwd)/credibility_system.py:/app/credibility_system.py" \
    $IMAGE_NAME

echo "Container exited."