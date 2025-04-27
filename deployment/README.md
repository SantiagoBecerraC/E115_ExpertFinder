# ExpertFinder Deployment

This directory contains the deployment configuration and scripts for the ExpertFinder application. The deployment process uses Ansible playbooks to build Docker images, push them to Google Container Registry (GCR), and deploy them to a Google Kubernetes Engine (GKE) cluster.

## Prerequisites

- Google Cloud Platform (GCP) project set up (expertfinder-452203)
- Google Cloud SDK installed and configured
- Ansible installed
- Docker installed
- Kubernetes CLI (kubectl) installed
- Valid GCP service account with appropriate permissions

## Authentication

Before deploying, you need to authenticate with Google Container Registry:

```bash
gcloud auth configure-docker
```

## Directory Contents

- `deploy-k8s-cluster.yml`: Ansible playbook for creating and configuring a GKE cluster
- `deploy-docker-images.yml`: Ansible playbook for building and pushing Docker images to GCR
- `deploy-docker-images-V1.yml`, `deploy-docker-images-V2.yml`: Alternative versions of the Docker image deployment playbook
- `Dockerfile`: Base Dockerfile for deployment components
- `build-amd64-images.sh`: Script to build platform-specific Docker images - temp script
- `docker-shell.sh`: Helper script for running Docker containers with appropriate environment
- `docker-entrypoint.sh`: Docker entrypoint script
- `inventory.yml`: Ansible inventory file specifying deployment targets

## Deployment Workflow

1. **Run the Deployment Container**:
   ```bash
   ./docker-shell.sh
   ```
   This builds and runs a deployment container with all necessary volumes mounted and environment variables set. **All subsequent deployment commands should be run inside this container.**

2. **Authenticate with GCR**:
   ```bash
   gcloud auth configure-docker
   ```

3. **Build and Push Docker Images**:
   This step is only required if you have NOT already done this

   ```bash
   ansible-playbook deploy-docker-images.yml -i inventory.yml
   ```
   This creates a timestamped Docker tag and saves it to `.docker-tag` file.

4. **Deploy to Kubernetes**:
   ```bash
   ansible-playbook deploy-k8s-cluster.yml -i inventory.yml --extra-vars cluster_state=present
   ```
   This creates/updates:
   - GKE cluster with specified configuration
   - Kubernetes namespace
   - NGINX ingress controller
   - Persistent volume claims
   - GCP secrets
   - Frontend, backend, and other service deployments

5. **To Delete the Cluster**:
   ```bash
   ansible-playbook deploy-k8s-cluster.yml - i inventory.yml --extra-vars cluster_state=absent
   ```

## Configuration

- Cluster settings are defined in the `vars` section of `deploy-k8s-cluster.yml`
- Default values:
  - Cluster name: expert-finder-cluster
  - Machine type: n2d-standard-2
  - Disk size: 30GB
  - Initial node count: 2
  - Autoscaling enabled (min: 1, max: specified by initial_node_count)

## Notes

- Secrets are stored in `../secrets/gcp-service.json`
- The deployment creates persistent volumes for application data and ChromaDB
- Deployment includes readiness and liveness probes for monitoring service health
- Services are exposed via NGINX ingress controller
