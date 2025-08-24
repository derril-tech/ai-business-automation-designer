#!/bin/bash

# AI Automation Platform Deployment Script
# This script deploys the complete platform using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found. Please create it from .env.example"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

backup_existing() {
    if [ -d "data" ]; then
        log_info "Creating backup of existing data..."
        mkdir -p "$BACKUP_DIR"
        cp -r data "$BACKUP_DIR/"
        log_success "Backup created at $BACKUP_DIR"
    fi
}

build_images() {
    log_info "Building Docker images..."
    
    # Build orchestrator
    log_info "Building orchestrator image..."
    docker build -f apps/orchestrator/Dockerfile.prod -t ai-automation/orchestrator:latest apps/orchestrator/
    
    # Build gateway
    log_info "Building gateway image..."
    docker build -f apps/gateway/Dockerfile.prod -t ai-automation/gateway:latest apps/gateway/
    
    # Build workers
    log_info "Building workers image..."
    docker build -f apps/workers/Dockerfile.prod -t ai-automation/workers:latest apps/workers/
    
    # Build frontend
    log_info "Building frontend image..."
    docker build -f apps/frontend/Dockerfile.prod -t ai-automation/frontend:latest apps/frontend/
    
    log_success "All images built successfully"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Services deployed successfully"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    log_info "Waiting for PostgreSQL..."
    until docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U ai_user; do
        sleep 2
    done
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    until docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping; do
        sleep 2
    done
    
    # Wait for NATS
    log_info "Waiting for NATS..."
    until curl -f http://localhost:8222/healthz; do
        sleep 2
    done
    
    # Wait for MinIO
    log_info "Waiting for MinIO..."
    until curl -f http://localhost:9000/minio/health/live; do
        sleep 2
    done
    
    # Wait for orchestrator
    log_info "Waiting for orchestrator..."
    until curl -f http://localhost:8000/health; do
        sleep 5
    done
    
    # Wait for gateway
    log_info "Waiting for gateway..."
    until curl -f http://localhost:3000/health; do
        sleep 5
    done
    
    # Wait for frontend
    log_info "Waiting for frontend..."
    until curl -f http://localhost:3001/api/health; do
        sleep 5
    done
    
    log_success "All services are ready"
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Run orchestrator migrations
    docker-compose -f "$COMPOSE_FILE" exec -T orchestrator alembic upgrade head
    
    log_success "Database migrations completed"
}

check_health() {
    log_info "Checking service health..."
    
    # Check all services
    services=(
        "http://localhost:8000/health"
        "http://localhost:3000/health"
        "http://localhost:3001/api/health"
        "http://localhost:9090/-/healthy"
        "http://localhost:3002/api/health"
    )
    
    for service in "${services[@]}"; do
        if curl -f "$service" > /dev/null 2>&1; then
            log_success "Service $service is healthy"
        else
            log_error "Service $service is not responding"
            return 1
        fi
    done
    
    log_success "All services are healthy"
}

show_status() {
    log_info "Deployment Status:"
    echo ""
    echo "Services:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "Access URLs:"
    echo "  Frontend: http://localhost:3001"
    echo "  API Gateway: http://localhost:3000"
    echo "  Orchestrator: http://localhost:8000"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3002 (admin/admin)"
    echo "  MinIO Console: http://localhost:9001"
    echo ""
    echo "Logs:"
    echo "  docker-compose -f $COMPOSE_FILE logs -f [service_name]"
    echo ""
    echo "Stop services:"
    echo "  docker-compose -f $COMPOSE_FILE down"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting AI Automation Platform deployment..."
    
    check_prerequisites
    backup_existing
    build_images
    deploy_services
    wait_for_services
    run_migrations
    check_health
    cleanup
    show_status
    
    log_success "Deployment completed successfully!"
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore backup if exists
    if [ -d "$BACKUP_DIR" ]; then
        log_info "Restoring from backup..."
        rm -rf data
        cp -r "$BACKUP_DIR/data" .
        log_success "Backup restored"
    fi
    
    log_success "Rollback completed"
}

# Show logs function
show_logs() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f
    else
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    fi
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "rollback")
        rollback
        ;;
    "logs")
        show_logs "$2"
        ;;
    "status")
        show_status
        ;;
    "stop")
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Services stopped"
        ;;
    "start")
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Services started"
        ;;
    "restart")
        docker-compose -f "$COMPOSE_FILE" restart
        log_success "Services restarted"
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|logs|status|stop|start|restart}"
        echo ""
        echo "Commands:"
        echo "  deploy    - Deploy the complete platform"
        echo "  rollback  - Rollback to previous deployment"
        echo "  logs      - Show logs (optionally specify service name)"
        echo "  status    - Show deployment status"
        echo "  stop      - Stop all services"
        echo "  start     - Start all services"
        echo "  restart   - Restart all services"
        exit 1
        ;;
esac
