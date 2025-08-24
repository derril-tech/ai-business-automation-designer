from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Business Automation Designer - Orchestrator"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Server
    ORCHESTRATOR_HOST: str = "0.0.0.0"
    ORCHESTRATOR_PORT: int = 8000
    ORCHESTRATOR_RELOAD: bool = True
    ORCHESTRATOR_WORKERS: int = 4
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_automation"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # NATS
    NATS_URL: str = "nats://localhost:4222"
    NATS_CLUSTER_ID: str = "ai-automation-cluster"
    NATS_CLIENT_ID: str = "ai-automation-orchestrator"
    
    # S3/MinIO
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "ai-automation-artifacts"
    S3_REGION: str = "us-east-1"
    S3_FORCE_PATH_STYLE: bool = True
    
    # AI & CrewAI
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    CREWAI_LLM_MODEL: str = "gpt-4"
    CREWAI_MAX_ITERATIONS: int = 10
    CREWAI_VERBOSE: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Features
    ENABLE_SWAGGER: bool = True
    ENABLE_GRAPHIQL: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
