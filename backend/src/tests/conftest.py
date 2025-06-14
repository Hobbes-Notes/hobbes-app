"""
Pytest Configuration and Shared Fixtures

This module provides shared fixtures for all test types, including
DI container overrides and mock configurations.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.services.dependencies import (
    get_ai_service, get_monitoring_service, get_auth_service,
    get_action_item_service, get_user_service, get_ai_file_service,
    get_capb_service, get_project_service, get_note_service
)
from api.services.ai_service import AIService
from api.services.monitoring_service import MonitoringService
from api.services.auth_service import AuthService


@pytest.fixture
def mock_ai_service():
    """Mock AI service for unit tests."""
    mock = Mock(spec=AIService)
    mock.generate_response = AsyncMock(return_value="Mock AI response")
    mock.analyze_content = AsyncMock(return_value={"analysis": "mock"})
    return mock


@pytest.fixture
def mock_monitoring_service():
    """Mock monitoring service for unit tests."""
    mock = Mock(spec=MonitoringService)
    mock.log_event = Mock()
    mock.track_metric = Mock()
    return mock


@pytest.fixture
def mock_auth_service():
    """Mock auth service for unit tests."""
    mock = Mock(spec=AuthService)
    mock.authenticate_user = AsyncMock(return_value={"user_id": "test_user"})
    mock.validate_token = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_note_repository():
    """Mock note repository for unit tests."""
    mock = Mock()
    mock.get_notes_by_project = AsyncMock(return_value=[])
    mock.create_note = AsyncMock(return_value={"id": "test_note"})
    mock.update_note = AsyncMock(return_value={"id": "test_note"})
    mock.delete_note = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_project_repository():
    """Mock project repository for unit tests."""
    mock = Mock()
    mock.get_project = AsyncMock(return_value={"id": "test_project"})
    mock.create_project = AsyncMock(return_value={"id": "test_project"})
    mock.update_project = AsyncMock(return_value={"id": "test_project"})
    mock.delete_project = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def test_app(
    mock_ai_service,
    mock_monitoring_service,
    mock_auth_service,
    mock_note_repository,
    mock_project_repository
):
    """
    Test FastAPI app with all dependencies mocked.
    
    This fixture provides a clean app for unit tests where
    each layer is mocked below the layer being tested.
    """
    from main import app
    
    # Override dependencies with mocks
    app.dependency_overrides[get_ai_service] = lambda: mock_ai_service
    app.dependency_overrides[get_monitoring_service] = lambda: mock_monitoring_service
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    yield app
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(test_app):
    """Test client for unit tests with mocked dependencies."""
    return TestClient(test_app)


@pytest.fixture
def integration_app():
    """
    Integration test app with real services but test configuration.
    
    This fixture provides an app for integration tests where
    services are real but configured for testing.
    """
    from main import app
    
    # No dependency overrides - use real services
    # Could add test-specific configuration here
    
    yield app


@pytest.fixture
def integration_client(integration_app):
    """Test client for integration tests with real services."""
    return TestClient(integration_app)


@pytest.fixture(scope="session")
def vcr_config():
    """VCR configuration for contract tests."""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "ignore_localhost": True,
        "record_mode": "once",
        "match_on": ["uri", "method", "body"],
    }


# Async test support
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 