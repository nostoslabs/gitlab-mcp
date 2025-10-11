"""Tests for create_issue tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.issues.create_issue import create_issue


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
    mock_issue.title = "Test Issue"
    mock_issue.description = "Test description"
    mock_issue.state = "opened"
    mock_issue.labels = ["bug"]
    mock_issue.web_url = "https://gitlab.example.com/project/-/issues/100"
    mock_issue.created_at = "2025-01-01T00:00:00Z"
    mock_issue.updated_at = "2025-01-01T00:00:00Z"
    mock_issue.author = {"username": "testuser", "name": "Test User"}

    # Chain mocks
    mock_project.issues.create.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.create_issue.client_factory")
async def test_create_issue_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful issue creation."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_issue(
        project_id="test-project",
        title="Test Issue",
        description="Test description",
        labels=["bug"],
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 1
    assert result["iid"] == 100
    assert result["project_id"] == 42
    assert result["title"] == "Test Issue"
    assert result["description"] == "Test description"
    assert result["state"] == "opened"
    assert result["labels"] == ["bug"]
    assert result["web_url"] == "https://gitlab.example.com/project/-/issues/100"
    assert result["created_at"] == "2025-01-01T00:00:00Z"
    assert result["updated_at"] == "2025-01-01T00:00:00Z"
    assert result["author"] == {"username": "testuser", "name": "Test User"}

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.create.assert_called_once_with(
        {"title": "Test Issue", "description": "Test description", "labels": "bug"}
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.create_issue.client_factory")
async def test_create_issue_minimal(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test issue creation with only required fields."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_issue(project_id="test-project", title="Minimal Issue", ctx=mock_context)

    # Verify
    assert result["title"] == "Test Issue"

    # Verify only title was passed (no description or labels)
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.create.assert_called_once_with({"title": "Minimal Issue"})


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.create_issue.client_factory")
async def test_create_issue_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_issue(project_id="nonexistent", title="Test", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.create_issue.client_factory")
async def test_create_issue_with_multiple_labels(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test issue creation with multiple labels."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await create_issue(
        project_id="test-project",
        title="Multi-label Issue",
        labels=["bug", "critical", "frontend"],
        ctx=mock_context,
    )

    # Verify labels are joined with comma
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.create.assert_called_once_with(
        {"title": "Multi-label Issue", "labels": "bug,critical,frontend"}
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.create_issue.client_factory")
async def test_create_issue_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test issue creation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await create_issue(project_id="test-project", title="Test", ctx=ctx)

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
