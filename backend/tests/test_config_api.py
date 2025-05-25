"""Tests for Configuration API endpoints"""
import pytest
from unittest.mock import patch, Mock, mock_open
from fastapi.testclient import TestClient
from fastapi import FastAPI
import yaml
import json

from app.api.config import router


@pytest.fixture
def app():
    """Create FastAPI app with config router"""
    app = FastAPI()
    app.include_router(router, prefix="/config")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_config():
    """Sample configuration data"""
    return {
        "app": {
            "name": "Olympian AI",
            "version": "1.0.0",
            "environment": "development"
        },
        "services": {
            "ollama": {
                "base_url": "http://localhost:11434",
                "timeout": 30
            },
            "mcp": {
                "servers": []
            }
        },
        "security": {
            "jwt_algorithm": "HS256",
            "cors_origins": ["http://localhost:3000"]
        }
    }


class TestConfigAPI:
    """Test suite for configuration API endpoints"""
    
    def test_get_config(self, client, mock_settings):
        """Test getting current configuration"""
        with patch('app.api.config.settings', mock_settings):
            response = client.get("/config")
            
            assert response.status_code == 200
            data = response.json()
            assert "environment" in data
            assert "discovered_services" in data
            assert data["environment"] == "test"
    
    
    def test_get_config_section(self, client, mock_settings):
        """Test getting specific configuration section"""
        with patch('app.api.config.settings', mock_settings):
            response = client.get("/config/discovered_services")
            
            assert response.status_code == 200
            data = response.json()
            assert "ollama" in data
            assert "endpoints" in data["ollama"]
    
    
    def test_get_config_nested_section(self, client, mock_settings):
        """Test getting nested configuration section"""
        with patch('app.api.config.settings', mock_settings):
            response = client.get("/config/discovered_services/ollama")
            
            assert response.status_code == 200
            data = response.json()
            assert "endpoints" in data
            assert "models" in data
            assert "capabilities" in data
    
    
    def test_get_config_invalid_section(self, client, mock_settings):
        """Test getting non-existent configuration section"""
        with patch('app.api.config.settings', mock_settings):
            response = client.get("/config/invalid_section")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    
    def test_update_config(self, client, sample_config):
        """Test updating configuration"""
        mock_file = mock_open()
        
        with patch('builtins.open', mock_file):
            with patch('os.path.exists', return_value=True):
                with patch('yaml.safe_load', return_value=sample_config):
                    response = client.put("/config", json={
                        "services": {
                            "ollama": {
                                "timeout": 60
                            }
                        }
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "updated"
                    
                    # Check that yaml.dump was called
                    handle = mock_file()
                    assert handle.write.called
    
    
    def test_update_config_section(self, client, sample_config):
        """Test updating specific configuration section"""
        mock_file = mock_open()
        
        with patch('builtins.open', mock_file):
            with patch('os.path.exists', return_value=True):
                with patch('yaml.safe_load', return_value=sample_config):
                    response = client.put("/config/services/ollama", json={
                        "timeout": 60,
                        "max_retries": 3
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "updated"
                    assert data["section"] == "services/ollama"
    
    
    def test_validate_config(self, client):
        """Test configuration validation"""
        config_data = {
            "app": {
                "name": "Test App"
            },
            "services": {
                "ollama": {
                    "base_url": "http://localhost:11434"
                }
            }
        }
        
        response = client.post("/config/validate", json=config_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "errors" in data
        assert len(data["errors"]) == 0
    
    
    def test_validate_config_invalid(self, client):
        """Test validation with invalid configuration"""
        config_data = {
            "services": {
                "ollama": {
                    "base_url": "not-a-url"  # Invalid URL
                }
            }
        }
        
        response = client.post("/config/validate", json=config_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
    
    
    def test_export_config(self, client, sample_config):
        """Test exporting configuration"""
        with patch('yaml.safe_load', return_value=sample_config):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=yaml.dump(sample_config))):
                    response = client.get("/config/export")
                    
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "application/x-yaml"
                    assert "attachment" in response.headers["content-disposition"]
    
    
    def test_export_config_json(self, client, sample_config):
        """Test exporting configuration as JSON"""
        with patch('yaml.safe_load', return_value=sample_config):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=yaml.dump(sample_config))):
                    response = client.get("/config/export?format=json")
                    
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "application/json"
                    data = response.json()
                    assert data == sample_config
    
    
    def test_import_config(self, client):
        """Test importing configuration"""
        config_data = {
            "app": {"name": "Imported App"},
            "services": {"ollama": {"base_url": "http://localhost:11434"}}
        }
        
        mock_file = mock_open()
        
        with patch('builtins.open', mock_file):
            with patch('os.path.exists', return_value=True):
                response = client.post("/config/import", json=config_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "imported"
                assert data["validated"] is True
    
    
    def test_reset_config(self, client):
        """Test resetting configuration to defaults"""
        default_config = {
            "app": {"name": "Olympian AI Default"},
            "services": {}
        }
        
        mock_file = mock_open()
        
        with patch('builtins.open', mock_file):
            with patch('os.path.exists', return_value=True):
                with patch('yaml.safe_load', return_value=default_config):
                    response = client.post("/config/reset")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "reset"
    
    
    def test_get_environment_info(self, client):
        """Test getting environment information"""
        with patch.dict('os.environ', {
            'NODE_ENV': 'development',
            'DATABASE_URL': 'postgresql://localhost/test',
            'API_KEY': 'secret-key'
        }):
            response = client.get("/config/environment")
            
            assert response.status_code == 200
            data = response.json()
            assert "environment_variables" in data
            assert "system_info" in data
            # API keys should be masked
            assert data["environment_variables"]["API_KEY"] == "***"
    
    
    def test_get_services_status(self, client, mock_settings):
        """Test getting services status"""
        with patch('app.api.config.settings', mock_settings):
            with patch('httpx.AsyncClient') as mock_http:
                # Mock health check responses
                mock_response = Mock()
                mock_response.status_code = 200
                mock_http.return_value.__aenter__.return_value.get = Mock(return_value=mock_response)
                
                response = client.get("/config/services/status")
                
                assert response.status_code == 200
                data = response.json()
                assert "services" in data
    
    
    def test_backup_config(self, client, sample_config):
        """Test creating configuration backup"""
        mock_file = mock_open()
        
        with patch('builtins.open', mock_file):
            with patch('os.path.exists', return_value=True):
                with patch('yaml.safe_load', return_value=sample_config):
                    with patch('os.makedirs'):
                        response = client.post("/config/backup")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["status"] == "backed_up"
                        assert "backup_file" in data
    
    
    def test_list_backups(self, client):
        """Test listing configuration backups"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=[
                'config_backup_2024_01_01_120000.yaml',
                'config_backup_2024_01_02_120000.yaml'
            ]):
                response = client.get("/config/backups")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data["backups"]) == 2
                assert data["backups"][0]["filename"].startswith("config_backup_")
    
    
    def test_restore_backup(self, client, sample_config):
        """Test restoring configuration from backup"""
        backup_file = "config_backup_2024_01_01_120000.yaml"
        mock_file = mock_open(read_data=yaml.dump(sample_config))
        
        with patch('builtins.open', mock_file):
            with patch('os.path.exists', return_value=True):
                response = client.post(f"/config/restore/{backup_file}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "restored"
                assert data["backup_file"] == backup_file
    
    
    def test_get_config_schema(self, client):
        """Test getting configuration schema"""
        response = client.get("/config/schema")
        
        assert response.status_code == 200
        data = response.json()
        assert "properties" in data
        assert "app" in data["properties"]
        assert "services" in data["properties"]
