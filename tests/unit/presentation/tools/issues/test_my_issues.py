"""Tests for my_issues tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.issues.my_issues import my_issues


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
    mock_issue1 = Mock()
    mock_issue2 = Mock()

    # Setup mock issue attributes
    mock_issue1.id = 100
    mock_issue1.iid = 10
    mock_issue1.title = "Bug in authentication"
    mock_issue1.description = "Login fails"
    mock_issue1.state = "opened"
    mock_issue1.labels = ["bug", "urgent"]
    mock_issue1.author = Mock(id=1, username="reporter")
    mock_issue1.assignees = [{"id": 2, "username": "test_user"}]
    mock_issue1.milestone = Mock(id=5, title="v1.0")
    mock_issue1.project_id = 50
    mock_issue1.web_url = "https://gitlab.com/project/issue/10"
    mock_issue1.created_at = "2025-01-15T10:00:00Z"
    mock_issue1.updated_at = "2025-01-15T11:00:00Z"
    mock_issue1.due_date = "2025-01-20"

    mock_issue2.id = 101
    mock_issue2.iid = 11
    mock_issue2.title = "Feature request"
    mock_issue2.description = "Add dark mode"
    mock_issue2.state = "opened"
    mock_issue2.labels = ["feature"]
    mock_issue2.author = Mock(id=3, username="requester")
    mock_issue2.assignees = [{"id": 2, "username": "test_user"}]
    mock_issue2.milestone = None
    mock_issue2.project_id = 51
    mock_issue2.web_url = "https://gitlab.com/project/issue/11"
    mock_issue2.created_at = "2025-01-16T10:00:00Z"
    mock_issue2.updated_at = "2025-01-16T10:00:00Z"
    mock_issue2.due_date = None

    # Chain mocks
    mock_gl.issues.list.return_value = [mock_issue1, mock_issue2]

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.my_issues.client_factory")
async def test_my_issues_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful my issues listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await my_issues(ctx=mock_context)

    # Verify result
    assert result["total_results"] == 2
    assert len(result["issues"]) == 2
    assert result["issues"][0]["title"] == "Bug in authentication"
    assert result["issues"][0]["labels"] == ["bug", "urgent"]
    assert result["issues"][1]["title"] == "Feature request"
    assert result["state"] == "opened"
    assert result["page"] == 1

    # Verify python-gitlab was called correctly
    mock_gitlab_client.issues.list.assert_called_once()
    call_kwargs = mock_gitlab_client.issues.list.call_args[1]
    assert call_kwargs["state"] == "opened"
    assert call_kwargs["scope"] == "assigned_to_me"
    assert call_kwargs["get_all"] is False


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.my_issues.client_factory")
async def test_my_issues_with_filters(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test my issues with filters."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    _result = await my_issues(
        state="closed",
        labels="bug,urgent",
        milestone="v1.0",
        order_by="updated_at",
        sort="asc",
        page=2,
        per_page=50,
        ctx=mock_context,
    )

    # Verify filters were passed
    call_kwargs = mock_gitlab_client.issues.list.call_args[1]
    assert call_kwargs["state"] == "closed"
    assert call_kwargs["labels"] == "bug,urgent"
    assert call_kwargs["milestone"] == "v1.0"
    assert call_kwargs["order_by"] == "updated_at"
    assert call_kwargs["sort"] == "asc"
    assert call_kwargs["page"] == 2
    assert call_kwargs["per_page"] == 50


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.my_issues.client_factory")
async def test_my_issues_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test my issues with no results."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make mock return empty list
    mock_gitlab_client.issues.list.return_value = []

    # Execute
    result = await my_issues(ctx=mock_context)

    # Verify result
    assert result["total_results"] == 0
    assert len(result["issues"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.my_issues.client_factory")
async def test_my_issues_fetch_error(mock_factory, mock_settings, mock_context):
    """Test error when fetching issues fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.issues.list.side_effect = Exception("API error")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Failed to fetch issues"):
        await my_issues(ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.my_issues.client_factory")
async def test_my_issues_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test my issues in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await my_issues(ctx=ctx)

    # Verify result
    assert result["total_results"] == 2

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
