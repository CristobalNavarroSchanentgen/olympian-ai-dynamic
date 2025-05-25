"""Tests for Ollama API endpoints"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import asyncio

from app.api.ollama import router


@pytest.fixture
def app():
    """Create FastAPI app with ollama router"""
    app = FastAPI()
    app.include_router(router, prefix="/ollama")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestOllamaAPI:
    """Test suite for Ollama API endpoints"""
    
    def test_list_models(self, client, mock_ollama_service):
        """Test listing available models"""
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.get("/ollama/models")
            
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert len(data["models"]) == 2
            assert data["models"][0]["name"] == "llama2:7b"
    
    
    def test_get_model_info(self, client, mock_ollama_service):
        """Test getting model information"""
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.get("/ollama/models/llama2:7b")
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "llama2:7b"
            assert "size" in data
            assert "modified_at" in data
    
    
    def test_get_model_info_not_found(self, client, mock_ollama_service):
        """Test getting info for non-existent model"""
        mock_ollama_service.get_model_info = AsyncMock(side_effect=Exception("Model not found"))
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.get("/ollama/models/non-existent")
            
            assert response.status_code == 404
    
    
    def test_pull_model(self, client, mock_ollama_service):
        """Test pulling a new model"""
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/models/pull", json={
                "name": "mistral:latest"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    
    def test_pull_model_stream(self, client, mock_ollama_service):
        """Test pulling a model with streaming"""
        async def mock_stream():
            yield {"status": "downloading", "progress": 50}
            yield {"status": "downloading", "progress": 100}
            yield {"status": "success"}
        
        mock_ollama_service.pull_model = Mock(return_value=mock_stream())
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/models/pull", json={
                "name": "mistral:latest",
                "stream": True
            })
            
            assert response.status_code == 200
            # For streaming responses, check if it indicates streaming
            assert response.headers.get("content-type") == "text/event-stream"
    
    
    def test_delete_model(self, client, mock_ollama_service):
        """Test deleting a model"""
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.delete("/ollama/models/llama2:7b")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    
    def test_delete_model_error(self, client, mock_ollama_service):
        """Test deleting model with error"""
        mock_ollama_service.delete_model = AsyncMock(side_effect=Exception("Cannot delete model"))
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.delete("/ollama/models/llama2:7b")
            
            assert response.status_code == 500
            assert "Cannot delete model" in response.json()["detail"]
    
    
    def test_generate_completion(self, client, mock_ollama_service):
        """Test generating text completion"""
        mock_ollama_service.generate = AsyncMock(return_value="Generated text response")
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/generate", json={
                "model": "llama2:7b",
                "prompt": "Write a haiku about coding"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Generated text response"
            assert data["model"] == "llama2:7b"
    
    
    def test_generate_completion_stream(self, client, mock_ollama_service):
        """Test generating completion with streaming"""
        async def mock_stream():
            yield "Generated "
            yield "streaming "
            yield "response"
        
        mock_ollama_service.generate_stream = Mock(return_value=mock_stream())
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/generate", json={
                "model": "llama2:7b",
                "prompt": "Write a haiku",
                "stream": True
            })
            
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream"
    
    
    def test_generate_embeddings(self, client, mock_ollama_service):
        """Test generating embeddings"""
        mock_embeddings = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        mock_ollama_service.embeddings = AsyncMock(return_value=mock_embeddings)
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/embeddings", json={
                "model": "llama2:7b",
                "prompt": "Hello world"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "embeddings" in data
            assert len(data["embeddings"]) == 1
            assert len(data["embeddings"][0]) == 5
    
    
    def test_model_health_check(self, client, mock_ollama_service):
        """Test model health check"""
        mock_ollama_service.health_check = AsyncMock(return_value={
            "status": "healthy",
            "models_loaded": 2,
            "memory_available": "8GB"
        })
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.get("/ollama/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "models_loaded" in data
    
    
    def test_copy_model(self, client, mock_ollama_service):
        """Test copying/creating model alias"""
        mock_ollama_service.copy_model = AsyncMock(return_value={"status": "success"})
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/models/copy", json={
                "source": "llama2:7b",
                "destination": "llama2:custom"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    
    def test_show_model_details(self, client, mock_ollama_service):
        """Test showing detailed model information"""
        mock_ollama_service.show_model = AsyncMock(return_value={
            "modelfile": "FROM llama2\nPARAMETER temperature 0.7",
            "parameters": {"temperature": 0.7},
            "template": "{{ .System }} {{ .Prompt }}"
        })
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.get("/ollama/models/llama2:7b/details")
            
            assert response.status_code == 200
            data = response.json()
            assert "modelfile" in data
            assert "parameters" in data
    
    
    def test_create_model(self, client, mock_ollama_service):
        """Test creating a custom model"""
        mock_ollama_service.create_model = AsyncMock(return_value={"status": "success"})
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/models/create", json={
                "name": "custom-model",
                "modelfile": "FROM llama2\nSYSTEM You are a helpful assistant"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    
    def test_push_model(self, client, mock_ollama_service):
        """Test pushing model to registry"""
        mock_ollama_service.push_model = AsyncMock(return_value={"status": "success"})
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/models/push", json={
                "name": "username/model:tag"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    
    def test_list_running_models(self, client, mock_ollama_service):
        """Test listing currently loaded models"""
        mock_ollama_service.list_running = AsyncMock(return_value=[
            {
                "name": "llama2:7b",
                "size": 3826793472,
                "digest": "abc123",
                "expires_at": "2024-01-01T12:00:00Z"
            }
        ])
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.get("/ollama/models/running")
            
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert len(data["models"]) == 1
            assert data["models"][0]["name"] == "llama2:7b"
    
    
    def test_model_benchmark(self, client, mock_ollama_service):
        """Test benchmarking a model"""
        mock_ollama_service.benchmark_model = AsyncMock(return_value={
            "tokens_per_second": 45.2,
            "time_to_first_token": 0.234,
            "total_duration": 2.5
        })
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/models/benchmark", json={
                "model": "llama2:7b",
                "prompt": "Test prompt",
                "num_iterations": 5
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "tokens_per_second" in data
            assert "time_to_first_token" in data
    
    
    def test_batch_generate(self, client, mock_ollama_service):
        """Test batch generation for multiple prompts"""
        mock_responses = [
            {"prompt": "Hello", "response": "Hi there!"},
            {"prompt": "Goodbye", "response": "See you later!"}
        ]
        mock_ollama_service.batch_generate = AsyncMock(return_value=mock_responses)
        
        with patch('app.api.ollama.ollama_service', mock_ollama_service):
            response = client.post("/ollama/generate/batch", json={
                "model": "llama2:7b",
                "prompts": ["Hello", "Goodbye"]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "responses" in data
            assert len(data["responses"]) == 2
