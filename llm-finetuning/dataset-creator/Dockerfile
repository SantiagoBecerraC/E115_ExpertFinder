# Use the official Debian-hosted Python image
FROM python:3.9-slim-buster

ARG DEBIAN_PACKAGES="build-essential git screen vim dos2unix coreutils file"

# Prevent apt from showing prompts
ENV DEBIAN_FRONTEND=noninteractive

# Python wants UTF-8 locale
ENV LANG=C.UTF-8

# Tell pipenv where the shell is. This allows us to use "pipenv shell" as a
# container entry point.
ENV PYENV_SHELL=/bin/bash

# Tell Python to disable buffering so we don't lose any logs.
ENV PYTHONUNBUFFERED=1

# Set initial PYTHONPATH
ENV PYTHONPATH=/app

# Ensure we have an up to date baseline, install dependencies and
# create a user so we don't run the app as root
RUN set -ex; \
    for i in $(seq 1 8); do mkdir -p "/usr/share/man/man${i}"; done && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $DEBIAN_PACKAGES && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pipenv && \
    useradd -ms /bin/bash app -d /home/app -u 1000 -p "$(openssl passwd -1 Passw0rd)" && \
    mkdir -p /app && \
    mkdir -p /persistent && \
    mkdir -p /secrets && \
    chown app:app /persistent && \
    chown app:app /app && \
    chown app:app /secrets && \
    chmod 755 /secrets

# Switch to the new user
USER app
WORKDIR /app

# Install python packages
ADD --chown=app:app Pipfile Pipfile.lock /app/

# Create virtual environment and install dependencies
RUN pipenv install --system --deploy

# Add the rest of the source code. This is done last so we don't invalidate all
# layers when we change a line of code.
ADD --chown=app:app . /app

# Ensure entrypoint script exists and has correct line endings and permissions
RUN if [ ! -f docker-entrypoint.sh ]; then \
        echo "Error: docker-entrypoint.sh not found!" && exit 1; \
    fi && \
    # Convert all shell scripts to Unix line endings
    find . -type f -name "*.sh" -exec dos2unix {} + && \
    chmod +x docker-entrypoint.sh && \
    # Verify the script has correct line endings
    echo "Checking entrypoint script line endings:" && \
    file docker-entrypoint.sh && \
    echo "Entrypoint script contents:" && \
    cat -A docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/bin/bash", "./docker-entrypoint.sh"]