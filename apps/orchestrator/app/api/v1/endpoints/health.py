from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    timestamp: str


@router.get("/", response_model=HealthResponse)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    import datetime
    
    return {
        "status": "healthy",
        "message": "AI Business Automation Designer Orchestrator is running",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint"""
    # TODO: Add database, Redis, NATS connectivity checks
    return {"status": "ready"}


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check endpoint"""
    return {"status": "alive"}
