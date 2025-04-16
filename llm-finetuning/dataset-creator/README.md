# Dataset Creator

This service is responsible for creating datasets for LLM fine-tuning.

## Environment-Specific Setup

### Linux Users
The service uses a Linux-based Docker container with a bash entrypoint script (`docker-entrypoint.sh`). This is the default and recommended setup.

### Windows Users
For Windows users, there is a Windows-specific entrypoint script (`docker-entrypoint.bat`) available. However, the Docker container itself still runs on Linux, so the bash entrypoint script is used inside the container. The Windows script is provided for local development and testing purposes.

## Building and Running

### Linux
```bash
docker build -t llm-dataset-creator:latest .
docker run -it llm-dataset-creator:latest
```

### Windows
```powershell
docker build -t llm-dataset-creator:latest .
docker run -it llm-dataset-creator:latest
```

Note: The container will use the Linux entrypoint script (`docker-entrypoint.sh`) regardless of your host operating system, as Docker containers run in a Linux environment. 