"""Webhook API Routes - Divine Event Management"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import hmac
import hashlib
from loguru import logger

from ..services.webhook_service import WebhookService
from ..core.config import settings
from ..core.websocket import WebSocketManager

router = APIRouter()
webhook_service = WebhookService()
ws_manager = WebSocketManager()


class WebhookCreate(BaseModel):
    """Webhook creation model"""
    name: str
    type: str  # supabase, mattermost, discord, generic
    config: Dict[str, Any]
    events: List[str]
    active: bool = True


class WebhookUpdate(BaseModel):
    """Webhook update model"""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    events: Optional[List[str]] = None
    active: Optional[bool] = None


@router.get("/discover")
async def discover_webhook_opportunities():
    """Discover available webhook integration opportunities"""
    from ..core.discovery import discovery_engine
    
    opportunities = await discovery_engine.discover_webhook_opportunities()
    return {
        "status": "success",
        "opportunities": opportunities
    }


@router.post("/auto-setup")
async def auto_setup_webhooks():
    """Automatically setup webhooks for discovered services"""
    opportunities = settings.discovered_services.webhooks
    setup_results = []
    
    for webhook_type in opportunities.get("available_types", []):
        try:
            # Generate webhook endpoint
            webhook_id = str(uuid.uuid4())
            endpoint = f"/api/webhooks/receive/{webhook_id}"
            
            # Create webhook configuration
            webhook_config = {
                "id": webhook_id,
                "type": webhook_type,
                "endpoint": endpoint,
                "created_at": datetime.now(),
                "active": True
            }
            
            # Register webhook
            result = await webhook_service.register_webhook(webhook_config)
            setup_results.append({
                "type": webhook_type,
                "status": "success" if result else "failed",
                "endpoint": endpoint
            })
        
        except Exception as e:
            logger.error(f"Failed to setup {webhook_type} webhook: {e}")
            setup_results.append({
                "type": webhook_type,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "status": "completed",
        "results": setup_results
    }


@router.get("/templates")
async def get_webhook_templates():
    """Get webhook configuration templates"""
    templates = {
        "supabase": {
            "name": "Supabase Realtime",
            "type": "supabase",
            "config": {
                "url": "${SUPABASE_URL}",
                "key": "${SUPABASE_KEY}",
                "table": "your_table_name",
                "events": ["INSERT", "UPDATE", "DELETE"]
            },
            "events": ["db_insert", "db_update", "db_delete"]
        },
        "mattermost": {
            "name": "Mattermost Integration",
            "type": "mattermost",
            "config": {
                "url": "${MATTERMOST_URL}",
                "token": "${MATTERMOST_TOKEN}",
                "channel": "town-square"
            },
            "events": ["message_posted", "user_mentioned"]
        },
        "discord": {
            "name": "Discord Webhook",
            "type": "discord",
            "config": {
                "webhook_url": "${DISCORD_WEBHOOK_URL}",
                "username": "Olympian AI",
                "avatar_url": "https://example.com/avatar.png"
            },
            "events": ["notification", "alert"]
        },
        "generic": {
            "name": "Generic Webhook",
            "type": "generic",
            "config": {
                "url": "https://your-endpoint.com/webhook",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer ${TOKEN}"
                },
                "secret": "${WEBHOOK_SECRET}"
            },
            "events": ["*"]
        }
    }
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/generate")
async def generate_webhook_endpoint(webhook: WebhookCreate):
    """Generate a new webhook endpoint"""
    webhook_id = str(uuid.uuid4())
    
    webhook_data = {
        "id": webhook_id,
        "name": webhook.name,
        "type": webhook.type,
        "config": webhook.config,
        "events": webhook.events,
        "endpoint": f"/api/webhooks/receive/{webhook_id}",
        "secret": webhook.config.get("secret", webhook_service.generate_secret()),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "active": webhook.active,
        "statistics": {
            "total_received": 0,
            "last_received": None,
            "errors": 0
        }
    }
    
    # Register webhook
    registered = await webhook_service.register_webhook(webhook_data)
    
    if not registered:
        raise HTTPException(status_code=500, detail="Failed to register webhook")
    
    return webhook_data


@router.get("")
async def list_webhooks(active_only: bool = False):
    """List all configured webhooks"""
    webhooks = await webhook_service.list_webhooks(active_only=active_only)
    
    return {
        "webhooks": webhooks,
        "total": len(webhooks),
        "active": sum(1 for w in webhooks if w.get("active", False))
    }


@router.get("/{webhook_id}")
async def get_webhook(webhook_id: str):
    """Get webhook details"""
    webhook = await webhook_service.get_webhook(webhook_id)
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return webhook


@router.put("/{webhook_id}")
async def update_webhook(webhook_id: str, update: WebhookUpdate):
    """Update webhook configuration"""
    webhook = await webhook_service.get_webhook(webhook_id)
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Update fields
    update_data = update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now()
    
    updated = await webhook_service.update_webhook(webhook_id, update_data)
    
    return updated


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str):
    """Delete a webhook"""
    success = await webhook_service.delete_webhook(webhook_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return {
        "status": "deleted",
        "webhook_id": webhook_id
    }


@router.post("/receive/{webhook_id}")
async def receive_webhook(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Receive webhook events"""
    webhook = await webhook_service.get_webhook(webhook_id)
    
    if not webhook or not webhook.get("active"):
        raise HTTPException(status_code=404, detail="Webhook not found or inactive")
    
    # Get request data
    body = await request.body()
    headers = dict(request.headers)
    
    # Verify webhook signature if configured
    if webhook.get("secret"):
        signature_header = headers.get("x-webhook-signature", "")
        expected_signature = hmac.new(
            webhook["secret"].encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if signature_header != expected_signature:
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    # Parse payload
    try:
        payload = await request.json()
    except:
        payload = {"raw": body.decode()}
    
    # Create event
    event = {
        "id": str(uuid.uuid4()),
        "webhook_id": webhook_id,
        "webhook_type": webhook["type"],
        "timestamp": datetime.now(),
        "headers": headers,
        "payload": payload
    }
    
    # Process in background
    background_tasks.add_task(
        process_webhook_event,
        webhook,
        event
    )
    
    # Update statistics
    await webhook_service.update_webhook(webhook_id, {
        "statistics.total_received": webhook["statistics"]["total_received"] + 1,
        "statistics.last_received": datetime.now()
    })
    
    return {
        "status": "received",
        "event_id": event["id"]
    }


async def process_webhook_event(webhook: Dict[str, Any], event: Dict[str, Any]):
    """Process webhook event in background"""
    try:
        # Route based on webhook type
        if webhook["type"] == "supabase":
            await process_supabase_event(webhook, event)
        elif webhook["type"] == "mattermost":
            await process_mattermost_event(webhook, event)
        elif webhook["type"] == "discord":
            await process_discord_event(webhook, event)
        else:
            await process_generic_event(webhook, event)
        
        # Notify connected clients
        await ws_manager.broadcast({
            "type": "webhook_event",
            "webhook_id": webhook["id"],
            "webhook_type": webhook["type"],
            "event": event,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error processing webhook event: {e}")
        # Update error count
        await webhook_service.update_webhook(webhook["id"], {
            "statistics.errors": webhook["statistics"]["errors"] + 1
        })


async def process_supabase_event(webhook: Dict[str, Any], event: Dict[str, Any]):
    """Process Supabase webhook event"""
    payload = event["payload"]
    
    # Extract event type and data
    event_type = payload.get("type")
    table = payload.get("table")
    record = payload.get("record")
    
    logger.info(f"Supabase event: {event_type} on {table}")
    
    # Process based on event type
    if event_type == "INSERT":
        # Handle new record
        pass
    elif event_type == "UPDATE":
        # Handle updated record
        pass
    elif event_type == "DELETE":
        # Handle deleted record
        pass


async def process_mattermost_event(webhook: Dict[str, Any], event: Dict[str, Any]):
    """Process Mattermost webhook event"""
    payload = event["payload"]
    
    # Extract message data
    post = payload.get("post")
    user = payload.get("user")
    channel = payload.get("channel")
    
    logger.info(f"Mattermost message from {user} in {channel}")
    
    # Could trigger AI response if mentioned
    # This would integrate with the chat service


async def process_discord_event(webhook: Dict[str, Any], event: Dict[str, Any]):
    """Process Discord webhook event"""
    # Discord webhooks are typically outgoing only
    # This would be used for sending notifications to Discord
    pass


async def process_generic_event(webhook: Dict[str, Any], event: Dict[str, Any]):
    """Process generic webhook event"""
    # Generic processing logic
    logger.info(f"Generic webhook event received: {event['id']}")


@router.post("/{webhook_id}/test")
async def test_webhook(webhook_id: str):
    """Send a test event to a webhook"""
    webhook = await webhook_service.get_webhook(webhook_id)
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Create test event
    test_event = {
        "id": str(uuid.uuid4()),
        "type": "test",
        "webhook_id": webhook_id,
        "timestamp": datetime.now(),
        "message": "This is a test event from Olympian AI"
    }
    
    # Send test based on webhook type
    result = await webhook_service.send_test_event(webhook, test_event)
    
    return {
        "status": "sent" if result else "failed",
        "test_event": test_event
    }


@router.get("/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: str,
    limit: int = 50,
    offset: int = 0
):
    """Get webhook event logs"""
    logs = await webhook_service.get_webhook_logs(webhook_id, limit, offset)
    
    return {
        "logs": logs,
        "total": len(logs),
        "limit": limit,
        "offset": offset
    }