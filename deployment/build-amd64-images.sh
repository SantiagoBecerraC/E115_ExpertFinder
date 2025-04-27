#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get timestamp for docker tag
TIMESTAMP=$(date +%Y%m%d%H%M%S)
echo "Using tag: $TIMESTAMP"

# Set the GCP project
GCP_PROJECT="expertfinder-452203"

# Configure docker to use gcloud credentials
echo "Configuring Docker with GCP credentials..."
gcloud auth configure-docker --quiet

# Make sure we're using the service account
echo "Ensuring we're using the service account..."
gcloud config set account umy-deployment@expertfinder-452203.iam.gserviceaccount.com

# Build and push frontend image using AMD64-specific Dockerfile
echo "Building frontend image for AMD64..."
cd /frontend
docker build --no-cache --platform=linux/amd64 -f Dockerfile.amd64 -t gcr.io/$GCP_PROJECT/expert-finder-frontend:$TIMESTAMP .
echo "Pushing frontend image to GCR..."
docker push gcr.io/$GCP_PROJECT/expert-finder-frontend:$TIMESTAMP

# Build and push backend image using AMD64-specific Dockerfile
echo "Building backend image for AMD64..."
cd /backend
docker build --no-cache --platform=linux/amd64 -f Dockerfile.amd64 -t gcr.io/$GCP_PROJECT/expert-finder-backend:$TIMESTAMP .
echo "Pushing backend image to GCR..."
docker push gcr.io/$GCP_PROJECT/expert-finder-backend:$TIMESTAMP

# Save the tag for later use
echo $TIMESTAMP > /app/.docker-tag

echo "Build and push completed successfully!"
echo "Now update your deployments with:"
echo "kubectl set image deployment/frontend frontend=gcr.io/$GCP_PROJECT/expert-finder-frontend:$TIMESTAMP -n expert-finder-cluster-namespace"
echo "kubectl set image deployment/backend backend=gcr.io/$GCP_PROJECT/expert-finder-backend:$TIMESTAMP -n expert-finder-cluster-namespace"
