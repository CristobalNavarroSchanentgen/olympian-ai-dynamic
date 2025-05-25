"""Service Discovery API Routes"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from loguru import logger

from ..core.discovery import discovery_engine
from ..core.websocket import WebSocketManager

router = APIRouter()
ws_manager = WebSocketManager()


@router.get("/scan")
async def trigger_discovery_scan(background_tasks: BackgroundTasks):
    """Trigger a comprehensive service discovery scan"""
    logger.info("🔍 Discovery scan triggered via API")
    
    # Run scan in background
    background_tasks.add_task(run_discovery_scan)
    
    return {
        "status": "scanning",
        "message": "Service discovery scan initiated"
    }


async def run_discovery_scan():
    """Run discovery scan and notify clients"""
    try:
        await discovery_engine.full_scan()
        
        # Notify all connected clients
        await ws_manager.notify_service_update(
            "all",
            "scan_complete",
            discovery_engine.get_discovered_services()
        )
    except Exception as e:
        logger.error(f"Discovery scan failed: {e}")


@router.get("/status")
async def get_discovery_status():
    """Get current discovery status and results"""
    return {
        "status": "active",
        "discovered_services": discovery_engine.get_discovered_services(),
        "service_health": await discovery_engine.get_service_health(),
        "last_scan": discovery_engine._last_scan
    }


@router.get("/services/{service_type}")
async def get_service_details(service_type: str):
    """Get detailed information about a specific service type"""
    services = discovery_engine.get_discovered_services()
    
    if service_type not in services.get("services", {}):
        raise HTTPException(status_code=404, detail=f"Service type '{service_type}' not found")
    
    return {
        "service_type": service_type,
        "details": services["services"][service_type],
        "capabilities": services["services"][service_type].get("capabilities", {})
    }


@router.post("/manual")
async def add_manual_service(service_config: Dict[str, Any]):
    """Manually add a service endpoint"""
    service_type = service_config.get("type")
    endpoint = service_config.get("endpoint")
    
    if not service_type or not endpoint:
        raise HTTPException(status_code=400, detail="Missing 'type' or 'endpoint'")
    
    # Test the connection based on service type
    if service_type == "ollama":
        test_result = await discovery_engine._check_ollama_endpoint(endpoint)
        success = test_result
        message = "Connection successful" if success else "Connection failed"
    else:
        success = False
        message = f"Service type '{service_type}' not supported for manual addition"
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "status": "added",
        "service_type": service_type,
        "endpoint": endpoint,
        "test_result": {"success": success, "message": message}
    }


@router.delete("/services/{service_type}/{service_id}")
async def remove_service(service_type: str, service_id: str):
    """Remove a service from active configuration"""
    # Implementation would disable the service
    return {
        "status": "removed",
        "service_type": service_type,
        "service_id": service_id
    }
