"""Tests for publish_draft_note tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.draft_notes.publish_draft_note import publish_draft_note


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

    # Chain mocks
    mock_mr.draftnotes.get.return_value = mock_draft
    mock_mr.iid = 10
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.publish_draft_note.client_factory")
async def test_publish_draft_note_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful draft note publication."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await publish_draft_note(
        project_id="test-project",
        mr_iid=10,
        draft_note_id=200,
        ctx=mock_context,
    )

    # Verify result
    assert result["success"] is True
    assert result["published_draft_note_id"] == 200
    assert result["mr_iid"] == 10

    # Verify publish was called
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.draftnotes.publish.assert_called_once_with(200)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.publish_draft_note.client_factory")
async def test_publish_draft_note_not_found(mock_factory, mock_settings, mock_context):
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
        await publish_draft_note(
            project_id="test-project",
            mr_iid=10,
            draft_note_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.publish_draft_note.client_factory")
async def test_publish_draft_note_publish_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when publication fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make publish raise error
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.draftnotes.publish.side_effect = Exception("Cannot publish")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to publish draft note"):
        await publish_draft_note(
            project_id="test-project",
            mr_iid=10,
            draft_note_id=200,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.publish_draft_note.client_factory")
async def test_publish_draft_note_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test publishing draft note in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await publish_draft_note(
        project_id="test-project",
        mr_iid=10,
        draft_note_id=200,
        ctx=ctx,
    )

    # Verify result
    assert result["success"] is True

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
