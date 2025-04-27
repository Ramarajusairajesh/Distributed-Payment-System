# Installation Guide

This guide provides detailed instructions on how to set up and run the Distributed Payment System.

## Prerequisites

Before proceeding with the installation, ensure that you have the following software installed:

- Docker and Docker Compose (for local development)
- Python 3.11 or higher
- Kubernetes cluster (for production deployment)
- kubectl command-line tool
- Helm (optional, for easier Kubernetes deployment)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Distributed-Payment-System.git
cd Distributed-Payment-System
```

### 2. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the sample `.env` file:

```bash
cp .env.example .env
```

Edit the `.env` file to set your configuration values.

### 4. Start Local Services with Docker Compose

```bash
docker-compose up -d
```

This will start all required services including PostgreSQL, Redis, Kafka, and Zookeeper.

### 5. Initialize Database (if needed)

```bash
python -m app.common.database.init_db
```

### 6. Start Services

For local development, you can run each service individually:

```bash
# In separate terminals
python -m app.auth_service.main
python -m app.account_service.main
python -m app.transaction_service.main
python -m app.notification_service.main
python -m app.api_gateway.main
```

Or use Docker Compose to start all services:

```bash
docker-compose up
```

### 7. Access the API

The API will be available at: http://localhost:8000

Swagger UI documentation is available at: http://localhost:8000/docs

## Production Deployment with Kubernetes

### 1. Configure Kubernetes Manifests

Update the following files in the `kubernetes/manifests` directory to match your environment:

- `configmap.yaml` - Update environment settings
- `secrets.yaml` - Set secure secrets
- `deployments.yaml` - Update image registry and versions

### 2. Deploy Infrastructure Services

```bash
kubectl apply -f kubernetes/manifests/namespace.yaml
kubectl apply -f kubernetes/manifests/postgres.yaml
kubectl apply -f kubernetes/manifests/redis.yaml
kubectl apply -f kubernetes/manifests/kafka.yaml
```

### 3. Deploy Configuration

```bash
kubectl apply -f kubernetes/manifests/configmap.yaml
kubectl apply -f kubernetes/manifests/secrets.yaml
```

### 4. Deploy Application Services

```bash
kubectl apply -f kubernetes/manifests/services.yaml
kubectl apply -f kubernetes/manifests/deployments.yaml
```

### 5. Check Deployment Status

```bash
kubectl get pods -n payment-system
kubectl get services -n payment-system
```

### 6. Access the API

Get the external IP of the API Gateway service:

```bash
kubectl get service api-gateway -n payment-system
```

The API will be available at: http://<EXTERNAL_IP>:8000

## Troubleshooting

### Check Service Logs

```bash
# Local (Docker Compose)
docker-compose logs auth_service

# Kubernetes
kubectl logs -f deployment/auth-service -n payment-system
```

### Check Database Connection

```bash
# Local
docker-compose exec postgres psql -U postgres -d payment_system

# Kubernetes
kubectl exec -it postgres-0 -n payment-system -- psql -U postgres -d payment_system
```

### Reset Database

```bash
# Local
docker-compose down -v
docker-compose up -d
``` 