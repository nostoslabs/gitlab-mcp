"""Tests for create_or_update_file tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.repository.create_or_update_file import (
    create_or_update_file,
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
def mock_gitlab_client_create():
    """Mock python-gitlab client for file creation."""
    mock_gl = Mock()
    mock_project = Mock()
    mock_file = Mock()

    # Setup mock file attributes (after creation)
    mock_file.file_path = "new_file.txt"
    mock_file.branch = "main"
    mock_file.last_commit_id = "commit456"
    mock_file.content_sha256 = "def456"

    # Make files.get raise GitlabGetError (file doesn't exist)
    import gitlab

    mock_project.files.get.side_effect = gitlab.exceptions.GitlabGetError("File not found")
    mock_project.files.create.return_value = mock_file
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.fixture
def mock_gitlab_client_update():
    """Mock python-gitlab client for file update."""
    mock_gl = Mock()
    mock_project = Mock()
    mock_file = Mock()

    # Setup mock file attributes (existing file)
    mock_file.file_path = "existing_file.txt"
    mock_file.branch = "main"
    mock_file.last_commit_id = "commit789"
    mock_file.content_sha256 = "ghi789"
    mock_file.content = "old content"

    # Make files.get succeed (file exists)
    mock_project.files.get.return_value = mock_file
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.create_or_update_file.client_factory")
async def test_create_file_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client_create
):
    """Test successful file creation (file doesn't exist)."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client_create

    # Execute
    result = await create_or_update_file(
        project_id="test-project",
        file_path="new_file.txt",
        content="Test content",
        branch="main",
        commit_message="Add new file",
        encoding="text",
        ctx=mock_context,
    )

    # Verify result
    assert result["file_path"] == "new_file.txt"
    assert result["branch"] == "main"
    assert result["action"] == "created"
    assert result["commit_id"] == "commit456"
    assert result["content_sha256"] == "def456"

    # Verify python-gitlab was called correctly
    mock_gitlab_client_create.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client_create.projects.get.return_value

    # Should try to get file first
    mock_project.files.get.assert_called_once_with(file_path="new_file.txt", ref="main")

    # Should create new file since get failed
    mock_project.files.create.assert_called_once_with(
        {
            "file_path": "new_file.txt",
            "branch": "main",
            "content": "Test content",
            "commit_message": "Add new file",
            "encoding": "text",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.create_or_update_file.client_factory")
async def test_update_file_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client_update
):
    """Test successful file update (file exists)."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client_update

    # Execute
    result = await create_or_update_file(
        project_id="test-project",
        file_path="existing_file.txt",
        content="Updated content",
        branch="main",
        commit_message="Update existing file",
        ctx=mock_context,
    )

    # Verify result
    assert result["file_path"] == "existing_file.txt"
    assert result["branch"] == "main"
    assert result["action"] == "updated"
    assert result["commit_id"] == "commit789"
    assert result["content_sha256"] == "ghi789"

    # Verify python-gitlab was called correctly
    mock_project = mock_gitlab_client_update.projects.get.return_value

    # Should try to get file first
    mock_project.files.get.assert_called_once_with(file_path="existing_file.txt", ref="main")

    # Should update existing file
    mock_file = mock_project.files.get.return_value
    assert mock_file.content == "Updated content"
    mock_file.save.assert_called_once_with(branch="main", commit_message="Update existing file")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.create_or_update_file.client_factory")
async def test_create_or_update_file_default_encoding(
    mock_factory, mock_settings, mock_context, mock_gitlab_client_create
):
    """Test file creation with default encoding."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client_create

    # Execute without specifying encoding
    await create_or_update_file(
        project_id="test-project",
        file_path="new_file.txt",
        content="Test content",
        branch="main",
        commit_message="Add new file",
        ctx=mock_context,
    )

    # Verify encoding defaults to 'text'
    mock_project = mock_gitlab_client_create.projects.get.return_value
    create_args = mock_project.files.create.call_args[0][0]
    assert create_args["encoding"] == "text"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.create_or_update_file.client_factory")
async def test_create_or_update_file_base64_encoding(
    mock_factory, mock_settings, mock_context, mock_gitlab_client_create
):
    """Test file creation with base64 encoding."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client_create

    # Execute with base64 encoding
    await create_or_update_file(
        project_id="test-project",
        file_path="image.png",
        content="iVBORw0KGgoAAAANSUhEUgAAAAUA",
        branch="main",
        commit_message="Add image",
        encoding="base64",
        ctx=mock_context,
    )

    # Verify encoding is 'base64'
    mock_project = mock_gitlab_client_create.projects.get.return_value
    create_args = mock_project.files.create.call_args[0][0]
    assert create_args["encoding"] == "base64"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.create_or_update_file.client_factory")
async def test_create_or_update_file_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_or_update_file(
            project_id="nonexistent",
            file_path="test.txt",
            content="Test",
            branch="main",
            commit_message="Test",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.create_or_update_file.client_factory")
async def test_create_or_update_file_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client_create
):
    """Test file creation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client_create

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await create_or_update_file(
        project_id="test-project",
        file_path="new_file.txt",
        content="Test",
        branch="main",
        commit_message="Add file",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
