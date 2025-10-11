"""Tests for create_issue_note tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.discussions.create_issue_note import create_issue_note


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
    mock_note = Mock()

    # Setup mock note attributes
    mock_note.id = 100
    mock_note.body = "This is a comment"
    mock_note.created_at = "2025-01-15T12:00:00Z"
    mock_note.updated_at = "2025-01-15T12:00:00Z"
    mock_note.system = False
    mock_note.noteable_id = 42
    mock_note.noteable_type = "Issue"
    mock_note.author = Mock(id=1, username="author", name="Author Name")

    # Chain mocks
    mock_issue.notes.create.return_value = mock_note
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.create_issue_note.client_factory")
async def test_create_issue_note_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful issue note creation."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_issue_note(
        project_id="test-project",
        issue_iid=42,
        body="This is a comment",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 100
    assert result["body"] == "This is a comment"
    assert result["author"]["id"] == 1
    assert result["author"]["username"] == "author"
    assert result["system"] is False

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.get.assert_called_once_with(42)
    mock_issue = mock_project.issues.get.return_value
    mock_issue.notes.create.assert_called_once_with({"body": "This is a comment"})


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.create_issue_note.client_factory")
async def test_create_issue_note_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_issue_note(
            project_id="nonexistent",
            issue_iid=42,
            body="Comment",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.create_issue_note.client_factory")
async def test_create_issue_note_issue_not_found(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when issue doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    # Make issues.get raise error
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Issue .* not found"):
        await create_issue_note(
            project_id="test-project",
            issue_iid=999,
            body="Comment",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.create_issue_note.client_factory")
async def test_create_issue_note_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test creating issue note in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await create_issue_note(
        project_id="test-project",
        issue_iid=42,
        body="Comment",
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 100

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
