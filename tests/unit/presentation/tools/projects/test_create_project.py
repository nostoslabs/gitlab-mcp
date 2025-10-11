"""Tests for create_project tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.projects.create_project import create_project


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
    mock_project.id = 123
    mock_project.name = "New Project"
    mock_project.path = "new-project"
    mock_project.path_with_namespace = "test-user/new-project"
    mock_project.description = "A new test project"
    mock_project.visibility = "private"
    mock_project.web_url = "https://gitlab.example.com/test-user/new-project"
    mock_project.created_at = "2025-01-15T12:00:00Z"
    mock_project.default_branch = "main"

    # Chain mocks
    mock_gl.projects.create.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.create_project.client_factory")
async def test_create_project_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful project creation."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_project(
        name="New Project",
        description="A new test project",
        visibility="private",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 123
    assert result["name"] == "New Project"
    assert result["path"] == "new-project"
    assert result["path_with_namespace"] == "test-user/new-project"
    assert result["description"] == "A new test project"
    assert result["visibility"] == "private"
    assert result["web_url"] == "https://gitlab.example.com/test-user/new-project"
    assert result["created_at"] == "2025-01-15T12:00:00Z"
    assert result["default_branch"] == "main"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.create.assert_called_once_with(
        {
            "name": "New Project",
            "visibility": "private",
            "description": "A new test project",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.create_project.client_factory")
async def test_create_project_minimal(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test project creation with minimal parameters."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with only required parameter
    await create_project(name="Minimal Project", ctx=mock_context)

    # Verify python-gitlab was called with minimal data
    mock_gitlab_client.projects.create.assert_called_once_with(
        {
            "name": "Minimal Project",
            "visibility": "private",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.create_project.client_factory")
async def test_create_project_with_readme(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test project creation with README initialization."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await create_project(
        name="Project with README",
        initialize_with_readme=True,
        ctx=mock_context,
    )

    # Verify python-gitlab was called with initialize_with_readme flag
    call_args = mock_gitlab_client.projects.create.call_args[0][0]
    assert call_args["initialize_with_readme"] is True


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.create_project.client_factory")
async def test_create_project_in_namespace(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test project creation in specific namespace."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await create_project(
        name="Namespaced Project",
        namespace_id=456,
        ctx=mock_context,
    )

    # Verify python-gitlab was called with namespace_id
    call_args = mock_gitlab_client.projects.create.call_args[0][0]
    assert call_args["namespace_id"] == 456


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.create_project.client_factory")
async def test_create_project_creation_error(mock_factory, mock_settings, mock_context):
    """Test error when project creation fails."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.create.side_effect = gitlab.exceptions.GitlabCreateError(
        "Project name already exists"
    )
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Failed to create project"):
        await create_project(name="Duplicate Project", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.create_project.client_factory")
async def test_create_project_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test project creation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await create_project(name="New Project", ctx=ctx)

    # Verify result
    assert result["id"] == 123

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
