#!/bin/bash

# Script to check Kubernetes application status and logs
# Author: ExpertFinder Team
# Date: May 4, 2025

set -e

# Default values
NAMESPACE="expert-finder-cluster-namespace"
COMPONENT=""
TAIL_LINES=50
SHOW_LOGS=false
CHECK_STATUS=true

# Help function
function show_help {
    echo "Usage: ./k8s-status.sh [OPTIONS]"
    echo "Check Kubernetes application status and logs for ExpertFinder application"
    echo
    echo "Options:"
    echo "  -n, --namespace NAMESPACE   Kubernetes namespace (default: expert-finder-cluster-namespace)"
    echo "  -c, --component COMPONENT   Component to check (frontend, backend, all). Default: all"
    echo "  -l, --logs                  Show logs for the component(s)"
    echo "  -t, --tail LINES            Number of log lines to show (default: 50)"
    echo "  -h, --help                  Show this help message"
    echo
    echo "Examples:"
    echo "  ./k8s-status.sh                       # Show status of all components"
    echo "  ./k8s-status.sh -c frontend -l        # Show status and logs for frontend"
    echo "  ./k8s-status.sh -c backend -l -t 100  # Show status and logs for backend with 100 lines"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -c|--component)
            COMPONENT="$2"
            shift 2
            ;;
        -l|--logs)
            SHOW_LOGS=true
            shift
            ;;
        -t|--tail)
            TAIL_LINES="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to check if kubectl is installed
function check_kubectl {
    if ! command -v kubectl &> /dev/null; then
        echo "kubectl could not be found. Please install kubectl."
        exit 1
    fi
}

# Function to check cluster connection
function check_cluster_connection {
    if ! kubectl cluster-info &> /dev/null; then
        echo "Error: Could not connect to Kubernetes cluster."
        echo "Please ensure you are connected to your GKE cluster using:"
        echo "gcloud container clusters get-credentials expert-finder-cluster --zone YOUR_ZONE --project YOUR_PROJECT"
        exit 1
    fi
}

# Function to check if namespace exists
function check_namespace {
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo "Error: Namespace '$NAMESPACE' does not exist."
        echo "Available namespaces:"
        kubectl get namespaces
        exit 1
    fi
}

# Function to display status for a component
function display_status {
    local component=$1
    echo "===== $component Status ====="
    
    echo "Deployments:"
    kubectl get deployment -n "$NAMESPACE" -l run="$component" -o wide
    
    echo "Pods:"
    kubectl get pods -n "$NAMESPACE" -l run="$component" -o wide
    
    echo "Services:"
    kubectl get services -n "$NAMESPACE" -l run="$component" -o wide
    
    if [ "$component" = "frontend" ]; then
        echo "Ingress:"
        kubectl get ingress -n "$NAMESPACE" 2>/dev/null || echo "No ingress resources found"
    fi
    
    echo "Events (last 5):"
    kubectl get events -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp | grep -i "$component" | tail -5
    
    # List all jobs
    kubectl get jobs -n expert-finder-cluster-namespace 

    # Delete the stuck job (replace JOB_NAME with the actual name)
    echo "kubectl delete job JOB_NAME -n expert-finder-cluster-namespace"
    
    echo
}

# Function to display logs for a component
function display_logs {
    local component=$1
    echo "===== $component Logs ====="
    
    # Get pod names for the component
    local pods=$(kubectl get pods -n "$NAMESPACE" -l run="$component" -o jsonpath='{.items[*].metadata.name}')
    
    if [ -z "$pods" ]; then
        echo "No pods found for $component"
        return
    fi
    
    # For each pod, display logs
    for pod in $pods; do
        echo "Logs for pod: $pod"
        kubectl logs -n "$NAMESPACE" "$pod" --tail="$TAIL_LINES"
        echo "----------------------------------------"
    done
    
    echo
}

# Main execution
echo "ExpertFinder Kubernetes Status Checker"
echo "==============================================="

# Check prerequisites
check_kubectl
check_cluster_connection
check_namespace

# Process based on component selection
if [ -z "$COMPONENT" ] || [ "$COMPONENT" = "all" ]; then
    components=("frontend" "backend")
else
    components=("$COMPONENT")
fi

# Display status and/or logs for selected components
for comp in "${components[@]}"; do
    if [ "$CHECK_STATUS" = true ]; then
        display_status "$comp"
    fi
    
    if [ "$SHOW_LOGS" = true ]; then
        display_logs "$comp"
    fi
done

echo "Status check completed."
