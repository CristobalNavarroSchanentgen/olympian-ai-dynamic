"""Pytest configuration and shared fixtures"""
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create FastAPI test client"""
    # Import here to avoid circular imports
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_conversations():
    """Mock conversations storage for testing"""
    conversations = {}
    with patch('app.api.chat.conversations', conversations):
        yield conversations


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch('app.core.config.settings') as mock:
        mock.environment = "test"
        mock.debug = True
        mock.supabase_url = "http://test.supabase.co"
        mock.supabase_key = "test-key"
        mock.jwt_secret_key = "test-secret-key"
        mock.jwt_algorithm = "HS256"
        mock.redis_url = "redis://localhost:6379"
        mock.cors_origins = ["http://localhost:3000"]
        mock.discovered_services = {
            "ollama": {
                "endpoints": ["http://localhost:11434"],
                "models": [
                    {"name": "llama2:7b", "size": 3826793472},
                    {"name": "mistral:7b", "size": 4109856768}
                ],
                "capabilities": {
                    "embeddings": True,
                    "chat": True,
                    "completion": True
                }
            }
        }
        yield mock


@pytest.fixture
def mock_ollama_service():
    """Mock OllamaService for testing"""
    with patch('app.services.ollama_service.OllamaService') as mock:
        instance = mock.return_value
        instance.chat = AsyncMock(return_value="Test response")
        instance.stream_chat = AsyncMock()
        instance.list_models = AsyncMock(return_value=[
            {"name": "llama2:7b", "size": 3826793472},
            {"name": "mistral:7b", "size": 4109856768}
        ])
        instance.pull_model = AsyncMock(return_value={"status": "success"})
        instance.delete_model = AsyncMock(return_value={"status": "success"})
        instance.get_model_info = AsyncMock(return_value={
            "name": "llama2:7b",
            "size": 3826793472,
            "modified_at": "2024-01-01T00:00:00Z"
        })
        yield instance


@pytest.fixture
def mock_project_service():
    """Mock ProjectService for testing"""
    with patch('app.services.project_service.ProjectService') as mock:
        instance = mock.return_value
        instance.create_project = AsyncMock(return_value={
            "id": "test-project-id",
            "name": "Test Project",
            "created_at": datetime.now().isoformat()
        })
        instance.get_project = AsyncMock(return_value={
            "id": "test-project-id",
            "name": "Test Project",
            "context": []
        })
        instance.list_projects = AsyncMock(return_value=[])
        instance.update_project = AsyncMock(return_value={
            "id": "test-project-id",
            "name": "Updated Project"
        })
        instance.delete_project = AsyncMock(return_value={"status": "deleted"})
        yield instance


@pytest.fixture
def mock_webhook_service():
    """Mock WebhookService for testing"""
    with patch('app.services.webhook_service.WebhookService') as mock:
        instance = mock.return_value
        instance.create_webhook = AsyncMock(return_value={
            "id": "test-webhook-id",
            "url": "http://test.com/webhook",
            "events": ["model.created"]
        })
        instance.list_webhooks = AsyncMock(return_value=[])
        instance.delete_webhook = AsyncMock(return_value={"status": "deleted"})
        instance.trigger_webhook = AsyncMock(return_value={"status": "triggered"})
        yield instance


@pytest.fixture
def mock_mcp_service():
    """Mock MCPService for testing"""
    with patch('app.services.mcp_service.MCPService') as mock:
        instance = mock.return_value
        instance.list_servers = AsyncMock(return_value=[])
        instance.connect_server = AsyncMock(return_value={"status": "connected"})
        instance.disconnect_server = AsyncMock(return_value={"status": "disconnected"})
        instance.list_tools = AsyncMock(return_value=[])
        instance.execute_tool = AsyncMock(return_value={"result": "success"})
        yield instance


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    with patch('redis.Redis') as mock:
        instance = mock.return_value
        instance.get = Mock(return_value=None)
        instance.set = Mock(return_value=True)
        instance.delete = Mock(return_value=1)
        instance.exists = Mock(return_value=False)
        instance.expire = Mock(return_value=True)
        yield instance


@pytest.fixture
def sample_chat_request():
    """Sample chat request data"""
    return {
        "message": "Hello, how are you?",
        "model": "llama2:7b",
        "temperature": 0.7,
        "stream": False
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation data"""
    return {
        "id": "conv-123",
        "title": "Test Conversation",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "model": "llama2:7b",
        "messages": [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Hi there!",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }


@pytest.fixture
def sample_project():
    """Sample project data"""
    return {
        "id": "proj-123",
        "name": "Test Project",
        "description": "A test project",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "settings": {
            "model": "llama2:7b",
            "temperature": 0.7
        },
        "context": []
    }


@pytest.fixture
def sample_webhook():
    """Sample webhook data"""
    return {
        "id": "webhook-123",
        "url": "http://example.com/webhook",
        "events": ["model.created", "chat.completed"],
        "active": True,
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing"""
    async with AsyncClient(base_url="http://test") as client:
        yield client
