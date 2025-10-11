"""Tests for update_milestone tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.milestones.update_milestone import update_milestone


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

    # Setup mock milestone
    mock_milestone = Mock()
    mock_milestone.id = 1
    mock_milestone.iid = 1
    mock_milestone.title = "v1.0 Updated"
    mock_milestone.description = "Updated description"
    mock_milestone.state = "active"
    mock_milestone.due_date = "2024-12-31"
    mock_milestone.start_date = "2024-01-01"
    mock_milestone.web_url = "https://gitlab.example.com/project/-/milestones/1"
    mock_milestone.created_at = "2024-01-01T00:00:00Z"
    mock_milestone.updated_at = "2024-01-02T00:00:00Z"

    # Chain mocks
    mock_project.milestones.get.return_value = mock_milestone
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.update_milestone.client_factory")
async def test_update_milestone_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful milestone update."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await update_milestone(
        project_id="test-project",
        milestone_id=1,
        title="v1.0 Updated",
        description="Updated description",
        due_date="2024-12-31",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 1
    assert result["title"] == "v1.0 Updated"
    assert result["description"] == "Updated description"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.get.assert_called_once_with(1)

    # Verify milestone was updated
    mock_milestone = mock_project.milestones.get.return_value
    assert mock_milestone.title == "v1.0 Updated"
    assert mock_milestone.description == "Updated description"
    assert mock_milestone.due_date == "2024-12-31"
    mock_milestone.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.update_milestone.client_factory")
async def test_update_milestone_partial(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test milestone update with only some fields."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with only title
    await update_milestone(
        project_id="test-project",
        milestone_id=1,
        title="v1.0 Updated",
        ctx=mock_context,
    )

    # Verify only title was updated
    mock_milestone = mock_gitlab_client.projects.get.return_value.milestones.get.return_value
    assert mock_milestone.title == "v1.0 Updated"
    mock_milestone.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.update_milestone.client_factory")
async def test_update_milestone_not_found(mock_factory, mock_settings, mock_context):
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
        await update_milestone(
            project_id="test-project",
            milestone_id=999,
            title="Updated",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.update_milestone.client_factory")
async def test_update_milestone_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await update_milestone(
            project_id="nonexistent",
            milestone_id=1,
            title="Updated",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.update_milestone.client_factory")
async def test_update_milestone_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test milestone update in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await update_milestone(
        project_id="test-project",
        milestone_id=1,
        title="Updated",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
