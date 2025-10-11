"""Tests for remove_issue_from_milestone tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.milestones.remove_issue_from_milestone import (
    remove_issue_from_milestone,
)


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

    # Setup mock issue (with milestone_id set initially)
    mock_issue = Mock()
    mock_issue.id = 101
    mock_issue.iid = 1
    mock_issue.title = "Bug in feature X"
    mock_issue.milestone_id = None  # Will be set to None

    # Chain mocks
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.remove_issue_from_milestone.client_factory")
async def test_remove_issue_from_milestone_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successfully removing issue from milestone."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await remove_issue_from_milestone(
        project_id="test-project",
        issue_iid=1,
        ctx=mock_context,
    )

    # Verify result
    assert result["issue_iid"] == 1
    assert "removed from milestone" in result["message"].lower()

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.get.assert_called_once_with(1)

    # Verify issue milestone was set to None and saved
    mock_issue = mock_project.issues.get.return_value
    assert mock_issue.milestone_id is None
    mock_issue.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.remove_issue_from_milestone.client_factory")
async def test_remove_issue_from_milestone_issue_not_found(
    mock_factory, mock_settings, mock_context
):
    """Test error when issue doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.issues.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Issue .* not found"):
        await remove_issue_from_milestone(
            project_id="test-project",
            issue_iid=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.remove_issue_from_milestone.client_factory")
async def test_remove_issue_from_milestone_project_not_found(
    mock_factory, mock_settings, mock_context
):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await remove_issue_from_milestone(
            project_id="nonexistent",
            issue_iid=1,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.remove_issue_from_milestone.client_factory")
async def test_remove_issue_from_milestone_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test removing issue from milestone in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await remove_issue_from_milestone(
        project_id="test-project",
        issue_iid=1,
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
