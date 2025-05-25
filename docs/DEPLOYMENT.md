# Olympian AI Deployment Guide

## 🏛️ Deployment Overview

This guide covers various deployment options for Olympian AI, from local development to production cloud deployments.

## 🏠 Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/olympian-ai/olympian-ai-dynamic.git
cd olympian-ai-dynamic

# Run setup script
./scripts/setup.sh  # Linux/macOS
# or
.\scripts\setup.ps1  # Windows PowerShell

# Start services
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
```

### Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Build and Push Docker Images**

```bash
# Build images
docker build -t olympian-backend ./backend
docker build -t olympian-frontend ./frontend

# Tag for ECR
docker tag olympian-backend:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/olympian-backend:latest
docker tag olympian-frontend:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/olympian-frontend:latest

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com
docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/olympian-backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/olympian-frontend:latest
```

2. **ECS Task Definition** (`ecs-task-definition.json`)

```json
{
  "family": "olympian-ai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/olympian-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "REDIS_URL", "value": "redis://redis:6379"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/olympian-ai",
          "awslogs-region": "${REGION}",
          "awslogs-stream-prefix": "backend"
        }
      }
    },
    {
      "name": "frontend",
      "image": "${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/olympian-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ]
    }
  ]
}
```

### Google Cloud Platform

#### Using Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/olympian-backend ./backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/olympian-frontend ./frontend

# Deploy backend
gcloud run deploy olympian-backend \
  --image gcr.io/$PROJECT_ID/olympian-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="REDIS_URL=redis://$REDIS_IP:6379"

# Deploy frontend
gcloud run deploy olympian-frontend \
  --image gcr.io/$PROJECT_ID/olympian-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# Create resource group
az group create --name olympian-rg --location eastus

# Create container registry
az acr create --resource-group olympian-rg --name olympianregistry --sku Basic

# Build and push images
az acr build --registry olympianregistry --image olympian-backend ./backend
az acr build --registry olympianregistry --image olympian-frontend ./frontend

# Deploy containers
az container create \
  --resource-group olympian-rg \
  --name olympian-app \
  --image olympianregistry.azurecr.io/olympian-backend:latest \
  --cpu 2 --memory 4 \
  --ports 8000 \
  --environment-variables REDIS_URL=redis://redis:6379
```

## 🌐 Kubernetes Deployment

### Kubernetes Manifests

#### Namespace (`namespace.yaml`)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: olympian-ai
```

#### Backend Deployment (`backend-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: olympian-backend
  namespace: olympian-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: olympian-backend
  template:
    metadata:
      labels:
        app: olympian-backend
    spec:
      containers:
      - name: backend
        image: olympian-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: olympian-ai
spec:
  selector:
    app: olympian-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### Frontend Deployment (`frontend-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: olympian-frontend
  namespace: olympian-ai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: olympian-frontend
  template:
    metadata:
      labels:
        app: olympian-frontend
    spec:
      containers:
      - name: frontend
        image: olympian-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: olympian-ai
spec:
  selector:
    app: olympian-frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

#### Ingress (`ingress.yaml`)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: olympian-ingress
  namespace: olympian-ai
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/websocket-services: backend-service
spec:
  tls:
  - hosts:
    - olympian.example.com
    secretName: olympian-tls
  rules:
  - host: olympian.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Helm Chart

```bash
# Install with Helm
helm install olympian-ai ./helm/olympian-ai \
  --namespace olympian-ai \
  --create-namespace \
  --values values.yaml
```

## 🔒 Production Security

### Environment Variables

```bash
# Backend (.env.production)
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false
JWT_SECRET=your-secure-secret-here
REDIS_URL=redis://redis:6379
CORS_ORIGINS=https://olympian.example.com

# Frontend (.env.production)
VITE_API_URL=https://api.olympian.example.com
VITE_WS_URL=wss://api.olympian.example.com/ws
```

### SSL/TLS Configuration

#### Using Certbot

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d olympian.example.com
```

#### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name olympian.example.com;

    ssl_certificate /etc/letsencrypt/live/olympian.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/olympian.example.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📦 CI/CD Pipeline

### GitHub Actions (`.github/workflows/deploy.yml`)

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Test Backend
      run: |
        cd backend
        pip install -r requirements.txt
        pytest
    
    - name: Test Frontend
      run: |
        cd frontend
        npm ci
        npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
      run: |
        echo "$KUBE_CONFIG" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        kubectl apply -f k8s/
        kubectl rollout status deployment/olympian-backend -n olympian-ai
        kubectl rollout status deployment/olympian-frontend -n olympian-ai
```

## 📋 Monitoring & Logging

### Prometheus Configuration

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'olympian-backend'
    static_configs:
    - targets: ['backend-service:8000']
```

### Grafana Dashboard

Import dashboard JSON from `monitoring/grafana-dashboard.json`

### Log Aggregation

```yaml
# fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: olympian-ai
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/olympian-*.log
      tag olympian.*
      format json
    </source>
    
    <match olympian.**>
      @type elasticsearch
      host elasticsearch
      port 9200
      logstash_format true
    </match>
```

## 🚀 Performance Optimization

### Backend Optimization

```python
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
```

### Frontend Optimization

```nginx
# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

# Cache static assets
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔄 Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

# Backup configuration
kubectl cp olympian-ai/backend-pod:/app/config.yaml ./backups/config-$(date +%Y%m%d).yaml

# Backup Redis
kubectl exec -n olympian-ai redis-pod -- redis-cli SAVE
kubectl cp olympian-ai/redis-pod:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb

# Upload to S3
aws s3 cp ./backups/ s3://olympian-backups/$(date +%Y%m%d)/ --recursive
```

### Disaster Recovery

1. **Database Recovery**
   ```bash
   kubectl cp ./backups/redis-backup.rdb olympian-ai/redis-pod:/data/dump.rdb
   kubectl exec -n olympian-ai redis-pod -- redis-cli SHUTDOWN NOSAVE
   kubectl delete pod redis-pod -n olympian-ai
   ```

2. **Configuration Recovery**
   ```bash
   kubectl cp ./backups/config-backup.yaml olympian-ai/backend-pod:/app/config.yaml
   kubectl rollout restart deployment/olympian-backend -n olympian-ai
   ```

---

For additional deployment support, consult our [community forums](https://community.olympian-ai.dev) or [enterprise support](https://olympian-ai.dev/support). ⚡