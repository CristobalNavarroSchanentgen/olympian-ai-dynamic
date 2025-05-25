"""Enhanced Ollama Configuration API - Sacred Endpoint Management"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime
from loguru import logger
import asyncio
import aiohttp

from ..core.config import settings
from ..core.websocket import WebSocketManager
from ..core.discovery import discovery_engine  # Fixed import - use the global instance

router = APIRouter()
ws_manager = WebSocketManager()


class OllamaEndpoint(BaseModel):
    """Ollama endpoint model with validation"""
    url: str
    name: Optional[str] = None
    enabled: bool = True
    timeout: int = 30
    priority: int = 0  # Higher priority = preferred endpoint
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            v = f'http://{v}'
        # Ensure it's a valid URL format
        if '://' not in v:
            raise ValueError('Invalid URL format')
        return v


class OllamaEndpointUpdate(BaseModel):
    """Model for updating Ollama endpoints"""
    endpoints: List[OllamaEndpoint]


class EndpointTestResult(BaseModel):
    """Result of endpoint connectivity test"""
    url: str
    status: str  # 'connected', 'error', 'timeout'
    response_time: Optional[float] = None
    models_count: Optional[int] = None
    error_message: Optional[str] = None
    ollama_version: Optional[str] = None


async def test_ollama_endpoint(url: str, timeout: int = 10) -> EndpointTestResult:
    """Test connectivity to an Ollama endpoint"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # Test basic connectivity
            async with session.get(f"{url}/api/version") as response:
                if response.status == 200:
                    version_data = await response.json()
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    # Get models count
                    try:
                        async with session.get(f"{url}/api/tags") as models_response:
                            if models_response.status == 200:
                                models_data = await models_response.json()
                                models_count = len(models_data.get('models', []))
                            else:
                                models_count = None
                    except Exception:
                        models_count = None
                    
                    return EndpointTestResult(
                        url=url,
                        status='connected',
                        response_time=response_time,
                        models_count=models_count,
                        ollama_version=version_data.get('version', 'unknown')
                    )
                else:
                    return EndpointTestResult(
                        url=url,
                        status='error',
                        error_message=f"HTTP {response.status}: {response.reason}"
                    )
    except asyncio.TimeoutError:
        return EndpointTestResult(
            url=url,
            status='timeout',
            error_message=f"Connection timeout after {timeout}s"
        )
    except Exception as e:
        return EndpointTestResult(
            url=url,
            status='error',
            error_message=str(e)
        )


