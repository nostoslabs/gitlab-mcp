"""Tests for list_milestone_merge_requests tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.milestones.list_milestone_merge_requests import (
    list_milestone_merge_requests,
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

    # Setup mock milestone
    mock_milestone = Mock()
    mock_milestone.id = 1

    # Setup mock merge requests
    mock_mr1 = Mock()
    mock_mr1.id = 201
    mock_mr1.iid = 1
    mock_mr1.title = "Add feature X"
    mock_mr1.state = "opened"
    mock_mr1.web_url = "https://gitlab.example.com/project/-/merge_requests/1"

    mock_mr2 = Mock()
    mock_mr2.id = 202
    mock_mr2.iid = 2
    mock_mr2.title = "Fix bug Y"
    mock_mr2.state = "merged"
    mock_mr2.web_url = "https://gitlab.example.com/project/-/merge_requests/2"

    # Chain mocks
    mock_milestone.merge_requests.return_value = [mock_mr1, mock_mr2]
    mock_project.milestones.get.return_value = mock_milestone
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_merge_requests.client_factory")
async def test_list_milestone_merge_requests_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful listing of milestone merge requests."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_milestone_merge_requests(
        project_id="test-project",
        milestone_id=1,
        ctx=mock_context,
    )

    # Verify result
    assert len(result["merge_requests"]) == 2
    assert result["merge_requests"][0]["id"] == 201
    assert result["merge_requests"][0]["title"] == "Add feature X"
    assert result["merge_requests"][1]["id"] == 202
    assert result["merge_requests"][1]["title"] == "Fix bug Y"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.get.assert_called_once_with(1)
    mock_milestone = mock_project.milestones.get.return_value
    mock_milestone.merge_requests.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_merge_requests.client_factory")
async def test_list_milestone_merge_requests_empty(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test milestone with no merge requests."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return empty list
    mock_milestone = mock_gitlab_client.projects.get.return_value.milestones.get.return_value
    mock_milestone.merge_requests.return_value = []

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_milestone_merge_requests(
        project_id="test-project",
        milestone_id=1,
        ctx=mock_context,
    )

    # Verify empty result
    assert result["merge_requests"] == []


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_merge_requests.client_factory")
async def test_list_milestone_merge_requests_milestone_not_found(
    mock_factory, mock_settings, mock_context
):
    """Test error when milestone doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.milestones.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Milestone .* not found"):
        await list_milestone_merge_requests(
            project_id="test-project",
            milestone_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_merge_requests.client_factory")
async def test_list_milestone_merge_requests_project_not_found(
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
        await list_milestone_merge_requests(
            project_id="nonexistent",
            milestone_id=1,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_merge_requests.client_factory")
async def test_list_milestone_merge_requests_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test listing merge requests in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_milestone_merge_requests(
        project_id="test-project",
        milestone_id=1,
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
