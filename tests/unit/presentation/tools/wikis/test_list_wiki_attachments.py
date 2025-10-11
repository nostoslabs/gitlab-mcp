"""Tests for list_wiki_attachments tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.wikis.list_wiki_attachments import list_wiki_attachments


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

    # Setup mock wiki page with attachments in content
    mock_wiki = Mock()
    mock_wiki.slug = "page-with-attachments"
    mock_wiki.title = "Page with Attachments"
    mock_wiki.format = "markdown"
    mock_wiki.content = """# Page with Attachments

Here is an image:
![Screenshot](/uploads/abc123/screenshot.png)

And a document:
[Document](/uploads/def456/document.pdf)

Some more text.
"""

    # Chain mocks
    mock_project.wikis.get.return_value = mock_wiki
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_attachments.client_factory")
async def test_list_wiki_attachments_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful wiki attachments listing."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_wiki_attachments(
        project_id="test-project",
        slug="page-with-attachments",
        ctx=mock_context,
    )

    # Verify result
    assert len(result["attachments"]) == 2
    assert result["attachments"][0]["url"] == "/uploads/abc123/screenshot.png"
    assert result["attachments"][0]["filename"] == "screenshot.png"
    assert result["attachments"][0]["alt_text"] == "Screenshot"
    assert result["attachments"][1]["url"] == "/uploads/def456/document.pdf"
    assert result["attachments"][1]["filename"] == "document.pdf"
    assert result["attachments"][1]["link_text"] == "Document"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.wikis.get.assert_called_once_with("page-with-attachments")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_attachments.client_factory")
async def test_list_wiki_attachments_no_attachments(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test wiki attachments listing with no attachments."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return wiki page with no attachments
    mock_wiki = mock_gitlab_client.projects.get.return_value.wikis.get.return_value
    mock_wiki.content = "# Simple Page\n\nJust text, no attachments."

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_wiki_attachments(
        project_id="test-project",
        slug="simple-page",
        ctx=mock_context,
    )

    # Verify empty result
    assert result["attachments"] == []


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_attachments.client_factory")
async def test_list_wiki_attachments_wiki_not_found(mock_factory, mock_settings, mock_context):
    """Test error when wiki page doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.wikis.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Wiki page .* not found"):
        await list_wiki_attachments(
            project_id="test-project",
            slug="nonexistent",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_attachments.client_factory")
async def test_list_wiki_attachments_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_wiki_attachments(
            project_id="nonexistent",
            slug="page",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_attachments.client_factory")
async def test_list_wiki_attachments_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test wiki attachments listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_wiki_attachments(
        project_id="test-project",
        slug="page-with-attachments",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
