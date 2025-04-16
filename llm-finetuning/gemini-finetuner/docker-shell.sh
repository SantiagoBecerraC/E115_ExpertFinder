#!/bin/bash

# Set strict error handling
set -e

# Disable Git Bash path conversion
export MSYS_NO_PATHCONV=1

# Function to convert Windows path to Docker format
convert_path_for_docker() {
    local path="$1"
    # For Windows Git Bash, convert C:\path\to\dir to /c/path/to/dir
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Remove any trailing backslashes
        path="${path%\\}"
        # Convert backslashes to forward slashes
        path="${path//\\//}"
        # Convert C: to /c
        path=$(echo "$path" | sed 's/^\([A-Za-z]\):/\/\L\1/')
    fi
    echo "$path"
}

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: $SCRIPT_DIR"

# Source environment variables
if [ -f "$SCRIPT_DIR/../env.dev" ]; then
    echo "Loading environment variables from env.dev..."
    source "$SCRIPT_DIR/../env.dev"
else
    echo "Warning: env.dev not found in $SCRIPT_DIR/../"
    exit 1
fi

# Determine the project root directory (3 levels up from script directory)
PROJECT_ROOT="$(cd "$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")" && pwd)"
SECRETS_DIR="${PROJECT_ROOT}/secrets"
BASE_DIR="$SCRIPT_DIR"

echo "Project root: $PROJECT_ROOT"
echo "Original secrets directory: $SECRETS_DIR"
echo "Original base directory: $BASE_DIR"

# Convert paths for Docker
SECRETS_DIR_DOCKER=$(convert_path_for_docker "$SECRETS_DIR")
BASE_DIR_DOCKER=$(convert_path_for_docker "$BASE_DIR")

echo "Docker-compatible secrets directory: $SECRETS_DIR_DOCKER"
echo "Docker-compatible base directory: $BASE_DIR_DOCKER"

# Check if secrets directory exists
if [ ! -d "$SECRETS_DIR" ]; then
    echo "Error: Secrets directory not found at $SECRETS_DIR"
    echo "Please ensure the secrets directory exists at the root of the project"
    exit 1
fi

# Check if service account file exists
if [ ! -f "$SECRETS_DIR/llm-service-account.json" ]; then
    echo "Error: Service account file not found at $SECRETS_DIR/llm-service-account.json"
    echo "Please ensure the service account file exists in the secrets directory"
    exit 1
fi

# List contents of secrets directory
echo "Contents of secrets directory:"
ls -la "$SECRETS_DIR"

# Build the Docker image
echo "Building Docker image..."
docker build -t llm-gemini-finetuner:latest .

# Run the container
echo "Starting container..."
docker run -it \
    --rm \
    -v "${SECRETS_DIR_DOCKER}:/secrets" \
    -v "${BASE_DIR_DOCKER}:/app" \
    -e GOOGLE_APPLICATION_CREDENTIALS="/secrets/llm-service-account.json" \
    -e GCP_PROJECT="$GCP_PROJECT" \
    -e GCS_BUCKET_NAME="$GCS_BUCKET_NAME" \
    -e GEMINI_MODEL_NAME="$GEMINI_MODEL_NAME" \
    -e GEMINI_MODEL_VERSION="$GEMINI_MODEL_VERSION" \
    -e GEMINI_MODEL_ENDPOINT="$GEMINI_MODEL_ENDPOINT" \
    -e GEMINI_MODEL_REGION="$GEMINI_MODEL_REGION" \
    -e LOCATION="$LOCATION" \
    --workdir="/app" \
    llm-gemini-finetuner:latest

echo "Container is running!!!"
