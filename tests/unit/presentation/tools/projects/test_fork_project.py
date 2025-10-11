"""Tests for fork_project tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.projects.fork_project import fork_project


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
    mock_source_project = Mock()
    mock_forked_project = Mock()

    # Setup source project attributes
    mock_source_project.id = 100
    mock_source_project.path_with_namespace = "original-owner/original-project"

    # Setup forked project attributes
    mock_forked_project.id = 200
    mock_forked_project.name = "Original Project"
    mock_forked_project.path = "original-project"
    mock_forked_project.path_with_namespace = "test-user/original-project"
    mock_forked_project.description = "A forked project"
    mock_forked_project.web_url = "https://gitlab.example.com/test-user/original-project"

    # Chain mocks
    mock_source_project.forks.create.return_value = mock_forked_project
    mock_gl.projects.get.return_value = mock_source_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.fork_project.client_factory")
async def test_fork_project_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful project fork."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await fork_project(
        project_id="original-owner/original-project",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 200
    assert result["name"] == "Original Project"
    assert result["path"] == "original-project"
    assert result["path_with_namespace"] == "test-user/original-project"
    assert result["description"] == "A forked project"
    assert result["web_url"] == "https://gitlab.example.com/test-user/original-project"
    assert result["forked_from_project"]["id"] == 100
    assert result["forked_from_project"]["path_with_namespace"] == "original-owner/original-project"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("original-owner/original-project")
    mock_source_project = mock_gitlab_client.projects.get.return_value
    mock_source_project.forks.create.assert_called_once_with({})


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.fork_project.client_factory")
async def test_fork_project_with_custom_name(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test forking with custom name and path."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await fork_project(
        project_id="original-owner/original-project",
        name="My Fork",
        path="my-fork",
        ctx=mock_context,
    )

    # Verify fork was created with custom parameters
    mock_source_project = mock_gitlab_client.projects.get.return_value
    mock_source_project.forks.create.assert_called_once_with(
        {
            "name": "My Fork",
            "path": "my-fork",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.fork_project.client_factory")
async def test_fork_project_to_namespace(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test forking to specific namespace."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await fork_project(
        project_id="original-owner/original-project",
        namespace_id=789,
        ctx=mock_context,
    )

    # Verify fork was created in specified namespace
    mock_source_project = mock_gitlab_client.projects.get.return_value
    mock_source_project.forks.create.assert_called_once_with(
        {
            "namespace_id": 789,
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.fork_project.client_factory")
async def test_fork_project_source_not_found(mock_factory, mock_settings, mock_context):
    """Test error when source project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await fork_project(project_id="nonexistent/project", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.fork_project.client_factory")
async def test_fork_project_fork_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when fork creation fails."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    # Make fork.create raise error
    mock_source_project = mock_gitlab_client.projects.get.return_value
    mock_source_project.forks.create.side_effect = gitlab.exceptions.GitlabCreateError(
        "Cannot fork this project"
    )

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to fork project"):
        await fork_project(project_id="protected/project", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.fork_project.client_factory")
async def test_fork_project_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test project fork in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await fork_project(project_id="original/project", ctx=ctx)

    # Verify result
    assert result["id"] == 200

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
