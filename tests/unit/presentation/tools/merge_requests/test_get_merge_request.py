"""Tests for get_merge_request tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.merge_requests.get_merge_request import (
    get_merge_request,
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

    # Setup mock MR attributes
    mock_mr.id = 1
    mock_mr.iid = 50
    mock_mr.project_id = 42
    mock_mr.title = "Test MR"
    mock_mr.description = "Test description"
    mock_mr.state = "opened"
    mock_mr.source_branch = "feature"
    mock_mr.target_branch = "main"
    mock_mr.author = {"id": 1, "username": "testuser", "name": "Test User"}
    mock_mr.assignee = {"id": 2, "username": "assignee", "name": "Assignee User"}
    mock_mr.labels = ["enhancement"]
    mock_mr.web_url = "https://gitlab.example.com/project/-/merge_requests/50"
    mock_mr.created_at = "2025-01-01T00:00:00Z"
    mock_mr.updated_at = "2025-01-01T00:00:00Z"
    mock_mr.merge_status = "can_be_merged"
    mock_mr.has_conflicts = False
    mock_mr.work_in_progress = False
    mock_mr.merged_by = None
    mock_mr.merged_at = None

    # Chain mocks
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.get_merge_request.client_factory")
async def test_get_merge_request_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful merge request retrieval."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_merge_request(project_id="test-project", mr_iid=50, ctx=mock_context)

    # Verify result
    assert result["id"] == 1
    assert result["iid"] == 50
    assert result["project_id"] == 42
    assert result["title"] == "Test MR"
    assert result["description"] == "Test description"
    assert result["state"] == "opened"
    assert result["source_branch"] == "feature"
    assert result["target_branch"] == "main"
    assert result["labels"] == ["enhancement"]
    assert result["web_url"] == "https://gitlab.example.com/project/-/merge_requests/50"
    assert result["author"] == {"id": 1, "username": "testuser", "name": "Test User"}
    assert result["assignee"] == {"id": 2, "username": "assignee", "name": "Assignee User"}
    assert result["merge_status"] == "can_be_merged"
    assert result["has_conflicts"] is False

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.mergerequests.get.assert_called_once_with(50)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.get_merge_request.client_factory")
async def test_get_merge_request_not_found(mock_factory, mock_settings, mock_context):
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
        await get_merge_request(project_id="test-project", mr_iid=999, ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.get_merge_request.client_factory")
async def test_get_merge_request_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await get_merge_request(project_id="nonexistent", mr_iid=50, ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.get_merge_request.client_factory")
async def test_get_merge_request_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test merge request retrieval in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await get_merge_request(project_id="test-project", mr_iid=50, ctx=ctx)

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.get_merge_request.client_factory")
async def test_get_merge_request_merged(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test retrieval of a merged merge request."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Update mock to show merged state
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.state = "merged"
    mock_mr.merged_by = {"id": 3, "username": "merger", "name": "Merger User"}
    mock_mr.merged_at = "2025-01-02T00:00:00Z"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_merge_request(project_id="test-project", mr_iid=50, ctx=mock_context)

    # Verify merged state
    assert result["state"] == "merged"
    assert result["merged_by"] == {"id": 3, "username": "merger", "name": "Merger User"}
    assert result["merged_at"] == "2025-01-02T00:00:00Z"
