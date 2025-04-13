#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Set variables
export BASE_DIR=$(pwd)
export IMAGE_NAME="expert-finder-frontend"

# Create the network if we don't have it yet
docker network inspect expert-finder-network >/dev/null 2>&1 || docker network create expert-finder-network

# Build the image based on the Dockerfile
docker build -t $IMAGE_NAME -f Dockerfile .

# Run All Containers
docker compose run --rm --service-ports $IMAGE_NAME

# Run Container
# docker run --rm --name $IMAGE_NAME -ti \
#     -v "$BASE_DIR":/app \
#     -p 3000:3000 \
#     -e NODE_ENV=development \
#     $IMAGE_NAME
