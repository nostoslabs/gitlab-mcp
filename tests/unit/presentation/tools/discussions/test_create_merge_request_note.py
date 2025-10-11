"""Tests for create_merge_request_note tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.discussions.create_merge_request_note import (
    create_merge_request_note,
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
    """Mock python-gitlab client."""
    mock_gl = Mock()
    mock_project = Mock()
    mock_mr = Mock()
    mock_note = Mock()

    # Setup mock note attributes
    mock_note.id = 300
    mock_note.body = "Great work on this MR!"
    mock_note.created_at = "2025-01-15T14:00:00Z"
    mock_note.updated_at = "2025-01-15T14:00:00Z"
    mock_note.system = False
    mock_note.noteable_id = 10
    mock_note.noteable_type = "MergeRequest"
    mock_note.author = Mock(id=5, username="reviewer", name="Reviewer Name")

    # Chain mocks
    mock_mr.notes.create.return_value = mock_note
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.create_merge_request_note.client_factory")
async def test_create_mr_note_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful merge request note creation."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_merge_request_note(
        project_id="test-project",
        mr_iid=10,
        body="Great work on this MR!",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 300
    assert result["body"] == "Great work on this MR!"
    assert result["noteable_type"] == "MergeRequest"
    assert result["author"]["username"] == "reviewer"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.notes.create.assert_called_once_with({"body": "Great work on this MR!"})


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.create_merge_request_note.client_factory")
async def test_create_mr_note_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_merge_request_note(
            project_id="missing-project",
            mr_iid=10,
            body="Comment",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.create_merge_request_note.client_factory")
async def test_create_mr_note_mr_not_found(mock_factory, mock_settings, mock_context):
    """Test error when merge request doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.mergerequests.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Merge request .* not found"):
        await create_merge_request_note(
            project_id="test-project",
            mr_iid=999,
            body="Comment",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.create_merge_request_note.client_factory")
async def test_create_mr_note_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test creating merge request note in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await create_merge_request_note(
        project_id="test-project",
        mr_iid=10,
        body="Comment",
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 300

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
