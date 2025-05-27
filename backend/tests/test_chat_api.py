"""Tests for Chat API endpoints"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.chat import router, conversations


@pytest.fixture
def app():
    """Create FastAPI app with chat router"""
    app = FastAPI()
    app.include_router(router, prefix="/chat")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_conversations():
    """Reset conversations before each test"""
    conversations.clear()
    yield conversations
    conversations.clear()


class TestChatAPI:
    """Test suite for chat API endpoints"""
    
    @pytest.mark.asyncio
    async def test_send_chat_message_new_conversation(self, client, mock_ollama_service, mock_conversations):
        """Test sending a message creates a new conversation"""
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            # Mock the stream_chat to return an async generator
            async def mock_stream():
                yield "Hello"
                yield " there!"
            
            mock_ollama_service.stream_chat = Mock(return_value=mock_stream())
            
            response = client.post("/chat/message", json={
                "message": "Hello",
                "model": "llama2:7b",
                "stream": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "conversation_id" in data
            assert data["message"]["role"] == "assistant"
            assert data["message"]["content"] == "Hello there!"
            assert data["model"] == "llama2:7b"
            
            # Check conversation was created
            assert len(mock_conversations) == 1
    
    
    @pytest.mark.asyncio
    async def test_send_chat_message_existing_conversation(self, client, mock_ollama_service, mock_conversations):
        """Test sending a message to existing conversation"""
        # Create a conversation first
        conv_id = "test-conv-123"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "created_at": datetime.now(),
            "model": "llama2:7b",
            "messages": [],
            "system_prompt": None
        }
        
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            async def mock_stream():
                yield "Response"
            
            mock_ollama_service.stream_chat = Mock(return_value=mock_stream())
            
            response = client.post("/chat/message", json={
                "message": "Hello again",
                "model": "llama2:7b",
                "conversation_id": conv_id,
                "stream": False
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == conv_id
            assert len(mock_conversations[conv_id]["messages"]) == 2
    
    
    def test_send_chat_message_streaming(self, client, mock_ollama_service):
        """Test streaming chat message response"""
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            response = client.post("/chat/message", json={
                "message": "Hello",
                "model": "llama2:7b",
                "stream": True
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["streaming"] is True
            assert "Use WebSocket" in data["message"]
    
    
    def test_send_chat_message_no_service(self, client):
        """Test sending message when ollama service not available"""
        with patch('app.api.chat.get_ollama_service', return_value=None):
            response = client.post("/chat/message", json={
                "message": "Hello",
                "model": "llama2:7b",
                "stream": False
            })
            
            assert response.status_code == 503
            assert "Ollama service not available" in response.json()["detail"]
    
    
    def test_send_chat_message_invalid_conversation(self, client, mock_ollama_service):
        """Test sending message to non-existent conversation"""
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            response = client.post("/chat/message", json={
                "message": "Hello",
                "model": "llama2:7b",
                "conversation_id": "non-existent"
            })
            
            assert response.status_code == 404
            assert response.json()["detail"] == "Conversation not found"
    
    
    def test_create_conversation(self, client, mock_conversations):
        """Test creating a new conversation"""
        response = client.post("/chat/conversations", json={
            "title": "Test Conversation",
            "model": "llama2:7b",
            "system_prompt": "You are a helpful assistant"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert data["model"] == "llama2:7b"
        assert data["system_prompt"] == "You are a helpful assistant"
        assert "id" in data
        assert len(mock_conversations) == 1
    
    
    def test_list_conversations(self, client, mock_conversations):
        """Test listing conversations"""
        # Create some test conversations
        for i in range(3):
            conv_id = f"conv-{i}"
            mock_conversations[conv_id] = {
                "id": conv_id,
                "title": f"Conversation {i}",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "model": "llama2:7b",
                "messages": []
            }
        
        response = client.get("/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["conversations"]) == 3
    
    
    def test_list_conversations_with_pagination(self, client, mock_conversations):
        """Test listing conversations with pagination"""
        # Create 5 conversations
        for i in range(5):
            conv_id = f"conv-{i}"
            mock_conversations[conv_id] = {
                "id": conv_id,
                "created_at": datetime.now(),
                "model": "llama2:7b",
                "messages": []
            }
        
        response = client.get("/chat/conversations?limit=2&offset=1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["conversations"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 1
    
    
    def test_get_conversation(self, client, mock_conversations, sample_conversation):
        """Test getting a specific conversation"""
        conv_id = sample_conversation["id"]
        mock_conversations[conv_id] = sample_conversation
        
        response = client.get(f"/chat/conversations/{conv_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert data["title"] == sample_conversation["title"]
    
    
    def test_get_conversation_not_found(self, client):
        """Test getting non-existent conversation"""
        response = client.get("/chat/conversations/non-existent")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Conversation not found"
    
    
    def test_delete_conversation(self, client, mock_conversations):
        """Test deleting a conversation"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {"id": conv_id}
        
        response = client.delete(f"/chat/conversations/{conv_id}")
        
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        assert conv_id not in mock_conversations
    
    
    def test_update_conversation(self, client, mock_conversations):
        """Test updating conversation metadata"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "title": "Old Title",
            "system_prompt": "Old prompt"
        }
        
        response = client.put(
            f"/chat/conversations/{conv_id}",
            params={"title": "New Title", "system_prompt": "New prompt"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["system_prompt"] == "New prompt"
        assert "updated_at" in data
    
    
    def test_clear_conversation(self, client, mock_conversations):
        """Test clearing conversation messages"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        response = client.post(f"/chat/conversations/{conv_id}/clear")
        
        assert response.status_code == 200
        assert response.json()["status"] == "cleared"
        assert len(mock_conversations[conv_id]["messages"]) == 0
    
    
    def test_fork_conversation(self, client, mock_conversations, sample_conversation):
        """Test forking a conversation"""
        conv_id = sample_conversation["id"]
        mock_conversations[conv_id] = sample_conversation
        
        response = client.post(f"/chat/conversations/{conv_id}/fork")
        
        assert response.status_code == 200
        data = response.json()
        assert "Fork" in data["title"]
        assert data["forked_from"] == conv_id
        assert len(data["messages"]) == len(sample_conversation["messages"])
        assert len(mock_conversations) == 2
    
    
    def test_fork_conversation_from_index(self, client, mock_conversations, sample_conversation):
        """Test forking a conversation from specific message index"""
        conv_id = sample_conversation["id"]
        mock_conversations[conv_id] = sample_conversation
        
        response = client.post(f"/chat/conversations/{conv_id}/fork?from_message_index=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 1
    
    
    def test_get_recommended_models(self, client, mock_settings):
        """Test getting recommended models"""
        with patch('app.api.chat.settings', mock_settings):
            response = client.get("/chat/models/recommended")
            
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data
            assert "fast" in data["recommendations"]
            assert "balanced" in data["recommendations"]
            assert "powerful" in data["recommendations"]
            assert "system_memory_gb" in data
    
    
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
            
            response = client.post(f"/chat/conversations/{conv_id}/regenerate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "regenerated"
            assert data["message"]["content"] == "Regenerated response"
            assert data["message"]["metadata"]["regenerated"] is True
    
    
    def test_regenerate_no_user_message(self, client, mock_ollama_service, mock_conversations):
        """Test regenerating when no user message exists"""
        conv_id = "test-conv"
        mock_conversations[conv_id] = {
            "id": conv_id,
            "messages": [{"role": "system", "content": "System prompt"}]
        }
        
        with patch('app.api.chat.get_ollama_service', return_value=mock_ollama_service):
            response = client.post(f"/chat/conversations/{conv_id}/regenerate")
            
            assert response.status_code == 400
            assert "No user message found" in response.json()["detail"]
    
    
    def test_stop_generation(self, client):
        """Test stopping generation"""
        with patch('app.api.chat.ws_manager') as mock_ws_manager:
            mock_ws_manager.get_client_stream_status.return_value = {
                "has_active_stream": True
            }
            mock_ws_manager._handle_stop_generation = AsyncMock()
            
            response = client.post("/chat/stop", json={"client_id": "test-client"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "stopped"
            assert data["client_id"] == "test-client"
    
    
    def test_stop_generation_no_active_stream(self, client):
        """Test stopping generation when no active stream"""
        with patch('app.api.chat.ws_manager') as mock_ws_manager:
            mock_ws_manager.get_client_stream_status.return_value = {
                "has_active_stream": False
            }
            
            response = client.post("/chat/stop", json={"client_id": "test-client"})
            
            assert response.status_code == 400
            assert "No active generation to stop" in response.json()["detail"]
    
    
    def test_get_chat_status(self, client):
        """Test getting chat status for a client"""
        with patch('app.api.chat.ws_manager') as mock_ws_manager:
            mock_ws_manager.get_client_stream_status.return_value = {
                "is_streaming": True,
                "has_active_stream": True
            }
            
            response = client.get("/chat/status/test-client")
            
            assert response.status_code == 200
            data = response.json()
            assert data["client_id"] == "test-client"
            assert data["is_streaming"] is True
            assert data["has_active_stream"] is True
            assert data["can_stop"] is True
