"""Tests for WebSocket core functionality"""
import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from app.core.websocket import WebSocketManager, ws_manager


@pytest.fixture
def websocket_manager():
    """Create WebSocketManager instance"""
    return WebSocketManager()


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket"""
    mock = AsyncMock(spec=WebSocket)
    mock.accept = AsyncMock()
    mock.send_text = AsyncMock()
    mock.send_json = AsyncMock()
    mock.receive_text = AsyncMock()
    mock.receive_json = AsyncMock()
    mock.close = AsyncMock()
    return mock


class TestWebSocketManager:
    """Test suite for WebSocketManager"""
    
    @pytest.mark.asyncio
    async def test_connect(self, websocket_manager, mock_websocket):
        """Test connecting a WebSocket client"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client-123")
        
        assert client_id in websocket_manager.active_connections
        assert websocket_manager.active_connections[client_id] == mock_websocket
        mock_websocket.accept.assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_disconnect(self, websocket_manager, mock_websocket):
        """Test disconnecting a WebSocket client"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client-123")
        
        # Then disconnect
        websocket_manager.disconnect(mock_websocket)
        
        assert client_id not in websocket_manager.active_connections
    
    
    @pytest.mark.asyncio
    async def test_send_message(self, websocket_manager, mock_websocket):
        """Test sending message to specific client"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client-123")
        message = {"type": "chat", "content": "Hello"}
        
        await websocket_manager.send_message(client_id, message)
        
        mock_websocket.send_json.assert_called_once_with(message)
    
    
    @pytest.mark.asyncio
    async def test_send_message_disconnected(self, websocket_manager):
        """Test sending message to disconnected client"""
        client_id = "non-existent"
        message = {"type": "chat", "content": "Hello"}
        
        # Should not raise exception
        await websocket_manager.send_message(client_id, message)
    
    
    @pytest.mark.asyncio
    async def test_broadcast(self, websocket_manager):
        """Test broadcasting message to all clients"""
        # Connect multiple clients
        clients = {}
        for i in range(3):
            mock_ws = AsyncMock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            client_id = await websocket_manager.connect(mock_ws, f"client-{i}")
            clients[client_id] = mock_ws
        
        message = {"type": "broadcast", "content": "Hello everyone"}
        await websocket_manager.broadcast(message)
        
        # Verify all clients received the message
        for mock_ws in clients.values():
            mock_ws.send_json.assert_called_once_with(message)
    
    
    @pytest.mark.asyncio
    async def test_broadcast_exclude(self, websocket_manager):
        """Test broadcasting message to all except specific clients"""
        # Connect multiple clients
        clients = {}
        client_ids = []
        for i in range(3):
            mock_ws = AsyncMock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            client_id = await websocket_manager.connect(mock_ws, f"client-{i}")
            clients[client_id] = mock_ws
            client_ids.append(client_id)
        
        exclude_id = client_ids[1]
        message = {"type": "broadcast", "content": "Hello"}
        await websocket_manager.broadcast(message, exclude={exclude_id})
        
        # Verify excluded client didn't receive message
        clients[exclude_id].send_json.assert_not_called()
        
        # Verify other clients received message
        for client_id, mock_ws in clients.items():
            if client_id != exclude_id:
                mock_ws.send_json.assert_called_once_with(message)
    
    
    @pytest.mark.asyncio
    async def test_handle_message(self, websocket_manager, mock_websocket):
        """Test handling incoming messages"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client-123")
        
        # Test ping message
        message = {"type": "ping"}
        await websocket_manager.handle_message(mock_websocket, message)
        
        # Should handle without errors
        assert True
    
    
    @pytest.mark.asyncio
    async def test_send_error(self, websocket_manager, mock_websocket):
        """Test sending error message"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client-123")
        
        await websocket_manager.send_error(client_id, "Test error")
        
        # Verify error message was sent
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["message"] == "Test error"
    
    
    @pytest.mark.asyncio
    async def test_disconnect_all(self, websocket_manager):
        """Test disconnecting all clients"""
        # Connect multiple clients
        for i in range(3):
            mock_ws = AsyncMock(spec=WebSocket)
            await websocket_manager.connect(mock_ws, f"client-{i}")
        
        await websocket_manager.disconnect_all()
        
        assert len(websocket_manager.active_connections) == 0
    
    
    def test_get_client_stream_status(self, websocket_manager):
        """Test getting client stream status"""
        client_id = "test-client"
        
        status = websocket_manager.get_client_stream_status(client_id)
        
        assert "is_streaming" in status
        assert "has_active_stream" in status
        assert status["is_streaming"] is False
        assert status["has_active_stream"] is False
    
    
    @pytest.mark.asyncio
    async def test_notify_service_update(self, websocket_manager):
        """Test service update notifications"""
        # Connect a client first
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        await websocket_manager.connect(mock_ws, "test-client")
        
        await websocket_manager.notify_service_update("ollama", "connected", {"models": 5})
        
        # Verify notification was broadcast
        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "service_update"
        assert call_args["service_type"] == "ollama"
        assert call_args["status"] == "connected"
    
    
    @pytest.mark.asyncio
    async def test_notify_config_change(self, websocket_manager):
        """Test configuration change notifications"""
        # Connect a client first
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        await websocket_manager.connect(mock_ws, "test-client")
        
        await websocket_manager.notify_config_change("model", {"selected": "llama2:7b"})
        
        # Verify notification was broadcast
        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "config_change"
        assert call_args["config_type"] == "model"
    
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect_handling(self, websocket_manager, mock_websocket):
        """Test handling WebSocket disconnection"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client")
        
        # Simulate disconnection during receive
        mock_websocket.receive_text.side_effect = WebSocketDisconnect()
        
        with pytest.raises(WebSocketDisconnect):
            # This would be called in the actual websocket endpoint
            data = await mock_websocket.receive_text()
    
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, websocket_manager):
        """Test handling multiple concurrent connections"""
        import asyncio
        
        async def connect_client(i):
            mock_ws = AsyncMock(spec=WebSocket)
            client_id = await websocket_manager.connect(mock_ws, f"client-{i}")
            return client_id
        
        # Connect multiple clients concurrently
        tasks = [connect_client(i) for i in range(10)]
        client_ids = await asyncio.gather(*tasks)
        
        assert len(websocket_manager.active_connections) == 10
        assert len(client_ids) == 10


class TestWebSocketEndpoint:
    """Test suite for WebSocket endpoint functionality"""
    
    @pytest.mark.asyncio
    async def test_chat_message_handling(self, websocket_manager, mock_websocket):
        """Test handling chat messages"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client")
        
        message = {
            "type": "chat",
            "content": "Hello AI",
            "model": "llama2:7b"
        }
        
        # Mock the message handling
        with patch.object(websocket_manager, '_handle_chat_message') as mock_handler:
            await websocket_manager.handle_message(mock_websocket, message)
            # The actual implementation would call the handler
    
    
    @pytest.mark.asyncio
    async def test_stop_generation_handling(self, websocket_manager, mock_websocket):
        """Test stopping generation"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client")
        
        message = {"type": "stop_generation"}
        
        await websocket_manager.handle_message(mock_websocket, message)
        
        # Should handle without errors
        assert True
    
    
    @pytest.mark.asyncio
    async def test_config_update_handling(self, websocket_manager, mock_websocket):
        """Test configuration updates"""
        client_id = await websocket_manager.connect(mock_websocket, "test-client")
        
        message = {
            "type": "config_update",
            "config_type": "model",
            "data": {"model": "mistral:7b"}
        }
        
        await websocket_manager.handle_message(mock_websocket, message)
        
        # Should handle without errors
        assert True