@router.get("/endpoints")
async def get_ollama_endpoints():
    """Get all configured Ollama endpoints"""
    # Get discovered endpoints
    discovered = settings.discovered_services.get("ollama", {}).get("endpoints", [])
    
    # Get custom endpoints from user preferences
    custom_endpoints = settings.user_preferences.custom_endpoints or []
    
    # Get stored endpoint configurations (if any)
    manual_overrides = settings.user_preferences.manual_overrides.get("ollama_endpoints", {})
    
    # Build unified endpoint list
    all_endpoints = []
    
    # Add discovered endpoints
    for endpoint in discovered:
        endpoint_config = manual_overrides.get(endpoint, {})
        all_endpoints.append({
            "url": endpoint,
            "name": f"Discovered Ollama ({endpoint})",
            "enabled": not endpoint in (settings.user_preferences.disabled_services or []),
            "source": "discovered",
            "priority": endpoint_config.get("priority", 0),
            "timeout": endpoint_config.get("timeout", 30)
        })
    
    # Add custom endpoints
    for endpoint in custom_endpoints:
        if endpoint not in discovered:  # Avoid duplicates
            endpoint_config = manual_overrides.get(endpoint, {})
            all_endpoints.append({
                "url": endpoint,
                "name": endpoint_config.get("name", f"Custom Ollama ({endpoint})"),
                "enabled": not endpoint in (settings.user_preferences.disabled_services or []),
                "source": "custom",
                "priority": endpoint_config.get("priority", 0),
                "timeout": endpoint_config.get("timeout", 30)
            })
    
    # Sort by priority (descending) then by name
    all_endpoints.sort(key=lambda x: (-x["priority"], x["name"]))
    
    return {
        "endpoints": all_endpoints,
        "count": len(all_endpoints),
        "primary_endpoint": settings.ollama_base_url,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/endpoints/test")
async def test_endpoint_connectivity(endpoint: OllamaEndpoint):
    """Test connectivity to a specific Ollama endpoint"""
    result = await test_ollama_endpoint(endpoint.url, endpoint.timeout)
    return result


@router.post("/endpoints/test-all")
async def test_all_endpoints(background_tasks: BackgroundTasks):
    """Test connectivity to all configured endpoints"""
    endpoints_response = await get_ollama_endpoints()
    endpoints = endpoints_response["endpoints"]
    
    # Test all endpoints concurrently
    tasks = [
        test_ollama_endpoint(ep["url"], ep.get("timeout", 30)) 
        for ep in endpoints
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    test_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            test_results.append(EndpointTestResult(
                url=endpoints[i]["url"],
                status='error',
                error_message=str(result)
            ))
        else:
            test_results.append(result)
    
    # Notify clients about test results
    background_tasks.add_task(
        ws_manager.notify_config_change,
        "ollama_endpoints_tested",
        {"results": [r.dict() for r in test_results]}
    )
    
    return {
        "results": test_results,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/endpoints")
async def add_ollama_endpoint(endpoint: OllamaEndpoint):
    """Add a new Ollama endpoint"""
    # Test the endpoint first
    test_result = await test_ollama_endpoint(endpoint.url, endpoint.timeout)
    
    if test_result.status != 'connected':
        logger.warning(f"Adding endpoint {endpoint.url} despite connectivity issues: {test_result.error_message}")
    
    # Add to custom endpoints
    current_custom = settings.user_preferences.custom_endpoints or []
    if endpoint.url not in current_custom:
        current_custom.append(endpoint.url)
        settings.user_preferences.custom_endpoints = current_custom
    
    # Store endpoint configuration in manual overrides
    endpoint_configs = settings.user_preferences.manual_overrides.get("ollama_endpoints", {})
    endpoint_configs[endpoint.url] = {
        "name": endpoint.name,
        "enabled": endpoint.enabled,
        "timeout": endpoint.timeout,
        "priority": endpoint.priority,
        "added_at": datetime.now().isoformat()
    }
    settings.user_preferences.manual_overrides["ollama_endpoints"] = endpoint_configs
    
    # Save configuration
    settings.save_config()
    
    # Notify clients
    await ws_manager.notify_config_change(
        "ollama_endpoint_added",
        {
            "endpoint": endpoint.dict(),
            "test_result": test_result.dict()
        }
    )
    
    return {
        "status": "added",
        "endpoint": endpoint.dict(),
        "test_result": test_result.dict(),
        "timestamp": datetime.now().isoformat()
    }


@router.put("/endpoints/{endpoint_url:path}")
async def update_ollama_endpoint(endpoint_url: str, endpoint: OllamaEndpoint):
    """Update an existing Ollama endpoint configuration"""
    # Update endpoint configuration in manual overrides
    endpoint_configs = settings.user_preferences.manual_overrides.get("ollama_endpoints", {})
    
    if endpoint_url not in endpoint_configs and endpoint_url not in (settings.user_preferences.custom_endpoints or []):
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    endpoint_configs[endpoint_url] = {
        "name": endpoint.name,
        "enabled": endpoint.enabled,
        "timeout": endpoint.timeout,
        "priority": endpoint.priority,
        "updated_at": datetime.now().isoformat()
    }
    settings.user_preferences.manual_overrides["ollama_endpoints"] = endpoint_configs
    
    # If URL changed, update custom endpoints list
    if endpoint.url != endpoint_url:
        current_custom = settings.user_preferences.custom_endpoints or []
        if endpoint_url in current_custom:
            # Replace old URL with new URL
            current_custom = [endpoint.url if url == endpoint_url else url for url in current_custom]
            settings.user_preferences.custom_endpoints = current_custom
            
            # Move configuration to new URL
            endpoint_configs[endpoint.url] = endpoint_configs.pop(endpoint_url)
    
    # Save configuration
    settings.save_config()
    
    # Notify clients
    await ws_manager.notify_config_change(
        "ollama_endpoint_updated",
        {
            "old_url": endpoint_url,
            "endpoint": endpoint.dict()
        }
    )
    
    return {
        "status": "updated",
        "endpoint": endpoint.dict(),
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/endpoints/{endpoint_url:path}")
async def remove_ollama_endpoint(endpoint_url: str):
    """Remove an Ollama endpoint"""
    # Remove from custom endpoints
    current_custom = settings.user_preferences.custom_endpoints or []
    if endpoint_url in current_custom:
        current_custom.remove(endpoint_url)
        settings.user_preferences.custom_endpoints = current_custom
    
    # Remove from manual overrides
    endpoint_configs = settings.user_preferences.manual_overrides.get("ollama_endpoints", {})
    if endpoint_url in endpoint_configs:
        del endpoint_configs[endpoint_url]
        settings.user_preferences.manual_overrides["ollama_endpoints"] = endpoint_configs
    
    # Add to disabled services if it's a discovered endpoint
    discovered = settings.discovered_services.get("ollama", {}).get("endpoints", [])
    if endpoint_url in discovered:
        disabled_services = settings.user_preferences.disabled_services or []
        if endpoint_url not in disabled_services:
            disabled_services.append(endpoint_url)
            settings.user_preferences.disabled_services = disabled_services
    
    # Save configuration
    settings.save_config()
    
    # Notify clients
    await ws_manager.notify_config_change(
        "ollama_endpoint_removed",
        {"endpoint_url": endpoint_url}
    )
    
    return {
        "status": "removed",
        "endpoint_url": endpoint_url,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/endpoints/set-primary")
async def set_primary_endpoint(endpoint_url: str):
    """Set the primary Ollama endpoint"""
    # Verify endpoint exists and is enabled
    endpoints_response = await get_ollama_endpoints()
    valid_endpoints = [ep for ep in endpoints_response["endpoints"] if ep["enabled"]]
    
    if not any(ep["url"] == endpoint_url for ep in valid_endpoints):
        raise HTTPException(status_code=400, detail="Endpoint not found or disabled")
    
    # Update primary endpoint
    settings.ollama_base_url = endpoint_url
    settings.save_config()
    
    # Notify clients
    await ws_manager.notify_config_change(
        "ollama_primary_endpoint_changed",
        {"primary_endpoint": endpoint_url}
    )
    
    return {
        "status": "updated",
        "primary_endpoint": endpoint_url,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/endpoints/reorder")
async def reorder_endpoints(endpoint_priorities: Dict[str, int]):
    """Reorder endpoints by setting priorities"""
    endpoint_configs = settings.user_preferences.manual_overrides.get("ollama_endpoints", {})
    
    for endpoint_url, priority in endpoint_priorities.items():
        if endpoint_url in endpoint_configs:
            endpoint_configs[endpoint_url]["priority"] = priority
        else:
            endpoint_configs[endpoint_url] = {"priority": priority}
    
    settings.user_preferences.manual_overrides["ollama_endpoints"] = endpoint_configs
    settings.save_config()
    
    # Notify clients
    await ws_manager.notify_config_change(
        "ollama_endpoints_reordered",
        {"priorities": endpoint_priorities}
    )
    
    return {
        "status": "reordered",
        "priorities": endpoint_priorities,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/discover")
async def trigger_ollama_discovery(background_tasks: BackgroundTasks):
    """Trigger Ollama-specific service discovery"""
    try:
        # Add background task to perform discovery
        background_tasks.add_task(_perform_ollama_discovery)
        
        return {
            "status": "discovery_started",
            "message": "Ollama service discovery initiated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start Ollama discovery: {e}")
        raise HTTPException(status_code=500, detail="Failed to start discovery")


async def _perform_ollama_discovery():
    """Background task to perform Ollama discovery"""
    try:
        # Use the global discovery engine instance
        ollama_data = await discovery_engine.discover_ollama_instances()
        
        # Update settings with discovered data
        if "ollama" not in settings.discovered_services:
            settings.discovered_services["ollama"] = {}
        
        settings.discovered_services["ollama"].update(ollama_data)
        
        # Notify clients when discovery completes
        await ws_manager.notify_config_change(
            "ollama_discovery_completed",
            {
                "discovered": ollama_data,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Ollama discovery failed: {e}")
        await ws_manager.notify_config_change(
            "ollama_discovery_failed",
            {"error": str(e), "timestamp": datetime.now().isoformat()}
        )
