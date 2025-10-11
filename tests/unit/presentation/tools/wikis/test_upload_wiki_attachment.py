"""Tests for upload_wiki_attachment tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.wikis.upload_wiki_attachment import upload_wiki_attachment


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

    # Setup mock upload response
    upload_result = {
        "url": "/uploads/abc123def456/test-file.png",
        "alt": "test-file",
        "markdown": "![test-file](/uploads/abc123def456/test-file.png)",
    }
    mock_project.upload.return_value = upload_result
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.upload_wiki_attachment.client_factory")
async def test_upload_wiki_attachment_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful wiki attachment upload."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await upload_wiki_attachment(
        project_id="test-project",
        filename="test-file.png",
        filepath="/path/to/test-file.png",
        ctx=mock_context,
    )

    # Verify result
    assert result["url"] == "/uploads/abc123def456/test-file.png"
    assert result["alt"] == "test-file"
    assert result["markdown"] == "![test-file](/uploads/abc123def456/test-file.png)"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.upload.assert_called_once_with("test-file.png", filepath="/path/to/test-file.png")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.upload_wiki_attachment.client_factory")
async def test_upload_wiki_attachment_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await upload_wiki_attachment(
            project_id="nonexistent",
            filename="test.png",
            filepath="/path/to/test.png",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.upload_wiki_attachment.client_factory")
async def test_upload_wiki_attachment_upload_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when file upload fails."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Mock upload failure
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.upload.side_effect = gitlab.exceptions.GitlabUploadError("Upload failed")
    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to upload attachment"):
        await upload_wiki_attachment(
            project_id="test-project",
            filename="test.png",
            filepath="/path/to/test.png",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.upload_wiki_attachment.client_factory")
async def test_upload_wiki_attachment_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test wiki attachment upload in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await upload_wiki_attachment(
        project_id="test-project",
        filename="test.png",
        filepath="/path/to/test.png",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
