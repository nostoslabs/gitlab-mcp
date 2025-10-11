"""Tests for list_merge_request_discussions tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.discussions.list_merge_request_discussions import (
    list_merge_request_discussions,
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
    mock_discussion = Mock()

    # Setup mock discussion attributes
    mock_discussion.id = "xyz789"
    mock_discussion.individual_note = False
    mock_discussion.attributes = {
        "notes": [
            {
                "id": 200,
                "body": "Review comment",
                "created_at": "2025-01-15T14:00:00Z",
                "updated_at": "2025-01-15T14:00:00Z",
                "system": False,
                "resolvable": True,
                "resolved": False,
                "author": {
                    "id": 5,
                    "username": "reviewer",
                    "name": "Reviewer Name",
                },
            }
        ]
    }

    # Chain mocks
    mock_mr.discussions.list.return_value = [mock_discussion]
    mock_project.mergerequests.get.return_value = mock_mr
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_merge_request_discussions.client_factory")
async def test_list_mr_discussions_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful merge request discussions listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_merge_request_discussions(
        project_id="test-project",
        mr_iid=10,
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 1
    assert len(result["discussions"]) == 1
    assert result["discussions"][0]["id"] == "xyz789"
    assert len(result["discussions"][0]["notes"]) == 1
    assert result["discussions"][0]["notes"][0]["body"] == "Review comment"
    assert result["discussions"][0]["notes"][0]["resolvable"] is True
    assert result["page"] == 1
    assert result["per_page"] == 20
    assert result["mr_iid"] == 10

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.discussions.list.assert_called_once_with(page=1, per_page=20, get_all=False)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_merge_request_discussions.client_factory")
async def test_list_mr_discussions_with_pagination(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test merge request discussions listing with pagination."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_merge_request_discussions(
        project_id="test-project",
        mr_iid=10,
        page=3,
        per_page=100,
        ctx=mock_context,
    )

    # Verify pagination parameters
    assert result["page"] == 3
    assert result["per_page"] == 100

    # Verify pagination parameters were passed
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.discussions.list.assert_called_once_with(page=3, per_page=100, get_all=False)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_merge_request_discussions.client_factory")
async def test_list_mr_discussions_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test merge request discussions listing with no results."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make mock return empty list
    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.discussions.list.return_value = []

    # Execute
    result = await list_merge_request_discussions(
        project_id="test-project",
        mr_iid=10,
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 0
    assert len(result["discussions"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_merge_request_discussions.client_factory")
async def test_list_mr_discussions_mr_not_found(mock_factory, mock_settings, mock_context):
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
        await list_merge_request_discussions(
            project_id="test-project",
            mr_iid=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_merge_request_discussions.client_factory")
async def test_list_mr_discussions_fetch_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when fetching discussions fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    mock_mr = mock_gitlab_client.projects.get.return_value.mergerequests.get.return_value
    mock_mr.discussions.list.side_effect = Exception("API error")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to fetch discussions"):
        await list_merge_request_discussions(
            project_id="test-project",
            mr_iid=10,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_merge_request_discussions.client_factory")
async def test_list_mr_discussions_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test listing merge request discussions in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await list_merge_request_discussions(
        project_id="test-project",
        mr_iid=10,
        ctx=ctx,
    )

    # Verify result
    assert result["total_results"] == 1

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
