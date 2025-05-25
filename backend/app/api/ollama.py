"""Ollama API Routes - The Oracle's Interface"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from loguru import logger

from ..services.ollama_service import OllamaService
from ..core.config import settings

router = APIRouter()
ollama_service = OllamaService()


class ChatRequest(BaseModel):
    """Chat request model"""
    model: str
    message: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    context: Optional[List[Dict[str, str]]] = None
    endpoint: Optional[str] = None


class GenerateRequest(BaseModel):
    """Generation request model"""
    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    endpoint: Optional[str] = None


class ModelRequest(BaseModel):
    """Model management request"""
    name: str
    endpoint: Optional[str] = None


@router.on_event("startup")
async def startup():
    """Initialize Ollama service on startup"""
    await ollama_service.initialize()


@router.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await ollama_service.close()


@router.get("/discover")
async def discover_ollama_instances():
    """Discover available Ollama instances"""
    from ..core.discovery import discovery_engine
    
    result = await discovery_engine.discover_ollama_instances()
    return {
        "status": "success",
        "discovered": result
    }


@router.get("/models")
async def get_models(endpoint: Optional[str] = Query(None)):
    """Get available models from specified or all endpoints"""
    if endpoint:
        models = await ollama_service.get_available_models(endpoint)
        return {
            "endpoint": endpoint,
            "models": models
        }
    else:
        # Get models from all endpoints
        all_models = {}
        for ep in ollama_service.get_active_endpoints():
            all_models[ep] = await ollama_service.get_available_models(ep)
        
        return {
            "endpoints": all_models,
            "total_models": sum(len(models) for models in all_models.values())
        }


@router.get("/models/all")
async def get_all_models():
    """Get all models from all discovered Ollama instances"""
    models = settings.discovered_services.ollama.get("models", [])
    return {
        "models": models,
        "count": len(models)
    }


@router.post("/chat")
async def chat(request: ChatRequest):
    """Send a chat message to Ollama"""
    # This would typically be handled via WebSocket for streaming
    # This endpoint is for non-streaming requests
    
    response_text = ""
    async for chunk in ollama_service.stream_chat(
        model=request.model,
        message=request.message,
        system_prompt=request.system_prompt,
        context=request.context,
        endpoint=request.endpoint,
        temperature=request.temperature
    ):
        response_text += chunk
    
    return {
        "model": request.model,
        "response": response_text
    }


@router.post("/generate")
async def generate(request: GenerateRequest):
    """Generate completion from Ollama"""
    response = await ollama_service.generate(
        model=request.model,
        prompt=request.prompt,
        endpoint=request.endpoint,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    return {
        "model": request.model,
        "response": response
    }


@router.post("/models/pull")
async def pull_model(request: ModelRequest):
    """Pull a new model from Ollama registry"""
    # This would typically stream progress updates
    status_messages = []
    
    async for status in ollama_service.pull_model(
        model_name=request.name,
        endpoint=request.endpoint
    ):
        status_messages.append(status)
    
    return {
        "model": request.name,
        "status": "complete",
        "messages": status_messages
    }


@router.delete("/models/{model_name}")
async def delete_model(
    model_name: str,
    endpoint: Optional[str] = Query(None)
):
    """Delete a model from Ollama"""
    success = await ollama_service.delete_model(model_name, endpoint)
    
    if success:
        return {
            "status": "deleted",
            "model": model_name
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to delete model")


@router.get("/models/{model_name}/info")
async def get_model_info(
    model_name: str,
    endpoint: Optional[str] = Query(None)
):
    """Get detailed information about a specific model"""
    info = await ollama_service.get_model_info(model_name, endpoint)
    
    if not info:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return info


@router.get("/endpoints")
async def get_active_endpoints():
    """Get list of active Ollama endpoints"""
    return {
        "endpoints": ollama_service.get_active_endpoints(),
        "default": ollama_service._default_endpoint
    }


@router.put("/endpoints/default")
async def set_default_endpoint(endpoint: str):
    """Set the default Ollama endpoint"""
    ollama_service.set_default_endpoint(endpoint)
    return {
        "status": "updated",
        "default_endpoint": endpoint
    }


@router.post("/endpoint/add")
async def add_custom_endpoint(endpoint: str):
    """Add a custom Ollama endpoint"""
    # Test the endpoint first
    from ..core.discovery import discovery_engine
    
    if await discovery_engine._check_ollama_endpoint(endpoint):
        # Add to configuration
        if endpoint not in settings.user_preferences.custom_endpoints:
            settings.user_preferences.custom_endpoints.append(endpoint)
            settings.save_config()
        
        # Reinitialize service
        await ollama_service.initialize()
        
        return {
            "status": "added",
            "endpoint": endpoint
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid Ollama endpoint")


@router.get("/health")
async def health_check():
    """Check health of all Ollama endpoints"""
    health_status = {}
    
    for endpoint in ollama_service.get_active_endpoints():
        # Check if we can get models
        models = await ollama_service.get_available_models(endpoint)
        health_status[endpoint] = {
            "healthy": len(models) > 0,
            "model_count": len(models)
        }
    
    return {
        "endpoints": health_status,
        "healthy_count": sum(1 for status in health_status.values() if status["healthy"])
    }