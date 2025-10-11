"""Tests for list_issue_discussions tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.discussions.list_issue_discussions import list_issue_discussions


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
    mock_discussion = Mock()

    # Setup mock discussion attributes
    mock_discussion.id = "abc123"
    mock_discussion.individual_note = False
    mock_discussion.attributes = {
        "notes": [
            {
                "id": 100,
                "body": "First comment",
                "created_at": "2025-01-15T12:00:00Z",
                "updated_at": "2025-01-15T12:00:00Z",
                "system": False,
                "noteable_id": 42,
                "noteable_type": "Issue",
                "author": {
                    "id": 1,
                    "username": "commenter",
                    "name": "Commenter Name",
                },
            },
            {
                "id": 101,
                "body": "Reply comment",
                "created_at": "2025-01-15T13:00:00Z",
                "updated_at": "2025-01-15T13:00:00Z",
                "system": False,
                "noteable_id": 42,
                "noteable_type": "Issue",
                "author": {
                    "id": 2,
                    "username": "replier",
                    "name": "Replier Name",
                },
            },
        ]
    }

    # Chain mocks
    mock_issue.discussions.list.return_value = [mock_discussion]
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_issue_discussions.client_factory")
async def test_list_issue_discussions_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful issue discussions listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_issue_discussions(
        project_id="test-project",
        issue_iid=42,
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 1
    assert len(result["discussions"]) == 1
    assert result["discussions"][0]["id"] == "abc123"
    assert len(result["discussions"][0]["notes"]) == 2
    assert result["discussions"][0]["notes"][0]["body"] == "First comment"
    assert result["discussions"][0]["notes"][1]["body"] == "Reply comment"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_issue = mock_gitlab_client.projects.get.return_value.issues.get.return_value
    mock_issue.discussions.list.assert_called_once_with(page=1, per_page=20)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_issue_discussions.client_factory")
async def test_list_issue_discussions_with_pagination(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test issue discussions listing with pagination."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    _result = await list_issue_discussions(
        project_id="test-project",
        issue_iid=42,
        page=2,
        per_page=50,
        ctx=mock_context,
    )

    # Verify pagination parameters were passed
    mock_issue = mock_gitlab_client.projects.get.return_value.issues.get.return_value
    mock_issue.discussions.list.assert_called_once_with(page=2, per_page=50)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_issue_discussions.client_factory")
async def test_list_issue_discussions_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test issue discussions listing with no results."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make mock return empty list
    mock_issue = mock_gitlab_client.projects.get.return_value.issues.get.return_value
    mock_issue.discussions.list.return_value = []

    # Execute
    result = await list_issue_discussions(
        project_id="test-project",
        issue_iid=42,
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 0
    assert len(result["discussions"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_issue_discussions.client_factory")
async def test_list_issue_discussions_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_issue_discussions(
            project_id="missing-project",
            issue_iid=42,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_issue_discussions.client_factory")
async def test_list_issue_discussions_issue_not_found(mock_factory, mock_settings, mock_context):
    """Test error when issue doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.issues.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Issue .* not found"):
        await list_issue_discussions(
            project_id="test-project",
            issue_iid=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.discussions.list_issue_discussions.client_factory")
async def test_list_issue_discussions_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test listing issue discussions in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await list_issue_discussions(
        project_id="test-project",
        issue_iid=42,
        ctx=ctx,
    )

    # Verify result
    assert result["total_results"] == 1

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
