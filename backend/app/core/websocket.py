"""WebSocket Manager - Real-time Divine Communication"""
import json
import asyncio
from typing import Dict, Set, Any, Optional
from datetime import datetime
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from .config import settings
from .service_manager import get_ollama_service, get_mcp_service, get_project_service


def safe_model_dump(obj):
    """Safely get dict representation of Pydantic model or return dict as-is"""
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    elif isinstance(obj, dict):
        return obj
    else:
        return {}


class WebSocketManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.active_streams: Dict[str, asyncio.Task] = {}  # Track active streaming tasks
        
        self._message_handlers = {
            "chat": self._handle_chat_message,
            "stop_generation": self._handle_stop_generation,
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
            "active_model": None,
            "is_streaming": False
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
            # Cancel any active streams for this client
            if client_id in self.active_streams:
                self.active_streams[client_id].cancel()
                del self.active_streams[client_id]
            
            del self.active_connections[client_id]
            del self.connection_metadata[client_id]
            logger.info(f"🌙 Divine connection closed: {client_id}")
    
    async def disconnect_all(self):
        """Disconnect all active connections"""
        # Cancel all active streams
        for task in self.active_streams.values():
            task.cancel()
        self.active_streams.clear()
        
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
        # Check if already streaming
        if self.connection_metadata[client_id].get("is_streaming"):
            await self.send_error(client_id, "Already processing a message. Please wait or stop the current generation.")
            return
        
        content = message.get("content", "")
        model = message.get("model") or self.connection_metadata[client_id].get("active_model")
        project_id = message.get("project_id") or self.connection_metadata[client_id].get("project_id")
        system_prompt = message.get("system_prompt")
        
        logger.info(f"💬 Chat message from {client_id}: model={model}, content_length={len(content)}")
        
        if not model:
            await self.send_error(client_id, "No model selected")
            return
        
        ollama_service = get_ollama_service()
        if not ollama_service:
            await self.send_error(client_id, "Ollama service not available")
            return
        
        # Create and start streaming task
        stream_task = asyncio.create_task(
            self._stream_chat_response(client_id, model, content, system_prompt, project_id)
        )
        self.active_streams[client_id] = stream_task
        self.connection_metadata[client_id]["is_streaming"] = True
        
        try:
            await stream_task
        except asyncio.CancelledError:
            logger.info(f"🛑 Chat stream cancelled for {client_id}")
            await self.send_message(client_id, {
                "type": "chat_response",
                "streaming": False,
                "cancelled": True,
                "timestamp": datetime.now().isoformat()
            })
        finally:
            # Clean up
            if client_id in self.active_streams:
                del self.active_streams[client_id]
            self.connection_metadata[client_id]["is_streaming"] = False
    
    async def _stream_chat_response(self, client_id: str, model: str, content: str, system_prompt: Optional[str], project_id: Optional[str]):
        """Stream chat response from Ollama"""
        ollama_service = get_ollama_service()
        
        # Send typing indicator
        await self.send_message(client_id, {
            "type": "chat_status",
            "status": "typing",
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            logger.info(f"🔮 Starting chat stream for {client_id} with model {model}")
            
            response_chunks = []
            async for chunk in ollama_service.stream_chat(
                model=model, 
                message=content, 
                system_prompt=system_prompt,
                project_id=project_id
            ):
                # This will raise CancelledError if cancelled - no need to check manually
                response_chunks.append(chunk)
                await self.send_message(client_id, {
                    "type": "chat_response",
                    "content": chunk,
                    "model": model,
                    "streaming": True,
                    "can_stop": True,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Send completion message (only if not cancelled)
            await self.send_message(client_id, {
                "type": "chat_response",
                "streaming": False,
                "complete": True,
                "total_chunks": len(response_chunks),
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"✅ Chat stream completed for {client_id}: {len(response_chunks)} chunks")
        
        except asyncio.CancelledError:
            # Re-raise cancellation to be handled by caller
            logger.info(f"🛑 Stream generation cancelled for {client_id}")
            raise
        except Exception as e:
            logger.error(f"❌ Error in chat stream for {client_id}: {e}")
            await self.send_error(client_id, f"Chat error: {str(e)}")
    
    async def _handle_stop_generation(self, client_id: str, message: Dict[str, Any]):
        """Handle stop generation requests"""
        logger.info(f"🛑 Stop generation requested by {client_id}")
        
        if client_id in self.active_streams:
            # Cancel the active stream
            self.active_streams[client_id].cancel()
            logger.info(f"🛑 Cancelled active stream for {client_id}")
            
            await self.send_message(client_id, {
                "type": "generation_stopped",
                "message": "Generation stopped by user",
                "timestamp": datetime.now().isoformat()
            })
        else:
            await self.send_message(client_id, {
                "type": "generation_stopped",
                "message": "No active generation to stop",
                "timestamp": datetime.now().isoformat()
            })
    
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
            if isinstance(settings.user_preferences, dict):
                from .config import UserPreferences
                settings.user_preferences = UserPreferences(**settings.user_preferences)
            
            settings.user_preferences.preferred_models = config_data.get("preferred_models", [])
            settings.user_preferences.custom_endpoints = config_data.get("custom_endpoints", [])
            settings.save_config()
            
            await self.send_message(client_id, {
                "type": "config_updated",
                "config_type": "preferences",
                "data": safe_model_dump(settings.user_preferences),
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
                "data": settings.discovered_services,
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
        mcp_service = get_mcp_service()
        
        if generation_type == "image":
            # Image generation logic
            pass
        elif generation_type == "code":
            # Code generation with MCP tools
            if mcp_service and mcp_service.is_connected():
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
                "active_streams": len(self.active_streams),
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
                "discovered_services": settings.discovered_services,
                "user_preferences": safe_model_dump(settings.user_preferences),
                "active_services": settings.get_active_services(),
                "features": {
                    "can_stop_generation": True,
                    "streaming_chat": True
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await websocket.send_json(welcome_data)
            logger.info(f"📨 Welcome message sent to {client_id}")
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
    
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
    
    def get_client_stream_status(self, client_id: str) -> Dict[str, Any]:
        """Get streaming status for a client"""
        return {
            "is_streaming": self.connection_metadata.get(client_id, {}).get("is_streaming", False),
            "has_active_stream": client_id in self.active_streams
        }
    
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


# Global WebSocket manager instance
ws_manager = WebSocketManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """WebSocket endpoint for real-time communication"""
    actual_client_id = None
    try:
        # Connect the client
        actual_client_id = await ws_manager.connect(websocket, client_id)
        logger.info(f"WebSocket connected: {actual_client_id}")
        
        # Handle messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                logger.debug(f"📨 Received message from {actual_client_id}: {message.get('type', 'unknown')}")
                
                # Handle the message
                await ws_manager.handle_message(websocket, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client {actual_client_id} disconnected normally")
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from client {actual_client_id}")
                if actual_client_id:
                    await ws_manager.send_error(actual_client_id, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error handling message from {actual_client_id}: {e}")
                if actual_client_id:
                    await ws_manager.send_error(actual_client_id, f"Message handling error: {str(e)}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        # Try to send error if connection was established
        if actual_client_id:
            try:
                await ws_manager.send_error(actual_client_id, f"Connection error: {str(e)}")
            except:
                pass
    
    finally:
        # Disconnect the client
        if actual_client_id:
            ws_manager.disconnect(websocket)
        else:
            # If we never got a client ID, just close the connection
            try:
                await websocket.close()
            except:
                pass