"""Tests for delete_branch tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.branches.delete_branch import delete_branch


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

    # Setup mock branches.delete to succeed
    mock_project.branches.delete.return_value = None

    # Chain mocks
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.delete_branch.client_factory")
async def test_delete_branch_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful branch deletion."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await delete_branch(
        project_id="test-project",
        branch="feature-branch",
        ctx=mock_context,
    )

    # Verify result
    assert result["success"]
    assert result["branch"] == "feature-branch"
    assert result["message"] == "Branch 'feature-branch' deleted successfully"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.branches.delete.assert_called_once_with("feature-branch")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.delete_branch.client_factory")
async def test_delete_branch_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await delete_branch(
            project_id="nonexistent",
            branch="feature-branch",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.delete_branch.client_factory")
async def test_delete_branch_not_found(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when branch doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Make branches.delete raise GitlabDeleteError
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.branches.delete.side_effect = gitlab.exceptions.GitlabDeleteError(
        "Branch not found"
    )

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to delete branch"):
        await delete_branch(
            project_id="test-project",
            branch="nonexistent-branch",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.delete_branch.client_factory")
async def test_delete_branch_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test branch deletion in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await delete_branch(
        project_id="test-project",
        branch="feature-branch",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
