"""MCP Service - Divine Tool Integration"""
import asyncio
from typing import Dict, List, Any, Optional
import httpx
from loguru import logger
import json

from ..core.config import settings


class MCPService:
    """Service for managing Model Context Protocol servers"""
    
    def __init__(self):
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._available_tools: Dict[str, List[str]] = {}
    
    async def initialize(self):
        """Initialize MCP service with discovered servers"""
        # Fix: access discovered_services as a dictionary
        mcp_config = settings.discovered_services.get("mcp_servers", {})
        servers = mcp_config.get("available", [])
        
        # If no discovered servers, use configured MCP servers
        if not servers and settings.mcp_servers:
            servers = settings.mcp_servers
        
        for server in servers:
            endpoint = server.get("endpoint")
            server_id = server.get("id")
            
            if not endpoint or not server_id:
                logger.warning(f"Skipping invalid MCP server config: {server}")
                continue
            
            self._servers[server_id] = server
            self._clients[server_id] = httpx.AsyncClient(
                base_url=endpoint,
                timeout=httpx.Timeout(30.0, connect=5.0)
            )
            
            # Get available tools
            tools = await self._get_server_tools(server_id)
            if tools:
                self._available_tools[server_id] = tools
        
        logger.info(f"MCP service initialized with {len(self._servers)} servers")
    
    async def _get_server_tools(self, server_id: str) -> List[str]:
        """Get available tools from MCP server"""
        client = self._clients.get(server_id)
        if not client:
            return []
        
        try:
            response = await client.get("/tools")
            if response.status_code == 200:
                data = response.json()
                return [tool["name"] for tool in data.get("tools", [])]
        except Exception as e:
            logger.error(f"Error getting tools from {server_id}: {e}")
        
        return []
    
    async def list_tools(self) -> Dict[str, List[str]]:
        """List all available tools from all MCP servers"""
        return self._available_tools.copy()
    
    async def execute_tool(
        self,
        server_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool on an MCP server"""
        client = self._clients.get(server_id)
        if not client:
            return {
                "error": f"MCP server {server_id} not found",
                "success": False
            }
        
        try:
            response = await client.post(
                f"/tools/{tool_name}/execute",
                json=parameters
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "result": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Tool execution failed with status {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name} on {server_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_tool_schema(
        self,
        server_id: str,
        tool_name: str
    ) -> Dict[str, Any]:
        """Get the schema/parameters for a specific tool"""
        client = self._clients.get(server_id)
        if not client:
            return {}
        
        try:
            response = await client.get(f"/tools/{tool_name}/schema")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting tool schema: {e}")
        
        return {}
    
    async def filesystem_read(
        self,
        path: str,
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Read file using filesystem MCP server"""
        # Find filesystem server
        if not server_id:
            for sid, server in self._servers.items():
                if server.get("type") == "filesystem":
                    server_id = sid
                    break
        
        if not server_id:
            return {
                "success": False,
                "error": "No filesystem MCP server available"
            }
        
        return await self.execute_tool(
            server_id,
            "read_file",
            {"path": path}
        )
    
    async def filesystem_write(
        self,
        path: str,
        content: str,
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Write file using filesystem MCP server"""
        # Find filesystem server
        if not server_id:
            for sid, server in self._servers.items():
                if server.get("type") == "filesystem":
                    server_id = sid
                    break
        
        if not server_id:
            return {
                "success": False,
                "error": "No filesystem MCP server available"
            }
        
        return await self.execute_tool(
            server_id,
            "write_file",
            {"path": path, "content": content}
        )
    
    async def git_operations(
        self,
        operation: str,
        params: Dict[str, Any],
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform git operations using git MCP server"""
        # Find git server
        if not server_id:
            for sid, server in self._servers.items():
                if server.get("type") == "git":
                    server_id = sid
                    break
        
        if not server_id:
            return {
                "success": False,
                "error": "No git MCP server available"
            }
        
        return await self.execute_tool(server_id, operation, params)
    
    async def github_operations(
        self,
        operation: str,
        params: Dict[str, Any],
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform GitHub operations using GitHub MCP server"""
        # Find GitHub server
        if not server_id:
            for sid, server in self._servers.items():
                if server.get("type") == "github":
                    server_id = sid
                    break
        
        if not server_id:
            return {
                "success": False,
                "error": "No GitHub MCP server available"
            }
        
        return await self.execute_tool(server_id, operation, params)
    
    def is_connected(self) -> bool:
        """Check if any MCP servers are connected"""
        return len(self._servers) > 0
    
    def get_connected_servers(self) -> List[Dict[str, Any]]:
        """Get list of connected MCP servers"""
        return [
            {
                "id": server_id,
                **server_info,
                "tools": self._available_tools.get(server_id, [])
            }
            for server_id, server_info in self._servers.items()
        ]
    
    async def test_server_connection(self, server_id: str) -> bool:
        """Test connection to a specific MCP server"""
        client = self._clients.get(server_id)
        if not client:
            return False
        
        try:
            response = await client.get("/health")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close all HTTP clients"""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()
        self._servers.clear()
        self._available_tools.clear()
