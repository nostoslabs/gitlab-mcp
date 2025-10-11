"""Tests for delete_milestone tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.milestones.delete_milestone import delete_milestone


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
    mock_milestone = Mock()

    # Setup mock milestone attributes
    mock_milestone.id = 10
    mock_milestone.title = "Version 1.0"

    # Chain mocks
    mock_project.milestones.get.return_value = mock_milestone
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.delete_milestone.client_factory")
async def test_delete_milestone_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful milestone deletion."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await delete_milestone(
        project_id="test-project",
        milestone_id=10,
        ctx=mock_context,
    )

    # Verify result
    assert result["success"] is True
    assert result["deleted_milestone_id"] == 10
    assert result["deleted_milestone_title"] == "Version 1.0"
    assert "deleted successfully" in result["message"]

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.get.assert_called_once_with(10)

    # Verify delete was called
    mock_milestone = mock_project.milestones.get.return_value
    mock_milestone.delete.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.delete_milestone.client_factory")
async def test_delete_milestone_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await delete_milestone(
            project_id="nonexistent",
            milestone_id=10,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.delete_milestone.client_factory")
async def test_delete_milestone_not_found(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when milestone doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    # Make milestone.get raise error
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Milestone .* not found"):
        await delete_milestone(
            project_id="test-project",
            milestone_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.delete_milestone.client_factory")
async def test_delete_milestone_delete_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when deletion fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make delete raise error
    mock_milestone = mock_gitlab_client.projects.get.return_value.milestones.get.return_value
    mock_milestone.delete.side_effect = Exception("Permission denied")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to delete milestone"):
        await delete_milestone(
            project_id="test-project",
            milestone_id=10,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.delete_milestone.client_factory")
async def test_delete_milestone_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test deleting milestone in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await delete_milestone(
        project_id="test-project",
        milestone_id=10,
        ctx=ctx,
    )

    # Verify result
    assert result["success"] is True

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
