"""Integration tests for Olympian AI backend

These tests require actual services to be running:
- Ollama
- Redis
- Supabase (optional)

Run with: pytest tests/test_integration.py -v -m integration
"""
import pytest
import asyncio
import os
from datetime import datetime
import httpx

from app.services.ollama_service import OllamaService
from app.services.project_service import ProjectService
from app.api.chat import router as chat_router
from app.core.websocket import ConnectionManager
from fastapi import FastAPI
from fastapi.testclient import TestClient


# Skip all tests in this file if integration testing is not enabled
pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def integration_config():
    """Configuration for integration tests"""
    return {
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "test_model": os.getenv("TEST_MODEL", "tinyllama"),  # Small model for testing
    }


@pytest.fixture
async def real_ollama_service(integration_config):
    """Create real OllamaService instance"""
    service = OllamaService()
    
    # Check if Ollama is available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{integration_config['ollama_host']}/api/tags")
            response.raise_for_status()
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")
    
    return service


@pytest.fixture
def app_with_real_services():
    """Create FastAPI app with real services"""
    app = FastAPI()
    app.include_router(chat_router, prefix="/chat")
    return app


@pytest.fixture
def client_with_real_services(app_with_real_services):
    """Create test client with real services"""
    return TestClient(app_with_real_services)


