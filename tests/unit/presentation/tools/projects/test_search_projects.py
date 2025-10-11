"""Tests for search_projects tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.projects.search_projects import search_projects


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

    # Create mock projects
    mock_project1 = Mock()
    mock_project1.id = 1
    mock_project1.name = "Django Project"
    mock_project1.path = "django-project"
    mock_project1.path_with_namespace = "group/django-project"
    mock_project1.description = "A Django web application"
    mock_project1.web_url = "https://gitlab.example.com/group/django-project"
    mock_project1.default_branch = "main"

    mock_project2 = Mock()
    mock_project2.id = 2
    mock_project2.name = "Django REST API"
    mock_project2.path = "django-api"
    mock_project2.path_with_namespace = "group/django-api"
    mock_project2.description = "REST API built with Django"
    mock_project2.web_url = "https://gitlab.example.com/group/django-api"
    mock_project2.default_branch = "develop"

    # Chain mocks - search returns list of projects
    mock_gl.projects.list.return_value = [mock_project1, mock_project2]

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.search_projects.client_factory")
async def test_search_projects_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful project search."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await search_projects(search="django", ctx=mock_context)

    # Verify result structure
    assert "projects" in result
    assert "total" in result
    assert "page" in result
    assert "per_page" in result

    # Verify projects
    assert len(result["projects"]) == 2
    assert result["projects"][0]["id"] == 1
    assert result["projects"][0]["name"] == "Django Project"
    assert result["projects"][1]["id"] == 2
    assert result["projects"][1]["name"] == "Django REST API"

    # Verify pagination
    assert result["total"] == 2
    assert result["page"] == 1
    assert result["per_page"] == 20

    # Verify python-gitlab was called correctly with search parameter
    mock_gitlab_client.projects.list.assert_called_once_with(page=1, per_page=20, search="django")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.search_projects.client_factory")
async def test_search_projects_empty_query(mock_factory, mock_settings, mock_context):
    """Test search without query returns error."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Execute - should raise ValueError for empty search
    with pytest.raises(ValueError, match="Search query is required"):
        await search_projects(search="", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.search_projects.client_factory")
async def test_search_projects_with_pagination(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test project search with pagination."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await search_projects(
        search="django",
        page=2,
        per_page=10,
        ctx=mock_context,
    )

    # Verify python-gitlab was called with pagination
    mock_gitlab_client.projects.list.assert_called_once_with(page=2, per_page=10, search="django")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.search_projects.client_factory")
async def test_search_projects_no_results(mock_factory, mock_settings, mock_context):
    """Test search when no projects match."""
    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.list.return_value = []
    mock_factory.get_client.return_value = mock_gl

    # Execute
    result = await search_projects(search="nonexistent", ctx=mock_context)

    # Verify
    assert result["total"] == 0
    assert len(result["projects"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.search_projects.client_factory")
async def test_search_projects_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test project search in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await search_projects(search="django", ctx=ctx)

    # Verify
    assert len(result["projects"]) == 2

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
