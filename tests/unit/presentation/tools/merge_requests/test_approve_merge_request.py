"""Tests for approve_merge_request tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.merge_requests.approve_merge_request import (
    approve_merge_request,
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
    mock_approval = Mock()

    # Setup mock approval attributes
    mock_approval.id = 1
    mock_approval.iid = 50
    mock_approval.approved = True
    mock_approval.approved_by = [{"user": {"id": 1, "username": "testuser", "name": "Test User"}}]

    # Mock approve method
    mock_mr.approve = Mock(return_value=mock_approval)

    # Chain mocks
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.approve_merge_request.client_factory")
async def test_approve_merge_request_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful merge request approval."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await approve_merge_request(project_id="test-project", mr_iid=50, ctx=mock_context)

    # Verify result
    assert result["id"] == 1
    assert result["iid"] == 50
    assert result["approved"] is True
    assert len(result["approved_by"]) == 1
    assert result["approved_by"][0]["user"]["username"] == "testuser"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.mergerequests.get.assert_called_once_with(50)

    # Verify approve was called
    mock_mr = mock_project.mergerequests.get.return_value
    mock_mr.approve.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.approve_merge_request.client_factory")
async def test_approve_merge_request_not_found(mock_factory, mock_settings, mock_context):
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
        await approve_merge_request(project_id="test-project", mr_iid=999, ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.approve_merge_request.client_factory")
async def test_approve_merge_request_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await approve_merge_request(project_id="nonexistent", mr_iid=50, ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.approve_merge_request.client_factory")
async def test_approve_merge_request_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test merge request approval in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await approve_merge_request(project_id="test-project", mr_iid=50, ctx=ctx)

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.approve_merge_request.client_factory")
async def test_approve_merge_request_multiple_approvers(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test approval with multiple approvers."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Update mock to have multiple approvers
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_approval = Mock()
    mock_approval.id = 1
    mock_approval.iid = 50
    mock_approval.approved = True
    mock_approval.approved_by = [
        {"user": {"id": 1, "username": "user1", "name": "User One"}},
        {"user": {"id": 2, "username": "user2", "name": "User Two"}},
    ]
    mock_mr.approve.return_value = mock_approval

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await approve_merge_request(project_id="test-project", mr_iid=50, ctx=mock_context)

    # Verify multiple approvers
    assert len(result["approved_by"]) == 2
    assert result["approved_by"][0]["user"]["username"] == "user1"
    assert result["approved_by"][1]["user"]["username"] == "user2"
