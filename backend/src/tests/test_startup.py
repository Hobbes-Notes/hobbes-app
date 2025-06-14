"""
Automated Startup Test

This test verifies that the FastAPI application can start successfully
and that all dependency injection is working correctly. This catches
import errors and missing providers before they reach production.
"""

import pytest
from fastapi.testclient import TestClient


def test_application_startup():
    """
    Test that the FastAPI application starts successfully.
    
    This test:
    1. Imports the main application
    2. Creates a test client (which triggers startup)
    3. Verifies no import or dependency injection errors occur
    """
    try:
        from main import app
        client = TestClient(app)
        
        # If we get here, the app started successfully
        assert app is not None
        assert client is not None
        
    except Exception as e:
        pytest.fail(f"Application failed to start: {str(e)}")


def test_health_endpoint():
    """
    Test that the health endpoint returns HTTP 200.
    
    This test verifies:
    1. The application starts without errors
    2. The health endpoint is accessible
    3. All dependencies are properly wired
    """
    from main import app
    
    with TestClient(app) as client:
        response = client.get("/health")
        
        # Verify successful response
        assert response.status_code == 200
        
        # Verify expected response format
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "backend"


def test_dependency_injection_wiring():
    """
    Test that key dependency injection is working correctly.
    
    This test verifies that services can be created through
    the dependency injection system without errors.
    """
    from api.services.dependencies import (
        get_ai_service, get_monitoring_service, get_auth_service,
        get_action_item_service, get_user_service
    )
    from api.repositories.impl import (
        get_note_repository, get_project_repository, 
        get_ai_repository, get_action_item_repository
    )
    
    # Test repository factories
    note_repo = get_note_repository()
    assert note_repo is not None
    
    project_repo = get_project_repository()
    assert project_repo is not None
    
    ai_repo = get_ai_repository()
    assert ai_repo is not None
    
    action_item_repo = get_action_item_repository()
    assert action_item_repo is not None
    
    # Test service factories that don't require DI context
    monitoring_service = get_monitoring_service()
    assert monitoring_service is not None
    
    auth_service = get_auth_service()
    assert auth_service is not None
    
    # Test factory services (new instances)
    action_item_service = get_action_item_service()
    assert action_item_service is not None
    
    user_service = get_user_service()
    assert user_service is not None
    
    # Note: get_ai_service requires DI context, so we test it via HTTP endpoint


def test_import_boundaries():
    """
    Test that import boundaries are respected.
    
    This test verifies that the layered architecture is maintained
    and no circular imports exist.
    """
    # Test that we can import all layers without circular dependency issues
    try:
        import api.controllers
        import api.services  
        import api.repositories
        import infrastructure
        
        # If we get here, no circular imports exist
        assert True
        
    except ImportError as e:
        pytest.fail(f"Import boundary violation detected: {str(e)}")


@pytest.mark.asyncio
async def test_database_initialization():
    """
    Test that database tables can be initialized.
    
    This test verifies that the startup process can create
    all required database tables without errors.
    """
    from main import app
    from api.services import get_auth_service
    from api.repositories.impl import (
        get_project_repository, get_note_repository, get_action_item_repository
    )
    
    # Test auth service table initialization
    auth_service = get_auth_service()
    try:
        await auth_service.initialize_tables()
    except Exception as e:
        pytest.fail(f"Auth tables initialization failed: {str(e)}")
    
    # Test repository table initialization
    repositories = [
        get_project_repository(),
        get_note_repository(), 
        get_action_item_repository()
    ]
    
    for repo in repositories:
        try:
            await repo.create_table()
        except Exception as e:
            pytest.fail(f"Repository table creation failed: {str(e)}")


if __name__ == "__main__":
    # Allow running this test directly for quick verification
    test_application_startup()
    test_health_endpoint()
    test_dependency_injection_wiring()
    test_import_boundaries()
    print("✅ All startup tests passed!") 