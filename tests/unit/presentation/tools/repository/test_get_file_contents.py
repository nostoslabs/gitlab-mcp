"""Tests for get_file_contents tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.repository.get_file_contents import get_file_contents


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
    mock_file.file_path = "README.md"
    mock_file.file_name = "README.md"
    mock_file.size = 1024
    mock_file.encoding = "text"
    mock_file.content = "IyBUZXN0IFByb2plY3Q="  # Base64: "# Test Project"
    mock_file.content_sha256 = "abc123"
    mock_file.ref = "main"
    mock_file.blob_id = "blob123"
    mock_file.commit_id = "commit123"
    mock_file.last_commit_id = "commit123"

    # Chain mocks
    mock_project.files.get.return_value = mock_file
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_file_contents.client_factory")
async def test_get_file_contents_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful file retrieval."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_file_contents(
        project_id="test-project",
        file_path="README.md",
        ref="main",
        ctx=mock_context,
    )

    # Verify result
    assert result["file_path"] == "README.md"
    assert result["file_name"] == "README.md"
    assert result["size"] == 1024
    assert result["encoding"] == "text"
    assert result["content"] == "IyBUZXN0IFByb2plY3Q="
    assert result["content_sha256"] == "abc123"
    assert result["ref"] == "main"
    assert result["blob_id"] == "blob123"
    assert result["commit_id"] == "commit123"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.files.get.assert_called_once_with(file_path="README.md", ref="main")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_file_contents.client_factory")
async def test_get_file_contents_default_ref(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test file retrieval with default ref."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute without specifying ref
    await get_file_contents(project_id="test-project", file_path="README.md", ctx=mock_context)

    # Verify ref defaults to 'main'
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.files.get.assert_called_once_with(file_path="README.md", ref="main")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_file_contents.client_factory")
async def test_get_file_contents_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await get_file_contents(project_id="nonexistent", file_path="README.md", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_file_contents.client_factory")
async def test_get_file_contents_file_not_found(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when file doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Make files.get raise GitlabGetError
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.files.get.side_effect = gitlab.exceptions.GitlabGetError("File not found")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="File .* not found"):
        await get_file_contents(
            project_id="test-project", file_path="nonexistent.txt", ctx=mock_context
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_file_contents.client_factory")
async def test_get_file_contents_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test file retrieval in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await get_file_contents(project_id="test-project", file_path="README.md", ctx=ctx)

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
