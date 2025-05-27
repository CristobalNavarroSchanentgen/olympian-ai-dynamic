"""Test chat API endpoints"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from fastapi.testclient import TestClient
import json


class TestChatAPI:
    """Test cases for Chat API"""

    def test_send_chat_message_new_conversation(self, client, mock_ollama_service, mock_conversations):
        """Test sending a chat message without conversation ID (creates new conversation)"""
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            async def mock_stream():
                yield "Hello there!"
            
            mock_ollama_service.stream_chat = Mock(return_value=mock_stream())
            
            response = client.post("/api/chat/message", json={
                "message": "Hello",
                "model": "llama2:7b",
                "stream": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "conversation_id" in data
            assert data["message"]["content"] == "Hello there!"
            assert data["message"]["role"] == "assistant"

    def test_send_chat_message_existing_conversation(self, client, mock_ollama_service, mock_conversations):
        """Test sending a chat message to existing conversation"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "model": "llama2:7b",
            "messages": [{"role": "user", "content": "Previous message"}]
        }
        
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            async def mock_stream():
                yield "Response to existing conversation"
            
            mock_ollama_service.stream_chat = Mock(return_value=mock_stream())
            
            response = client.post("/api/chat/message", json={
                "message": "Hello again",
                "model": "llama2:7b",
                "conversation_id": conv_id,
                "stream": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == conv_id
            assert data["message"]["content"] == "Response to existing conversation"

    def test_send_chat_message_streaming(self, client, mock_ollama_service):
        """Test sending a chat message with streaming enabled"""
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            response = client.post("/api/chat/message", json={
                "message": "Hello",
                "model": "llama2:7b",
                "stream": True
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["streaming"] is True
            assert "conversation_id" in data

    def test_send_chat_message_no_service(self, client):
        """Test sending a chat message when Ollama service is not available"""
        with patch('app.api.chat.get_ollama_service', return_value=None):
            response = client.post("/api/chat/message", json={
                "message": "Hello",
                "model": "llama2:7b"
            })
            
            assert response.status_code == 503
            assert "Ollama service not available" in response.json()["detail"]

    def test_send_chat_message_invalid_conversation(self, client, mock_ollama_service):
        """Test sending a chat message to non-existent conversation"""
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            response = client.post("/api/chat/message", json={
                "message": "Hello",
                "model": "llama2:7b",
                "conversation_id": "non-existent"
            })
            
            assert response.status_code == 404
            assert "Conversation not found" in response.json()["detail"]

    def test_create_conversation(self, client):
        """Test creating a new conversation"""
        response = client.post("/api/chat/conversations", json={
            "title": "Test Conversation",
            "model": "llama2:7b"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert data["model"] == "llama2:7b"
        assert "id" in data
        assert data["messages"] == []

    def test_list_conversations(self, client, mock_conversations):
        """Test listing conversations"""
        # Add some test conversations
        mock_conversations["conv1"] = {
            "id": "conv1",
            "title": "Conversation 1",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "model": "llama2:7b",
            "messages": []
        }
        mock_conversations["conv2"] = {
            "id": "conv2", 
            "title": "Conversation 2",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "model": "llama2:13b",
            "messages": []
        }
        
        response = client.get("/api/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert data["total"] == 2

    def test_list_conversations_with_pagination(self, client, mock_conversations):
        """Test listing conversations with pagination"""
        # Add test conversations
        for i in range(5):
            mock_conversations[f"conv{i}"] = {
                "id": f"conv{i}",
                "title": f"Conversation {i}",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "model": "llama2:7b",
                "messages": []
            }
        
        response = client.get("/api/chat/conversations?limit=2&offset=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["conversations"]) <= 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 1

    def test_get_conversation(self, client, mock_conversations):
        """Test getting a specific conversation"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "title": "Test Conversation",
            "model": "llama2:7b",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        response = client.get(f"/api/chat/conversations/{conv_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert data["title"] == "Test Conversation"
        assert len(data["messages"]) == 1

    def test_get_conversation_not_found(self, client):
        """Test getting a non-existent conversation"""
        response = client.get("/api/chat/conversations/non-existent")
        
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    def test_delete_conversation(self, client, mock_conversations):
        """Test deleting a conversation"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "title": "Test Conversation",
            "model": "llama2:7b",
            "messages": []
        }
        
        response = client.delete(f"/api/chat/conversations/{conv_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["conversation_id"] == conv_id
        assert conv_id not in mock_conversations

    def test_update_conversation(self, client, mock_conversations):
        """Test updating conversation metadata"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "title": "Old Title",
            "model": "llama2:7b",
            "messages": [],
            "created_at": datetime.now()
        }
        
        response = client.put(f"/api/chat/conversations/{conv_id}?title=New Title")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["id"] == conv_id

    def test_clear_conversation(self, client, mock_conversations):
        """Test clearing all messages from a conversation"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "title": "Test Conversation",
            "model": "llama2:7b",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        
        response = client.post(f"/api/chat/conversations/{conv_id}/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"
        assert data["conversation_id"] == conv_id
        assert len(mock_conversations[conv_id]["messages"]) == 0

    def test_fork_conversation(self, client, mock_conversations):
        """Test forking a conversation"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "title": "Original Conversation",
            "model": "llama2:7b",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        
        response = client.post(f"/api/chat/conversations/{conv_id}/fork")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Original Conversation (Fork)"
        assert data["model"] == "llama2:7b"
        assert data["forked_from"] == conv_id
        assert len(data["messages"]) == 2

    def test_fork_conversation_from_index(self, client, mock_conversations):
        """Test forking a conversation from a specific message index"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "title": "Original Conversation",
            "model": "llama2:7b",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"},
                {"role": "assistant", "content": "I'm good!"}
            ]
        }
        
        response = client.post(f"/api/chat/conversations/{conv_id}/fork?from_message_index=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2  # Only first 2 messages

    def test_get_recommended_models(self, client):
        """Test getting recommended models"""
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.total = 16 * (1024**3)  # 16GB
            
            with patch('app.core.config.settings') as mock_settings:
                mock_settings.discovered_services = {
                    "ollama": {
                        "models": [
                            {"name": "llama2:7b"},
                            {"name": "llama2:13b"},
                            {"name": "phi:3b"}
                        ]
                    }
                }
                
                response = client.get("/api/chat/models/recommended")
                
                assert response.status_code == 200
                data = response.json()
                assert "recommendations" in data
                assert "system_memory_gb" in data
                assert data["system_memory_gb"] == 16.0

    def test_regenerate_last_response(self, client, mock_ollama_service, mock_conversations):
        """Test regenerating the last assistant response"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "model": "llama2:7b",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            async def mock_stream():
                yield "Regenerated response"
            
            mock_ollama_service.stream_chat = Mock(return_value=mock_stream())
            
            # Fix: Use correct endpoint path with /api/chat prefix
            response = client.post(f"/api/chat/regenerate/{conv_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "regenerated"
            assert data["message"]["content"] == "Regenerated response"
            assert data["message"]["metadata"]["regenerated"] is True
