# Use the official Debian-hosted Python image with Python 3.12
FROM python:3.12-slim-bullseye

# Tell pipenv where the shell is. 
# This allows us to use "pipenv shell" as a container entry point.
ENV PYENV_SHELL=/bin/bash

# Set Google credentials environment variable to use the mounted secrets file
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets.json

# Ensure we have an up to date baseline, install dependencies 
RUN set -ex; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install --no-cache-dir --upgrade pip && \
    pip install pipenv && \
    mkdir -p /app

WORKDIR /app

# Add Pipfile, Pipfile.lock
ADD Pipfile Pipfile.lock /app/

RUN pipenv sync

# Source code
ADD . /app

# Entry point
ENTRYPOINT ["/bin/bash"]

# Get into the pipenv shell
CMD ["-c", "pipenv shell"]