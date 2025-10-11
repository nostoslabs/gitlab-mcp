"""Tests for delete_issue_link tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.issue_links.delete_issue_link import delete_issue_link


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
    mock_issue = Mock()
    mock_link = Mock()

    # Chain mocks
    mock_issue.iid = 42
    mock_issue.links.get.return_value = mock_link
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.delete_issue_link.client_factory")
async def test_delete_issue_link_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful issue link deletion."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await delete_issue_link(
        project_id="test-project",
        issue_iid=42,
        link_id=999,
        ctx=mock_context,
    )

    # Verify result
    assert result["success"] is True
    assert result["deleted_link_id"] == 999
    assert result["source_issue_iid"] == 42

    # Verify delete was called
    mock_link = (
        mock_gitlab_client.projects.get.return_value.issues.get.return_value.links.get.return_value
    )
    mock_link.delete.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.delete_issue_link.client_factory")
async def test_delete_issue_link_issue_not_found(mock_factory, mock_settings, mock_context):
    """Test error when issue doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.issues.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Issue .* not found"):
        await delete_issue_link(
            project_id="test-project",
            issue_iid=999,
            link_id=123,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.delete_issue_link.client_factory")
async def test_delete_issue_link_link_not_found(mock_factory, mock_settings, mock_context):
    """Test error when link doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_issue = Mock()
    mock_issue.links.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Issue link .* not found"):
        await delete_issue_link(
            project_id="test-project",
            issue_iid=42,
            link_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.delete_issue_link.client_factory")
async def test_delete_issue_link_delete_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when deletion fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make delete raise error
    mock_link = (
        mock_gitlab_client.projects.get.return_value.issues.get.return_value.links.get.return_value
    )
    mock_link.delete.side_effect = Exception("Permission denied")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to delete issue link"):
        await delete_issue_link(
            project_id="test-project",
            issue_iid=42,
            link_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.delete_issue_link.client_factory")
async def test_delete_issue_link_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test deleting issue link in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await delete_issue_link(
        project_id="test-project",
        issue_iid=42,
        link_id=999,
        ctx=ctx,
    )

    # Verify result
    assert result["success"] is True

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
