"""Tests for MCP API endpoints"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

from app.api.mcp import router


@pytest.fixture
def app():
    """Create FastAPI app with MCP router"""
    app = FastAPI()
    app.include_router(router, prefix="/mcp")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_mcp_servers():
    """Mock MCP servers data"""
    return {
        "server-1": {
            "id": "server-1",
            "name": "Test MCP Server",
            "command": "npx",
            "args": ["test-server"],
            "status": "connected",
            "tools": ["tool1", "tool2"]
        }
    }


class TestMCPAPI:
    """Test suite for MCP API endpoints"""
    
    def test_list_servers(self, client, mock_mcp_service):
        """Test listing MCP servers"""
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.get("/mcp/servers")
            
            assert response.status_code == 200
            data = response.json()
            assert "servers" in data
    
    
    def test_connect_server(self, client, mock_mcp_service):
        """Test connecting to an MCP server"""
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.post("/mcp/servers/connect", json={
                "name": "Test Server",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-filesystem"]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "connected"
    
    
    def test_connect_server_invalid_command(self, client):
        """Test connecting with invalid command"""
        response = client.post("/mcp/servers/connect", json={
            "name": "Test Server",
            "command": "",
            "args": []
        })
        
        assert response.status_code == 422
    
    
    def test_disconnect_server(self, client, mock_mcp_service):
        """Test disconnecting from an MCP server"""
        server_id = "server-123"
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.post(f"/mcp/servers/{server_id}/disconnect")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "disconnected"
    
    
    def test_get_server_info(self, client, mock_mcp_service, mock_mcp_servers):
        """Test getting MCP server information"""
        server_id = "server-1"
        mock_mcp_service.get_server_info = AsyncMock(return_value=mock_mcp_servers["server-1"])
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.get(f"/mcp/servers/{server_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == server_id
            assert data["name"] == "Test MCP Server"
    
    
    def test_list_tools(self, client, mock_mcp_service):
        """Test listing available MCP tools"""
        mock_tools = [
            {
                "name": "read_file",
                "description": "Read file contents",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}
            },
            {
                "name": "write_file",
                "description": "Write file contents",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}
            }
        ]
        mock_mcp_service.list_tools = AsyncMock(return_value=mock_tools)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.get("/mcp/tools")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["tools"]) == 2
            assert data["tools"][0]["name"] == "read_file"
    
    
    def test_execute_tool(self, client, mock_mcp_service):
        """Test executing an MCP tool"""
        mock_result = {"content": "File contents", "success": True}
        mock_mcp_service.execute_tool = AsyncMock(return_value=mock_result)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.post("/mcp/tools/execute", json={
                "server_id": "server-1",
                "tool_name": "read_file",
                "arguments": {"path": "/test/file.txt"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["result"]["success"] is True
    
    
    def test_execute_tool_invalid_server(self, client, mock_mcp_service):
        """Test executing tool with invalid server"""
        mock_mcp_service.execute_tool = AsyncMock(side_effect=Exception("Server not found"))
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.post("/mcp/tools/execute", json={
                "server_id": "invalid",
                "tool_name": "read_file",
                "arguments": {}
            })
            
            assert response.status_code == 500
    
    
    def test_list_resources(self, client, mock_mcp_service):
        """Test listing MCP resources"""
        mock_resources = [
            {
                "uri": "file:///path/to/resource",
                "name": "test.txt",
                "mime_type": "text/plain"
            }
        ]
        mock_mcp_service.list_resources = AsyncMock(return_value=mock_resources)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.get("/mcp/resources?server_id=server-1")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["resources"]) == 1
            assert data["resources"][0]["name"] == "test.txt"
    
    
    def test_read_resource(self, client, mock_mcp_service):
        """Test reading an MCP resource"""
        mock_content = {"content": "Resource content", "mime_type": "text/plain"}
        mock_mcp_service.read_resource = AsyncMock(return_value=mock_content)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.post("/mcp/resources/read", json={
                "server_id": "server-1",
                "uri": "file:///path/to/resource"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "Resource content"
    
    
    def test_list_prompts(self, client, mock_mcp_service):
        """Test listing MCP prompts"""
        mock_prompts = [
            {
                "name": "summarize",
                "description": "Summarize content",
                "arguments": [{"name": "content", "required": True}]
            }
        ]
        mock_mcp_service.list_prompts = AsyncMock(return_value=mock_prompts)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.get("/mcp/prompts?server_id=server-1")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["prompts"]) == 1
            assert data["prompts"][0]["name"] == "summarize"
    
    
    def test_get_prompt(self, client, mock_mcp_service):
        """Test getting a specific MCP prompt"""
        mock_prompt = {
            "prompt": "Summarize the following: {content}",
            "arguments": {"content": "Test content"}
        }
        mock_mcp_service.get_prompt = AsyncMock(return_value=mock_prompt)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.post("/mcp/prompts/get", json={
                "server_id": "server-1",
                "prompt_name": "summarize",
                "arguments": {"content": "Test content"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "Summarize the following" in data["prompt"]
    
    
    def test_server_health_check(self, client, mock_mcp_service):
        """Test MCP server health check"""
        mock_health = {
            "server-1": {"status": "healthy", "uptime": 3600},
            "server-2": {"status": "unhealthy", "error": "Connection lost"}
        }
        mock_mcp_service.health_check_all = AsyncMock(return_value=mock_health)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.get("/mcp/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["servers"]["server-1"]["status"] == "healthy"
            assert data["servers"]["server-2"]["status"] == "unhealthy"
    
    
    def test_reload_server(self, client, mock_mcp_service):
        """Test reloading an MCP server"""
        server_id = "server-1"
        mock_mcp_service.reload_server = AsyncMock(return_value={"status": "reloaded"})
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.post(f"/mcp/servers/{server_id}/reload")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "reloaded"
    
    
    def test_get_server_logs(self, client, mock_mcp_service):
        """Test getting MCP server logs"""
        server_id = "server-1"
        mock_logs = [
            {"timestamp": "2024-01-01T00:00:00Z", "level": "info", "message": "Server started"},
            {"timestamp": "2024-01-01T00:01:00Z", "level": "error", "message": "Connection error"}
        ]
        mock_mcp_service.get_server_logs = AsyncMock(return_value=mock_logs)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.get(f"/mcp/servers/{server_id}/logs")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["logs"]) == 2
            assert data["logs"][1]["level"] == "error"
    
    
    def test_update_server_config(self, client, mock_mcp_service):
        """Test updating MCP server configuration"""
        server_id = "server-1"
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.put(f"/mcp/servers/{server_id}/config", json={
                "env": {"API_KEY": "new-key"},
                "args": ["--verbose"]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"
    
    
    def test_batch_execute_tools(self, client, mock_mcp_service):
        """Test executing multiple tools in batch"""
        mock_results = [
            {"tool": "read_file", "result": {"content": "File 1"}},
            {"tool": "read_file", "result": {"content": "File 2"}}
        ]
        mock_mcp_service.batch_execute = AsyncMock(return_value=mock_results)
        
        with patch('app.api.mcp.mcp_service', mock_mcp_service):
            response = client.post("/mcp/tools/batch", json={
                "executions": [
                    {
                        "server_id": "server-1",
                        "tool_name": "read_file",
                        "arguments": {"path": "/file1.txt"}
                    },
                    {
                        "server_id": "server-1",
                        "tool_name": "read_file",
                        "arguments": {"path": "/file2.txt"}
                    }
                ]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 2
