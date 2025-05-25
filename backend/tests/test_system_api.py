"""Tests for System API endpoints"""
import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI
import psutil
import platform

from app.api.system import router


@pytest.fixture
def app():
    """Create FastAPI app with system router"""
    app = FastAPI()
    app.include_router(router, prefix="/system")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_system_info():
    """Mock system information"""
    return {
        "cpu": {
            "count": 8,
            "percent": 25.5,
            "frequency": {"current": 2400, "min": 800, "max": 3600}
        },
        "memory": {
            "total": 16 * 1024**3,  # 16GB
            "available": 8 * 1024**3,  # 8GB
            "percent": 50.0,
            "used": 8 * 1024**3
        },
        "disk": {
            "total": 500 * 1024**3,  # 500GB
            "used": 200 * 1024**3,  # 200GB
            "free": 300 * 1024**3,  # 300GB
            "percent": 40.0
        },
        "gpu": {
            "available": True,
            "devices": [{"name": "NVIDIA RTX 3080", "memory": "10GB"}]
        }
    }


class TestSystemAPI:
    """Test suite for system API endpoints"""
    
    def test_get_system_info(self, client):
        """Test getting system information"""
        with patch('psutil.cpu_count', return_value=8):
            with patch('psutil.cpu_percent', return_value=25.5):
                with patch('psutil.virtual_memory') as mock_mem:
                    mock_mem.return_value = MagicMock(
                        total=16 * 1024**3,
                        available=8 * 1024**3,
                        percent=50.0
                    )
                    
                    response = client.get("/system/info")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "cpu" in data
                    assert "memory" in data
                    assert "disk" in data
                    assert data["cpu"]["count"] == 8
    
    
    def test_get_system_health(self, client):
        """Test system health check"""
        response = client.get("/system/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime" in data
        assert "checks" in data
    
    
    def test_get_system_metrics(self, client):
        """Test getting system metrics"""
        response = client.get("/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "metrics" in data
        assert "cpu_percent" in data["metrics"]
        assert "memory_percent" in data["metrics"]
    
    
    def test_get_system_processes(self, client):
        """Test listing system processes"""
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_process.name.return_value = "python"
        mock_process.cpu_percent.return_value = 5.0
        mock_process.memory_percent.return_value = 2.5
        mock_process.status.return_value = "running"
        
        with patch('psutil.process_iter', return_value=[mock_process]):
            response = client.get("/system/processes?sort_by=cpu")
            
            assert response.status_code == 200
            data = response.json()
            assert "processes" in data
            assert len(data["processes"]) > 0
            assert data["processes"][0]["name"] == "python"
    
    
    def test_kill_process(self, client):
        """Test killing a process"""
        pid = 1234
        mock_process = MagicMock()
        
        with patch('psutil.Process', return_value=mock_process):
            response = client.delete(f"/system/processes/{pid}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "terminated"
            assert data["pid"] == pid
            mock_process.terminate.assert_called_once()
    
    
    def test_kill_process_not_found(self, client):
        """Test killing non-existent process"""
        with patch('psutil.Process', side_effect=psutil.NoSuchProcess(9999)):
            response = client.delete("/system/processes/9999")
            
            assert response.status_code == 404
            assert "Process not found" in response.json()["detail"]
    
    
    def test_get_network_info(self, client):
        """Test getting network information"""
        mock_stats = MagicMock()
        mock_stats.bytes_sent = 1000000
        mock_stats.bytes_recv = 2000000
        mock_stats.packets_sent = 1000
        mock_stats.packets_recv = 2000
        
        with patch('psutil.net_io_counters', return_value=mock_stats):
            response = client.get("/system/network")
            
            assert response.status_code == 200
            data = response.json()
            assert "interfaces" in data
            assert "stats" in data
            assert data["stats"]["bytes_sent"] == 1000000
    
    
    def test_get_docker_info(self, client):
        """Test getting Docker information"""
        mock_docker = MagicMock()
        mock_docker.version.return_value = {"Version": "20.10.0"}
        mock_docker.containers.list.return_value = [
            MagicMock(name="container1", status="running"),
            MagicMock(name="container2", status="exited")
        ]
        
        with patch('docker.from_env', return_value=mock_docker):
            response = client.get("/system/docker")
            
            assert response.status_code == 200
            data = response.json()
            assert data["docker_installed"] is True
            assert data["version"] == "20.10.0"
            assert len(data["containers"]) == 2
    
    
    def test_optimize_system(self, client):
        """Test system optimization endpoint"""
        response = client.post("/system/optimize")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "optimized"
        assert "actions" in data
    
    
    def test_clear_cache(self, client):
        """Test clearing system cache"""
        response = client.post("/system/cache/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"
        assert "freed_space" in data
    
    
    def test_get_logs(self, client):
        """Test getting system logs"""
        with patch('builtins.open', mock_open(read_data="Log line 1\nLog line 2\n")):
            response = client.get("/system/logs?lines=10")
            
            assert response.status_code == 200
            data = response.json()
            assert "logs" in data
            assert len(data["logs"]) > 0
    
    
    def test_get_gpu_info(self, client):
        """Test getting GPU information"""
        # Test when GPUtil is available
        mock_gpu = MagicMock()
        mock_gpu.name = "NVIDIA RTX 3080"
        mock_gpu.memoryTotal = 10240
        mock_gpu.memoryUsed = 2048
        mock_gpu.load = 0.15
        
        with patch('GPUtil.getGPUs', return_value=[mock_gpu]):
            response = client.get("/system/gpu")
            
            assert response.status_code == 200
            data = response.json()
            assert data["available"] is True
            assert len(data["devices"]) == 1
            assert data["devices"][0]["name"] == "NVIDIA RTX 3080"
    
    
    def test_get_temperature_info(self, client):
        """Test getting temperature information"""
        mock_temps = {
            "coretemp": [
                MagicMock(label="Core 0", current=45.0, high=80.0, critical=100.0),
                MagicMock(label="Core 1", current=47.0, high=80.0, critical=100.0)
            ]
        }
        
        with patch('psutil.sensors_temperatures', return_value=mock_temps):
            response = client.get("/system/temperature")
            
            assert response.status_code == 200
            data = response.json()
            assert "temperatures" in data
            assert "coretemp" in data["temperatures"]
    
    
    def test_restart_service(self, client):
        """Test restarting a system service"""
        response = client.post("/system/services/ollama/restart")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "restarted"
        assert data["service"] == "ollama"
    
    
    def test_get_environment_variables(self, client):
        """Test getting environment variables"""
        with patch.dict('os.environ', {'TEST_VAR': 'test_value', 'API_KEY': 'secret'}):
            response = client.get("/system/env")
            
            assert response.status_code == 200
            data = response.json()
            assert "variables" in data
            assert data["variables"]["TEST_VAR"] == "test_value"
            # API keys should be masked
            assert data["variables"]["API_KEY"] == "***"
    
    
    def test_system_benchmark(self, client):
        """Test running system benchmark"""
        response = client.post("/system/benchmark")
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "cpu_score" in data["results"]
        assert "memory_score" in data["results"]
        assert "disk_score" in data["results"]
    
    
    def test_get_system_alerts(self, client):
        """Test getting system alerts"""
        response = client.get("/system/alerts")
        
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
    
    
    def test_schedule_maintenance(self, client):
        """Test scheduling system maintenance"""
        response = client.post("/system/maintenance", json={
            "type": "cleanup",
            "schedule": "daily",
            "time": "02:00"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scheduled"
        assert data["type"] == "cleanup"
    
    
    def test_export_system_report(self, client):
        """Test exporting system report"""
        response = client.get("/system/report/export?format=json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "system_info" in data
        assert "timestamp" in data
        assert "health_status" in data
