"""
Health check and utility API endpoints.
"""
import redis
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.database import get_db
from app.models.schemas import HealthResponse
from app.core.config import settings
from app.tasks.celery_app import celery_app

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint to verify all systems are operational."""
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        redis_client = redis.Redis.from_url(settings.effective_redis_url)
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # Check Celery
    try:
        # Check if Celery workers are active
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            celery_status = "healthy"
        else:
            celery_status = "no active workers"
    except Exception as e:
        celery_status = f"unhealthy: {str(e)}"
    
    # Determine overall status
    overall_status = "healthy"
    if "unhealthy" in db_status or "unhealthy" in redis_status or "unhealthy" in celery_status:
        overall_status = "unhealthy"
    elif "no active workers" in celery_status:
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        celery=celery_status,
        timestamp=datetime.utcnow()
    )


@router.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Product Importer API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }