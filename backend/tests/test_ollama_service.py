"""Tests for Ollama Service"""
import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
import httpx
from datetime import datetime

from app.services.ollama_service import OllamaService


@pytest.fixture
def ollama_service():
    """Create OllamaService instance"""
    return OllamaService()


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient"""
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    return mock


class TestOllamaService:
    """Test suite for Ollama service"""
    
    @pytest.mark.asyncio
    async def test_list_models(self, ollama_service, mock_httpx_client):
        """Test listing available models"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "llama2:7b",
                    "size": 3826793472,
                    "digest": "abc123",
                    "modified_at": "2024-01-01T00:00:00Z"
                },
                {
                    "name": "mistral:7b",
                    "size": 4109856768,
                    "digest": "def456",
                    "modified_at": "2024-01-02T00:00:00Z"
                }
            ]
        }
        mock_httpx_client.get.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            models = await ollama_service.list_models()
            
            assert len(models) == 2
            assert models[0]["name"] == "llama2:7b"
            assert models[1]["name"] == "mistral:7b"
    
    
    @pytest.mark.asyncio
    async def test_chat(self, ollama_service, mock_httpx_client):
        """Test chat completion"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "model": "llama2:7b",
            "created_at": "2024-01-01T00:00:00Z",
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            },
            "done": True
        }
        mock_httpx_client.post.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            response = await ollama_service.chat(
                model="llama2:7b",
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            assert response == "Hello! How can I help you?"
            mock_httpx_client.post.assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_stream_chat(self, ollama_service, mock_httpx_client):
        """Test streaming chat completion"""
        # Mock streaming response
        mock_response = MagicMock()
        mock_response.aiter_lines = AsyncMock()
        
        async def mock_lines():
            yield '{"message": {"content": "Hello"}, "done": false}'
            yield '{"message": {"content": " there!"}, "done": false}'
            yield '{"message": {"content": ""}, "done": true}'
        
        mock_response.aiter_lines.return_value = mock_lines()
        mock_httpx_client.post.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            result = []
            async for chunk in ollama_service.stream_chat(
                model="llama2:7b",
                message="Hi",
                system_prompt="You are helpful"
            ):
                result.append(chunk)
            
            assert result == ["Hello", " there!", ""]
    
    
    @pytest.mark.asyncio
    async def test_generate(self, ollama_service, mock_httpx_client):
        """Test text generation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "model": "llama2:7b",
            "created_at": "2024-01-01T00:00:00Z",
            "response": "Generated text response",
            "done": True
        }
        mock_httpx_client.post.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            response = await ollama_service.generate(
                model="llama2:7b",
                prompt="Write a story"
            )
            
            assert response == "Generated text response"
    
    
    @pytest.mark.asyncio
    async def test_embeddings(self, ollama_service, mock_httpx_client):
        """Test generating embeddings"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3, 0.4, 0.5]]
        }
        mock_httpx_client.post.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            embeddings = await ollama_service.embeddings(
                model="llama2:7b",
                prompt="Hello world"
            )
            
            assert len(embeddings) == 1
            assert len(embeddings[0]) == 5
            assert embeddings[0][0] == 0.1
    
    
    @pytest.mark.asyncio
    async def test_pull_model(self, ollama_service, mock_httpx_client):
        """Test pulling a model"""
        mock_response = MagicMock()
        mock_response.aiter_lines = AsyncMock()
        
        async def mock_lines():
            yield '{"status": "pulling manifest"}'
            yield '{"status": "downloading", "completed": 1000, "total": 2000}'
            yield '{"status": "success"}'
        
        mock_response.aiter_lines.return_value = mock_lines()
        mock_httpx_client.post.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            result = []
            async for status in ollama_service.pull_model("llama2:latest"):
                result.append(status)
            
            assert len(result) == 3
            assert result[0]["status"] == "pulling manifest"
            assert result[1]["status"] == "downloading"
            assert result[2]["status"] == "success"
    
    
    @pytest.mark.asyncio
    async def test_delete_model(self, ollama_service, mock_httpx_client):
        """Test deleting a model"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_httpx_client.delete.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            result = await ollama_service.delete_model("llama2:7b")
            
            assert result["status"] == "success"
            mock_httpx_client.delete.assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, ollama_service, mock_httpx_client):
        """Test getting model information"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "llama2:7b",
            "modified_at": "2024-01-01T00:00:00Z",
            "size": 3826793472,
            "digest": "abc123",
            "details": {
                "format": "gguf",
                "family": "llama",
                "parameter_size": "7B"
            }
        }
        mock_httpx_client.get.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            info = await ollama_service.get_model_info("llama2:7b")
            
            assert info["name"] == "llama2:7b"
            assert info["size"] == 3826793472
            assert info["details"]["parameter_size"] == "7B"
    
    
    @pytest.mark.asyncio
    async def test_copy_model(self, ollama_service, mock_httpx_client):
        """Test copying/creating model alias"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_httpx_client.post.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            result = await ollama_service.copy_model(
                source="llama2:7b",
                destination="llama2:custom"
            )
            
            assert result["status"] == "success"
    
    
    @pytest.mark.asyncio
    async def test_create_model(self, ollama_service, mock_httpx_client):
        """Test creating a custom model"""
        mock_response = MagicMock()
        mock_response.aiter_lines = AsyncMock()
        
        async def mock_lines():
            yield '{"status": "parsing modelfile"}'
            yield '{"status": "success"}'
        
        mock_response.aiter_lines.return_value = mock_lines()
        mock_httpx_client.post.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            modelfile = "FROM llama2\nSYSTEM You are a helpful assistant"
            result = []
            
            async for status in ollama_service.create_model(
                name="custom-model",
                modelfile=modelfile
            ):
                result.append(status)
            
            assert len(result) == 2
            assert result[1]["status"] == "success"
    
    
    @pytest.mark.asyncio
    async def test_health_check(self, ollama_service, mock_httpx_client):
        """Test service health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_httpx_client.get.return_value = mock_response
        
        # Mock list_models for loaded models count
        with patch.object(ollama_service, 'list_models', return_value=[
            {"name": "llama2:7b"},
            {"name": "mistral:7b"}
        ]):
            with patch('httpx.AsyncClient', return_value=mock_httpx_client):
                health = await ollama_service.health_check()
                
                assert health["status"] == "healthy"
                assert health["models_loaded"] == 2
    
    
    @pytest.mark.asyncio
    async def test_error_handling(self, ollama_service, mock_httpx_client):
        """Test error handling in service calls"""
        mock_httpx_client.get.side_effect = httpx.HTTPError("Connection failed")
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            with pytest.raises(Exception) as exc_info:
                await ollama_service.list_models()
            
            assert "Connection failed" in str(exc_info.value)
    
    
    @pytest.mark.asyncio
    async def test_context_handling(self, ollama_service, mock_httpx_client):
        """Test handling of conversation context"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Response with context"},
            "done": True
        }
        mock_httpx_client.post.return_value = mock_response
        
        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            response = await ollama_service.chat(
                model="llama2:7b",
                messages=[{"role": "user", "content": "New message"}],
                context=context
            )
            
            # Verify context was included in request
            call_args = mock_httpx_client.post.call_args
            request_data = call_args[1]["json"]
            assert len(request_data["messages"]) == 3  # Context + new message
    
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, ollama_service, mock_httpx_client):
        """Test timeout handling for long-running requests"""
        mock_httpx_client.post.side_effect = httpx.TimeoutException("Request timed out")
        
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            with pytest.raises(Exception) as exc_info:
                await ollama_service.generate(
                    model="llama2:7b",
                    prompt="Long prompt"
                )
            
            assert "timed out" in str(exc_info.value).lower()
