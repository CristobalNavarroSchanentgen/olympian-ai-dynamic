"""Tests for Configuration API endpoints"""
import pytest
from unittest.mock import patch, Mock, mock_open
import yaml
import json
from urllib.parse import quote


class TestConfigAPI:
    """Test suite for configuration API endpoints"""
    
    def test_get_config(self, client, mock_settings):
        """Test getting current configuration"""
        with patch('app.api.config.settings', mock_settings):
            # Use the correct endpoint - /api/config/dynamic instead of /config
            response = client.get("/api/config/dynamic")
            
            assert response.status_code == 200
            data = response.json()
            assert "server" in data
            assert "discovered_services" in data
            assert "user_preferences" in data
            assert data["server"]["environment"] == "test"
    
    
    def test_get_user_preferences(self, client, mock_settings):
        """Test getting user preferences"""
        with patch('app.api.config.settings', mock_settings):
            response = client.get("/api/config/preferences")
            
            assert response.status_code == 200
            data = response.json()
            assert "preferences" in data
            assert "timestamp" in data
    
    
    def test_update_user_preferences(self, client, mock_settings):
        """Test updating user preferences"""
        # Create a proper data structure instead of Mock to avoid recursion
        user_prefs_data = {
            "preferred_models": ["llama2:7b"],
            "custom_endpoints": [],
            "disabled_services": [],
            "manual_overrides": {}
        }
        
        # Mock user preferences as a simple object that behaves like a model
        mock_user_prefs = Mock()
        mock_user_prefs.preferred_models = ["llama2:7b"]
        mock_user_prefs.custom_endpoints = []
        mock_user_prefs.disabled_services = []
        mock_user_prefs.manual_overrides = {}
        mock_settings.user_preferences = mock_user_prefs
        mock_settings.save_config = Mock()
        
        with patch('app.api.config.settings', mock_settings):
            # Mock the safe_model_dump function to return consistent data
            with patch('app.api.config.safe_model_dump', return_value=user_prefs_data):
                with patch('app.api.config.ws_manager.notify_config_change') as mock_notify:
                    response = client.put("/api/config/preferences", json={
                        "preferred_models": ["llama2:13b", "mistral:7b"]
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "updated"
                    assert "preferences" in data
                    mock_settings.save_config.assert_called_once()
    
    
    def test_add_service_override(self, client, mock_settings):
        """Test adding service override"""
        mock_user_prefs = Mock()
        mock_user_prefs.manual_overrides = {}
        mock_settings.user_preferences = mock_user_prefs
        mock_settings.save_config = Mock()
        
        with patch('app.api.config.settings', mock_settings):
            with patch('app.api.config.ws_manager.notify_config_change') as mock_notify:
                response = client.post("/api/config/override", json={
                    "service_type": "ollama",
                    "config": {"timeout": 60}
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "added"
                assert data["service_type"] == "ollama"
                mock_settings.save_config.assert_called_once()
    
    
    def test_remove_service_override(self, client, mock_settings):
        """Test removing service override"""
        mock_user_prefs = Mock()
        mock_user_prefs.manual_overrides = {"ollama": {"timeout": 60}}
        mock_settings.user_preferences = mock_user_prefs
        mock_settings.save_config = Mock()
        
        with patch('app.api.config.settings', mock_settings):
            with patch('app.api.config.ws_manager.notify_config_change') as mock_notify:
                response = client.delete("/api/config/override/ollama")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "removed"
                assert data["service_type"] == "ollama"
    
    
    def test_remove_nonexistent_override(self, client, mock_settings):
        """Test removing non-existent service override"""
        mock_user_prefs = Mock()
        mock_user_prefs.manual_overrides = {}
        mock_settings.user_preferences = mock_user_prefs
        
        with patch('app.api.config.settings', mock_settings):
            response = client.delete("/api/config/override/nonexistent")
            
            assert response.status_code == 404
            assert "Override not found" in response.json()["detail"]
    
    
    def test_get_cors_origins(self, client, mock_settings):
        """Test getting CORS origins"""
        mock_settings.cors_origins = ["http://localhost:3000", "http://localhost:8080"]
        
        with patch('app.api.config.settings', mock_settings):
            response = client.get("/api/config/cors")
            
            assert response.status_code == 200
            data = response.json()
            assert "origins" in data
            assert data["count"] == 2
            assert "http://localhost:3000" in data["origins"]
    
    
    def test_add_cors_origin(self, client, mock_settings):
        """Test adding CORS origin"""
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.add_cors_origin = Mock()
        
        with patch('app.api.config.settings', mock_settings):
            response = client.post("/api/config/cors/add?origin=http://localhost:8080")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "added"
            assert data["origin"] == "http://localhost:8080"
            mock_settings.add_cors_origin.assert_called_once_with("http://localhost:8080")
    
    
    def test_remove_cors_origin(self, client, mock_settings):
        """Test removing CORS origin"""
        mock_settings.cors_origins = ["http://localhost:3000", "http://localhost:8080"]
        mock_settings.save_config = Mock()
        
        with patch('app.api.config.settings', mock_settings):
            # URL encode the origin to handle special characters like ://
            encoded_origin = quote("http://localhost:8080", safe='')
            response = client.delete(f"/api/config/cors/{encoded_origin}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "removed"
            # The API should return the decoded origin
            assert data["origin"] == "http://localhost:8080"
    
    
    def test_get_discovery_config(self, client, mock_settings):
        """Test getting discovery configuration"""
        mock_settings.is_service_discovery_enabled = Mock(return_value=True)
        mock_settings.get_effective_scan_interval = Mock(return_value=30)
        
        with patch('app.api.config.settings', mock_settings):
            response = client.get("/api/config/discovery")
            
            assert response.status_code == 200
            data = response.json()
            assert "config" in data
            assert data["enabled"] is True
            assert data["scan_interval"] == 30
    
    
    def test_update_discovery_config(self, client, mock_settings):
        """Test updating discovery configuration"""
        mock_settings.is_service_discovery_enabled = Mock(return_value=False)
        mock_settings.get_effective_scan_interval = Mock(return_value=60)
        mock_settings.save_config = Mock()
        
        with patch('app.api.config.settings', mock_settings):
            with patch('app.api.config.ws_manager.notify_config_change') as mock_notify:
                response = client.put("/api/config/discovery?enabled=false&scan_interval=60")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "updated"
                assert "config" in data
                mock_settings.save_config.assert_called_once()
    
    
    def test_reset_configuration_preferences(self, client, mock_settings):
        """Test resetting user preferences"""
        mock_settings.save_config = Mock()
        
        with patch('app.api.config.settings', mock_settings):
            with patch('app.api.config.ws_manager.notify_config_change') as mock_notify:
                response = client.post("/api/config/reset?section=preferences")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "reset"
                assert data["section"] == "preferences"
                mock_settings.save_config.assert_called_once()
    
    
    def test_reset_configuration_invalid_section(self, client, mock_settings):
        """Test resetting with invalid section"""
        with patch('app.api.config.settings', mock_settings):
            response = client.post("/api/config/reset?section=invalid")
            
            assert response.status_code == 400
            assert "Invalid section" in response.json()["detail"]
    
    
    def test_export_configuration(self, client, mock_settings):
        """Test exporting configuration"""
        mock_settings.server_host = "localhost"
        mock_settings.server_port = 8000
        mock_settings.environment = "test"
        mock_settings.debug = True
        mock_settings.is_service_discovery_enabled = Mock(return_value=True)
        mock_settings.get_effective_scan_interval = Mock(return_value=30)
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expiration_minutes = 60
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.discovered_services = {}
        
        # Mock user preferences
        mock_user_prefs = Mock()
        mock_settings.user_preferences = mock_user_prefs
        
        with patch('app.api.config.settings', mock_settings):
            with patch('app.api.config.safe_model_dump', return_value={}):
                response = client.get("/api/config/export")
                
                assert response.status_code == 200
                data = response.json()
                assert "version" in data
                assert "exported_at" in data
                assert "configuration" in data
                assert data["version"] == "1.0.0"
    
    
    def test_import_configuration(self, client, mock_settings):
        """Test importing configuration"""
        mock_settings.save_config = Mock()
        
        import_data = {
            "version": "1.0.0",
            "configuration": {
                "user_preferences": {
                    "preferred_models": ["llama2:7b"]
                },
                "cors_origins": ["http://localhost:3000"],
                "server": {
                    "discovery": {
                        "enabled": True,
                        "scan_interval": 30
                    }
                }
            }
        }
        
        with patch('app.api.config.settings', mock_settings):
            with patch('app.api.config.ws_manager.notify_config_change') as mock_notify:
                response = client.post("/api/config/import", json=import_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "imported"
                assert "timestamp" in data
                mock_settings.save_config.assert_called_once()
    
    
    def test_import_configuration_invalid_version(self, client, mock_settings):
        """Test importing configuration with invalid version"""
        import_data = {
            "version": "2.0.0",  # Invalid version
            "configuration": {}
        }
        
        with patch('app.api.config.settings', mock_settings):
            response = client.post("/api/config/import", json=import_data)
            
            assert response.status_code == 400
            assert "Import failed" in response.json()["detail"]
