FROM python:3.12-slim-bookworm

# Tell pipenv where the shell is. 
# This allows us to use "pipenv shell" as a container entry point.
ENV PYENV_SHELL=/bin/bash

# Set Google credentials environment variable to use the mounted secrets file
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets.json

# Ensure we have an up to date baseline, install dependencies 
RUN set -ex; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libsqlite3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install pipenv \
    && mkdir -p /app

# Create .dockerignore file to exclude .venv
RUN echo ".venv/" > /app/.dockerignore

WORKDIR /app

# Add Pipfile, Pipfile.lock
COPY Pipfile Pipfile.lock /app/

# Install dependencies
RUN pipenv sync

# Source code (will exclude .venv due to .dockerignore)
COPY . /app/

# Entry point
ENTRYPOINT ["/bin/bash"]

# Get into the pipenv shell
CMD ["-c", "pipenv shell"]