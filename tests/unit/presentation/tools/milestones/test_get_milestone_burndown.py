"""Tests for get_milestone_burndown tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.milestones.get_milestone_burndown import get_milestone_burndown


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

    # Setup mock milestone with burndown data
    mock_milestone = Mock()
    mock_milestone.id = 1
    mock_milestone.iid = 1
    mock_milestone.title = "v1.0"
    mock_milestone.state = "active"

    # Mock attributes that might contain burndown/statistics
    mock_milestone.attributes = {
        "id": 1,
        "iid": 1,
        "title": "v1.0",
        "state": "active",
        "total_issues_count": 10,
        "closed_issues_count": 7,
    }

    # Chain mocks
    mock_project.milestones.get.return_value = mock_milestone
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.get_milestone_burndown.client_factory")
async def test_get_milestone_burndown_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful milestone burndown retrieval."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_milestone_burndown(
        project_id="test-project",
        milestone_id=1,
        ctx=mock_context,
    )

    # Verify result
    assert result["milestone_id"] == 1
    assert result["title"] == "v1.0"
    assert "statistics" in result
    assert result["statistics"]["total_issues_count"] == 10
    assert result["statistics"]["closed_issues_count"] == 7

    # Verify python-gitlab was called correctly with lazy=False
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.get.assert_called_once_with(1, lazy=False)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.get_milestone_burndown.client_factory")
async def test_get_milestone_burndown_not_found(mock_factory, mock_settings, mock_context):
    """Test error when milestone doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.milestones.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Milestone .* not found"):
        await get_milestone_burndown(
            project_id="test-project",
            milestone_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.get_milestone_burndown.client_factory")
async def test_get_milestone_burndown_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await get_milestone_burndown(
            project_id="nonexistent",
            milestone_id=1,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.get_milestone_burndown.client_factory")
async def test_get_milestone_burndown_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test milestone burndown retrieval in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await get_milestone_burndown(
        project_id="test-project",
        milestone_id=1,
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