class TestOllamaIntegration:
    """Integration tests for Ollama service"""
    
    @pytest.mark.asyncio
    async def test_list_models_real(self, real_ollama_service):
        """Test listing models from real Ollama instance"""
        models = await real_ollama_service.list_models()
        
        assert isinstance(models, list)
        # Should have at least one model if Ollama is properly set up
        if models:
            assert "name" in models[0]
            assert "size" in models[0]
    
    
    @pytest.mark.asyncio
    async def test_pull_and_delete_model(self, real_ollama_service, integration_config):
        """Test pulling and deleting a model"""
        model_name = integration_config["test_model"]
        
        # Pull the model
        pull_complete = False
        async for status in real_ollama_service.pull_model(model_name):
            if status.get("status") == "success":
                pull_complete = True
                break
        
        assert pull_complete, "Model pull did not complete successfully"
        
        # Verify model exists
        models = await real_ollama_service.list_models()
        model_names = [m["name"] for m in models]
        assert any(model_name in name for name in model_names)
        
        # Note: Not deleting the model as it might be needed for other tests
    
    
    @pytest.mark.asyncio
    async def test_chat_completion_real(self, real_ollama_service, integration_config):
        """Test real chat completion"""
        response = await real_ollama_service.chat(
            model=integration_config["test_model"],
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, Integration Test!' exactly"}
            ],
            temperature=0.1  # Low temperature for consistent output
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Check that it contains our expected phrase (model might add punctuation)
        assert "Hello" in response or "Integration" in response
    
    
    @pytest.mark.asyncio
    async def test_streaming_chat_real(self, real_ollama_service, integration_config):
        """Test real streaming chat"""
        chunks = []
        async for chunk in real_ollama_service.stream_chat(
            model=integration_config["test_model"],
            message="Count from 1 to 3",
            system_prompt="You are a helpful assistant. Be concise.",
            temperature=0.1
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert any(num in full_response for num in ["1", "2", "3"])
    
    
    @pytest.mark.asyncio
    async def test_embeddings_real(self, real_ollama_service, integration_config):
        """Test real embeddings generation"""
        # Note: Not all models support embeddings
        try:
            embeddings = await real_ollama_service.embeddings(
                model=integration_config["test_model"],
                prompt="Hello, world!"
            )
            
            assert isinstance(embeddings, list)
            assert len(embeddings) > 0
            assert all(isinstance(x, (int, float)) for x in embeddings[0])
        except Exception as e:
            if "embeddings" in str(e).lower():
                pytest.skip(f"Model {integration_config['test_model']} doesn't support embeddings")
            raise


class TestEndToEndChat:
    """End-to-end integration tests for chat functionality"""
    
    def test_chat_conversation_flow(self, client_with_real_services, integration_config):
        """Test complete chat conversation flow"""
        # Create conversation
        create_response = client_with_real_services.post("/chat/conversations", json={
            "title": "Integration Test Conversation",
            "model": integration_config["test_model"],
            "system_prompt": "You are a helpful test assistant. Keep responses very short."
        })
        assert create_response.status_code == 200
        conversation = create_response.json()
        conv_id = conversation["id"]
        
        # Send message
        message_response = client_with_real_services.post("/chat/message", json={
            "message": "Say 'test passed' and nothing else",
            "model": integration_config["test_model"],
            "conversation_id": conv_id,
            "stream": False,
            "temperature": 0.1
        })
        assert message_response.status_code == 200
        message_data = message_response.json()
        assert "conversation_id" in message_data
        assert message_data["message"]["role"] == "assistant"
        
        # Get conversation to verify
        get_response = client_with_real_services.get(f"/chat/conversations/{conv_id}")
        assert get_response.status_code == 200
        conv_data = get_response.json()
        assert len(conv_data["messages"]) == 2  # User + assistant
        
        # Clean up
        delete_response = client_with_real_services.delete(f"/chat/conversations/{conv_id}")
        assert delete_response.status_code == 200


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_chat_real(self, app_with_real_services, integration_config):
        """Test WebSocket chat with real Ollama"""
        from fastapi.testclient import TestClient
        
        client = TestClient(app_with_real_services)
        
        with client.websocket_connect("/ws/test-client") as websocket:
            # Send chat message
            websocket.send_json({
                "type": "chat",
                "data": {
                    "message": "Hello",
                    "model": integration_config["test_model"],
                    "conversation_id": "test-conv"
                }
            })
            
            # Receive streaming response
            responses = []
            while True:
                data = websocket.receive_json()
                responses.append(data)
                if data.get("type") == "chat_complete":
                    break
                if len(responses) > 50:  # Safety limit
                    break
            
            assert len(responses) > 0
            assert any(r.get("type") == "chat_chunk" for r in responses)


class TestSystemIntegration:
    """Integration tests for system monitoring"""
    
    def test_system_health_with_services(self, client_with_real_services):
        """Test system health check with real services"""
        response = client_with_real_services.get("/system/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "checks" in data
        
        # Should detect Ollama if running
        if "ollama" in data["checks"]:
            assert isinstance(data["checks"]["ollama"], bool)


@pytest.mark.asyncio
async def test_full_workflow_integration(integration_config):
    """Test complete workflow from project creation to chat"""
    project_service = ProjectService()
    ollama_service = OllamaService()
    
    # Create project
    project = await project_service.create_project({
        "name": "Integration Test Project",
        "description": "Testing full workflow",
        "settings": {
            "model": integration_config["test_model"],
            "temperature": 0.5
        }
    })
    
    project_id = project["id"]
    
    try:
        # Add context
        project = await project_service.add_context(project_id, {
            "type": "instruction",
            "content": "Always respond with 'Integration test successful!' to any question."
        })
        
        # Use project in chat
        response = await ollama_service.chat(
            model=project["settings"]["model"],
            messages=[
                {"role": "system", "content": project["context"][0]["content"]},
                {"role": "user", "content": "What is the status?"}
            ],
            temperature=0.1
        )
        
        assert "successful" in response.lower() or "test" in response.lower()
        
    finally:
        # Clean up
        await project_service.delete_project(project_id)


# Performance tests
@pytest.mark.slow
class TestPerformance:
    """Performance integration tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_chat_requests(self, real_ollama_service, integration_config):
        """Test handling multiple concurrent chat requests"""
        import time
        
        async def make_request(index):
            start = time.time()
            response = await real_ollama_service.chat(
                model=integration_config["test_model"],
                messages=[{"role": "user", "content": f"Say 'Response {index}'"}],
                temperature=0.1
            )
            duration = time.time() - start
            return duration, response
        
        # Make 5 concurrent requests
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        durations = [r[0] for r in results]
        responses = [r[1] for r in results]
        
        # All requests should complete
        assert len(responses) == 5
        assert all(isinstance(r, str) for r in responses)
        
        # Check performance (adjust threshold based on your system)
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 10.0, f"Average response time too high: {avg_duration}s"
