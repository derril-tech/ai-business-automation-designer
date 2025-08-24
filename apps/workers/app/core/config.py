from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Business Automation Designer - Workers"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_automation"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # NATS
    NATS_URL: str = "nats://localhost:4222"
    NATS_CLUSTER_ID: str = "ai-automation-cluster"
    NATS_CLIENT_ID: str = "ai-automation-workers"
    
    # S3/MinIO
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "ai-automation-artifacts"
    S3_REGION: str = "us-east-1"
    S3_FORCE_PATH_STYLE: bool = True
    
    # Workers
    WORKERS_CONCURRENCY: int = 4
    WORKERS_PREFETCH_MULTIPLIER: int = 1
    WORKERS_TASK_ACKS_LATE: bool = True
    WORKERS_TASK_REJECT_ON_WORKER_LOST: bool = True
    
    # Observability
    OTEL_ENDPOINT: Optional[str] = None
    OTEL_SERVICE_NAME: str = "ai-automation-workers"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
