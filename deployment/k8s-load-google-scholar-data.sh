#!/bin/bash

# Script to run Google Scholar commands in the Kubernetes backend pod
# This script needs to be executed within the deployment container

# Define variables
NAMESPACE="expert-finder-cluster-namespace"
COMMAND="${1:-pipeline}"  # Default command: pipeline (download, process, vectorize)
QUERY="${2:-\"artificial intelligence\"}"  # Default query if not provided
START_YEAR="${3:-2022}"
END_YEAR="${4:-2025}"
NUM_RESULTS="${5:-50}"
COLLECTION="${6:-google_scholar}"

# Print execution information
echo "Executing Google Scholar CLI in Kubernetes backend pod"
echo "Command: $COMMAND"
echo "Query: $QUERY"
echo "Years: $START_YEAR-$END_YEAR"
echo "Number of results: $NUM_RESULTS"
echo "Collection: $COLLECTION"
echo "-----------------------------------------"

# Initialize GKE authentication
echo "Authenticating with GKE cluster..."
gcloud container clusters get-credentials expert-finder-cluster --zone=us-east1-b --project=expertfinder-452203
if [ $? -ne 0 ]; then
  echo "Error: Failed to authenticate with GKE cluster"
  exit 1
fi

# Get the backend pod name
echo "Finding backend pod..."
BACKEND_POD=$(kubectl get pods -n $NAMESPACE -l run=backend -o jsonpath="{.items[0].metadata.name}")

if [ -z "$BACKEND_POD" ]; then
  echo "Error: Backend pod not found in namespace $NAMESPACE"
  exit 1
fi

echo "Using backend pod: $BACKEND_POD"

# Execute the command based on the selected operation
case $COMMAND in
  download)
    echo "Downloading Google Scholar data..."
    kubectl exec -it -n $NAMESPACE $BACKEND_POD -- python google_scholar/cli.py download --query $QUERY --start-year $START_YEAR --end-year $END_YEAR --num-results $NUM_RESULTS
    ;;
    
  process)
    echo "Processing Google Scholar data..."
    kubectl exec -it -n $NAMESPACE $BACKEND_POD -- python google_scholar/cli.py process
    ;;
    
  vectorize)
    echo "Vectorizing Google Scholar data..."
    kubectl exec -it -n $NAMESPACE $BACKEND_POD -- python google_scholar/cli.py vectorize --collection $COLLECTION
    ;;
    
  test)
    echo "Testing Google Scholar data retrieval..."
    kubectl exec -it -n $NAMESPACE $BACKEND_POD -- python google_scholar/cli.py test --query $QUERY --collection $COLLECTION
    ;;
    
  pipeline)
    echo "Running complete Google Scholar pipeline..."
    kubectl exec -it -n $NAMESPACE $BACKEND_POD -- python google_scholar/cli.py pipeline --query $QUERY --start-year $START_YEAR --end-year $END_YEAR --num-results $NUM_RESULTS --collection $COLLECTION
    ;;
    
  archive)
    echo "Archiving Google Scholar data to GCP..."
    kubectl exec -it -n $NAMESPACE $BACKEND_POD -- python google_scholar/cli.py archive
    ;;
    
  *)
    echo "Unknown command: $COMMAND"
    echo "Available commands: download, process, vectorize, test, pipeline, archive"
    kubectl exec -it -n $NAMESPACE $BACKEND_POD -- python google_scholar/cli.py --help
    exit 1
    ;;
esac

echo "-----------------------------------------"
echo "Command execution completed"
