"""Tests for Project Service"""
import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from datetime import datetime
import json
import os

from app.services.project_service import ProjectService


@pytest.fixture
def project_service():
    """Create ProjectService instance"""
    return ProjectService()


@pytest.fixture
def sample_project_data():
    """Sample project data for testing"""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing",
        "settings": {
            "model": "llama2:7b",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "tags": ["test", "development"],
        "metadata": {
            "author": "Test User",
            "version": "1.0.0"
        }
    }


class TestProjectService:
    """Test suite for Project service"""
    
    @pytest.mark.asyncio
    async def test_create_project(self, project_service, sample_project_data):
        """Test creating a new project"""
        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()):
                project = await project_service.create_project(sample_project_data)
                
                assert "id" in project
                assert project["name"] == sample_project_data["name"]
                assert project["description"] == sample_project_data["description"]
                assert "created_at" in project
                assert "updated_at" in project
                assert project["context"] == []
    
    
    @pytest.mark.asyncio
    async def test_get_project(self, project_service):
        """Test getting a project by ID"""
        project_id = "test-project-123"
        mock_project_data = {
            "id": project_id,
            "name": "Test Project",
            "created_at": datetime.now().isoformat()
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_project_data))):
                project = await project_service.get_project(project_id)
                
                assert project["id"] == project_id
                assert project["name"] == "Test Project"
    
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, project_service):
        """Test getting non-existent project"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(Exception) as exc_info:
                await project_service.get_project("non-existent")
            
            assert "not found" in str(exc_info.value).lower()
    
    
    @pytest.mark.asyncio
    async def test_list_projects(self, project_service):
        """Test listing all projects"""
        mock_projects = ["project1.json", "project2.json", "not-a-project.txt"]
        mock_project_data = {
            "id": "test-id",
            "name": "Test Project",
            "created_at": datetime.now().isoformat()
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=mock_projects):
                with patch('builtins.open', mock_open(read_data=json.dumps(mock_project_data))):
                    projects = await project_service.list_projects()
                    
                    assert len(projects) == 2  # Only .json files
                    assert all(p["name"] == "Test Project" for p in projects)
    
    
    @pytest.mark.asyncio
    async def test_update_project(self, project_service):
        """Test updating a project"""
        project_id = "test-project-123"
        existing_data = {
            "id": project_id,
            "name": "Old Name",
            "description": "Old description"
        }
        update_data = {
            "name": "New Name",
            "settings": {"model": "mistral:7b"}
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(existing_data))):
                project = await project_service.update_project(project_id, update_data)
                
                assert project["name"] == "New Name"
                assert project["description"] == "Old description"  # Unchanged
                assert "updated_at" in project
    
    
    @pytest.mark.asyncio
    async def test_delete_project(self, project_service):
        """Test deleting a project"""
        project_id = "test-project-123"
        
        with patch('os.path.exists', return_value=True):
            with patch('os.remove') as mock_remove:
                with patch('shutil.rmtree') as mock_rmtree:
                    result = await project_service.delete_project(project_id)
                    
                    assert result["status"] == "deleted"
                    mock_remove.assert_called_once()
                    mock_rmtree.assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_add_context(self, project_service):
        """Test adding context to a project"""
        project_id = "test-project-123"
        existing_data = {
            "id": project_id,
            "name": "Test Project",
            "context": []
        }
        context_data = {
            "type": "file",
            "content": "Important context information",
            "metadata": {"filename": "context.txt"}
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(existing_data))):
                project = await project_service.add_context(project_id, context_data)
                
                assert len(project["context"]) == 1
                assert project["context"][0]["content"] == context_data["content"]
                assert "id" in project["context"][0]
                assert "created_at" in project["context"][0]
    
    
    @pytest.mark.asyncio
    async def test_remove_context(self, project_service):
        """Test removing context from a project"""
        project_id = "test-project-123"
        context_id = "context-456"
        existing_data = {
            "id": project_id,
            "name": "Test Project",
            "context": [
                {
                    "id": context_id,
                    "content": "To be removed"
                },
                {
                    "id": "context-789",
                    "content": "To be kept"
                }
            ]
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(existing_data))):
                project = await project_service.remove_context(project_id, context_id)
                
                assert len(project["context"]) == 1
                assert project["context"][0]["id"] == "context-789"
    
    
    @pytest.mark.asyncio
    async def test_export_project(self, project_service):
        """Test exporting a project"""
        project_id = "test-project-123"
        project_data = {
            "id": project_id,
            "name": "Test Project",
            "settings": {"model": "llama2:7b"}
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(project_data))):
                export_data = await project_service.export_project(project_id)
                
                assert export_data["name"] == "Test Project"
                assert "export_date" in export_data
                assert "version" in export_data
    
    
    @pytest.mark.asyncio
    async def test_import_project(self, project_service):
        """Test importing a project"""
        import_data = {
            "name": "Imported Project",
            "description": "An imported project",
            "settings": {"model": "llama2:7b"},
            "context": [],
            "export_date": datetime.now().isoformat()
        }
        
        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()):
                project = await project_service.import_project(import_data)
                
                assert project["name"] == "Imported Project"
                assert "id" in project
                assert project["id"] != import_data.get("id")  # New ID generated
    
    
    @pytest.mark.asyncio
    async def test_duplicate_project(self, project_service):
        """Test duplicating a project"""
        project_id = "test-project-123"
        existing_data = {
            "id": project_id,
            "name": "Original Project",
            "settings": {"model": "llama2:7b"},
            "context": [{"id": "ctx-1", "content": "Context"}]
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('os.makedirs'):
                with patch('builtins.open', mock_open(read_data=json.dumps(existing_data))):
                    duplicate = await project_service.duplicate_project(project_id)
                    
                    assert duplicate["name"] == "Original Project (Copy)"
                    assert duplicate["id"] != project_id
                    assert len(duplicate["context"]) == len(existing_data["context"])
    
    
    @pytest.mark.asyncio
    async def test_search_projects(self, project_service):
        """Test searching projects"""
        mock_projects = ["project1.json", "project2.json"]
        project1_data = {"id": "1", "name": "Machine Learning Project", "description": "ML stuff"}
        project2_data = {"id": "2", "name": "Web Dev", "description": "Website project"}
        
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=mock_projects):
                with patch('builtins.open') as mock_file:
                    # Return different data for each file
                    mock_file.side_effect = [
                        mock_open(read_data=json.dumps(project1_data)).return_value,
                        mock_open(read_data=json.dumps(project2_data)).return_value
                    ]
                    
                    results = await project_service.search_projects("machine learning")
                    
                    assert len(results) == 1
                    assert results[0]["name"] == "Machine Learning Project"
    
    
    @pytest.mark.asyncio
    async def test_get_project_stats(self, project_service):
        """Test getting project statistics"""
        project_id = "test-project-123"
        project_data = {
            "id": project_id,
            "name": "Test Project",
            "created_at": "2024-01-01T00:00:00Z",
            "context": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
            "conversations": ["conv-1", "conv-2"]
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(project_data))):
                stats = await project_service.get_project_stats(project_id)
                
                assert stats["context_count"] == 3
                assert stats["conversation_count"] == 2
                assert "created_at" in stats
                assert "last_accessed" in stats
    
    
    @pytest.mark.asyncio
    async def test_archive_project(self, project_service):
        """Test archiving a project"""
        project_id = "test-project-123"
        project_data = {
            "id": project_id,
            "name": "Test Project",
            "archived": False
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(project_data))):
                project = await project_service.archive_project(project_id)
                
                assert project["archived"] is True
                assert "archived_at" in project
    
    
    @pytest.mark.asyncio
    async def test_validate_project_data(self, project_service):
        """Test project data validation"""
        # Valid data
        valid_data = {"name": "Test Project"}
        assert project_service.validate_project_data(valid_data) is True
        
        # Invalid data - missing name
        invalid_data = {"description": "No name"}
        assert project_service.validate_project_data(invalid_data) is False
        
        # Invalid data - empty name
        empty_name = {"name": ""}
        assert project_service.validate_project_data(empty_name) is False
