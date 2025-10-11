"""Tests for create_wiki_page tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.wikis.create_wiki_page import create_wiki_page


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

    # Setup mock wiki page creation
    mock_wiki = Mock()
    mock_wiki.slug = "new-page"
    mock_wiki.title = "New Page"
    mock_wiki.format = "markdown"
    mock_wiki.content = "# New Page\n\nThis is a new page."

    # Chain mocks
    mock_project.wikis.create.return_value = mock_wiki
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.create_wiki_page.client_factory")
async def test_create_wiki_page_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful wiki page creation."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_wiki_page(
        project_id="test-project",
        title="New Page",
        content="# New Page\n\nThis is a new page.",
        ctx=mock_context,
    )

    # Verify result
    assert result["slug"] == "new-page"
    assert result["title"] == "New Page"
    assert result["format"] == "markdown"
    assert result["content"] == "# New Page\n\nThis is a new page."

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.wikis.create.assert_called_once_with(
        {
            "title": "New Page",
            "content": "# New Page\n\nThis is a new page.",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.create_wiki_page.client_factory")
async def test_create_wiki_page_with_format(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test wiki page creation with custom format."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with format parameter
    await create_wiki_page(
        project_id="test-project",
        title="New Page",
        content="= New Page\n\nContent here",
        format="asciidoc",
        ctx=mock_context,
    )

    # Verify format parameter was passed
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.wikis.create.assert_called_once_with(
        {
            "title": "New Page",
            "content": "= New Page\n\nContent here",
            "format": "asciidoc",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.create_wiki_page.client_factory")
async def test_create_wiki_page_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_wiki_page(
            project_id="nonexistent",
            title="New Page",
            content="Content",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.create_wiki_page.client_factory")
async def test_create_wiki_page_creation_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when wiki page creation fails."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Mock creation failure
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.wikis.create.side_effect = gitlab.exceptions.GitlabCreateError("Creation failed")
    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to create wiki page"):
        await create_wiki_page(
            project_id="test-project",
            title="New Page",
            content="Content",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.create_wiki_page.client_factory")
async def test_create_wiki_page_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test wiki page creation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await create_wiki_page(
        project_id="test-project",
        title="New Page",
        content="Content",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
