#!/bin/bash

# Script to apply increased memory limits to the backend deployment
# This script needs to be executed within the deployment container

# Initialize GKE authentication
echo "Authenticating with GKE cluster..."
gcloud container clusters get-credentials expert-finder-cluster --zone=us-east1-b --project=expertfinder-452203
if [ $? -ne 0 ]; then
  echo "Error: Failed to authenticate with GKE cluster"
  exit 1
fi

# Apply the patch
echo "Applying memory patch to backend deployment..."
kubectl patch deployment backend -n expert-finder-cluster-namespace --patch-file k8s-backend-memory-patch.yaml
if [ $? -ne 0 ]; then
  echo "Error: Failed to apply patch"
  exit 1
fi

echo "Waiting for deployment to update..."
kubectl rollout status deployment/backend -n expert-finder-cluster-namespace
if [ $? -ne 0 ]; then
  echo "Error: Deployment rollout failed"
  exit 1
fi

echo "Memory patch applied successfully. The backend pod now has 2Gi memory limit."
echo ""
echo "You can now run the Google Scholar CLI commands with the increased memory:"
echo "./k8s-load-google-scholar-data.sh download \"danuglipron\" 2022 2025 20 google_scholar"
echo "./k8s-load-google-scholar-data.sh process"
echo "./k8s-load-google-scholar-data.sh vectorize"
echo "./k8s-load-google-scholar-data.sh test \"danuglipron\""
