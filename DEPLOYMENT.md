# Google Cloud Run Deployment Guide

## Enable Required APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Build and Deploy
```bash
# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Set region (choose one close to your Memorystore instance)
gcloud config set run/region us-central1

# Build and deploy to Cloud Run
gcloud run deploy ragpdf-api \
  --source . \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars GOOGLE_API_KEY=your-key,QDRANT_URL=your-url,QDRANT_API=your-key,REDIS_HOST=10.148.208.51,REDIS_PORT=6379
```

## Important Notes
1. Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID
2. Replace environment variable values with your actual credentials
3. Make sure your Cloud Run service is in the same VPC as your Memorystore instance
4. You may need to configure VPC connector for Cloud Run to access Memorystore

## Deploy Worker Separately
The worker needs to run as a separate service:
```bash
# Create a Dockerfile.worker for the worker
# Then deploy it as a separate Cloud Run job or use Compute Engine
```
