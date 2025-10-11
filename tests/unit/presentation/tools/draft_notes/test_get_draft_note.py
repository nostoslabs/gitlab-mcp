"""Tests for get_draft_note tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.draft_notes.get_draft_note import get_draft_note


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
    mock_note.id = 200
    mock_note.note = "This is a draft comment"
    mock_note.resolve_discussion = False
    mock_note.author = Mock(id=1, username="reviewer", name="Reviewer Name")
    mock_note.position = None

    # Chain mocks
    mock_mr.draft_notes.get.return_value = mock_note
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.get_draft_note.client_factory")
async def test_get_draft_note_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful draft note retrieval."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_draft_note(
        project_id="test-project",
        mr_iid=10,
        draft_note_id=200,
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 200
    assert result["note"] == "This is a draft comment"
    assert result["resolve_discussion"] is False
    assert result["author"]["username"] == "reviewer"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.draft_notes.get.assert_called_once_with(200)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.get_draft_note.client_factory")
async def test_get_draft_note_feature_not_available(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test when draft notes feature is not available."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make draft_notes attribute missing (older GitLab version)
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    del mock_mr.draft_notes

    with pytest.raises(ValueError, match="Draft notes feature not available"):
        await get_draft_note(
            project_id="test-project",
            mr_iid=10,
            draft_note_id=200,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.get_draft_note.client_factory")
async def test_get_draft_note_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await get_draft_note(
            project_id="missing-project",
            mr_iid=10,
            draft_note_id=200,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.get_draft_note.client_factory")
async def test_get_draft_note_mr_not_found(mock_factory, mock_settings, mock_context):
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
        await get_draft_note(
            project_id="test-project",
            mr_iid=999,
            draft_note_id=200,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.get_draft_note.client_factory")
async def test_get_draft_note_not_found(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when draft note doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.draft_notes.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Draft note .* not found"):
        await get_draft_note(
            project_id="test-project",
            mr_iid=10,
            draft_note_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.get_draft_note.client_factory")
async def test_get_draft_note_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test getting draft note in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await get_draft_note(
        project_id="test-project",
        mr_iid=10,
        draft_note_id=200,
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 200

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
