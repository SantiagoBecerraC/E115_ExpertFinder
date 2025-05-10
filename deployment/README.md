# ExpertFinder Deployment

This directory contains the deployment configuration and scripts for the ExpertFinder application. The deployment process uses Ansible playbooks to build Docker images, push them to Google Container Registry (GCR), and deploy them to a Google Kubernetes Engine (GKE) cluster.

## Directory Contents
- `deploy-k8s-cluster.yml`: Ansible playbook for creating and configuring a GKE cluster
- `deploy-docker-images.yml`: Ansible playbook for building and pushing Docker images to GCR
- `Dockerfile`: Base Dockerfile for deployment components
- `docker-shell.sh`: Helper script for running Docker containers with appropriate environment
- `docker-entrypoint.sh`: Docker entrypoint script
- `inventory.yml`: Ansible inventory file specifying deployment targets

## Prerequisites
- Google Cloud Platform (GCP) project set up (expertfinder-452203)
- Google Cloud SDK installed and configured
- Ansible installed
- Docker installed
- Kubernetes CLI (kubectl) installed
- API's to enable in GCP for Project
   Search for each of these in the GCP search bar and click enable to enable these API's
   - Vertex AI API
   - Compute Engine API
   - Service Usage API
   - Cloud Resource Manager API
   - Google Container Registry API
   - Kubernetes Engine API
- Setup a Service Account for deployment(ex. gcp-service) with the following roles:
   - Compute Admin
   - Compute OS Login
   - Container Registry Service Agent
   - Kubernetes Engine Admin
   - Service Account User
   - Storage Admin
   - Vertex AI Administrator
- Download the gcp service account json file (gco-service.json) and save it in serect folder which is at the project level
- Cluster settings are defined in the `vars` section of `deploy-k8s-cluster.yml`
   - Default values:
      - Cluster name: expert-finder-cluster
      - Machine type: n2d-standard-2
      - Disk size: 30GB
      - Initial node count: 2
      - Autoscaling enabled (min: 1, max: specified by initial_node_count)

## Deployment Workflow

1. **Run the Deployment Container**:
   ```bash
   ./docker-shell.sh
   ```
   This builds and runs a deployment container with all necessary volumes mounted and environment variables set. **All subsequent deployment commands should be run inside this container.**

2. **Log into gcloud**
   ```bash
   gcloud auth login
   ```

3. **Authenticate with GCR**:
   ```bash
   gcloud auth configure-docker
   ```

4. **Build and Push Docker Images**:
   This step is only required if you have NOT already done this

   ```bash
   ansible-playbook deploy-docker-images.yml -i inventory.yml
   ```
   This creates a timestamped Docker tag and saves it to `.docker-tag` file.

5. **Build & Push Docker Images to GCR**:
   ```bash
   ansible-playbook deploy-docker-images.yml -i inventory.yml
   ```

6. **Deploy to Kubernetes**:
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

7. **To Delete the Cluster**:
   ```bash
   ansible-playbook deploy-k8s-cluster.yml - i inventory.yml --extra-vars cluster_state=absent
   ```

8. **To check the status of the k8s cluster**:
   ```bash
   gcloud container clusters describe expert-finder-cluster
   ```

9. **To check the status of the k8s cluster nodes**:
   ```bash
   gcloud container nodes describe expert-finder-cluster
   ```

10. **To check the stats of the k8s pods**:
   ```bash
   kubectl get pods -n expert-finder-cluster-namespace
   ```

11. **To check the stats of the k8s services**:
   ```bash
   kubectl get services -n expert-finder-cluster-namespace
   ```

12. **For first time Chromadb setup ONLY (no need to run afterwards)**:
   - Copy the backend pod name
   - find the backend pod hash from the output of the previous command
   - Run both pipelines from the backend pod:
   ```bash
   kubectl exec -it [backend-pod-hash] -n expert-finder-cluster-namespace —- python -m linkedin_data_processing.cli pipeline  

   kubectl exec -it [backend-pod-hash] -n expert-finder-cluster-namespace —- python -m google_scholar.cli pipeline —query “machine learning”
   ```

13. **how to find the nginx ingress ip address:**
   ```bash
   kubectl get ingress -n expert-finder-cluster-namespace
   ```
   
14. **how to access the frontend application:**
   - Copy the ingress ip address from the previous command
   - Open the browser and go to `http://<ingress-ip>`

## Notes

- Secrets are stored in `../secrets/gcp-service.json`
- The deployment creates persistent volumes for application data and ChromaDB
- Deployment includes readiness and liveness probes for monitoring service health
- Services are exposed via NGINX ingress controller
