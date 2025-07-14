from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn

from .core.config import settings
from .core.database import create_tables
from .api import github_router, user_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Devlog Radar API...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created")
    
    yield
    
    logger.info("Shutting down Devlog Radar API...")


# Create FastAPI app
app = FastAPI(
    title="Devlog Radar API",
    description="Developer productivity tracker with GitHub integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(github_router)
app.include_router(user_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Devlog Radar API",
        "version": "1.0.0",
        "description": "Developer productivity tracker with GitHub integration",
        "docs_url": "/docs",
        "health_check": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"  # Could add actual DB health check here
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )