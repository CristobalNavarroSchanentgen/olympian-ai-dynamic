"""Tests for WebSocket core functionality"""
import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from app.core.websocket import ConnectionManager, WebSocketHandler


@pytest.fixture
def connection_manager():
    """Create ConnectionManager instance"""
    return ConnectionManager()


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


class TestConnectionManager:
    """Test suite for ConnectionManager"""
    
    @pytest.mark.asyncio
    async def test_connect(self, connection_manager, mock_websocket):
        """Test connecting a WebSocket client"""
        client_id = "test-client-123"
        
        await connection_manager.connect(client_id, mock_websocket)
        
        assert client_id in connection_manager.active_connections
        assert connection_manager.active_connections[client_id] == mock_websocket
        mock_websocket.accept.assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_disconnect(self, connection_manager, mock_websocket):
        """Test disconnecting a WebSocket client"""
        client_id = "test-client-123"
        
        # First connect
        await connection_manager.connect(client_id, mock_websocket)
        
        # Then disconnect
        await connection_manager.disconnect(client_id)
        
        assert client_id not in connection_manager.active_connections
    
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """Test sending message to specific client"""
        client_id = "test-client-123"
        message = {"type": "chat", "content": "Hello"}
        
        await connection_manager.connect(client_id, mock_websocket)
        await connection_manager.send_personal_message(message, client_id)
        
        mock_websocket.send_json.assert_called_once_with(message)
    
    
    @pytest.mark.asyncio
    async def test_send_personal_message_disconnected(self, connection_manager):
        """Test sending message to disconnected client"""
        client_id = "non-existent"
        message = {"type": "chat", "content": "Hello"}
        
        # Should not raise exception
        await connection_manager.send_personal_message(message, client_id)
    
    
    @pytest.mark.asyncio
    async def test_broadcast(self, connection_manager):
        """Test broadcasting message to all clients"""
        # Connect multiple clients
        clients = {}
        for i in range(3):
            client_id = f"client-{i}"
            mock_ws = AsyncMock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            clients[client_id] = mock_ws
            await connection_manager.connect(client_id, mock_ws)
        
        message = {"type": "broadcast", "content": "Hello everyone"}
        await connection_manager.broadcast(message)
        
        # Verify all clients received the message
        for mock_ws in clients.values():
            mock_ws.send_json.assert_called_once_with(message)
    
    
    @pytest.mark.asyncio
    async def test_broadcast_except(self, connection_manager):
        """Test broadcasting message to all except specific client"""
        # Connect multiple clients
        clients = {}
        for i in range(3):
            client_id = f"client-{i}"
            mock_ws = AsyncMock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            clients[client_id] = mock_ws
            await connection_manager.connect(client_id, mock_ws)
        
        exclude_id = "client-1"
        message = {"type": "broadcast", "content": "Hello"}
        await connection_manager.broadcast_except(message, exclude_id)
        
        # Verify excluded client didn't receive message
        clients[exclude_id].send_json.assert_not_called()
        
        # Verify other clients received message
        for client_id, mock_ws in clients.items():
            if client_id != exclude_id:
                mock_ws.send_json.assert_called_once_with(message)
    
    
    @pytest.mark.asyncio
    async def test_send_to_group(self, connection_manager):
        """Test sending message to group of clients"""
        # Connect clients and assign to groups
        connection_manager.groups = {
            "group1": ["client-0", "client-1"],
            "group2": ["client-2"]
        }
        
        clients = {}
        for i in range(3):
            client_id = f"client-{i}"
            mock_ws = AsyncMock(spec=WebSocket)
            mock_ws.send_json = AsyncMock()
            clients[client_id] = mock_ws
            await connection_manager.connect(client_id, mock_ws)
        
        message = {"type": "group", "content": "Group message"}
        await connection_manager.send_to_group("group1", message)
        
        # Verify only group1 clients received message
        clients["client-0"].send_json.assert_called_once_with(message)
        clients["client-1"].send_json.assert_called_once_with(message)
        clients["client-2"].send_json.assert_not_called()
    
    
    def test_add_to_group(self, connection_manager):
        """Test adding client to group"""
        client_id = "test-client"
        group_name = "test-group"
        
        connection_manager.add_to_group(client_id, group_name)
        
        assert group_name in connection_manager.groups
        assert client_id in connection_manager.groups[group_name]
    
    
    def test_remove_from_group(self, connection_manager):
        """Test removing client from group"""
        client_id = "test-client"
        group_name = "test-group"
        
        connection_manager.add_to_group(client_id, group_name)
        connection_manager.remove_from_group(client_id, group_name)
        
        assert client_id not in connection_manager.groups.get(group_name, [])
    
    
    def test_get_client_groups(self, connection_manager):
        """Test getting all groups for a client"""
        client_id = "test-client"
        
        connection_manager.add_to_group(client_id, "group1")
        connection_manager.add_to_group(client_id, "group2")
        connection_manager.add_to_group("other-client", "group3")
        
        groups = connection_manager.get_client_groups(client_id)
        
        assert len(groups) == 2
        assert "group1" in groups
        assert "group2" in groups
        assert "group3" not in groups


