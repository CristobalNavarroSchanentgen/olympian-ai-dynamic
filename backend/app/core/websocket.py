"""WebSocket Manager - Real-time Divine Communication"""
import json
import asyncio
from typing import Dict, Set, Any, Optional
from datetime import datetime
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from .config import settings
from ..services.ollama_service import OllamaService
from ..services.mcp_service import MCPService


class WebSocketManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.ollama_service = OllamaService()
        self.mcp_service = MCPService()
        self._message_handlers = {
            "chat": self._handle_chat_message,
            "config_update": self._handle_config_update,
            "service_discovery": self._handle_service_discovery,
            "project": self._handle_project_message,
            "generation": self._handle_generation_request,
            "system": self._handle_system_message
        }
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "project_id": None,
            "active_model": None
        }
        
        # Send welcome message with configuration
        await self._send_welcome_message(websocket, client_id)
        
        logger.info(f"✨ New divine connection established: {client_id}")
        return client_id
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        client_id = None
        for cid, ws in self.active_connections.items():
            if ws == websocket:
                client_id = cid
                break
        
        if client_id:
            del self.active_connections[client_id]
            del self.connection_metadata[client_id]
            logger.info(f"🌙 Divine connection closed: {client_id}")
    
    async def disconnect_all(self):
        """Disconnect all active connections"""
        for client_id in list(self.active_connections.keys()):
            websocket = self.active_connections[client_id]
            await websocket.close()
            del self.active_connections[client_id]
            del self.connection_metadata[client_id]
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Route incoming messages to appropriate handlers"""
        client_id = self._get_client_id(websocket)
        if not client_id:
            logger.error("Received message from unknown client")
            return
        
        # Update last activity
        self.connection_metadata[client_id]["last_activity"] = datetime.now()
        
        message_type = message.get("type")
        handler = self._message_handlers.get(message_type)
        
        if handler:
            try:
                await handler(client_id, message)
            except Exception as e:
                logger.error(f"Error handling message type {message_type}: {e}")
                await self.send_error(client_id, str(e))
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await self.send_error(client_id, f"Unknown message type: {message_type}")
    
    async def _handle_chat_message(self, client_id: str, message: Dict[str, Any]):
        """Handle chat messages"""
        content = message.get("content", "")
        model = message.get("model") or self.connection_metadata[client_id].get("active_model")
        project_id = message.get("project_id") or self.connection_metadata[client_id].get("project_id")
        
        if not model:
            await self.send_error(client_id, "No model selected")
            return
        
        # Send typing indicator
        await self.send_message(client_id, {
            "type": "chat_status",
            "status": "typing",
            "timestamp": datetime.now().isoformat()
        })
        
        # Stream response from Ollama
        try:
            async for chunk in self.ollama_service.stream_chat(model, content, project_id=project_id):
                await self.send_message(client_id, {
                    "type": "chat_response",
                    "content": chunk,
                    "model": model,
                    "streaming": True,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Send completion message
            await self.send_message(client_id, {
                "type": "chat_response",
                "streaming": False,
                "complete": True,
                "timestamp": datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error in chat handler: {e}")
            await self.send_error(client_id, f"Chat error: {str(e)}")
    
    async def _handle_config_update(self, client_id: str, message: Dict[str, Any]):
        """Handle configuration updates"""
        config_type = message.get("config_type")
        config_data = message.get("data")
        
        if config_type == "model":
            self.connection_metadata[client_id]["active_model"] = config_data.get("model")
            await self.send_message(client_id, {
                "type": "config_updated",
                "config_type": "model",
                "data": config_data,
                "timestamp": datetime.now().isoformat()
            })
        
        elif config_type == "project":
            self.connection_metadata[client_id]["project_id"] = config_data.get("project_id")
            await self.send_message(client_id, {
                "type": "config_updated",
                "config_type": "project",
                "data": config_data,
                "timestamp": datetime.now().isoformat()
            })
        
        elif config_type == "preferences":
            # Update user preferences
            settings.user_preferences.preferred_models = config_data.get("preferred_models", [])
            settings.user_preferences.custom_endpoints = config_data.get("custom_endpoints", [])
            settings.save_config()
            
            await self.send_message(client_id, {
                "type": "config_updated",
                "config_type": "preferences",
                "data": settings.user_preferences.dict(),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_service_discovery(self, client_id: str, message: Dict[str, Any]):
        """Handle service discovery requests"""
        action = message.get("action")
        
        if action == "scan":
            # Trigger a service scan
            await self.send_message(client_id, {
                "type": "discovery_status",
                "status": "scanning",
                "timestamp": datetime.now().isoformat()
            })
            
            # The actual scan will be handled by the discovery engine
            # This just notifies the client
            await self.send_message(client_id, {
                "type": "discovery_status",
                "status": "complete",
                "timestamp": datetime.now().isoformat()
            })
        
        elif action == "get_services":
            # Send current discovered services
            await self.send_message(client_id, {
                "type": "discovered_services",
                "data": settings.discovered_services.dict(),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_project_message(self, client_id: str, message: Dict[str, Any]):
        """Handle project-related messages"""
        action = message.get("action")
        project_data = message.get("data", {})
        
        if action == "create":
            # Create new project
            project_id = str(uuid.uuid4())
            # Project creation logic would go here
            
            await self.send_message(client_id, {
                "type": "project_created",
                "project_id": project_id,
                "data": project_data,
                "timestamp": datetime.now().isoformat()
            })
        
        elif action == "switch":
            # Switch to different project
            project_id = project_data.get("project_id")
            self.connection_metadata[client_id]["project_id"] = project_id
            
            await self.send_message(client_id, {
                "type": "project_switched",
                "project_id": project_id,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_generation_request(self, client_id: str, message: Dict[str, Any]):
        """Handle content generation requests"""
        generation_type = message.get("generation_type")
        params = message.get("params", {})
        
        await self.send_message(client_id, {
            "type": "generation_started",
            "generation_type": generation_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Route to appropriate generation service
        if generation_type == "image":
            # Image generation logic
            pass
        elif generation_type == "code":
            # Code generation with MCP tools
            if self.mcp_service.is_connected():
                # Use MCP for code generation
                pass
        elif generation_type == "audio":
            # Audio generation logic
            pass
        
        # For now, send a placeholder response
        await asyncio.sleep(2)  # Simulate generation time
        
        await self.send_message(client_id, {
            "type": "generation_complete",
            "generation_type": generation_type,
            "result": {
                "status": "success",
                "message": f"{generation_type} generation completed"
            },
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_system_message(self, client_id: str, message: Dict[str, Any]):
        """Handle system-related messages"""
        action = message.get("action")
        
        if action == "get_stats":
            # Send system statistics
            stats = {
                "connected_clients": len(self.active_connections),
                "active_services": settings.get_active_services(),
                "uptime": "calculating...",  # Would calculate actual uptime
                "timestamp": datetime.now().isoformat()
            }
            
            await self.send_message(client_id, {
                "type": "system_stats",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _send_welcome_message(self, websocket: WebSocket, client_id: str):
        """Send welcome message with initial configuration"""
        welcome_data = {
            "type": "welcome",
            "client_id": client_id,
            "message": "Welcome to Olympian AI - The Divine Interface",
            "config": {
                "discovered_services": settings.discovered_services.dict(),
                "user_preferences": settings.user_preferences.dict(),
                "active_services": settings.get_active_services()
            },
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send_json(welcome_data)
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast message to all connected clients"""
        exclude = exclude or set()
        
        for client_id, websocket in self.active_connections.items():
            if client_id not in exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    self.disconnect(websocket)
    
    async def send_error(self, client_id: str, error_message: str):
        """Send error message to client"""
        await self.send_message(client_id, {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def _get_client_id(self, websocket: WebSocket) -> Optional[str]:
        """Get client ID from websocket"""
        for client_id, ws in self.active_connections.items():
            if ws == websocket:
                return client_id
        return None
    
    async def notify_service_update(self, service_type: str, status: str, details: Dict[str, Any]):
        """Notify all clients about service updates"""
        await self.broadcast({
            "type": "service_update",
            "service_type": service_type,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def notify_config_change(self, config_type: str, config_data: Dict[str, Any]):
        """Notify all clients about configuration changes"""
        await self.broadcast({
            "type": "config_change",
            "config_type": config_type,
            "data": config_data,
            "timestamp": datetime.now().isoformat()
        })