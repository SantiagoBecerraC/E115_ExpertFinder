# Use the official Debian-hosted Python image
FROM python:3.11.5-bookworm 

# Tell pipenv where the shell is. 
# This allows us to use "pipenv shell" as a container entry point.
ENV PYENV_SHELL=/bin/bash

# Force PyTorch to use CPU-only mode
ENV CUDA_VISIBLE_DEVICES=""
# Add environment variables to help with NumPy 2.0 compatibility issues
ENV NUMPY_EXPERIMENTAL_ARRAY_FUNCTION=0
ENV PYTHONWARNINGS="ignore::UserWarning"

# Ensure we have an up to date baseline, install dependencies 
RUN set -ex; \
 apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libsqlite3-dev && \
    pip install --no-cache-dir --upgrade pip && \
    pip install pipenv && \
    mkdir -p /app

WORKDIR /app

# Add Pipfile, Pipfile.lock
ADD Pipfile Pipfile.lock /app/

# Install dependencies
RUN pipenv install --system --deploy --skip-lock

# Install debugpy for interactive debugging
RUN pip install debugpy

# Source code
ADD . /app

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose port 8000
EXPOSE 8000

# Run the application
ENTRYPOINT ["/app/docker-entrypoint.sh"]