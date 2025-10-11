"""Tests for list_merge_requests tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.merge_requests.list_merge_requests import (
    list_merge_requests,
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
    """Mock python-gitlab client with multiple MRs."""
    mock_gl = Mock()
    mock_project = Mock()

    # Create mock MRs
    mock_mr1 = Mock()
    mock_mr1.id = 1
    mock_mr1.iid = 50
    mock_mr1.title = "Test MR 1"
    mock_mr1.state = "opened"
    mock_mr1.labels = ["enhancement"]
    mock_mr1.web_url = "https://gitlab.example.com/project/-/merge_requests/50"
    mock_mr1.source_branch = "feature-1"
    mock_mr1.target_branch = "main"

    mock_mr2 = Mock()
    mock_mr2.id = 2
    mock_mr2.iid = 51
    mock_mr2.title = "Test MR 2"
    mock_mr2.state = "opened"
    mock_mr2.labels = ["bug"]
    mock_mr2.web_url = "https://gitlab.example.com/project/-/merge_requests/51"
    mock_mr2.source_branch = "fix-bug"
    mock_mr2.target_branch = "main"

    # Chain mocks
    mock_project.mergerequests.list.return_value = [mock_mr1, mock_mr2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.list_merge_requests.client_factory")
async def test_list_merge_requests_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful merge requests listing."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_merge_requests(project_id="test-project", ctx=mock_context)

    # Verify result
    assert "merge_requests" in result
    assert len(result["merge_requests"]) == 2
    assert result["total"] == 2
    assert result["page"] == 1
    assert result["per_page"] == 20

    # Verify first MR
    mr1 = result["merge_requests"][0]
    assert mr1["id"] == 1
    assert mr1["iid"] == 50
    assert mr1["title"] == "Test MR 1"
    assert mr1["state"] == "opened"
    assert mr1["labels"] == ["enhancement"]

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.mergerequests.list.assert_called_once_with(page=1, per_page=20)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.list_merge_requests.client_factory")
async def test_list_merge_requests_with_filters(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test merge requests listing with filters."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with filters
    await list_merge_requests(
        project_id="test-project",
        state="opened",
        labels=["bug", "critical"],
        search="fix",
        page=2,
        per_page=50,
        ctx=mock_context,
    )

    # Verify filters were passed
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.mergerequests.list.assert_called_once_with(
        page=2, per_page=50, state="opened", labels="bug,critical", search="fix"
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.list_merge_requests.client_factory")
async def test_list_merge_requests_empty(mock_factory, mock_settings, mock_context):
    """Test listing when no merge requests exist."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.mergerequests.list.return_value = []
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    # Execute
    result = await list_merge_requests(project_id="test-project", ctx=mock_context)

    # Verify empty result
    assert result["merge_requests"] == []
    assert result["total"] == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.list_merge_requests.client_factory")
async def test_list_merge_requests_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_merge_requests(project_id="nonexistent", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.list_merge_requests.client_factory")
async def test_list_merge_requests_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test merge requests listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_merge_requests(project_id="test-project", ctx=ctx)

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.merge_requests.list_merge_requests.client_factory")
async def test_list_merge_requests_with_pagination(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test merge requests listing with custom pagination."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with custom pagination
    result = await list_merge_requests(
        project_id="test-project", page=3, per_page=10, ctx=mock_context
    )

    # Verify pagination in result
    assert result["page"] == 3
    assert result["per_page"] == 10

    # Verify pagination was passed to API
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.mergerequests.list.assert_called_once_with(page=3, per_page=10)
