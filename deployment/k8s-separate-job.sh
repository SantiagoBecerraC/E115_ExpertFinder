#!/bin/bash

# Script to run Google Scholar commands in a separate Kubernetes job
# This avoids interfering with the main backend application
# This script needs to be executed within the deployment container

# Define variables
NAMESPACE="expert-finder-cluster-namespace"
COMMAND="${1:-download}"  # Command: download, process, vectorize, test
QUERY="${2:-\"artificial intelligence\"}"  # Default query if not provided
START_YEAR="${3:-2022}"
END_YEAR="${4:-2025}"
NUM_RESULTS="${5:-10}"
COLLECTION="${6:-google_scholar}"

# Print execution information
echo "Creating Kubernetes job to run Google Scholar CLI"
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

# Generate a unique job name with timestamp
JOB_NAME="scholar-job-$(date +%s)"

# Create a random identifier for the job
RANDOM_ID=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 6 | head -n 1)
JOB_NAME="scholar-$COMMAND-$RANDOM_ID"

# Create job YAML
TMP_JOB_YAML="/tmp/$JOB_NAME.yaml"

echo "Creating job definition..."

# Generate appropriate CLI command based on the operation
SCHOLAR_CMD=""
case $COMMAND in
  download)
    SCHOLAR_CMD="python google_scholar/cli.py download --query $QUERY --start-year $START_YEAR --end-year $END_YEAR --num-results $NUM_RESULTS"
    ;;
  process)
    SCHOLAR_CMD="python google_scholar/cli.py process"
    ;;
  vectorize)
    SCHOLAR_CMD="python google_scholar/cli.py vectorize --collection $COLLECTION"
    ;;
  test)
    SCHOLAR_CMD="python google_scholar/cli.py test --query $QUERY --collection $COLLECTION"
    ;;
  pipeline)
    SCHOLAR_CMD="python google_scholar/cli.py pipeline --query $QUERY --start-year $START_YEAR --end-year $END_YEAR --num-results $NUM_RESULTS --collection $COLLECTION"
    ;;
  *)
    echo "Unknown command: $COMMAND"
    echo "Available commands: download, process, vectorize, test, pipeline"
    exit 1
    ;;
esac

# Create the job YAML
cat > $TMP_JOB_YAML << EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: $JOB_NAME
  namespace: $NAMESPACE
spec:
  backoffLimit: 1
  template:
    spec:
      containers:
      - name: scholar-job
        image: gcr.io/expertfinder-452203/expert-finder-backend:20250504115129
        command: ["/bin/bash", "-c"]
        args:
        - "source /app/secrets/.env && $SCHOLAR_CMD"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
          - name: persistent-vol
            mountPath: /chromadb
          - name: google-cloud-key
            mountPath: /secrets
            readOnly: true
          - name: env-file
            mountPath: /app/secrets
            readOnly: true
        env:
          - name: GOOGLE_APPLICATION_CREDENTIALS
            value: /secrets/service-account.json
      volumes:
        - name: persistent-vol
          persistentVolumeClaim:
            claimName: persistent-pvc
        - name: google-cloud-key
          secret:
            secretName: gcp-service-key
        - name: env-file
          secret:
            secretName: serpapi-key
      restartPolicy: Never
EOF

# Apply the job
echo "Creating job $JOB_NAME..."
kubectl apply -f $TMP_JOB_YAML

if [ $? -ne 0 ]; then
  echo "Error: Failed to create job"
  exit 1
fi

echo "Job created successfully. Waiting for job to complete..."

# Watch job status
kubectl get job $JOB_NAME -n $NAMESPACE -w &
JOB_WATCH_PID=$!

# Wait for a moment to let the job start
sleep 5

# Loop to check if job is done
while true; do
  STATUS=$(kubectl get job $JOB_NAME -n $NAMESPACE -o jsonpath='{.status.succeeded}')
  if [ "$STATUS" == "1" ]; then
    echo "Job completed successfully!"
    break
  fi
  
  FAILED=$(kubectl get job $JOB_NAME -n $NAMESPACE -o jsonpath='{.status.failed}')
  if [ "$FAILED" == "1" ]; then
    echo "Job failed!"
    break
  fi
  
  echo "Job still running..."
  sleep 10
done

# Kill the watch process
kill $JOB_WATCH_PID 2>/dev/null

# Get logs from the job pod
echo "-----------------------------------------"
echo "Job logs:"
JOB_POD=$(kubectl get pods -n $NAMESPACE -l job-name=$JOB_NAME -o jsonpath='{.items[0].metadata.name}')
kubectl logs -n $NAMESPACE $JOB_POD

# Clean up
echo "-----------------------------------------"
echo "Job execution completed. Delete job? (y/n)"
read DELETE_JOB

if [ "$DELETE_JOB" == "y" ]; then
  kubectl delete job $JOB_NAME -n $NAMESPACE
  echo "Job deleted."
else
  echo "Job left in the cluster for inspection."
fi
