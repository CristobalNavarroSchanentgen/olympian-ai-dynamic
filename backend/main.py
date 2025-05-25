"""
Olympian AI Dynamic - Main Application Entry Point
Divine intelligence meets mortal ambition
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
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
from app.core.discovery import discovery_engine
from app.core.service_manager import set_ollama_service, set_mcp_service, set_project_service
from app.services.ollama_service import OllamaService
from app.services.mcp_service import MCPService
from app.services.project_service import ProjectService

# Configure logger
logger.add(
    "logs/olympian_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

# Global service instances
ollama_service = OllamaService()
mcp_service = MCPService()
project_service = ProjectService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("🏛️ Olympian AI starting up...")
    
    # Startup tasks
    try:
        # Initialize discovery engine
        await discovery_engine.start()
        logger.info("🔍 Discovery engine started")
        
        # Run initial service discovery
        discovered_data = await discovery_engine.full_scan()
        logger.info("✨ Initial service discovery completed")
        
        # Update settings with discovered services
        if "services" in discovered_data:
            settings.discovered_services = discovered_data["services"]
            logger.info(f"📋 Updated settings with {len(discovered_data['services'])} service types")
        
        # Initialize services with discovered endpoints
        await ollama_service.initialize()
        await mcp_service.initialize()
        
        # Register services globally
        set_ollama_service(ollama_service)
        set_mcp_service(mcp_service)
        set_project_service(project_service)
        
        logger.info("🎯 All services initialized and registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
    
    yield
    
    # Shutdown tasks
    logger.info("🌅 Olympian AI shutting down...")
    try:
        discovery_engine.stop()
        await ollama_service.close()
        await mcp_service.close()
        logger.info("✅ Graceful shutdown completed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


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
            "websocket": "/ws/{client_id}",
            "websocket_auto": "/ws",
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
        "timestamp": os.popen('date').read().strip(),
        "services": {
            "discovery_engine": "active" if discovery_engine._running else "inactive",
            "ollama_endpoints": len(ollama_service.get_active_endpoints()),
            "discovered_services": len(settings.discovered_services)
        }
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

# Add WebSocket endpoints - both with and without client_id
@app.websocket("/ws/{client_id}")
async def websocket_route_with_id(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication with specific client ID"""
    await websocket_endpoint(websocket, client_id)


@app.websocket("/ws")
async def websocket_route_auto_id(websocket: WebSocket):
    """WebSocket endpoint for real-time communication with auto-generated client ID"""
    await websocket_endpoint(websocket, None)


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
    logger.info(f"WebSocket URL: ws://localhost:8000/ws/{{client_id}}")
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
