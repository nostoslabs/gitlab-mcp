"""Tests for update_draft_note tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.draft_notes.update_draft_note import update_draft_note


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
    mock_draft = Mock()

    # Setup mock draft note attributes
    mock_draft.id = 200
    mock_draft.note = "Updated review comment"
    mock_draft.position = None
    mock_draft.created_at = "2025-01-15T12:00:00Z"
    mock_draft.updated_at = "2025-01-15T13:00:00Z"
    mock_draft.author = Mock(id=1, username="author", name="Author Name")

    # Chain mocks
    mock_mr.draftnotes.get.return_value = mock_draft
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.update_draft_note.client_factory")
async def test_update_draft_note_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful draft note update."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await update_draft_note(
        project_id="test-project",
        mr_iid=10,
        draft_note_id=200,
        note="Updated review comment",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 200
    assert result["note"] == "Updated review comment"

    # Verify save was called
    mock_draft = (
        mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value.draftnotes.get.return_value
    )
    assert mock_draft.note == "Updated review comment"
    mock_draft.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.update_draft_note.client_factory")
async def test_update_draft_note_not_found(mock_factory, mock_settings, mock_context):
    """Test error when draft note doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_mr = Mock()
    mock_mr.draftnotes.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Draft note .* not found"):
        await update_draft_note(
            project_id="test-project",
            mr_iid=10,
            draft_note_id=999,
            note="Updated",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.update_draft_note.client_factory")
async def test_update_draft_note_save_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when save fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make save raise error
    mock_draft = (
        mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value.draftnotes.get.return_value
    )
    mock_draft.save.side_effect = Exception("Permission denied")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to update draft note"):
        await update_draft_note(
            project_id="test-project",
            mr_iid=10,
            draft_note_id=200,
            note="Updated",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.update_draft_note.client_factory")
async def test_update_draft_note_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test updating draft note in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await update_draft_note(
        project_id="test-project",
        mr_iid=10,
        draft_note_id=200,
        note="Updated",
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 200

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
