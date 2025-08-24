from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    print("🚀 Orchestrator starting up...")
    yield
    # Shutdown
    print("🛑 Orchestrator shutting down...")


def create_application() -> FastAPI:
    app = FastAPI(
        title="AI Business Automation Designer - Orchestrator",
        description="FastAPI orchestrator for AI-powered business automation design",
        version="1.0.0",
        docs_url="/docs" if settings.ENABLE_SWAGGER else None,
        redoc_url="/redoc" if settings.ENABLE_SWAGGER else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

    # Include API router
    app.include_router(api_router, prefix="/v1")

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.ORCHESTRATOR_HOST,
        port=settings.ORCHESTRATOR_PORT,
        reload=settings.ORCHESTRATOR_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
