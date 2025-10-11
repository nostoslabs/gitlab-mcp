"""Tests for delete_wiki_page tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.wikis.delete_wiki_page import delete_wiki_page


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
    mock_wiki.slug = "page-to-delete"

    # Chain mocks
    mock_project.wikis.get.return_value = mock_wiki
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.delete_wiki_page.client_factory")
async def test_delete_wiki_page_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful wiki page deletion."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await delete_wiki_page(
        project_id="test-project",
        slug="page-to-delete",
        ctx=mock_context,
    )

    # Verify result
    assert result["success"] is True
    assert result["slug"] == "page-to-delete"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.wikis.get.assert_called_once_with("page-to-delete")

    # Verify delete was called
    mock_wiki = mock_project.wikis.get.return_value
    mock_wiki.delete.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.delete_wiki_page.client_factory")
async def test_delete_wiki_page_not_found(mock_factory, mock_settings, mock_context):
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
        await delete_wiki_page(
            project_id="test-project",
            slug="nonexistent",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.delete_wiki_page.client_factory")
async def test_delete_wiki_page_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await delete_wiki_page(
            project_id="nonexistent",
            slug="page",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.delete_wiki_page.client_factory")
async def test_delete_wiki_page_delete_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when wiki page deletion fails."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Mock delete failure
    mock_wiki = mock_gitlab_client.projects.get.return_value.wikis.get.return_value
    mock_wiki.delete.side_effect = gitlab.exceptions.GitlabDeleteError("Delete failed")
    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to delete wiki page"):
        await delete_wiki_page(
            project_id="test-project",
            slug="page-to-delete",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.delete_wiki_page.client_factory")
async def test_delete_wiki_page_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test wiki page deletion in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await delete_wiki_page(
        project_id="test-project",
        slug="page-to-delete",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
