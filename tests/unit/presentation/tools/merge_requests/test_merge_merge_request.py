"""Tests for merge_merge_request tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.merge_requests.merge_merge_request import (
    merge_merge_request,
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
    mock_mr = Mock()

    # Setup mock MR attributes (after merge)
    mock_mr.id = 1
    mock_mr.iid = 50
    mock_mr.title = "Test MR"
    mock_mr.state = "merged"
    mock_mr.merged_by = {"id": 1, "username": "testuser", "name": "Test User"}
    mock_mr.merged_at = "2025-01-02T00:00:00Z"
    mock_mr.web_url = "https://gitlab.example.com/project/-/merge_requests/50"

    # Mock merge method
    mock_mr.merge = Mock()

    # Chain mocks
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.merge_merge_request.client_factory")
async def test_merge_merge_request_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful merge request merge."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await merge_merge_request(project_id="test-project", mr_iid=50, ctx=mock_context)

    # Verify result
    assert result["id"] == 1
    assert result["iid"] == 50
    assert result["title"] == "Test MR"
    assert result["state"] == "merged"
    assert result["merged_by"] == {"id": 1, "username": "testuser", "name": "Test User"}
    assert result["merged_at"] == "2025-01-02T00:00:00Z"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value

    # Verify MR was retrieved twice (before and after merge)
    assert mock_project.mergerequests.get.call_count == 2
    mock_project.mergerequests.get.assert_called_with(50)

    # Verify merge was called with default params
    mock_mr = mock_project.mergerequests.get.return_value
    mock_mr.merge.assert_called_once_with(should_remove_source_branch=False, squash=False)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.merge_merge_request.client_factory")
async def test_merge_merge_request_with_options(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test merge with custom options."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with options
    await merge_merge_request(
        project_id="test-project",
        mr_iid=50,
        merge_commit_message="Custom merge message",
        should_remove_source_branch=True,
        squash=True,
        ctx=mock_context,
    )

    # Verify merge was called with custom params
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.merge.assert_called_once_with(
        should_remove_source_branch=True,
        squash=True,
        merge_commit_message="Custom merge message",
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.merge_merge_request.client_factory")
async def test_merge_merge_request_not_found(mock_factory, mock_settings, mock_context):
    """Test error when merge request doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.mergerequests.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Merge request .* not found"):
        await merge_merge_request(project_id="test-project", mr_iid=999, ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.merge_merge_request.client_factory")
async def test_merge_merge_request_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await merge_merge_request(project_id="nonexistent", mr_iid=50, ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.merge_merge_request.client_factory")
async def test_merge_merge_request_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test merge in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await merge_merge_request(project_id="test-project", mr_iid=50, ctx=ctx)

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.merge_merge_request.client_factory")
async def test_merge_merge_request_with_squash_only(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test merge with squash option only."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with squash only
    await merge_merge_request(project_id="test-project", mr_iid=50, squash=True, ctx=mock_context)

    # Verify merge was called with squash=True but remove_source_branch=False
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.merge.assert_called_once_with(should_remove_source_branch=False, squash=True)
