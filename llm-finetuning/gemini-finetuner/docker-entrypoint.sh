#!/bin/bash

# Ensure we're using Unix line endings
set -e
IFS=$'\n'

echo "Container is running!!!"

# Ensure we're using the correct Python path
export PATH="/usr/local/bin:${PATH}"
export PYTHONPATH="/app:${PYTHONPATH}"

# Verify secrets directory and file
echo "Checking secrets directory..."
if [ ! -d "/secrets" ]; then
    echo "Error: /secrets directory not found!"
    exit 1
fi

ls -la /secrets || true

if [ ! -f "/secrets/llm-service-account.json" ]; then
    echo "Error: Service account file not found at /secrets/llm-service-account.json"
    echo "Current directory contents:"
    ls -la /secrets || true
    exit 1
fi

echo "Service account file found!"

args="$@"
echo "Arguments: $args"

if [ -z "$args" ]; then
    # If no arguments provided, start an interactive shell
    echo "Starting interactive shell..."
    exec /bin/bash
else
    # If arguments provided, run them with Python
    echo "Running Python command..."
    exec /usr/local/bin/python $args
fi