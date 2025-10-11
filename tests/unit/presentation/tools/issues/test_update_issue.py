"""Tests for update_issue tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.issues.update_issue import update_issue


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

    # Setup mock issue attributes
    mock_issue.id = 1
    mock_issue.iid = 100
    mock_issue.project_id = 42
    mock_issue.title = "Updated Issue"
    mock_issue.description = "Updated description"
    mock_issue.state = "closed"
    mock_issue.labels = ["bug", "resolved"]
    mock_issue.web_url = "https://gitlab.example.com/project/-/issues/100"
    mock_issue.updated_at = "2025-01-02T00:00:00Z"

    # Chain mocks
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.update_issue.client_factory")
async def test_update_issue_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful issue update."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await update_issue(
        project_id="test-project",
        issue_iid=100,
        title="Updated Issue",
        description="Updated description",
        labels=["bug", "resolved"],
        state_event="close",
        ctx=mock_context,
    )

    # Verify result
    assert result["iid"] == 100
    assert result["title"] == "Updated Issue"
    assert result["description"] == "Updated description"
    assert result["state"] == "closed"
    assert result["labels"] == ["bug", "resolved"]

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.get.assert_called_once_with(100)

    # Verify issue was updated
    mock_issue = mock_project.issues.get.return_value
    assert mock_issue.title == "Updated Issue"
    assert mock_issue.description == "Updated description"
    assert mock_issue.labels == ["bug", "resolved"]
    assert mock_issue.state_event == "close"
    mock_issue.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.update_issue.client_factory")
async def test_update_issue_partial_update(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test partial issue update (only title)."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute - only update title
    await update_issue(
        project_id="test-project", issue_iid=100, title="New Title", ctx=mock_context
    )

    # Verify title was updated
    mock_issue = mock_gitlab_client.projects.get.return_value.issues.get.return_value
    assert mock_issue.title == "New Title"
    # save() should be called to persist the change
    mock_issue.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.update_issue.client_factory")
async def test_update_issue_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await update_issue(project_id="nonexistent", issue_iid=100, title="Test", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.update_issue.client_factory")
async def test_update_issue_not_found(mock_factory, mock_settings, mock_context):
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
        await update_issue(project_id="test-project", issue_iid=999, title="Test", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.update_issue.client_factory")
async def test_update_issue_single_tenant_mode(mock_factory, mock_settings):
    """Test issue update in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    # Setup mock GitLab client
    mock_gl = Mock()
    mock_project = Mock()
    mock_issue = Mock()
    mock_issue.id = 1
    mock_issue.iid = 100
    mock_issue.project_id = 42
    mock_issue.title = "Updated"  # Will be set by the update
    mock_issue.description = "Test"
    mock_issue.state = "opened"
    mock_issue.labels = []
    mock_issue.web_url = "https://gitlab.com/project/-/issues/100"
    mock_issue.updated_at = "2025-01-02T00:00:00Z"

    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    # Create context without headers
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await update_issue(project_id="test-project", issue_iid=100, title="Updated", ctx=ctx)

    # Verify the title was updated
    assert result["title"] == "Updated"

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
