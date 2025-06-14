"""
Integration Tests - Golden Path

This test verifies the complete HTTP request flow through all layers
to ensure the wiring remains valid. This is the "golden" happy-path
test that should run in CI to catch integration issues.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app


def test_golden_path_create_and_get_project(integration_client):
    """
    Golden path integration test: Create project and retrieve it.
    
    This test exercises the complete stack:
    1. HTTP request → Controller
    2. Controller → Service
    3. Service → Repository
    4. Repository → Infrastructure
    5. Response back through all layers
    
    This test should always pass in CI to verify wiring is intact.
    """
    # Mock external dependencies to avoid real API calls
    with patch('api.services.ai_service.AIService.generate_response') as mock_ai:
        mock_ai.return_value = "Mock project analysis"
        
        # Step 1: Create a project
        create_payload = {
            "name": "Golden Path Test Project",
            "description": "Integration test project",
            "type": "test"
        }
        
        create_response = integration_client.post("/api/projects", json=create_payload)
        
        # Verify creation succeeded
        assert create_response.status_code == 200
        project_data = create_response.json()
        assert project_data["name"] == create_payload["name"]
        project_id = project_data["id"]
        
        # Step 2: Retrieve the created project
        get_response = integration_client.get(f"/api/projects/{project_id}")
        
        # Verify retrieval succeeded
        assert get_response.status_code == 200
        retrieved_project = get_response.json()
        assert retrieved_project["id"] == project_id
        assert retrieved_project["name"] == create_payload["name"]
        
        # Step 3: List all projects (should include our test project)
        list_response = integration_client.get("/api/projects")
        
        # Verify listing succeeded
        assert list_response.status_code == 200
        projects = list_response.json()
        assert any(p["id"] == project_id for p in projects)


def test_golden_path_note_workflow(integration_client):
    """
    Golden path for note workflow: Create project, add note, retrieve notes.
    
    This test verifies the note service integration with project service.
    """
    with patch('api.services.ai_service.AIService.analyze_content') as mock_ai:
        mock_ai.return_value = {"sentiment": "positive", "topics": ["test"]}
        
        # Step 1: Create a project for the note
        project_payload = {
            "name": "Note Test Project",
            "description": "Project for note testing"
        }
        
        project_response = integration_client.post("/api/projects", json=project_payload)
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]
        
        # Step 2: Create a note in the project
        note_payload = {
            "title": "Test Note",
            "content": "This is a test note for integration testing",
            "project_id": project_id
        }
        
        note_response = integration_client.post("/api/notes", json=note_payload)
        assert note_response.status_code == 200
        note_data = note_response.json()
        assert note_data["title"] == note_payload["title"]
        note_id = note_data["id"]
        
        # Step 3: Retrieve notes for the project
        notes_response = integration_client.get(f"/api/projects/{project_id}/notes")
        assert notes_response.status_code == 200
        notes = notes_response.json()
        assert len(notes) >= 1
        assert any(n["id"] == note_id for n in notes)


def test_golden_path_error_handling(integration_client):
    """
    Golden path for error handling: Verify proper error responses.
    
    This test ensures error handling works correctly through all layers.
    """
    # Test 404 for non-existent project
    response = integration_client.get("/api/projects/non-existent-id")
    assert response.status_code == 404
    
    # Test validation error for invalid payload
    invalid_payload = {
        "name": "",  # Empty name should fail validation
        "description": "Test"
    }
    
    response = integration_client.post("/api/projects", json=invalid_payload)
    assert response.status_code == 422  # Validation error 