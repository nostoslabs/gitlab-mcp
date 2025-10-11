"""Tests for list_milestones tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.milestones.list_milestones import list_milestones


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

    # Setup mock milestones
    mock_milestone1 = Mock()
    mock_milestone1.id = 1
    mock_milestone1.iid = 1
    mock_milestone1.title = "v1.0"
    mock_milestone1.description = "First release"
    mock_milestone1.state = "active"
    mock_milestone1.due_date = "2024-12-31"
    mock_milestone1.start_date = "2024-01-01"
    mock_milestone1.web_url = "https://gitlab.example.com/project/-/milestones/1"
    mock_milestone1.created_at = "2024-01-01T00:00:00Z"
    mock_milestone1.updated_at = "2024-01-01T00:10:00Z"

    mock_milestone2 = Mock()
    mock_milestone2.id = 2
    mock_milestone2.iid = 2
    mock_milestone2.title = "v2.0"
    mock_milestone2.description = "Second release"
    mock_milestone2.state = "closed"
    mock_milestone2.due_date = "2025-06-30"
    mock_milestone2.start_date = "2024-06-01"
    mock_milestone2.web_url = "https://gitlab.example.com/project/-/milestones/2"
    mock_milestone2.created_at = "2024-06-01T00:00:00Z"
    mock_milestone2.updated_at = "2024-06-01T00:10:00Z"

    # Chain mocks
    mock_project.milestones.list.return_value = [mock_milestone1, mock_milestone2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestones.client_factory")
async def test_list_milestones_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful milestone listing."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_milestones(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify result
    assert len(result["milestones"]) == 2
    assert result["milestones"][0]["id"] == 1
    assert result["milestones"][0]["title"] == "v1.0"
    assert result["milestones"][0]["state"] == "active"
    assert result["milestones"][1]["id"] == 2
    assert result["milestones"][1]["title"] == "v2.0"
    assert result["milestones"][1]["state"] == "closed"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.list.assert_called_once_with(all=True)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestones.client_factory")
async def test_list_milestones_with_state_filter(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test milestone listing with state filter."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with state filter
    await list_milestones(
        project_id="test-project",
        state="active",
        ctx=mock_context,
    )

    # Verify filter parameters were passed
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.list.assert_called_once_with(all=True, state="active")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestones.client_factory")
async def test_list_milestones_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test milestone listing with no milestones."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return empty list
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.list.return_value = []

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_milestones(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify empty result
    assert result["milestones"] == []


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestones.client_factory")
async def test_list_milestones_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_milestones(
            project_id="nonexistent",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestones.client_factory")
async def test_list_milestones_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test milestone listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_milestones(
        project_id="test-project",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
