#!/bin/bash

# Script to check logs from the Kubernetes backend pod
# This script needs to be executed within the deployment container

# Options:
# -p, --previous   Show logs from previous container instance (if it crashed)
# -f, --follow     Follow logs in real-time
# -t, --tail=N     Show last N lines (default: 100)

# Define variables
NAMESPACE="expert-finder-cluster-namespace"
PREVIOUS=false
FOLLOW=false
TAIL_LINES=100

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--previous)
      PREVIOUS=true
      shift
      ;;
    -f|--follow)
      FOLLOW=true
      shift
      ;;
    -t|--tail)
      TAIL_LINES=$2
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

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

# Build kubectl command based on options
CMD="kubectl logs -n $NAMESPACE $BACKEND_POD"

if [ "$PREVIOUS" = true ]; then
  CMD="$CMD --previous"
  echo "Showing logs from previous container instance (if it crashed)"
fi

if [ "$FOLLOW" = true ]; then
  CMD="$CMD -f"
  echo "Following logs in real-time (press Ctrl+C to exit)"
fi

CMD="$CMD --tail=$TAIL_LINES"
echo "Showing last $TAIL_LINES lines"

echo "-----------------------------------------"

# Execute the command
eval $CMD

echo "-----------------------------------------"

# Check pod events which might show resource issues
echo "Pod events (might show resource issues):"
kubectl describe pod -n $NAMESPACE $BACKEND_POD | grep -A 10 "Events:"

echo "-----------------------------------------"
echo "Resource limits on the pod:"
kubectl describe pod -n $NAMESPACE $BACKEND_POD | grep -A 6 "Limits:"
