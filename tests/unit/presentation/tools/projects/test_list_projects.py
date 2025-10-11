"""Tests for list_projects tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.projects.list_projects import list_projects


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
    mock_project1.name = "First Project"
    mock_project1.path = "first-project"
    mock_project1.path_with_namespace = "group/first-project"
    mock_project1.description = "First project description"
    mock_project1.web_url = "https://gitlab.example.com/group/first-project"
    mock_project1.default_branch = "main"

    mock_project2 = Mock()
    mock_project2.id = 2
    mock_project2.name = "Second Project"
    mock_project2.path = "second-project"
    mock_project2.path_with_namespace = "group/second-project"
    mock_project2.description = "Second project description"
    mock_project2.web_url = "https://gitlab.example.com/group/second-project"
    mock_project2.default_branch = "develop"

    # Chain mocks
    mock_gl.projects.list.return_value = [mock_project1, mock_project2]

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.list_projects.client_factory")
async def test_list_projects_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful project listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_projects(ctx=mock_context)

    # Verify result structure
    assert "projects" in result
    assert "total" in result
    assert "page" in result
    assert "per_page" in result

    # Verify projects
    assert len(result["projects"]) == 2
    assert result["projects"][0]["id"] == 1
    assert result["projects"][0]["name"] == "First Project"
    assert result["projects"][0]["path"] == "first-project"
    assert result["projects"][0]["path_with_namespace"] == "group/first-project"
    assert result["projects"][1]["id"] == 2
    assert result["projects"][1]["name"] == "Second Project"

    # Verify pagination
    assert result["total"] == 2
    assert result["page"] == 1
    assert result["per_page"] == 20

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.list.assert_called_once_with(page=1, per_page=20)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.list_projects.client_factory")
async def test_list_projects_with_filters(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test project listing with filters."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await list_projects(
        search="test",
        owned=True,
        starred=True,
        visibility="public",
        page=2,
        per_page=10,
        ctx=mock_context,
    )

    # Verify python-gitlab was called with filters
    mock_gitlab_client.projects.list.assert_called_once_with(
        page=2,
        per_page=10,
        search="test",
        owned=True,
        starred=True,
        visibility="public",
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.list_projects.client_factory")
async def test_list_projects_empty_result(mock_factory, mock_settings, mock_context):
    """Test listing when no projects exist."""
    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.list.return_value = []
    mock_factory.get_client.return_value = mock_gl

    # Execute
    result = await list_projects(ctx=mock_context)

    # Verify
    assert result["total"] == 0
    assert len(result["projects"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.projects.list_projects.client_factory")
async def test_list_projects_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test project listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await list_projects(ctx=ctx)

    # Verify
    assert len(result["projects"]) == 2

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
