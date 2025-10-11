"""Tests for cancel_pipeline tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.pipelines.cancel_pipeline import cancel_pipeline


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

    # Setup mock pipeline
    mock_pipeline = Mock()
    mock_pipeline.id = 123
    mock_pipeline.iid = 1
    mock_pipeline.status = "canceled"
    mock_pipeline.ref = "main"
    mock_pipeline.sha = "abc123def456"
    mock_pipeline.web_url = "https://gitlab.example.com/project/-/pipelines/123"

    # Mock cancel method
    mock_pipeline.cancel.return_value = None

    # Chain mocks
    mock_project.pipelines.get.return_value = mock_pipeline
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.cancel_pipeline.client_factory")
async def test_cancel_pipeline_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful pipeline cancellation."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await cancel_pipeline(
        project_id="test-project",
        pipeline_id=123,
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 123
    assert result["status"] == "canceled"
    assert result["message"] == "Pipeline canceled successfully"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.pipelines.get.assert_called_once_with(123)
    mock_pipeline = mock_project.pipelines.get.return_value
    mock_pipeline.cancel.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.cancel_pipeline.client_factory")
async def test_cancel_pipeline_not_found(mock_factory, mock_settings, mock_context):
    """Test error when pipeline doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.pipelines.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Pipeline .* not found"):
        await cancel_pipeline(
            project_id="test-project",
            pipeline_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.cancel_pipeline.client_factory")
async def test_cancel_pipeline_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await cancel_pipeline(
            project_id="nonexistent",
            pipeline_id=123,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.cancel_pipeline.client_factory")
async def test_cancel_pipeline_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test pipeline cancellation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await cancel_pipeline(
        project_id="test-project",
        pipeline_id=123,
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
