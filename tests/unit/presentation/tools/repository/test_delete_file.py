"""Tests for delete_file tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.repository.delete_file import delete_file


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
    mock_file = Mock()

    # Setup mock file attributes
    mock_file.file_path = "to_delete.txt"
    mock_file.branch = "main"
    mock_file.last_commit_id = "commit999"

    # Chain mocks
    mock_project.files.get.return_value = mock_file
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.delete_file.client_factory")
async def test_delete_file_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful file deletion."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await delete_file(
        project_id="test-project",
        file_path="to_delete.txt",
        branch="main",
        commit_message="Delete file",
        ctx=mock_context,
    )

    # Verify result
    assert result["file_path"] == "to_delete.txt"
    assert result["branch"] == "main"
    assert result["deleted"] is True
    assert result["commit_id"] == "commit999"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.files.get.assert_called_once_with(file_path="to_delete.txt", ref="main")

    # Verify delete was called
    mock_file = mock_project.files.get.return_value
    mock_file.delete.assert_called_once_with(branch="main", commit_message="Delete file")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.delete_file.client_factory")
async def test_delete_file_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await delete_file(
            project_id="nonexistent",
            file_path="test.txt",
            branch="main",
            commit_message="Delete",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.delete_file.client_factory")
async def test_delete_file_not_found(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test error when file doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Make files.get raise GitlabGetError
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.files.get.side_effect = gitlab.exceptions.GitlabGetError("File not found")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="File .* not found"):
        await delete_file(
            project_id="test-project",
            file_path="nonexistent.txt",
            branch="main",
            commit_message="Delete",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.delete_file.client_factory")
async def test_delete_file_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test file deletion in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await delete_file(
        project_id="test-project",
        file_path="to_delete.txt",
        branch="main",
        commit_message="Delete file",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
