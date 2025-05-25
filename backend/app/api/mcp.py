"""MCP API Routes - Divine Tool Management"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from loguru import logger

from ..services.mcp_service import MCPService
from ..core.config import settings

router = APIRouter()
mcp_service = MCPService()


class ToolExecutionRequest(BaseModel):
    """Tool execution request model"""
    server_id: str
    tool_name: str
    parameters: Dict[str, Any]


class FileOperationRequest(BaseModel):
    """File operation request model"""
    path: str
    content: Optional[str] = None
    server_id: Optional[str] = None


class GitOperationRequest(BaseModel):
    """Git operation request model"""
    operation: str
    params: Dict[str, Any]
    server_id: Optional[str] = None


@router.on_event("startup")
async def startup():
    """Initialize MCP service on startup"""
    await mcp_service.initialize()


@router.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await mcp_service.close()


@router.get("/discover")
async def discover_mcp_servers():
    """Discover available MCP servers"""
    from ..core.discovery import discovery_engine
    
    result = await discovery_engine.discover_mcp_servers()
    return {
        "status": "success",
        "discovered": result
    }


@router.post("/auto-configure")
async def auto_configure_servers():
    """Auto-configure all discovered MCP servers"""
    # Reinitialize with latest discoveries
    await mcp_service.initialize()
    
    configured = mcp_service.get_connected_servers()
    
    # Update configuration
    settings.discovered_services.mcp_servers["configured"] = configured
    settings.save_config()
    
    return {
        "status": "configured",
        "servers": configured
    }


@router.get("/servers")
async def get_connected_servers():
    """Get list of connected MCP servers"""
    return {
        "servers": mcp_service.get_connected_servers(),
        "total": len(mcp_service.get_connected_servers())
    }


@router.get("/tools")
async def list_all_tools():
    """List all available tools from all MCP servers"""
    tools = await mcp_service.list_tools()
    
    # Flatten tools list
    all_tools = []
    for server_id, server_tools in tools.items():
        for tool in server_tools:
            all_tools.append({
                "server_id": server_id,
                "tool_name": tool
            })
    
    return {
        "tools_by_server": tools,
        "all_tools": all_tools,
        "total_tools": len(all_tools)
    }


@router.get("/capabilities")
async def get_all_capabilities():
    """Get capabilities of all connected MCP servers"""
    capabilities = {}
    
    for server in mcp_service.get_connected_servers():
        server_id = server["id"]
        capabilities[server_id] = {
            "type": server["type"],
            "endpoint": server["endpoint"],
            "tools": server["tools"],
            "capabilities": server.get("capabilities", {})
        }
    
    return capabilities


@router.post("/tools/execute")
async def execute_tool(request: ToolExecutionRequest):
    """Execute a tool on an MCP server"""
    result = await mcp_service.execute_tool(
        server_id=request.server_id,
        tool_name=request.tool_name,
        parameters=request.parameters
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Tool execution failed"))
    
    return result


@router.get("/tools/{server_id}/{tool_name}/schema")
async def get_tool_schema(server_id: str, tool_name: str):
    """Get the schema for a specific tool"""
    schema = await mcp_service.get_tool_schema(server_id, tool_name)
    
    if not schema:
        raise HTTPException(status_code=404, detail="Tool schema not found")
    
    return schema


@router.post("/filesystem/read")
async def read_file(request: FileOperationRequest):
    """Read a file using filesystem MCP server"""
    result = await mcp_service.filesystem_read(
        path=request.path,
        server_id=request.server_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "File read failed"))
    
    return result


@router.post("/filesystem/write")
async def write_file(request: FileOperationRequest):
    """Write a file using filesystem MCP server"""
    if request.content is None:
        raise HTTPException(status_code=400, detail="Content is required for write operation")
    
    result = await mcp_service.filesystem_write(
        path=request.path,
        content=request.content,
        server_id=request.server_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "File write failed"))
    
    return result


@router.post("/git")
async def git_operation(request: GitOperationRequest):
    """Perform git operations using git MCP server"""
    result = await mcp_service.git_operations(
        operation=request.operation,
        params=request.params,
        server_id=request.server_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Git operation failed"))
    
    return result


@router.post("/github")
async def github_operation(request: GitOperationRequest):
    """Perform GitHub operations using GitHub MCP server"""
    result = await mcp_service.github_operations(
        operation=request.operation,
        params=request.params,
        server_id=request.server_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "GitHub operation failed"))
    
    return result


@router.post("/servers/{server_id}/test")
async def test_server_connection(server_id: str):
    """Test connection to a specific MCP server"""
    connected = await mcp_service.test_server_connection(server_id)
    
    return {
        "server_id": server_id,
        "connected": connected,
        "status": "healthy" if connected else "unreachable"
    }


@router.post("/bulk-connect")
async def bulk_connect_servers(server_ids: List[str]):
    """Connect to multiple MCP servers at once"""
    results = {}
    
    for server_id in server_ids:
        connected = await mcp_service.test_server_connection(server_id)
        results[server_id] = {
            "connected": connected,
            "status": "connected" if connected else "failed"
        }
    
    return {
        "results": results,
        "total_requested": len(server_ids),
        "total_connected": sum(1 for r in results.values() if r["connected"])
    }