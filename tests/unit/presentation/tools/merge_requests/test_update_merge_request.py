"""Tests for update_merge_request tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.merge_requests.update_merge_request import update_merge_request


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
    mock_mr = Mock()

    # Setup mock merge request attributes
    mock_mr.iid = 5
    mock_mr.id = 100
    mock_mr.title = "Updated MR Title"
    mock_mr.description = "Updated description"
    mock_mr.state = "opened"
    mock_mr.draft = False
    mock_mr.source_branch = "feature-branch"
    mock_mr.target_branch = "main"
    mock_mr.author = Mock(id=1, username="author")
    mock_mr.assignees = [{"id": 2, "username": "assignee1"}]
    mock_mr.labels = ["bug", "priority:high"]
    mock_mr.web_url = "https://gitlab.example.com/project/-/merge_requests/5"
    mock_mr.created_at = "2025-01-01T00:00:00Z"
    mock_mr.updated_at = "2025-01-15T12:00:00Z"

    # Chain mocks
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.update_merge_request.client_factory")
async def test_update_merge_request_title(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test updating merge request title."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await update_merge_request(
        project_id="test-project",
        mr_iid=5,
        title="Updated MR Title",
        ctx=mock_context,
    )

    # Verify result
    assert result["iid"] == 5
    assert result["title"] == "Updated MR Title"

    # Verify save was called
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.save.assert_called_once()
    assert mock_mr.title == "Updated MR Title"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.update_merge_request.client_factory")
async def test_update_merge_request_multiple_fields(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test updating multiple merge request fields."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await update_merge_request(
        project_id="test-project",
        mr_iid=5,
        title="New Title",
        description="New description",
        labels=["bug", "priority:high"],
        draft=True,
        ctx=mock_context,
    )

    # Verify result
    assert result["iid"] == 5

    # Verify merge request was updated
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    assert mock_mr.title == "New Title"
    assert mock_mr.description == "New description"
    assert mock_mr.labels == ["bug", "priority:high"]
    assert mock_mr.draft is True
    mock_mr.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.update_merge_request.client_factory")
async def test_update_merge_request_assignees(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test updating merge request assignees."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await update_merge_request(
        project_id="test-project",
        mr_iid=5,
        assignee_ids=[10, 20],
        ctx=mock_context,
    )

    # Verify assignees were updated
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    assert mock_mr.assignee_ids == [10, 20]
    mock_mr.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.update_merge_request.client_factory")
async def test_update_merge_request_state_close(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test closing a merge request."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await update_merge_request(
        project_id="test-project",
        mr_iid=5,
        state_event="close",
        ctx=mock_context,
    )

    # Verify state was updated
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    assert mock_mr.state_event == "close"
    mock_mr.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.update_merge_request.client_factory")
async def test_update_merge_request_not_found(mock_factory, mock_settings, mock_context):
    """Test error when merge request doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.mergerequests.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Merge request .* not found"):
        await update_merge_request(
            project_id="test-project",
            mr_iid=999,
            title="Updated Title",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.update_merge_request.client_factory")
async def test_update_merge_request_save_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when save fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make save raise error
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.save.side_effect = Exception("Permission denied")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to update merge request"):
        await update_merge_request(
            project_id="test-project",
            mr_iid=5,
            title="Updated Title",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.update_merge_request.client_factory")
async def test_update_merge_request_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test updating merge request in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await update_merge_request(
        project_id="test-project",
        mr_iid=5,
        title="Updated Title",
        ctx=ctx,
    )

    # Verify result
    assert result["iid"] == 5

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
