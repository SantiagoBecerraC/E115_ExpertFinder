#!/bin/bash
# Script to start Docker services required for testing

set -e  # Exit on error

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Determine if we're running in CI or locally
if [ -n "$CI" ]; then
  echo "Running in CI environment"
  COMPOSE_FILE="../docker-compose.test.yml"
else
  echo "Running in local environment"
  COMPOSE_FILE="../docker-compose.test.yml"
fi

# Check if the compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Error: Docker Compose file not found: $COMPOSE_FILE"
  exit 1
fi

echo "Starting test services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
MAX_RETRIES=30
RETRY_INTERVAL=2

# Check ChromaDB availability
retries=0
until curl -s http://localhost:8000/api/v1/heartbeat > /dev/null || [ $retries -eq $MAX_RETRIES ]; do
  echo "Waiting for ChromaDB to be ready... ($(($retries+1))/$MAX_RETRIES)"
  sleep $RETRY_INTERVAL
  retries=$((retries+1))
done

if [ $retries -eq $MAX_RETRIES ]; then
  echo "Error: ChromaDB service did not become available in time"
  docker-compose -f "$COMPOSE_FILE" logs
  docker-compose -f "$COMPOSE_FILE" down
  exit 1
fi

echo "Test environment is ready!"
echo "Run your tests now. When finished, run stop_test_environment.sh to clean up."
