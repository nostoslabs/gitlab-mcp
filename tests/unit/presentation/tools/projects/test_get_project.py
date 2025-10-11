"""Tests for get_project tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.projects.get_project import get_project


@pytest.fixture
def mock_context():
    """Mock FastMCP context for multi-tenant mode."""
    ctx = Mock()
    ctx.request.headers = {
        "X-User-ID": "test_user",
        "X-GitLab-Token": "test_token",
        "X-GitLab-URL": "https://gitlab.example.com",
    }
    return ctx


@pytest.fixture
def mock_gitlab_client():
    """Mock python-gitlab client."""
    mock_gl = Mock()
    mock_project = Mock()

    # Setup mock project attributes
    mock_project.id = 42
    mock_project.name = "Test Project"
    mock_project.path = "test-project"
    mock_project.path_with_namespace = "test-group/test-project"
    mock_project.description = "A test project"
    mock_project.web_url = "https://gitlab.example.com/test-group/test-project"
    mock_project.default_branch = "main"
    mock_project.visibility = "private"
    mock_project.created_at = "2025-01-01T00:00:00Z"
    mock_project.last_activity_at = "2025-01-15T12:00:00Z"

    # Chain mocks
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.get_project.client_factory")
async def test_get_project_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful project retrieval."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_project(project_id="test-project", ctx=mock_context)

    # Verify result
    assert result["id"] == 42
    assert result["name"] == "Test Project"
    assert result["path"] == "test-project"
    assert result["path_with_namespace"] == "test-group/test-project"
    assert result["description"] == "A test project"
    assert result["web_url"] == "https://gitlab.example.com/test-group/test-project"
    assert result["default_branch"] == "main"
    assert result["visibility"] == "private"
    assert result["created_at"] == "2025-01-01T00:00:00Z"
    assert result["last_activity_at"] == "2025-01-15T12:00:00Z"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.get_project.client_factory")
async def test_get_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await get_project(project_id="nonexistent", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.get_project.client_factory")
async def test_get_project_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test project retrieval in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await get_project(project_id="test-project", ctx=ctx)

    # Verify result
    assert result["id"] == 42

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
