"""Tests for list_pipelines tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.pipelines.list_pipelines import list_pipelines


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

    # Setup mock pipelines
    mock_pipeline1 = Mock()
    mock_pipeline1.id = 123
    mock_pipeline1.iid = 1
    mock_pipeline1.status = "success"
    mock_pipeline1.ref = "main"
    mock_pipeline1.sha = "abc123"
    mock_pipeline1.web_url = "https://gitlab.example.com/project/-/pipelines/123"
    mock_pipeline1.created_at = "2024-01-01T00:00:00Z"
    mock_pipeline1.updated_at = "2024-01-01T00:10:00Z"

    mock_pipeline2 = Mock()
    mock_pipeline2.id = 124
    mock_pipeline2.iid = 2
    mock_pipeline2.status = "running"
    mock_pipeline2.ref = "feature-branch"
    mock_pipeline2.sha = "def456"
    mock_pipeline2.web_url = "https://gitlab.example.com/project/-/pipelines/124"
    mock_pipeline2.created_at = "2024-01-02T00:00:00Z"
    mock_pipeline2.updated_at = "2024-01-02T00:05:00Z"

    # Chain mocks
    mock_project.pipelines.list.return_value = [mock_pipeline1, mock_pipeline2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipelines.client_factory")
async def test_list_pipelines_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful pipeline listing."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_pipelines(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify result
    assert len(result["pipelines"]) == 2
    assert result["pipelines"][0]["id"] == 123
    assert result["pipelines"][0]["status"] == "success"
    assert result["pipelines"][0]["ref"] == "main"
    assert result["pipelines"][1]["id"] == 124
    assert result["pipelines"][1]["status"] == "running"
    assert result["pipelines"][1]["ref"] == "feature-branch"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.pipelines.list.assert_called_once_with(all=True)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipelines.client_factory")
async def test_list_pipelines_with_filters(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test pipeline listing with ref and status filters."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with filters
    await list_pipelines(
        project_id="test-project",
        ref="main",
        status="success",
        ctx=mock_context,
    )

    # Verify filter parameters were passed
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.pipelines.list.assert_called_once_with(all=True, ref="main", status="success")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipelines.client_factory")
async def test_list_pipelines_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test pipeline listing with no pipelines."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return empty list
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.pipelines.list.return_value = []

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_pipelines(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify empty result
    assert result["pipelines"] == []


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipelines.client_factory")
async def test_list_pipelines_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_pipelines(
            project_id="nonexistent",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipelines.client_factory")
async def test_list_pipelines_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test pipeline listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_pipelines(
        project_id="test-project",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
