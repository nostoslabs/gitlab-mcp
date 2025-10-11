"""Tests for create_draft_note tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.draft_notes.create_draft_note import create_draft_note


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
    mock_draft.note = "This needs review"
    mock_draft.position = None
    mock_draft.created_at = "2025-01-15T12:00:00Z"
    mock_draft.updated_at = "2025-01-15T12:00:00Z"
    mock_draft.author = Mock(id=1, username="author", name="Author Name")

    # Chain mocks
    mock_mr.draftnotes.create.return_value = mock_draft
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.create_draft_note.client_factory")
async def test_create_draft_note_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful draft note creation."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_draft_note(
        project_id="test-project",
        mr_iid=10,
        note="This needs review",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 200
    assert result["note"] == "This needs review"
    assert result["author"]["username"] == "author"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.draftnotes.create.assert_called_once_with({"note": "This needs review"})


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.create_draft_note.client_factory")
async def test_create_draft_note_with_position(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test draft note creation with position (inline comment)."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    position = {
        "base_sha": "abc123",
        "head_sha": "def456",
        "start_sha": "abc123",
        "new_path": "file.py",
        "new_line": 10,
    }

    # Execute
    await create_draft_note(
        project_id="test-project",
        mr_iid=10,
        note="Inline comment",
        position=position,
        ctx=mock_context,
    )

    # Verify position was included
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    call_args = mock_mr.draftnotes.create.call_args[0][0]
    assert call_args["position"] == position


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.create_draft_note.client_factory")
async def test_create_draft_note_mr_not_found(mock_factory, mock_settings, mock_context):
    """Test error when MR doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.mergerequests.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Merge request .* not found"):
        await create_draft_note(
            project_id="test-project",
            mr_iid=999,
            note="Comment",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.create_draft_note.client_factory")
async def test_create_draft_note_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test creating draft note in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await create_draft_note(
        project_id="test-project",
        mr_iid=10,
        note="Comment",
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 200

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
