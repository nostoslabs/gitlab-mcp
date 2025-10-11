"""Tests for get_pipeline_job_log tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.pipelines.get_pipeline_job_log import (
    get_pipeline_job_log,
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

    # Setup mock job
    mock_job = Mock()
    mock_job.id = 123
    mock_job.name = "build"
    mock_job.status = "success"
    mock_job.web_url = "https://gitlab.example.com/project/-/jobs/123"

    # Mock trace method to return log output
    mock_job.trace.return_value = b"Building project...\nTests passed\nDeploy complete"

    # Chain mocks
    mock_project.jobs.get.return_value = mock_job
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.get_pipeline_job_log.client_factory")
async def test_get_pipeline_job_log_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful job log retrieval."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_pipeline_job_log(
        project_id="test-project",
        job_id=123,
        ctx=mock_context,
    )

    # Verify result
    assert result["job_id"] == 123
    assert result["job_name"] == "build"
    assert result["status"] == "success"
    assert "Building project" in result["log"]
    assert "Tests passed" in result["log"]
    assert "Deploy complete" in result["log"]

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.jobs.get.assert_called_once_with(123)
    mock_job = mock_project.jobs.get.return_value
    mock_job.trace.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.get_pipeline_job_log.client_factory")
async def test_get_pipeline_job_log_empty_log(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test job log retrieval with empty log."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return empty log
    mock_job = mock_gitlab_client.projects.get.return_value.jobs.get.return_value
    mock_job.trace.return_value = b""

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_pipeline_job_log(
        project_id="test-project",
        job_id=123,
        ctx=mock_context,
    )

    # Verify empty log
    assert result["log"] == ""


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.get_pipeline_job_log.client_factory")
async def test_get_pipeline_job_log_job_not_found(mock_factory, mock_settings, mock_context):
    """Test error when job doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.jobs.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Job .* not found"):
        await get_pipeline_job_log(
            project_id="test-project",
            job_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.get_pipeline_job_log.client_factory")
async def test_get_pipeline_job_log_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await get_pipeline_job_log(
            project_id="nonexistent",
            job_id=123,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.get_pipeline_job_log.client_factory")
async def test_get_pipeline_job_log_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test job log retrieval in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await get_pipeline_job_log(
        project_id="test-project",
        job_id=123,
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
