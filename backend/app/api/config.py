"""Configuration API Routes - Divine Settings Management"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from ..core.config import settings
from ..core.websocket import WebSocketManager

router = APIRouter()
ws_manager = WebSocketManager()


class PreferencesUpdate(BaseModel):
    """User preferences update model"""
    preferred_models: Optional[List[str]] = None
    custom_endpoints: Optional[List[str]] = None
    disabled_services: Optional[List[str]] = None
    manual_overrides: Optional[Dict[str, Any]] = None


class ServiceOverride(BaseModel):
    """Service override model"""
    service_type: str
    config: Dict[str, Any]


@router.get("/dynamic")
async def get_dynamic_configuration():
    """Get current dynamic configuration"""
    # Build server info from individual settings attributes
    server_info = {
        "host": settings.server_host,
        "port": settings.server_port,
        "environment": settings.environment,
        "debug": settings.debug,
        "discovery": {
            "enabled": settings.is_service_discovery_enabled(),
            "scan_interval": settings.get_effective_scan_interval()
        }
    }
    
    return {
        "server": server_info,
        "discovered_services": settings.discovered_services,
        "user_preferences": settings.user_preferences.model_dump(),
        "active_services": settings.get_active_services(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/preferences")
async def get_user_preferences():
    """Get user preferences"""
    return {
        "preferences": settings.user_preferences.model_dump(),
        "timestamp": datetime.now().isoformat()
    }


@router.put("/preferences")
async def update_user_preferences(preferences: PreferencesUpdate):
    """Update user preferences"""
    updated = False
    
    if preferences.preferred_models is not None:
        settings.user_preferences.preferred_models = preferences.preferred_models
        updated = True
    
    if preferences.custom_endpoints is not None:
        settings.user_preferences.custom_endpoints = preferences.custom_endpoints
        updated = True
    
    if preferences.disabled_services is not None:
        settings.user_preferences.disabled_services = preferences.disabled_services
        updated = True
    
    if preferences.manual_overrides is not None:
        settings.user_preferences.manual_overrides = preferences.manual_overrides
        updated = True
    
    if updated:
        settings.save_config()
        
        # Notify all connected clients
        await ws_manager.notify_config_change(
            "preferences",
            settings.user_preferences.model_dump()
        )
    
    return {
        "status": "updated" if updated else "no_changes",
        "preferences": settings.user_preferences.model_dump(),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/override")
async def add_service_override(override: ServiceOverride):
    """Add a manual service override"""
    # Add to manual overrides
    settings.user_preferences.manual_overrides[override.service_type] = override.config
    settings.save_config()
    
    # Notify clients
    await ws_manager.notify_config_change(
        "service_override",
        {
            "service_type": override.service_type,
            "config": override.config
        }
    )
    
    return {
        "status": "added",
        "service_type": override.service_type,
        "config": override.config,
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/override/{service_type}")
async def remove_service_override(service_type: str):
    """Remove a service override"""
    if service_type in settings.user_preferences.manual_overrides:
        del settings.user_preferences.manual_overrides[service_type]
        settings.save_config()
        
        # Notify clients
        await ws_manager.notify_config_change(
            "service_override_removed",
            {"service_type": service_type}
        )
        
        return {
            "status": "removed",
            "service_type": service_type,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="Override not found")


@router.get("/cors")
async def get_cors_origins():
    """Get configured CORS origins"""
    return {
        "origins": settings.cors_origins,
        "count": len(settings.cors_origins)
    }


@router.post("/cors/add")
async def add_cors_origin(origin: str):
    """Add a new CORS origin"""
    settings.add_cors_origin(origin)
    
    return {
        "status": "added",
        "origin": origin,
        "origins": settings.cors_origins
    }


@router.delete("/cors/{origin}")
async def remove_cors_origin(origin: str):
    """Remove a CORS origin"""
    if origin in settings.cors_origins:
        settings.cors_origins.remove(origin)
        settings.save_config()
        
        return {
            "status": "removed",
            "origin": origin,
            "origins": settings.cors_origins
        }
    else:
        raise HTTPException(status_code=404, detail="Origin not found")


@router.get("/discovery")
async def get_discovery_config():
    """Get service discovery configuration"""
    discovery_config = {
        "enabled": settings.is_service_discovery_enabled(),
        "scan_interval": settings.get_effective_scan_interval(),
        "network_ranges": []  # Could be added to settings later
    }
    
    return {
        "config": discovery_config,
        "enabled": discovery_config["enabled"],
        "scan_interval": discovery_config["scan_interval"]
    }


@router.put("/discovery")
async def update_discovery_config(
    enabled: Optional[bool] = None,
    scan_interval: Optional[int] = None,
    network_ranges: Optional[List[str]] = None
):
    """Update discovery configuration"""
    updated = False
    
    if enabled is not None:
        settings.discovery_enabled = enabled
        updated = True
    
    if scan_interval is not None and scan_interval > 0:
        settings.discovery_scan_interval = scan_interval
        updated = True
    
    # Note: network_ranges would need to be added to the Settings model
    
    if updated:
        settings.save_config()
        
        # Notify clients
        discovery_config = {
            "enabled": settings.is_service_discovery_enabled(),
            "scan_interval": settings.get_effective_scan_interval()
        }
        await ws_manager.notify_config_change("discovery", discovery_config)
    
    return {
        "status": "updated" if updated else "no_changes",
        "config": {
            "enabled": settings.is_service_discovery_enabled(),
            "scan_interval": settings.get_effective_scan_interval()
        },
        "timestamp": datetime.now().isoformat()
    }


@router.post("/reset")
async def reset_configuration(section: Optional[str] = None):
    """Reset configuration to defaults"""
    if section == "preferences":
        settings.user_preferences = settings.user_preferences.__class__()
    elif section == "discovery":
        settings.discovery_enabled = True
        settings.discovery_scan_interval = 30
    elif section == "all":
        # Reset everything except discovered services
        settings.user_preferences = settings.user_preferences.__class__()
        settings.discovery_enabled = True
        settings.discovery_scan_interval = 30
    else:
        raise HTTPException(status_code=400, detail="Invalid section. Use 'preferences', 'discovery', or 'all'")
    
    settings.save_config()
    
    # Notify clients
    await ws_manager.notify_config_change("reset", {"section": section})
    
    return {
        "status": "reset",
        "section": section,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/export")
async def export_configuration():
    """Export current configuration"""
    return {
        "version": "1.0.0",
        "exported_at": datetime.now().isoformat(),
        "configuration": {
            "server": {
                "host": settings.server_host,
                "port": settings.server_port,
                "environment": settings.environment,
                "debug": settings.debug,
                "discovery": {
                    "enabled": settings.is_service_discovery_enabled(),
                    "scan_interval": settings.get_effective_scan_interval()
                }
            },
            "security": {
                "jwt_algorithm": settings.jwt_algorithm,
                "jwt_expiration_minutes": settings.jwt_expiration_minutes
                # Exclude jwt_secret for security
            },
            "user_preferences": settings.user_preferences.model_dump(),
            "discovered_services": settings.discovered_services,
            "cors_origins": settings.cors_origins
        }
    }


@router.post("/import")
async def import_configuration(config: Dict[str, Any]):
    """Import configuration from export"""
    try:
        # Validate version
        if config.get("version") != "1.0.0":
            raise ValueError("Incompatible configuration version")
        
        configuration = config.get("configuration", {})
        
        # Import user preferences
        if "user_preferences" in configuration:
            for key, value in configuration["user_preferences"].items():
                if hasattr(settings.user_preferences, key):
                    setattr(settings.user_preferences, key, value)
        
        # Import CORS origins
        if "cors_origins" in configuration:
            settings.cors_origins = configuration["cors_origins"]
        
        # Import discovery settings
        if "server" in configuration and "discovery" in configuration["server"]:
            discovery_config = configuration["server"]["discovery"]
            if "enabled" in discovery_config:
                settings.discovery_enabled = discovery_config["enabled"]
            if "scan_interval" in discovery_config:
                settings.discovery_scan_interval = discovery_config["scan_interval"]
        
        settings.save_config()
        
        # Notify clients
        await ws_manager.notify_config_change(
            "imported",
            {"timestamp": datetime.now().isoformat()}
        )
        
        return {
            "status": "imported",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
