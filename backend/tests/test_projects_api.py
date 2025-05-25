"""Tests for Projects API endpoints"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.projects import router, projects


@pytest.fixture
def app():
    """Create FastAPI app with projects router"""
    app = FastAPI()
    app.include_router(router, prefix="/projects")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_projects():
    """Reset projects before each test"""
    projects.clear()
    yield projects
    projects.clear()


class TestProjectsAPI:
    """Test suite for projects API endpoints"""
    
    def test_create_project(self, client, mock_projects, mock_project_service):
        """Test creating a new project"""
        with patch('app.api.projects.project_service', mock_project_service):
            response = client.post("/projects", json={
                "name": "Test Project",
                "description": "A test project",
                "settings": {
                    "model": "llama2:7b",
                    "temperature": 0.7
                }
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Project"
            assert "id" in data
            assert len(mock_projects) == 1
    
    
    def test_create_project_missing_name(self, client):
        """Test creating project without name"""
        response = client.post("/projects", json={
            "description": "A test project"
        })
        
        assert response.status_code == 422  # Validation error
    
    
    def test_list_projects(self, client, mock_projects):
        """Test listing all projects"""
        # Create some test projects
        for i in range(3):
            project_id = f"proj-{i}"
            mock_projects[project_id] = {
                "id": project_id,
                "name": f"Project {i}",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        response = client.get("/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 3
        assert data["total"] == 3
    
    
    def test_list_projects_with_search(self, client, mock_projects):
        """Test listing projects with search filter"""
        # Create test projects
        mock_projects["proj-1"] = {"id": "proj-1", "name": "Machine Learning Project"}
        mock_projects["proj-2"] = {"id": "proj-2", "name": "Web Development"}
        mock_projects["proj-3"] = {"id": "proj-3", "name": "Data Analysis"}
        
        response = client.get("/projects?search=learning")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 1
        assert data["projects"][0]["name"] == "Machine Learning Project"
    
    
    def test_get_project(self, client, mock_projects, sample_project):
        """Test getting a specific project"""
        project_id = sample_project["id"]
        mock_projects[project_id] = sample_project
        
        response = client.get(f"/projects/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == sample_project["name"]
    
    
    def test_get_project_not_found(self, client):
        """Test getting non-existent project"""
        response = client.get("/projects/non-existent")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"
    
    
    def test_update_project(self, client, mock_projects, sample_project, mock_project_service):
        """Test updating a project"""
        project_id = sample_project["id"]
        mock_projects[project_id] = sample_project
        
        with patch('app.api.projects.project_service', mock_project_service):
            response = client.put(f"/projects/{project_id}", json={
                "name": "Updated Project",
                "description": "Updated description"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Project"
            assert "updated_at" in data
    
    
    def test_delete_project(self, client, mock_projects, mock_project_service):
        """Test deleting a project"""
        project_id = "test-project"
        mock_projects[project_id] = {"id": project_id}
        
        with patch('app.api.projects.project_service', mock_project_service):
            response = client.delete(f"/projects/{project_id}")
            
            assert response.status_code == 200
            assert response.json()["status"] == "deleted"
            assert project_id not in mock_projects
    
    
    def test_add_project_context(self, client, mock_projects, sample_project):
        """Test adding context to a project"""
        project_id = sample_project["id"]
        mock_projects[project_id] = sample_project
        
        response = client.post(f"/projects/{project_id}/context", json={
            "type": "file",
            "content": "Important context information",
            "metadata": {"filename": "context.txt"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["context"]) == 1
        assert data["context"][0]["content"] == "Important context information"
    
    
    def test_get_project_context(self, client, mock_projects, sample_project):
        """Test getting project context"""
        project_id = sample_project["id"]
        sample_project["context"] = [
            {
                "id": "ctx-1",
                "type": "file",
                "content": "Context 1"
            }
        ]
        mock_projects[project_id] = sample_project
        
        response = client.get(f"/projects/{project_id}/context")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["context"]) == 1
        assert data["total"] == 1
    
    
    def test_remove_project_context(self, client, mock_projects, sample_project):
        """Test removing context from project"""
        project_id = sample_project["id"]
        context_id = "ctx-1"
        sample_project["context"] = [
            {
                "id": context_id,
                "type": "file",
                "content": "Context to remove"
            }
        ]
        mock_projects[project_id] = sample_project
        
        response = client.delete(f"/projects/{project_id}/context/{context_id}")
        
        assert response.status_code == 200
        assert response.json()["status"] == "removed"
        assert len(mock_projects[project_id]["context"]) == 0
    
    
    def test_update_project_settings(self, client, mock_projects, sample_project):
        """Test updating project settings"""
        project_id = sample_project["id"]
        mock_projects[project_id] = sample_project
        
        response = client.put(f"/projects/{project_id}/settings", json={
            "model": "mistral:7b",
            "temperature": 0.9,
            "max_tokens": 2000
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["model"] == "mistral:7b"
        assert data["settings"]["temperature"] == 0.9
    
    
    def test_duplicate_project(self, client, mock_projects, sample_project):
        """Test duplicating a project"""
        project_id = sample_project["id"]
        mock_projects[project_id] = sample_project
        
        response = client.post(f"/projects/{project_id}/duplicate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == f"{sample_project['name']} (Copy)"
        assert data["id"] != project_id
        assert len(mock_projects) == 2
    
    
    def test_export_project(self, client, mock_projects, sample_project):
        """Test exporting a project"""
        project_id = sample_project["id"]
        mock_projects[project_id] = sample_project
        
        response = client.get(f"/projects/{project_id}/export")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers["content-disposition"]
    
    
    def test_import_project(self, client, mock_projects):
        """Test importing a project"""
        project_data = {
            "name": "Imported Project",
            "description": "An imported project",
            "settings": {"model": "llama2:7b"},
            "context": []
        }
        
        response = client.post("/projects/import", json=project_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Imported Project"
        assert "id" in data
        assert len(mock_projects) == 1
    
    
    def test_get_project_stats(self, client, mock_projects, sample_project):
        """Test getting project statistics"""
        project_id = sample_project["id"]
        sample_project["conversations"] = ["conv-1", "conv-2"]
        sample_project["context"] = [{"id": "ctx-1"}, {"id": "ctx-2"}, {"id": "ctx-3"}]
        mock_projects[project_id] = sample_project
        
        response = client.get(f"/projects/{project_id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_count"] == 2
        assert data["context_count"] == 3
        assert "created_at" in data
    
    
    def test_archive_project(self, client, mock_projects, sample_project):
        """Test archiving a project"""
        project_id = sample_project["id"]
        mock_projects[project_id] = sample_project
        
        response = client.post(f"/projects/{project_id}/archive")
        
        assert response.status_code == 200
        data = response.json()
        assert data["archived"] is True
        assert mock_projects[project_id]["archived"] is True
    
    
    def test_unarchive_project(self, client, mock_projects, sample_project):
        """Test unarchiving a project"""
        project_id = sample_project["id"]
        sample_project["archived"] = True
        mock_projects[project_id] = sample_project
        
        response = client.post(f"/projects/{project_id}/unarchive")
        
        assert response.status_code == 200
        data = response.json()
        assert data["archived"] is False
        assert mock_projects[project_id]["archived"] is False
    
    
    def test_list_archived_projects(self, client, mock_projects):
        """Test listing only archived projects"""
        # Create mix of archived and active projects
        mock_projects["proj-1"] = {"id": "proj-1", "name": "Active", "archived": False}
        mock_projects["proj-2"] = {"id": "proj-2", "name": "Archived 1", "archived": True}
        mock_projects["proj-3"] = {"id": "proj-3", "name": "Archived 2", "archived": True}
        
        response = client.get("/projects?archived=true")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 2
        assert all(p["archived"] for p in data["projects"])
    
    
    def test_batch_delete_projects(self, client, mock_projects, mock_project_service):
        """Test deleting multiple projects at once"""
        # Create test projects
        project_ids = ["proj-1", "proj-2", "proj-3"]
        for pid in project_ids:
            mock_projects[pid] = {"id": pid}
        
        with patch('app.api.projects.project_service', mock_project_service):
            response = client.post("/projects/batch/delete", json={
                "project_ids": ["proj-1", "proj-3"]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["deleted_count"] == 2
            assert len(mock_projects) == 1
            assert "proj-2" in mock_projects
