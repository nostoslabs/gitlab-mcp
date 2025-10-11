"""Tests for list_wiki_pages tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.wikis.list_wiki_pages import list_wiki_pages


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

    # Setup mock wiki pages
    mock_wiki1 = Mock()
    mock_wiki1.slug = "home"
    mock_wiki1.title = "Home"
    mock_wiki1.format = "markdown"
    mock_wiki1.content = "# Welcome\n\nThis is the home page."

    mock_wiki2 = Mock()
    mock_wiki2.slug = "getting-started"
    mock_wiki2.title = "Getting Started"
    mock_wiki2.format = "markdown"
    mock_wiki2.content = "# Getting Started\n\nFollow these steps..."

    # Chain mocks
    mock_project.wikis.list.return_value = [mock_wiki1, mock_wiki2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_pages.client_factory")
async def test_list_wiki_pages_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful wiki pages listing."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_wiki_pages(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify result
    assert len(result["wiki_pages"]) == 2
    assert result["wiki_pages"][0]["slug"] == "home"
    assert result["wiki_pages"][0]["title"] == "Home"
    assert result["wiki_pages"][0]["format"] == "markdown"
    assert result["wiki_pages"][1]["slug"] == "getting-started"
    assert result["wiki_pages"][1]["title"] == "Getting Started"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.wikis.list.assert_called_once_with(all=True)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_pages.client_factory")
async def test_list_wiki_pages_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test wiki pages listing with no pages."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return empty list
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.wikis.list.return_value = []

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_wiki_pages(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify empty result
    assert result["wiki_pages"] == []


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_pages.client_factory")
async def test_list_wiki_pages_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_wiki_pages(
            project_id="nonexistent",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.wikis.list_wiki_pages.client_factory")
async def test_list_wiki_pages_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test wiki pages listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_wiki_pages(
        project_id="test-project",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
