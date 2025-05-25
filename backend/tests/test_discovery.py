"""Tests for Service Discovery Engine"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from app.core.discovery import ServiceDiscoveryEngine


@pytest.mark.asyncio
async def test_discovery_engine_initialization():
    """Test discovery engine initialization"""
    engine = ServiceDiscoveryEngine()
    assert engine._running == False
    assert engine._scan_task is None
    
    await engine.start()
    assert engine._running == True
    assert engine._http_client is not None
    
    engine.stop()
    assert engine._running == False


@pytest.mark.asyncio
async def test_ollama_discovery():
    """Test Ollama instance discovery"""
    engine = ServiceDiscoveryEngine()
    
    # Mock HTTP client
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2:7b", "size": 3826793472},
            {"name": "mistral:7b", "size": 4109856768}
        ]
    }
    
    with patch.object(engine, '_http_client') as mock_client:
        mock_client.get = AsyncMock(return_value=mock_response)
        
        result = await engine.discover_ollama_instances()
        
        assert "endpoints" in result
        assert "models" in result
        assert "capabilities" in result


@pytest.mark.asyncio
async def test_system_resource_scan():
    """Test system resource scanning"""
    engine = ServiceDiscoveryEngine()
    
    resources = await engine.scan_system_resources()
    
    assert "cpu" in resources
    assert "memory" in resources
    assert "disk" in resources
    assert "gpu" in resources
    
    # Check CPU info
    assert "count" in resources["cpu"]
    assert "percent" in resources["cpu"]
    
    # Check memory info
    assert "total" in resources["memory"]
    assert "available" in resources["memory"]
    assert "percent" in resources["memory"]


@pytest.mark.asyncio
async def test_service_health_check():
    """Test service health checking"""
    engine = ServiceDiscoveryEngine()
    
    # Mock discovered services
    engine.discovered_services = {
        "ollama": {
            "endpoints": ["http://localhost:11434"]
        }
    }
    
    with patch.object(engine, '_check_ollama_endpoint', return_value=True):
        health = await engine.get_service_health()
        
        assert "ollama_http://localhost:11434" in health
        assert health["ollama_http://localhost:11434"] == True
        assert "system" in health