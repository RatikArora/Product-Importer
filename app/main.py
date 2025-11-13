"""
Main FastAPI application.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db
from app.api import products, upload, webhooks, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A scalable product import system with CSV processing, webhooks, and real-time progress tracking.",
    debug=settings.debug,
    lifespan=lifespan
)

# Define frontend path globally
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

# Serve the frontend at root FIRST (before other routes)
@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the frontend application."""
    from fastapi.responses import FileResponse
    frontend_file = os.path.join(frontend_path, "index.html")
    return FileResponse(frontend_file, media_type="text/html")

# Serve JavaScript file directly at root level
@app.get("/app.js", include_in_schema=False)
async def serve_app_js():
    """Serve the JavaScript file."""
    from fastapi.responses import FileResponse
    js_file = os.path.join(frontend_path, "app.js")
    return FileResponse(js_file, media_type="application/javascript")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router)
app.include_router(products.router, prefix=settings.api_v1_str)
app.include_router(upload.router, prefix=settings.api_v1_str)
app.include_router(webhooks.router, prefix=settings.api_v1_str)

# API info endpoint
@app.get("/api", include_in_schema=False)
async def api_info():
    """API information endpoint."""
    return {
        "message": "Product Importer API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }

# Mount static files for other assets
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )