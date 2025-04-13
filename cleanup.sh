#!/bin/bash

# exit on error
set -e

echo "🧹 Starting cleanup process..."

# Function to check and kill process using a port
cleanup_port() {
    local port=$1
    echo "Checking port $port..."
    if lsof -i ":$port" > /dev/null; then
        echo "Found process using port $port. Stopping it..."
        lsof -ti ":$port" | xargs kill -9 2>/dev/null || true
    else
        echo "No process found using port $port"
    fi
}

# Stop all running containers
echo "Stopping all running containers..."
docker compose down 2>/dev/null || true
docker stop $(docker ps -a -q) 2>/dev/null || true

# Remove all containers
echo "Removing stopped containers..."
docker rm $(docker ps -a -q) 2>/dev/null || true

# Remove the network
echo "Removing docker network..."
docker network rm expert-finder-network 2>/dev/null || true

# Cleanup ports
echo "Cleaning up ports..."
cleanup_port 3000  # Frontend port
cleanup_port 8000  # Backend port

# Prune Docker system
echo "Pruning Docker system..."
docker system prune -f

echo "✨ Cleanup complete! You can now start the application fresh."
