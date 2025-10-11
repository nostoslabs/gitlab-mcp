"""Tests for update_issue_note tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.discussions.update_issue_note import update_issue_note


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
    mock_note.body = "Updated comment text"
    mock_note.created_at = "2025-01-15T12:00:00Z"
    mock_note.updated_at = "2025-01-15T13:00:00Z"
    mock_note.system = False
    mock_note.noteable_type = "Issue"
    mock_note.author = Mock(id=1, username="author", name="Author Name")

    # Chain mocks
    mock_issue.notes.get.return_value = mock_note
    mock_issue.iid = 42
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.update_issue_note.client_factory")
async def test_update_issue_note_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful issue note update."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await update_issue_note(
        project_id="test-project",
        issue_iid=42,
        note_id=100,
        body="Updated comment text",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 100
    assert result["body"] == "Updated comment text"
    assert result["noteable_iid"] == 42

    # Verify save was called
    mock_note = (
        mock_gitlab_client.projects.get.return_value.issues.get.return_value.notes.get.return_value
    )
    assert mock_note.body == "Updated comment text"
    mock_note.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.update_issue_note.client_factory")
async def test_update_issue_note_not_found(mock_factory, mock_settings, mock_context):
    """Test error when note doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_issue = Mock()
    mock_issue.notes.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Note .* not found"):
        await update_issue_note(
            project_id="test-project",
            issue_iid=42,
            note_id=999,
            body="Updated text",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.update_issue_note.client_factory")
async def test_update_issue_note_save_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when save fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make save raise error
    mock_note = (
        mock_gitlab_client.projects.get.return_value.issues.get.return_value.notes.get.return_value
    )
    mock_note.save.side_effect = Exception("Permission denied")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to update issue note"):
        await update_issue_note(
            project_id="test-project",
            issue_iid=42,
            note_id=100,
            body="Updated text",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.update_issue_note.client_factory")
async def test_update_issue_note_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test updating issue note in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await update_issue_note(
        project_id="test-project",
        issue_iid=42,
        note_id=100,
        body="Updated text",
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 100

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
