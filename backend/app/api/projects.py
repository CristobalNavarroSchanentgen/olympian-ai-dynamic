"""Project API Routes - Divine Workspace Management"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
from loguru import logger

from ..services.project_service import ProjectService
from ..core.config import settings

router = APIRouter()
project_service = ProjectService()

# Test projects storage for compatibility
projects = {}


class ProjectCreate(BaseModel):
    """Project creation model"""
    name: str
    description: Optional[str] = None
    model: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    tools: Optional[List[str]] = None
    context_files: Optional[List[str]] = None


class ProjectUpdate(BaseModel):
    """Project update model"""
    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    tools: Optional[List[str]] = None
    active: Optional[bool] = None


@router.post("")
async def create_project(project: ProjectCreate):
    """Create a new project"""
    project_data = {
        "id": str(uuid.uuid4()),
        "name": project.name,
        "description": project.description,
        "model": project.model,
        "system_prompt": project.system_prompt,
        "temperature": project.temperature,
        "tools": project.tools or [],
        "context_files": project.context_files or [],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "active": True,
        "statistics": {
            "total_messages": 0,
            "total_tokens": 0,
            "last_used": None
        }
    }
    
    created_project = await project_service.create_project(project_data)
    return created_project


@router.get("")
async def list_projects(
    active_only: bool = False,
    limit: int = 20,
    offset: int = 0
):
    """List all projects"""
    projects = await project_service.list_projects(active_only=active_only)
    
    # Sort by updated_at
    sorted_projects = sorted(
        projects,
        key=lambda x: x["updated_at"],
        reverse=True
    )
    
    # Paginate
    total = len(sorted_projects)
    paginated = sorted_projects[offset:offset + limit]
    
    return {
        "projects": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get a specific project"""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}")
async def update_project(project_id: str, update: ProjectUpdate):
    """Update a project"""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    update_data = update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now()
    
    updated_project = await project_service.update_project(project_id, update_data)
    return updated_project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    success = await project_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "status": "deleted",
        "project_id": project_id
    }


@router.post("/{project_id}/context")
async def add_context_file(
    project_id: str,
    file: UploadFile = File(...)
):
    """Add a context file to a project"""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Read file content
    content = await file.read()
    
    # Store file
    file_id = await project_service.add_context_file(
        project_id,
        file.filename,
        content
    )
    
    return {
        "status": "added",
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content)
    }


@router.delete("/{project_id}/context/{file_id}")
async def remove_context_file(project_id: str, file_id: str):
    """Remove a context file from a project"""
    success = await project_service.remove_context_file(project_id, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "status": "removed",
        "file_id": file_id
    }


@router.get("/{project_id}/context")
async def list_context_files(project_id: str):
    """List all context files for a project"""
    files = await project_service.list_context_files(project_id)
    return {
        "files": files,
        "total": len(files)
    }


@router.post("/{project_id}/tools")
async def update_project_tools(project_id: str, tools: List[str]):
    """Update the tools enabled for a project"""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate tools against available MCP tools
    from ..services.mcp_service import mcp_service
    available_tools = await mcp_service.list_tools()
    all_available = []
    for server_tools in available_tools.values():
        all_available.extend(server_tools)
    
    invalid_tools = [t for t in tools if t not in all_available]
    if invalid_tools:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tools: {invalid_tools}"
        )
    
    # Update project
    updated = await project_service.update_project(
        project_id,
        {"tools": tools, "updated_at": datetime.now()}
    )
    
    return {
        "status": "updated",
        "tools": tools
    }


@router.post("/{project_id}/duplicate")
async def duplicate_project(project_id: str, new_name: Optional[str] = None):
    """Duplicate a project"""
    original = await project_service.get_project(project_id)
    if not original:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create duplicate
    duplicate_data = original.copy()
    duplicate_data["id"] = str(uuid.uuid4())
    duplicate_data["name"] = new_name or f"{original['name']} (Copy)"
    duplicate_data["created_at"] = datetime.now()
    duplicate_data["updated_at"] = datetime.now()
    duplicate_data["statistics"] = {
        "total_messages": 0,
        "total_tokens": 0,
        "last_used": None
    }
    
    duplicated = await project_service.create_project(duplicate_data)
    
    # Copy context files
    for file_info in original.get("context_files", []):
        # This would copy the actual files
        pass
    
    return duplicated


@router.get("/{project_id}/export")
async def export_project(project_id: str):
    """Export a project configuration"""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Remove internal fields
    export_data = {
        "version": "1.0.0",
        "exported_at": datetime.now().isoformat(),
        "project": {
            k: v for k, v in project.items()
            if k not in ["id", "created_at", "updated_at", "statistics"]
        }
    }
    
    return export_data


@router.post("/import")
async def import_project(project_data: Dict[str, Any]):
    """Import a project from export data"""
    if project_data.get("version") != "1.0.0":
        raise HTTPException(status_code=400, detail="Incompatible project version")
    
    project_config = project_data.get("project", {})
    
    # Create new project with imported data
    new_project = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "active": True,
        "statistics": {
            "total_messages": 0,
            "total_tokens": 0,
            "last_used": None
        },
        **project_config
    }
    
    created = await project_service.create_project(new_project)
    
    return {
        "status": "imported",
        "project": created
    }


@router.get("/{project_id}/statistics")
async def get_project_statistics(project_id: str):
    """Get detailed statistics for a project"""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    stats = project.get("statistics", {})
    
    # Add additional computed statistics
    enhanced_stats = {
        **stats,
        "average_message_length": 0,  # Would calculate from conversation history
        "most_used_tools": [],  # Would track tool usage
        "peak_usage_time": None,  # Would analyze usage patterns
        "estimated_cost": 0  # Would calculate based on token usage
    }
    
    return enhanced_stats


@router.post("/{project_id}/archive")
async def archive_project(project_id: str):
    """Archive a project"""
    updated = await project_service.update_project(
        project_id,
        {"active": False, "archived_at": datetime.now()}
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "status": "archived",
        "project_id": project_id
    }


@router.post("/{project_id}/restore")
async def restore_project(project_id: str):
    """Restore an archived project"""
    updated = await project_service.update_project(
        project_id,
        {"active": True, "archived_at": None}
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "status": "restored",
        "project_id": project_id
    }
