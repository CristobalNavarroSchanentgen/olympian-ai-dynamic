"""Webhook Service - Divine Event Management"""
import asyncio
from typing import Dict, List, Any, Optional
import httpx
import secrets
import json
from datetime import datetime
from loguru import logger

from ..core.config import settings


class WebhookService:
    """Service for managing webhooks and event processing"""
    
    def __init__(self):
        self._webhooks: Dict[str, Dict[str, Any]] = {}
        self._event_logs: Dict[str, List[Dict[str, Any]]] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """Initialize webhook service"""
        self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        
        # Load webhooks from configuration
        # In production, this would load from database
        logger.info("Webhook service initialized")
    
    def generate_secret(self) -> str:
        """Generate a secure webhook secret"""
        return secrets.token_urlsafe(32)
    
    async def register_webhook(self, webhook_config: Dict[str, Any]) -> bool:
        """Register a new webhook"""
        webhook_id = webhook_config["id"]
        
        try:
            # Store webhook configuration
            self._webhooks[webhook_id] = webhook_config
            
            # Initialize event log
            self._event_logs[webhook_id] = []
            
            # Register with external service if needed
            if webhook_config["type"] == "supabase":
                await self._register_supabase_webhook(webhook_config)
            elif webhook_config["type"] == "mattermost":
                await self._register_mattermost_webhook(webhook_config)
            
            logger.info(f"Webhook registered: {webhook_id} ({webhook_config['type']})")
            return True
        
        except Exception as e:
            logger.error(f"Failed to register webhook: {e}")
            return False
    
    async def _register_supabase_webhook(self, config: Dict[str, Any]):
        """Register webhook with Supabase"""
        # Implementation would use Supabase admin API
        # to register the webhook endpoint
        pass
    
    async def _register_mattermost_webhook(self, config: Dict[str, Any]):
        """Register webhook with Mattermost"""
        # Implementation would use Mattermost API
        # to create incoming/outgoing webhook
        pass
    
    async def list_webhooks(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all webhooks"""
        webhooks = list(self._webhooks.values())
        
        if active_only:
            webhooks = [w for w in webhooks if w.get("active", False)]
        
        return webhooks
    
    async def get_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook by ID"""
        return self._webhooks.get(webhook_id)
    
    async def update_webhook(
        self,
        webhook_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update webhook configuration"""
        if webhook_id not in self._webhooks:
            return None
        
        webhook = self._webhooks[webhook_id]
        
        # Handle nested updates (e.g., statistics.total_received)
        for key, value in update_data.items():
            if "." in key:
                # Nested update
                parts = key.split(".")
                current = webhook
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                webhook[key] = value
        
        return webhook
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        if webhook_id not in self._webhooks:
            return False
        
        # Unregister from external service if needed
        webhook = self._webhooks[webhook_id]
        if webhook["type"] == "supabase":
            await self._unregister_supabase_webhook(webhook)
        elif webhook["type"] == "mattermost":
            await self._unregister_mattermost_webhook(webhook)
        
        # Remove webhook
        del self._webhooks[webhook_id]
        
        # Remove logs
        if webhook_id in self._event_logs:
            del self._event_logs[webhook_id]
        
        logger.info(f"Webhook deleted: {webhook_id}")
        return True
    
    async def _unregister_supabase_webhook(self, webhook: Dict[str, Any]):
        """Unregister webhook from Supabase"""
        pass
    
    async def _unregister_mattermost_webhook(self, webhook: Dict[str, Any]):
        """Unregister webhook from Mattermost"""
        pass
    
    async def send_test_event(
        self,
        webhook: Dict[str, Any],
        test_event: Dict[str, Any]
    ) -> bool:
        """Send a test event to verify webhook configuration"""
        try:
            if webhook["type"] == "discord":
                # Send to Discord webhook
                config = webhook["config"]
                webhook_url = config.get("webhook_url")
                
                if webhook_url:
                    payload = {
                        "username": config.get("username", "Olympian AI"),
                        "avatar_url": config.get("avatar_url"),
                        "content": f"Test event from Olympian AI\n```json\n{json.dumps(test_event, indent=2)}\n```"
                    }
                    
                    response = await self._http_client.post(webhook_url, json=payload)
                    return response.status_code in [200, 204]
            
            elif webhook["type"] == "generic":
                # Send to generic webhook endpoint
                config = webhook["config"]
                url = config.get("url")
                method = config.get("method", "POST")
                headers = config.get("headers", {})
                
                if url:
                    response = await self._http_client.request(
                        method=method,
                        url=url,
                        json=test_event,
                        headers=headers
                    )
                    return response.status_code < 400
            
            # For other types, assume success for now
            return True
        
        except Exception as e:
            logger.error(f"Failed to send test event: {e}")
            return False
    
    async def log_event(
        self,
        webhook_id: str,
        event: Dict[str, Any],
        status: str = "received"
    ):
        """Log a webhook event"""
        if webhook_id not in self._event_logs:
            self._event_logs[webhook_id] = []
        
        log_entry = {
            "id": event.get("id"),
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "event_type": event.get("type"),
            "payload_size": len(json.dumps(event.get("payload", {})))
        }
        
        # Keep only last 1000 logs per webhook
        logs = self._event_logs[webhook_id]
        logs.append(log_entry)
        if len(logs) > 1000:
            self._event_logs[webhook_id] = logs[-1000:]
    
    async def get_webhook_logs(
        self,
        webhook_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get webhook event logs"""
        logs = self._event_logs.get(webhook_id, [])
        
        # Sort by timestamp (newest first)
        sorted_logs = sorted(
            logs,
            key=lambda x: x["timestamp"],
            reverse=True
        )
        
        # Paginate
        return sorted_logs[offset:offset + limit]
    
    async def process_incoming_webhook(
        self,
        webhook_id: str,
        headers: Dict[str, str],
        payload: Any
    ) -> Dict[str, Any]:
        """Process an incoming webhook event"""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return {
                "success": False,
                "error": "Webhook not found"
            }
        
        # Create event
        event = {
            "id": str(uuid.uuid4()),
            "webhook_id": webhook_id,
            "webhook_type": webhook["type"],
            "timestamp": datetime.now(),
            "headers": headers,
            "payload": payload
        }
        
        # Log event
        await self.log_event(webhook_id, event)
        
        # Process based on webhook type
        try:
            if webhook["type"] == "supabase":
                result = await self._process_supabase_event(webhook, event)
            elif webhook["type"] == "mattermost":
                result = await self._process_mattermost_event(webhook, event)
            else:
                result = await self._process_generic_event(webhook, event)
            
            return {
                "success": True,
                "event_id": event["id"],
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_supabase_event(
        self,
        webhook: Dict[str, Any],
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process Supabase webhook event"""
        payload = event["payload"]
        
        # Extract Supabase event details
        event_type = payload.get("type")
        table = payload.get("table")
        record = payload.get("record")
        old_record = payload.get("old_record")
        
        result = {
            "event_type": event_type,
            "table": table,
            "record_id": record.get("id") if record else None
        }
        
        # Trigger actions based on event type and table
        # This could trigger AI responses, notifications, etc.
        
        return result
    
    async def _process_mattermost_event(
        self,
        webhook: Dict[str, Any],
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process Mattermost webhook event"""
        payload = event["payload"]
        
        # Extract Mattermost event details
        trigger_word = payload.get("trigger_word")
        text = payload.get("text")
        user_name = payload.get("user_name")
        channel_name = payload.get("channel_name")
        
        result = {
            "trigger_word": trigger_word,
            "user": user_name,
            "channel": channel_name
        }
        
        # Could trigger AI response if mentioned
        if trigger_word and text:
            # Remove trigger word from text
            prompt = text.replace(trigger_word, "").strip()
            # This would integrate with chat service to generate response
            result["ai_response_triggered"] = True
            result["prompt"] = prompt
        
        return result
    
    async def _process_generic_event(
        self,
        webhook: Dict[str, Any],
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process generic webhook event"""
        # Generic processing - just acknowledge receipt
        return {
            "processed": True,
            "event_id": event["id"]
        }
    
    async def send_outgoing_webhook(
        self,
        webhook_type: str,
        payload: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send an outgoing webhook"""
        try:
            if webhook_type == "discord":
                # Find Discord webhook configuration
                discord_webhooks = [
                    w for w in self._webhooks.values()
                    if w["type"] == "discord" and w.get("active")
                ]
                
                if not discord_webhooks and not config:
                    logger.error("No Discord webhook configured")
                    return False
                
                webhook_config = config or discord_webhooks[0]["config"]
                webhook_url = webhook_config.get("webhook_url")
                
                if webhook_url:
                    response = await self._http_client.post(
                        webhook_url,
                        json=payload
                    )
                    return response.status_code in [200, 204]
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to send outgoing webhook: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()