class TestWebSocketHandler:
    """Test suite for WebSocketHandler"""
    
    @pytest.fixture
    def websocket_handler(self, mock_ollama_service):
        """Create WebSocketHandler instance"""
        return WebSocketHandler(ollama_service=mock_ollama_service)
    
    
    @pytest.mark.asyncio
    async def test_handle_chat_message(self, websocket_handler, mock_websocket):
        """Test handling chat message"""
        client_id = "test-client"
        message = {
            "type": "chat",
            "data": {
                "message": "Hello",
                "model": "llama2:7b",
                "conversation_id": "conv-123"
            }
        }
        
        # Mock streaming response
        async def mock_stream():
            yield "Hello "
            yield "there!"
        
        websocket_handler.ollama_service.stream_chat = Mock(return_value=mock_stream())
        
        await websocket_handler.handle_message(client_id, message, mock_websocket)
        
        # Verify streaming responses were sent
        assert mock_websocket.send_json.call_count >= 2
    
    
    @pytest.mark.asyncio
    async def test_handle_model_list(self, websocket_handler, mock_websocket):
        """Test handling model list request"""
        client_id = "test-client"
        message = {"type": "model_list"}
        
        websocket_handler.ollama_service.list_models = AsyncMock(return_value=[
            {"name": "llama2:7b"},
            {"name": "mistral:7b"}
        ])
        
        await websocket_handler.handle_message(client_id, message, mock_websocket)
        
        # Verify models were sent
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "model_list"
        assert len(call_args["data"]["models"]) == 2
    
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat(self, websocket_handler, mock_websocket):
        """Test handling heartbeat/ping message"""
        client_id = "test-client"
        message = {"type": "ping"}
        
        await websocket_handler.handle_message(client_id, message, mock_websocket)
        
        # Verify pong was sent
        mock_websocket.send_json.assert_called_once_with({"type": "pong"})
    
    
    @pytest.mark.asyncio
    async def test_handle_error(self, websocket_handler, mock_websocket):
        """Test error handling in message processing"""
        client_id = "test-client"
        message = {
            "type": "chat",
            "data": {"message": "Hello"}  # Missing required fields
        }
        
        websocket_handler.ollama_service.stream_chat = Mock(
            side_effect=Exception("Test error")
        )
        
        await websocket_handler.handle_message(client_id, message, mock_websocket)
        
        # Verify error was sent
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert "Test error" in call_args["data"]["message"]
    
    
    @pytest.mark.asyncio
    async def test_handle_join_group(self, websocket_handler, mock_websocket, connection_manager):
        """Test handling group join request"""
        client_id = "test-client"
        message = {
            "type": "join_group",
            "data": {"group": "project-123"}
        }
        
        websocket_handler.connection_manager = connection_manager
        await websocket_handler.handle_message(client_id, message, mock_websocket)
        
        # Verify client was added to group
        assert client_id in connection_manager.groups.get("project-123", [])
    
    
    @pytest.mark.asyncio
    async def test_handle_leave_group(self, websocket_handler, mock_websocket, connection_manager):
        """Test handling group leave request"""
        client_id = "test-client"
        group_name = "project-123"
        
        # First add to group
        connection_manager.add_to_group(client_id, group_name)
        
        message = {
            "type": "leave_group",
            "data": {"group": group_name}
        }
        
        websocket_handler.connection_manager = connection_manager
        await websocket_handler.handle_message(client_id, message, mock_websocket)
        
        # Verify client was removed from group
        assert client_id not in connection_manager.groups.get(group_name, [])
    
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect_handling(self, websocket_handler, mock_websocket):
        """Test handling WebSocket disconnection"""
        client_id = "test-client"
        
        # Simulate disconnection during receive
        mock_websocket.receive_text.side_effect = WebSocketDisconnect()
        
        with pytest.raises(WebSocketDisconnect):
            await websocket_handler.handle_connection(client_id, mock_websocket)
    
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(self, connection_manager):
        """Test handling multiple concurrent connections"""
        import asyncio
        
        async def connect_client(client_id):
            mock_ws = AsyncMock(spec=WebSocket)
            await connection_manager.connect(client_id, mock_ws)
            return mock_ws
        
        # Connect multiple clients concurrently
        tasks = [connect_client(f"client-{i}") for i in range(10)]
        await asyncio.gather(*tasks)
        
        assert len(connection_manager.active_connections) == 10
