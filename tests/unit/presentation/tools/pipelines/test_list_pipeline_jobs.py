"""Tests for list_pipeline_jobs tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.pipelines.list_pipeline_jobs import list_pipeline_jobs


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

    # Setup mock jobs
    mock_job1 = Mock()
    mock_job1.id = 1
    mock_job1.name = "build"
    mock_job1.status = "success"
    mock_job1.stage = "build"
    mock_job1.ref = "main"
    mock_job1.created_at = "2024-01-01T00:00:00Z"
    mock_job1.started_at = "2024-01-01T00:01:00Z"
    mock_job1.finished_at = "2024-01-01T00:05:00Z"
    mock_job1.duration = 240
    mock_job1.web_url = "https://gitlab.example.com/project/-/jobs/1"

    mock_job2 = Mock()
    mock_job2.id = 2
    mock_job2.name = "test"
    mock_job2.status = "failed"
    mock_job2.stage = "test"
    mock_job2.ref = "main"
    mock_job2.created_at = "2024-01-01T00:05:00Z"
    mock_job2.started_at = "2024-01-01T00:06:00Z"
    mock_job2.finished_at = "2024-01-01T00:08:00Z"
    mock_job2.duration = 120
    mock_job2.web_url = "https://gitlab.example.com/project/-/jobs/2"

    # Chain mocks
    mock_pipeline.jobs.list.return_value = [mock_job1, mock_job2]
    mock_project.pipelines.get.return_value = mock_pipeline
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipeline_jobs.client_factory")
async def test_list_pipeline_jobs_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful pipeline jobs listing."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_pipeline_jobs(
        project_id="test-project",
        pipeline_id=123,
        ctx=mock_context,
    )

    # Verify result
    assert len(result["jobs"]) == 2
    assert result["jobs"][0]["id"] == 1
    assert result["jobs"][0]["name"] == "build"
    assert result["jobs"][0]["status"] == "success"
    assert result["jobs"][0]["stage"] == "build"
    assert result["jobs"][1]["id"] == 2
    assert result["jobs"][1]["name"] == "test"
    assert result["jobs"][1]["status"] == "failed"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.pipelines.get.assert_called_once_with(123)
    mock_pipeline = mock_project.pipelines.get.return_value
    mock_pipeline.jobs.list.assert_called_once_with(all=True)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipeline_jobs.client_factory")
async def test_list_pipeline_jobs_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test pipeline jobs listing with no jobs."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return empty list
    mock_pipeline = mock_gitlab_client.projects.get.return_value.pipelines.get.return_value
    mock_pipeline.jobs.list.return_value = []

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_pipeline_jobs(
        project_id="test-project",
        pipeline_id=123,
        ctx=mock_context,
    )

    # Verify empty result
    assert result["jobs"] == []


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipeline_jobs.client_factory")
async def test_list_pipeline_jobs_pipeline_not_found(mock_factory, mock_settings, mock_context):
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
        await list_pipeline_jobs(
            project_id="test-project",
            pipeline_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipeline_jobs.client_factory")
async def test_list_pipeline_jobs_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_pipeline_jobs(
            project_id="nonexistent",
            pipeline_id=123,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.pipelines.list_pipeline_jobs.client_factory")
async def test_list_pipeline_jobs_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test pipeline jobs listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_pipeline_jobs(
        project_id="test-project",
        pipeline_id=123,
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
