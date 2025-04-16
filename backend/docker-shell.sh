#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Set variables
export BASE_DIR=$(pwd)
export PERSISTENT_DIR=$(pwd)/../database/
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

# Run All Containers
docker compose run --rm --service-ports $IMAGE_NAME


# Run Container
# docker run --rm --name $IMAGE_NAME -ti \
#     -v "$BASE_DIR":/app \
#     -v "$SECRETS_DIR":/secrets \
#     -v "$PERSISTENT_DIR":/persistent \
#     -e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
#     -e GCP_PROJECT=$GCP_PROJECT \
#     $IMAGE_NAME


#