"""Tests for list_draft_notes tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.draft_notes.list_draft_notes import list_draft_notes


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
    mock_note1 = Mock()
    mock_note2 = Mock()

    # Setup mock note attributes
    mock_note1.id = 100
    mock_note1.note = "Draft comment 1"
    mock_note1.resolve_discussion = False
    mock_note1.author = Mock(id=1, username="reviewer", name="Reviewer Name")
    mock_note1.position = None

    mock_note2.id = 101
    mock_note2.note = "Draft comment 2"
    mock_note2.resolve_discussion = True
    mock_note2.author = Mock(id=1, username="reviewer", name="Reviewer Name")
    mock_note2.position = None

    # Chain mocks
    mock_mr.draft_notes.list.return_value = [mock_note1, mock_note2]
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.list_draft_notes.client_factory")
async def test_list_draft_notes_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful draft notes listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_draft_notes(
        project_id="test-project",
        mr_iid=10,
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 2
    assert len(result["draft_notes"]) == 2
    assert result["draft_notes"][0]["note"] == "Draft comment 1"
    assert result["draft_notes"][0]["resolve_discussion"] is False
    assert result["draft_notes"][1]["resolve_discussion"] is True

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.draft_notes.list.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.list_draft_notes.client_factory")
async def test_list_draft_notes_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test draft notes listing with no results."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make mock return empty list
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.draft_notes.list.return_value = []

    # Execute
    result = await list_draft_notes(
        project_id="test-project",
        mr_iid=10,
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 0
    assert len(result["draft_notes"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.list_draft_notes.client_factory")
async def test_list_draft_notes_feature_not_available(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test when draft notes feature is not available."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make draft_notes attribute missing (older GitLab version)
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    del mock_mr.draft_notes

    # Execute
    result = await list_draft_notes(
        project_id="test-project",
        mr_iid=10,
        ctx=mock_context,
    )

    # Verify result contains message about unavailable feature
    assert result["total_results"] == 0
    assert "message" in result
    assert "not available" in result["message"]


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.list_draft_notes.client_factory")
async def test_list_draft_notes_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_draft_notes(
            project_id="missing-project",
            mr_iid=10,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.list_draft_notes.client_factory")
async def test_list_draft_notes_mr_not_found(mock_factory, mock_settings, mock_context):
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
        await list_draft_notes(
            project_id="test-project",
            mr_iid=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.draft_notes.list_draft_notes.client_factory")
async def test_list_draft_notes_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test listing draft notes in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await list_draft_notes(
        project_id="test-project",
        mr_iid=10,
        ctx=ctx,
    )

    # Verify result
    assert result["total_results"] == 2

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
