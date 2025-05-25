"""Tests for Webhooks API endpoints"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

from app.api.webhooks import router, webhooks


@pytest.fixture
def app():
    """Create FastAPI app with webhooks router"""
    app = FastAPI()
    app.include_router(router, prefix="/webhooks")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_webhooks():
    """Reset webhooks before each test"""
    webhooks.clear()
    yield webhooks
    webhooks.clear()


class TestWebhooksAPI:
    """Test suite for webhooks API endpoints"""
    
    def test_create_webhook(self, client, mock_webhooks, mock_webhook_service):
        """Test creating a new webhook"""
        with patch('app.api.webhooks.webhook_service', mock_webhook_service):
            response = client.post("/webhooks", json={
                "url": "https://example.com/webhook",
                "events": ["model.created", "chat.completed"],
                "secret": "test-secret"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["url"] == "https://example.com/webhook"
            assert "id" in data
            assert len(data["events"]) == 2
            assert len(mock_webhooks) == 1
    
    
    def test_create_webhook_invalid_url(self, client):
        """Test creating webhook with invalid URL"""
        response = client.post("/webhooks", json={
            "url": "not-a-url",
            "events": ["model.created"]
        })
        
        assert response.status_code == 422
    
    
    def test_create_webhook_no_events(self, client):
        """Test creating webhook without events"""
        response = client.post("/webhooks", json={
            "url": "https://example.com/webhook",
            "events": []
        })
        
        assert response.status_code == 422
    
    
    def test_list_webhooks(self, client, mock_webhooks):
        """Test listing all webhooks"""
        # Create test webhooks
        for i in range(3):
            webhook_id = f"webhook-{i}"
            mock_webhooks[webhook_id] = {
                "id": webhook_id,
                "url": f"https://example.com/webhook{i}",
                "events": ["model.created"],
                "active": True
            }
        
        response = client.get("/webhooks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["webhooks"]) == 3
        assert data["total"] == 3
    
    
    def test_get_webhook(self, client, mock_webhooks, sample_webhook):
        """Test getting a specific webhook"""
        webhook_id = sample_webhook["id"]
        mock_webhooks[webhook_id] = sample_webhook
        
        response = client.get(f"/webhooks/{webhook_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == webhook_id
        assert data["url"] == sample_webhook["url"]
    
    
    def test_get_webhook_not_found(self, client):
        """Test getting non-existent webhook"""
        response = client.get("/webhooks/non-existent")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Webhook not found"
    
    
    def test_update_webhook(self, client, mock_webhooks, sample_webhook):
        """Test updating a webhook"""
        webhook_id = sample_webhook["id"]
        mock_webhooks[webhook_id] = sample_webhook
        
        response = client.put(f"/webhooks/{webhook_id}", json={
            "url": "https://new-example.com/webhook",
            "events": ["model.deleted"],
            "active": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://new-example.com/webhook"
        assert data["active"] is False
        assert "model.deleted" in data["events"]
    
    
    def test_delete_webhook(self, client, mock_webhooks, mock_webhook_service):
        """Test deleting a webhook"""
        webhook_id = "test-webhook"
        mock_webhooks[webhook_id] = {"id": webhook_id}
        
        with patch('app.api.webhooks.webhook_service', mock_webhook_service):
            response = client.delete(f"/webhooks/{webhook_id}")
            
            assert response.status_code == 200
            assert response.json()["status"] == "deleted"
            assert webhook_id not in mock_webhooks
    
    
    def test_toggle_webhook(self, client, mock_webhooks):
        """Test toggling webhook active status"""
        webhook_id = "test-webhook"
        mock_webhooks[webhook_id] = {
            "id": webhook_id,
            "active": True
        }
        
        response = client.post(f"/webhooks/{webhook_id}/toggle")
        
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False
        
        # Toggle again
        response = client.post(f"/webhooks/{webhook_id}/toggle")
        assert response.json()["active"] is True
    
    
    @pytest.mark.asyncio
    async def test_trigger_webhook(self, client, mock_webhooks, mock_webhook_service):
        """Test manually triggering a webhook"""
        webhook_id = "test-webhook"
        mock_webhooks[webhook_id] = {
            "id": webhook_id,
            "url": "https://example.com/webhook",
            "active": True
        }
        
        with patch('app.api.webhooks.webhook_service', mock_webhook_service):
            response = client.post(f"/webhooks/{webhook_id}/trigger", json={
                "event": "test.event",
                "data": {"message": "Test data"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "triggered"
    
    
    def test_trigger_inactive_webhook(self, client, mock_webhooks):
        """Test triggering inactive webhook"""
        webhook_id = "test-webhook"
        mock_webhooks[webhook_id] = {
            "id": webhook_id,
            "active": False
        }
        
        response = client.post(f"/webhooks/{webhook_id}/trigger", json={
            "event": "test.event",
            "data": {}
        })
        
        assert response.status_code == 400
        assert "not active" in response.json()["detail"]
    
    
    def test_get_webhook_logs(self, client, mock_webhooks):
        """Test getting webhook execution logs"""
        webhook_id = "test-webhook"
        mock_webhooks[webhook_id] = {
            "id": webhook_id,
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "event": "model.created",
                    "status": "success",
                    "response_code": 200
                }
            ]
        }
        
        response = client.get(f"/webhooks/{webhook_id}/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 1
        assert data["logs"][0]["status"] == "success"
    
    
    def test_verify_webhook_signature(self, client):
        """Test webhook signature verification endpoint"""
        response = client.post("/webhooks/verify", json={
            "payload": {"test": "data"},
            "signature": "sha256=test-signature",
            "secret": "test-secret"
        })
        
        assert response.status_code == 200
        # Note: Actual verification logic would need proper implementation
    
    
    def test_batch_create_webhooks(self, client, mock_webhook_service):
        """Test creating multiple webhooks at once"""
        with patch('app.api.webhooks.webhook_service', mock_webhook_service):
            response = client.post("/webhooks/batch", json={
                "webhooks": [
                    {
                        "url": "https://example1.com/webhook",
                        "events": ["model.created"]
                    },
                    {
                        "url": "https://example2.com/webhook",
                        "events": ["chat.completed"]
                    }
                ]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["created_count"] == 2
    
    
    def test_get_webhook_stats(self, client, mock_webhooks):
        """Test getting webhook statistics"""
        # Create webhooks with different statuses
        mock_webhooks["w1"] = {"id": "w1", "active": True, "success_count": 10, "failure_count": 2}
        mock_webhooks["w2"] = {"id": "w2", "active": False, "success_count": 5, "failure_count": 1}
        
        response = client.get("/webhooks/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_webhooks"] == 2
        assert data["active_webhooks"] == 1
        assert data["total_deliveries"] == 18  # 10+2+5+1
    
    
    def test_test_webhook_connection(self, client, mock_webhooks):
        """Test webhook connection test endpoint"""
        webhook_id = "test-webhook"
        mock_webhooks[webhook_id] = {
            "id": webhook_id,
            "url": "https://example.com/webhook"
        }
        
        with patch('httpx.AsyncClient') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_http.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            response = client.post(f"/webhooks/{webhook_id}/test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    
    def test_filter_webhooks_by_event(self, client, mock_webhooks):
        """Test filtering webhooks by event type"""
        mock_webhooks["w1"] = {"id": "w1", "events": ["model.created", "model.deleted"]}
        mock_webhooks["w2"] = {"id": "w2", "events": ["chat.completed"]}
        mock_webhooks["w3"] = {"id": "w3", "events": ["model.created"]}
        
        response = client.get("/webhooks?event=model.created")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["webhooks"]) == 2  # w1 and w3
    
    
    def test_clear_webhook_logs(self, client, mock_webhooks):
        """Test clearing webhook logs"""
        webhook_id = "test-webhook"
        mock_webhooks[webhook_id] = {
            "id": webhook_id,
            "logs": [{"event": "test"}]
        }
        
        response = client.delete(f"/webhooks/{webhook_id}/logs")
        
        assert response.status_code == 200
        assert response.json()["status"] == "cleared"
        assert len(mock_webhooks[webhook_id]["logs"]) == 0
