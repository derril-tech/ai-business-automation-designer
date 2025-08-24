from fastapi import APIRouter
from app.api.v1.endpoints import health, design, execution, simulation

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(design.router, prefix="/design", tags=["design"])
api_router.include_router(execution.router, prefix="/execution", tags=["execution"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
