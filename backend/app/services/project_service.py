"""Project Service - Divine Workspace Management"""
import asyncio
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime
from pathlib import Path
import aiofiles
from loguru import logger

from ..core.config import settings


class ProjectService:
    """Service for managing AI projects and workspaces"""
    
    def __init__(self):
        self._projects: Dict[str, Dict[str, Any]] = {}
        self._project_files: Dict[str, Dict[str, Any]] = {}
        self._projects_dir = settings.data_dir / "projects"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure project directories exist"""
        self._projects_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project"""
        project_id = project_data["id"]
        
        # Create project directory
        project_dir = self._projects_dir / project_id
        project_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (project_dir / "context").mkdir(exist_ok=True)
        (project_dir / "outputs").mkdir(exist_ok=True)
        (project_dir / "conversations").mkdir(exist_ok=True)
        
        # Store project data
        self._projects[project_id] = project_data
        
        # Save project metadata
        await self._save_project_metadata(project_id, project_data)
        
        logger.info(f"Project created: {project_id} - {project_data['name']}")
        return project_data
    
    async def _save_project_metadata(self, project_id: str, project_data: Dict[str, Any]):
        """Save project metadata to file"""
        project_dir = self._projects_dir / project_id
        metadata_file = project_dir / "project.json"
        
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(project_data, indent=2, default=str))
    
    async def load_projects(self):
        """Load all projects from disk"""
        for project_dir in self._projects_dir.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / "project.json"
                if metadata_file.exists():
                    async with aiofiles.open(metadata_file, 'r') as f:
                        content = await f.read()
                        project_data = json.loads(content)
                        self._projects[project_data["id"]] = project_data
        
        logger.info(f"Loaded {len(self._projects)} projects")
    
    async def list_projects(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all projects"""
        projects = list(self._projects.values())
        
        if active_only:
            projects = [p for p in projects if p.get("active", True)]
        
        return projects
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        return self._projects.get(project_id)
    
    async def update_project(
        self,
        project_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update project data"""
        if project_id not in self._projects:
            return None
        
        project = self._projects[project_id]
        project.update(update_data)
        
        # Save updated metadata
        await self._save_project_metadata(project_id, project)
        
        return project
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        if project_id not in self._projects:
            return False
        
        # Remove from memory
        del self._projects[project_id]
        
        # Remove project directory
        project_dir = self._projects_dir / project_id
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
        
        logger.info(f"Project deleted: {project_id}")
        return True
    
    async def add_context_file(
        self,
        project_id: str,
        filename: str,
        content: bytes
    ) -> str:
        """Add a context file to a project"""
        if project_id not in self._projects:
            raise ValueError("Project not found")
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        
        # Save file
        context_dir = self._projects_dir / project_id / "context"
        file_path = context_dir / f"{file_id}_{filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Store file metadata
        if project_id not in self._project_files:
            self._project_files[project_id] = {}
        
        self._project_files[project_id][file_id] = {
            "id": file_id,
            "filename": filename,
            "path": str(file_path),
            "size": len(content),
            "added_at": datetime.now().isoformat(),
            "content_type": self._guess_content_type(filename)
        }
        
        # Update project metadata
        project = self._projects[project_id]
        if "context_files" not in project:
            project["context_files"] = []
        project["context_files"].append(file_id)
        await self._save_project_metadata(project_id, project)
        
        logger.info(f"Context file added to project {project_id}: {filename}")
        return file_id
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        ext = Path(filename).suffix.lower()
        content_types = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
            ".py": "text/x-python",
            ".js": "text/javascript",
            ".ts": "text/typescript",
            ".html": "text/html",
            ".css": "text/css",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg"
        }
        return content_types.get(ext, "application/octet-stream")
    
    async def remove_context_file(
        self,
        project_id: str,
        file_id: str
    ) -> bool:
        """Remove a context file from a project"""
        if project_id not in self._project_files:
            return False
        
        if file_id not in self._project_files[project_id]:
            return False
        
        # Get file info
        file_info = self._project_files[project_id][file_id]
        file_path = Path(file_info["path"])
        
        # Remove file
        if file_path.exists():
            file_path.unlink()
        
        # Remove from metadata
        del self._project_files[project_id][file_id]
        
        # Update project
        project = self._projects[project_id]
        if "context_files" in project:
            project["context_files"] = [
                fid for fid in project["context_files"] if fid != file_id
            ]
            await self._save_project_metadata(project_id, project)
        
        return True
    
    async def list_context_files(self, project_id: str) -> List[Dict[str, Any]]:
        """List all context files for a project"""
        if project_id not in self._project_files:
            return []
        
        return list(self._project_files[project_id].values())
    
    async def get_context_file_content(
        self,
        project_id: str,
        file_id: str
    ) -> Optional[bytes]:
        """Get content of a context file"""
        if project_id not in self._project_files:
            return None
        
        if file_id not in self._project_files[project_id]:
            return None
        
        file_info = self._project_files[project_id][file_id]
        file_path = Path(file_info["path"])
        
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def get_project_context(
        self,
        project_id: str,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all context for a project"""
        context = []
        
        # Get context files
        files = await self.list_context_files(project_id)
        
        for file_info in files:
            context_item = {
                "type": "file",
                "filename": file_info["filename"],
                "content_type": file_info["content_type"],
                "size": file_info["size"]
            }
            
            if include_content:
                content = await self.get_context_file_content(
                    project_id,
                    file_info["id"]
                )
                if content:
                    # Only include text content
                    if file_info["content_type"].startswith("text/"):
                        try:
                            context_item["content"] = content.decode('utf-8')
                        except:
                            context_item["content"] = "[Binary content]"
                    else:
                        context_item["content"] = "[Binary content]"
            
            context.append(context_item)
        
        return context
    
    async def save_project_output(
        self,
        project_id: str,
        output_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save project output (generation result)"""
        if project_id not in self._projects:
            raise ValueError("Project not found")
        
        # Generate output ID
        output_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Create filename
        filename = f"{output_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{output_id[:8]}"
        
        # Determine file extension
        extensions = {
            "code": ".py",
            "document": ".md",
            "image": ".png",
            "audio": ".mp3",
            "video": ".mp4"
        }
        filename += extensions.get(output_type, ".txt")
        
        # Save file
        output_dir = self._projects_dir / project_id / "outputs"
        file_path = output_dir / filename
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(content)
        
        # Store output metadata
        output_info = {
            "id": output_id,
            "type": output_type,
            "filename": filename,
            "path": str(file_path),
            "created_at": timestamp.isoformat(),
            "metadata": metadata or {}
        }
        
        # Update project statistics
        project = self._projects[project_id]
        stats = project.get("statistics", {})
        stats["last_used"] = timestamp.isoformat()
        project["statistics"] = stats
        await self._save_project_metadata(project_id, project)
        
        logger.info(f"Saved {output_type} output for project {project_id}")
        return output_id
    
    async def export_project(self, project_id: str) -> Dict[str, Any]:
        """Export project with all data"""
        project = self._projects.get(project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Get all context files
        context_files = []
        for file_info in await self.list_context_files(project_id):
            content = await self.get_context_file_content(project_id, file_info["id"])
            if content:
                context_files.append({
                    "filename": file_info["filename"],
                    "content_type": file_info["content_type"],
                    "content": content.decode('utf-8') if file_info["content_type"].startswith("text/") else None
                })
        
        # Create export package
        export_data = {
            "version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "project": project,
            "context_files": context_files
        }
        
        return export_data
    
    async def import_project(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import project from export data"""
        if export_data.get("version") != "1.0.0":
            raise ValueError("Incompatible export version")
        
        # Extract project data
        project_data = export_data["project"]
        
        # Generate new project ID
        new_project_id = str(uuid.uuid4())
        project_data["id"] = new_project_id
        project_data["created_at"] = datetime.now()
        project_data["updated_at"] = datetime.now()
        
        # Create project
        created_project = await self.create_project(project_data)
        
        # Import context files
        for file_data in export_data.get("context_files", []):
            if file_data.get("content"):
                await self.add_context_file(
                    new_project_id,
                    file_data["filename"],
                    file_data["content"].encode('utf-8')
                )
        
        return created_project