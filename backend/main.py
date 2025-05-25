"""
Olympian AI Dynamic - Main Application Entry Point
Divine intelligence meets mortal ambition
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# Import routers
from app.api import (
    chat,
    config,
    discovery,
    mcp,
    ollama,
    projects,
    system,
    webhooks
)
from app.core.websocket import websocket_endpoint
from app.core.config import settings

# Configure logger
logger.add(
    "logs/olympian_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("🏛️ Olympian AI starting up...")
    
    # Startup tasks
    # TODO: Initialize database connections
    # TODO: Start background tasks
    # TODO: Run initial service discovery
    
    yield
    
    # Shutdown tasks
    logger.info("🌅 Olympian AI shutting down...")
    # TODO: Close database connections
    # TODO: Cancel background tasks


# Create FastAPI application
app = FastAPI(
    title="Olympian AI Dynamic",
    description="Divine-themed AI interface with dynamic service discovery",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Welcome to Olympian AI"""
    return {
        "name": "Olympian AI Dynamic",
        "version": "1.0.0",
        "status": "operational",
        "message": "Welcome to the realm of divine intelligence! 🏛️",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api": {
                "chat": "/api/chat",
                "ollama": "/api/ollama",
                "projects": "/api/projects",
                "config": "/api/config",
                "system": "/api/system",
                "discovery": "/api/discovery",
                "mcp": "/api/mcp",
                "webhooks": "/api/webhooks"
            }
        }
    }


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "service": "Olympian AI Backend",
        "version": "1.0.0",
        "timestamp": os.popen('date').read().strip()
    }


# Include API routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(ollama.router, prefix="/api/ollama", tags=["ollama"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(discovery.router, prefix="/api/discovery", tags=["discovery"])
app.include_router(mcp.router, prefix="/api/mcp", tags=["mcp"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

# Add WebSocket endpoint
app.add_api_websocket_route("/ws/{client_id}", websocket_endpoint)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "type": type(exc).__name__,
            "message": str(exc) if settings.debug else "Internal server error"
        }
    )


# Startup message
@app.on_event("startup")
async def startup_message():
    """Display startup message"""
    logger.info("=" * 60)
    logger.info("🏛️  OLYMPIAN AI DYNAMIC")
    logger.info("=" * 60)
    logger.info("Divine intelligence meets mortal ambition")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API URL: http://localhost:8000")
    logger.info(f"Docs URL: http://localhost:8000/docs")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
