"""Tests for create_pipeline tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.pipelines.create_pipeline import create_pipeline


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

    # Setup mock created pipeline
    mock_pipeline = Mock()
    mock_pipeline.id = 125
    mock_pipeline.iid = 3
    mock_pipeline.status = "pending"
    mock_pipeline.ref = "main"
    mock_pipeline.sha = "abc123def456"
    mock_pipeline.web_url = "https://gitlab.example.com/project/-/pipelines/125"
    mock_pipeline.created_at = "2024-01-03T00:00:00Z"
    mock_pipeline.updated_at = "2024-01-03T00:00:00Z"

    # Chain mocks
    mock_project.pipelines.create.return_value = mock_pipeline
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.create_pipeline.client_factory")
async def test_create_pipeline_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful pipeline creation."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_pipeline(
        project_id="test-project",
        ref="main",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 125
    assert result["iid"] == 3
    assert result["status"] == "pending"
    assert result["ref"] == "main"
    assert result["sha"] == "abc123def456"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.pipelines.create.assert_called_once_with({"ref": "main"})


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.create_pipeline.client_factory")
async def test_create_pipeline_with_variables(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test pipeline creation with variables."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with variables
    variables = [
        {"key": "VAR1", "value": "value1"},
        {"key": "VAR2", "value": "value2"},
    ]
    await create_pipeline(
        project_id="test-project",
        ref="feature-branch",
        variables=variables,
        ctx=mock_context,
    )

    # Verify variables were passed
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.pipelines.create.assert_called_once_with(
        {"ref": "feature-branch", "variables": variables}
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.create_pipeline.client_factory")
async def test_create_pipeline_failure(mock_factory, mock_settings, mock_context):
    """Test error when pipeline creation fails."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.pipelines.create.side_effect = gitlab.exceptions.GitlabCreateError(
        "Creation failed"
    )
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Failed to create pipeline"):
        await create_pipeline(
            project_id="test-project",
            ref="main",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.create_pipeline.client_factory")
async def test_create_pipeline_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_pipeline(
            project_id="nonexistent",
            ref="main",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.create_pipeline.client_factory")
async def test_create_pipeline_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test pipeline creation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await create_pipeline(
        project_id="test-project",
        ref="main",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
