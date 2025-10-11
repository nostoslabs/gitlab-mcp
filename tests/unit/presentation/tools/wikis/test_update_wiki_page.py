"""Tests for update_wiki_page tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.wikis.update_wiki_page import update_wiki_page


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

    # Setup mock wiki page
    mock_wiki = Mock()
    mock_wiki.slug = "existing-page"
    mock_wiki.title = "Existing Page"
    mock_wiki.format = "markdown"
    mock_wiki.content = "# Updated Content\n\nThis has been updated."

    # Chain mocks
    mock_project.wikis.get.return_value = mock_wiki
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.update_wiki_page.client_factory")
async def test_update_wiki_page_content_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful wiki page content update."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await update_wiki_page(
        project_id="test-project",
        slug="existing-page",
        content="# Updated Content\n\nThis has been updated.",
        ctx=mock_context,
    )

    # Verify result
    assert result["slug"] == "existing-page"
    assert result["title"] == "Existing Page"
    assert result["content"] == "# Updated Content\n\nThis has been updated."

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.wikis.get.assert_called_once_with("existing-page")

    # Verify wiki was updated
    mock_wiki = mock_project.wikis.get.return_value
    assert mock_wiki.content == "# Updated Content\n\nThis has been updated."
    mock_wiki.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.update_wiki_page.client_factory")
async def test_update_wiki_page_title_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful wiki page title update."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await update_wiki_page(
        project_id="test-project",
        slug="existing-page",
        title="New Title",
        ctx=mock_context,
    )

    # Verify wiki was updated
    mock_wiki = mock_gitlab_client.projects.get.return_value.wikis.get.return_value
    assert mock_wiki.title == "New Title"
    mock_wiki.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.update_wiki_page.client_factory")
async def test_update_wiki_page_format_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful wiki page format update."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await update_wiki_page(
        project_id="test-project",
        slug="existing-page",
        format="asciidoc",
        ctx=mock_context,
    )

    # Verify wiki was updated
    mock_wiki = mock_gitlab_client.projects.get.return_value.wikis.get.return_value
    assert mock_wiki.format == "asciidoc"
    mock_wiki.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.update_wiki_page.client_factory")
async def test_update_wiki_page_all_fields(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test updating all wiki page fields at once."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await update_wiki_page(
        project_id="test-project",
        slug="existing-page",
        title="New Title",
        content="New content",
        format="rdoc",
        ctx=mock_context,
    )

    # Verify all fields were updated
    mock_wiki = mock_gitlab_client.projects.get.return_value.wikis.get.return_value
    assert mock_wiki.title == "New Title"
    assert mock_wiki.content == "New content"
    assert mock_wiki.format == "rdoc"
    mock_wiki.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.update_wiki_page.client_factory")
async def test_update_wiki_page_not_found(mock_factory, mock_settings, mock_context):
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
        await update_wiki_page(
            project_id="test-project",
            slug="nonexistent",
            content="New content",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.update_wiki_page.client_factory")
async def test_update_wiki_page_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await update_wiki_page(
            project_id="nonexistent",
            slug="page",
            content="Content",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.update_wiki_page.client_factory")
async def test_update_wiki_page_save_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when wiki page update fails."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Mock save failure
    mock_wiki = mock_gitlab_client.projects.get.return_value.wikis.get.return_value
    mock_wiki.save.side_effect = gitlab.exceptions.GitlabUpdateError("Update failed")
    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to update wiki page"):
        await update_wiki_page(
            project_id="test-project",
            slug="existing-page",
            content="New content",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.update_wiki_page.client_factory")
async def test_update_wiki_page_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test wiki page update in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await update_wiki_page(
        project_id="test-project",
        slug="existing-page",
        content="New content",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
