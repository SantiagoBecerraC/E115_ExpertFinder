#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Debug information
echo "docker-shell-interactive.sh started"

# Set variables
export BASE_DIR=$(pwd)
export PERSISTENT_DIR=$(pwd)/../../chromadb/
export SECRETS_DIR=$(pwd)/../../secrets
export DATA_DIR=$(pwd)/../google-scholar-data/
export GCP_PROJECT="expertfinder-452203"
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

# Run the container in interactive mode with a bash shell
echo "Starting interactive shell in the backend container"
echo "You can manually start the application with 'python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload'"
echo "Or you can use the Python interactive shell with 'python' to test specific modules"

docker run --rm -it --name expert-finder-backend-interactive \
    --network expert-finder-network \
    -p 8000:8000 \
    -v "$BASE_DIR":/app \
    -v "$SECRETS_DIR":/secrets \
    -v "$PERSISTENT_DIR":/chromadb \
    -v "$DATA_DIR":/google-scholar-data \
    -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/expertfinder.json \
    -e GCP_PROJECT=$GCP_PROJECT \
    -e DATA_DIR=/google-scholar-data \
    -e SECRETS_DIR=/secrets \
    -e BASE_DIR=/app \
    -e OPENAI_API_KEY=$OPENAI_API_KEY \
    -e PERSISTENT_DIR=/persistent \
    -e PYTHONPATH=/app \
    --entrypoint /bin/bash \
    $IMAGE_NAME
