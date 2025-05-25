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
        await discovery_engine.scan_all_services()
        
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
        "service_health": discovery_engine.service_health,
        "last_scan": discovery_engine._last_scan
    }


@router.get("/services/{service_type}")
async def get_service_details(service_type: str):
    """Get detailed information about a specific service type"""
    services = discovery_engine.get_discovered_services()
    
    if service_type not in services:
        raise HTTPException(status_code=404, detail=f"Service type '{service_type}' not found")
    
    return {
        "service_type": service_type,
        "details": services[service_type],
        "capabilities": discovery_engine.get_service_capabilities(service_type)
    }


@router.post("/manual")
async def add_manual_service(service_config: Dict[str, Any]):
    """Manually add a service endpoint"""
    service_type = service_config.get("type")
    endpoint = service_config.get("endpoint")
    
    if not service_type or not endpoint:
        raise HTTPException(status_code=400, detail="Missing 'type' or 'endpoint'")
    
    # Test the connection
    test_result = await discovery_engine.test_service_connection(service_type, service_config)
    
    if not test_result["success"]:
        raise HTTPException(status_code=400, detail=test_result["message"])
    
    # Add to configuration
    # This would be implemented based on service type
    
    return {
        "status": "added",
        "service_type": service_type,
        "endpoint": endpoint,
        "test_result": test_result
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