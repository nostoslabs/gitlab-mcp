"""Tests for delete_issue tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.issues.delete_issue import delete_issue


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

    # Chain mocks
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.delete_issue.client_factory")
async def test_delete_issue_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful issue deletion."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await delete_issue(project_id="test-project", issue_iid=100, ctx=mock_context)

    # Verify result
    assert result["success"] is True
    assert result["message"] == "Issue 100 deleted successfully"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.get.assert_called_once_with(100)

    # Verify issue was deleted
    mock_issue = mock_project.issues.get.return_value
    mock_issue.delete.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.delete_issue.client_factory")
async def test_delete_issue_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await delete_issue(project_id="nonexistent", issue_iid=100, ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.delete_issue.client_factory")
async def test_delete_issue_not_found(mock_factory, mock_settings, mock_context):
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
        await delete_issue(project_id="test-project", issue_iid=999, ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.delete_issue.client_factory")
async def test_delete_issue_single_tenant_mode(mock_factory, mock_settings):
    """Test issue deletion in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    # Setup mock GitLab client
    mock_gl = Mock()
    mock_project = Mock()
    mock_issue = Mock()
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    # Create context without headers
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await delete_issue(project_id="test-project", issue_iid=100, ctx=ctx)

    # Verify
    assert result["success"] is True

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
