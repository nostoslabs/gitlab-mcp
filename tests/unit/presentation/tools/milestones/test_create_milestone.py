"""Tests for create_milestone tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.milestones.create_milestone import create_milestone


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

    # Setup mock milestone (created)
    mock_milestone = Mock()
    mock_milestone.id = 1
    mock_milestone.iid = 1
    mock_milestone.title = "v1.0"
    mock_milestone.description = "First release"
    mock_milestone.state = "active"
    mock_milestone.due_date = "2024-12-31"
    mock_milestone.start_date = "2024-01-01"
    mock_milestone.web_url = "https://gitlab.example.com/project/-/milestones/1"
    mock_milestone.created_at = "2024-01-01T00:00:00Z"
    mock_milestone.updated_at = "2024-01-01T00:10:00Z"

    # Chain mocks
    mock_project.milestones.create.return_value = mock_milestone
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.create_milestone.client_factory")
async def test_create_milestone_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful milestone creation."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_milestone(
        project_id="test-project",
        title="v1.0",
        description="First release",
        due_date="2024-12-31",
        start_date="2024-01-01",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 1
    assert result["title"] == "v1.0"
    assert result["description"] == "First release"
    assert result["state"] == "active"
    assert result["due_date"] == "2024-12-31"
    assert result["start_date"] == "2024-01-01"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.create.assert_called_once_with(
        {
            "title": "v1.0",
            "description": "First release",
            "due_date": "2024-12-31",
            "start_date": "2024-01-01",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.create_milestone.client_factory")
async def test_create_milestone_minimal(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test milestone creation with only required fields."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with only title
    await create_milestone(
        project_id="test-project",
        title="v1.0",
        ctx=mock_context,
    )

    # Verify only title was passed
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.create.assert_called_once_with(
        {
            "title": "v1.0",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.create_milestone.client_factory")
async def test_create_milestone_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_milestone(
            project_id="nonexistent",
            title="v1.0",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.create_milestone.client_factory")
async def test_create_milestone_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test milestone creation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await create_milestone(
        project_id="test-project",
        title="v1.0",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
