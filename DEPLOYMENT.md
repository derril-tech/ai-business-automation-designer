# AI Automation Platform - Deployment Guide

This guide covers deploying the AI Automation Platform in various environments, from local development to production Kubernetes clusters.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Production Deployment](#production-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Monitoring and Observability](#monitoring-and-observability)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For version control
- **curl**: For health checks
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: Minimum 20GB free space
- **CPU**: 4 cores minimum (8 cores recommended)

### Required Software

```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

## Local Development

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-business-automation-designer
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3001
   - API Gateway: http://localhost:3000
   - Orchestrator: http://localhost:8000
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3002

### Development Workflow

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down

# Rebuild specific service
docker-compose -f docker-compose.dev.yml build orchestrator
docker-compose -f docker-compose.dev.yml up -d orchestrator
```

## Production Deployment

### Using Docker Compose

1. **Prepare environment**
   ```bash
   cp .env.example .env
   # Configure production environment variables
   ```

2. **Deploy using the deployment script**
   ```bash
   ./deploy.sh deploy
   ```

3. **Or deploy manually**
   ```bash
   # Build images
   docker build -f apps/orchestrator/Dockerfile.prod -t ai-automation/orchestrator:latest apps/orchestrator/
   docker build -f apps/gateway/Dockerfile.prod -t ai-automation/gateway:latest apps/gateway/
   docker build -f apps/workers/Dockerfile.prod -t ai-automation/workers:latest apps/workers/
   docker build -f apps/frontend/Dockerfile.prod -t ai-automation/frontend:latest apps/frontend/

   # Deploy services
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Deployment Script Commands

```bash
# Deploy the complete platform
./deploy.sh deploy

# Check deployment status
./deploy.sh status

# View logs
./deploy.sh logs
./deploy.sh logs orchestrator

# Stop services
./deploy.sh stop

# Start services
./deploy.sh start

# Restart services
./deploy.sh restart

# Rollback deployment
./deploy.sh rollback
```

### Environment Configuration

Create a `.env` file with the following variables:

```bash
# Database Configuration
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://ai_user:your_secure_password@postgres:5432/ai_automation

# Redis Configuration
REDIS_PASSWORD=your_redis_password
REDIS_URL=redis://:your_redis_password@redis:6379

# NATS Configuration
NATS_URL=nats://nats:4222

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_minio_password

# AI API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# JWT Configuration
JWT_SECRET=your_jwt_secret_key

# CORS Configuration
CORS_ORIGINS=https://your-domain.com

# Worker Configuration
WORKER_CONCURRENCY=4
WORKER_REPLICAS=2

# Monitoring Configuration
GRAFANA_PASSWORD=your_grafana_password
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Helm (optional)
- cert-manager (for SSL certificates)
- nginx-ingress controller

### Deployment Steps

1. **Create namespace**
   ```bash
   kubectl apply -f k8s/namespace.yml
   ```

2. **Create secrets**
   ```bash
   # Update k8s/secrets.yml with base64 encoded values
   kubectl apply -f k8s/secrets.yml
   ```

3. **Create configmap**
   ```bash
   kubectl apply -f k8s/configmap.yml
   ```

4. **Deploy services**
   ```bash
   kubectl apply -f k8s/deployments.yml
   kubectl apply -f k8s/services.yml
   kubectl apply -f k8s/ingress.yml
   ```

5. **Verify deployment**
   ```bash
   kubectl get pods -n ai-automation
   kubectl get services -n ai-automation
   kubectl get ingress -n ai-automation
   ```

### Using Helm (Optional)

```bash
# Create Helm chart
helm create ai-automation

# Install with custom values
helm install ai-automation ./ai-automation -n ai-automation -f values.yml
```

### Scaling

```bash
# Scale workers
kubectl scale deployment workers --replicas=5 -n ai-automation

# Scale orchestrator
kubectl scale deployment orchestrator --replicas=3 -n ai-automation

# Scale gateway
kubectl scale deployment gateway --replicas=3 -n ai-automation
```

## Monitoring and Observability

### Prometheus Metrics

The platform exposes Prometheus metrics at `/metrics` endpoints:

- **Orchestrator**: http://localhost:8000/metrics
- **Gateway**: http://localhost:3000/metrics
- **Workers**: http://localhost:8000/metrics

### Key Metrics

- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: HTTP request duration
- `workflow_executions_total`: Workflow execution counts
- `step_executions_total`: Step execution counts
- `ai_agent_calls_total`: AI agent call counts
- `active_workflows`: Currently active workflows
- `database_connections`: Active database connections

### Grafana Dashboards

Access Grafana at http://localhost:3002 (admin/admin):

1. **System Overview**: Overall platform health
2. **Workflow Metrics**: Execution statistics
3. **API Performance**: Response times and throughput
4. **Resource Usage**: CPU, memory, and storage

### Logging

Structured JSON logs are available for all services:

```bash
# View orchestrator logs
docker-compose -f docker-compose.prod.yml logs -f orchestrator

# View gateway logs
docker-compose -f docker-compose.prod.yml logs -f gateway

# View worker logs
docker-compose -f docker-compose.prod.yml logs -f workers
```

### Health Checks

All services provide health check endpoints:

- **Orchestrator**: http://localhost:8000/health
- **Gateway**: http://localhost:3000/health
- **Frontend**: http://localhost:3001/api/health

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database status
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U ai_user

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres
```

#### 2. Redis Connection Issues

```bash
# Check Redis status
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Check Redis logs
docker-compose -f docker-compose.prod.yml logs redis
```

#### 3. Service Not Starting

```bash
# Check service logs
docker-compose -f docker-compose.prod.yml logs orchestrator

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Restart specific service
docker-compose -f docker-compose.prod.yml restart orchestrator
```

#### 4. Memory Issues

```bash
# Check resource usage
docker stats

# Increase memory limits in docker-compose.prod.yml
```

#### 5. Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep :3000

# Change ports in docker-compose.prod.yml
```

### Debug Mode

Enable debug logging by setting environment variables:

```bash
# In .env file
LOG_LEVEL=DEBUG
DEBUG=true
```

### Performance Tuning

#### Database Optimization

```sql
-- Increase connection pool
ALTER SYSTEM SET max_connections = 200;

-- Optimize query performance
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_created_at ON workflow_executions(created_at);
```

#### Redis Optimization

```bash
# Configure Redis for performance
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Worker Optimization

```bash
# Increase worker concurrency
WORKER_CONCURRENCY=8

# Scale worker replicas
WORKER_REPLICAS=4
```

### Backup and Recovery

#### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U ai_user ai_automation > backup.sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U ai_user ai_automation < backup.sql
```

#### Volume Backup

```bash
# Backup volumes
docker run --rm -v ai-automation_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v ai-automation_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Security Considerations

### SSL/TLS Configuration

1. **Generate SSL certificates**
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem
   ```

2. **Configure nginx with SSL**
   - Update `nginx/nginx.conf` with certificate paths
   - Enable HTTPS redirects

### Secrets Management

1. **Use Kubernetes secrets**
   ```bash
   kubectl create secret generic ai-automation-secrets \
     --from-literal=postgres-password=your_password \
     --from-literal=jwt-secret=your_jwt_secret
   ```

2. **Use external secret managers**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault

### Network Security

1. **Configure firewalls**
   ```bash
   # Allow only necessary ports
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow 22/tcp
   ```

2. **Use private networks**
   - Deploy in private subnets
   - Use VPN for remote access
   - Implement network policies

## Support

For additional support:

1. Check the [GitHub Issues](https://github.com/your-repo/issues)
2. Review the [Documentation](https://docs.your-domain.com)
3. Contact the development team

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
