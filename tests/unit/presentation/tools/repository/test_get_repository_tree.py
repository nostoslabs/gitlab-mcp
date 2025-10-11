"""Tests for get_repository_tree tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.repository.get_repository_tree import get_repository_tree


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

    # Create mock tree objects with attributes
    mock_obj1 = Mock()
    mock_obj1.id = "abc123"
    mock_obj1.name = "README.md"
    mock_obj1.type = "blob"
    mock_obj1.path = "README.md"
    mock_obj1.mode = "100644"

    mock_obj2 = Mock()
    mock_obj2.id = "def456"
    mock_obj2.name = "src"
    mock_obj2.type = "tree"
    mock_obj2.path = "src"
    mock_obj2.mode = "040000"

    # Setup repository.tree to return list of objects
    mock_project.repository_tree.return_value = [mock_obj1, mock_obj2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_repository_tree.client_factory")
async def test_get_repository_tree_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful repository tree retrieval."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_repository_tree(
        project_id="test-project", path="", ref="main", ctx=mock_context
    )

    # Verify result
    assert "tree" in result
    assert len(result["tree"]) == 2
    assert result["tree"][0]["name"] == "README.md"
    assert result["tree"][0]["type"] == "blob"
    assert result["tree"][0]["path"] == "README.md"
    assert result["tree"][1]["name"] == "src"
    assert result["tree"][1]["type"] == "tree"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.repository_tree.assert_called_once_with(path="", ref="main", recursive=False)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_repository_tree.client_factory")
async def test_get_repository_tree_with_path(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test repository tree retrieval with specific path."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await get_repository_tree(project_id="test-project", path="src", ref="main", ctx=mock_context)

    # Verify path parameter was used
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.repository_tree.assert_called_once_with(path="src", ref="main", recursive=False)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_repository_tree.client_factory")
async def test_get_repository_tree_recursive(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test repository tree retrieval with recursive option."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await get_repository_tree(
        project_id="test-project", path="", ref="main", recursive=True, ctx=mock_context
    )

    # Verify recursive parameter was used
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.repository_tree.assert_called_once_with(path="", ref="main", recursive=True)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_repository_tree.client_factory")
async def test_get_repository_tree_default_ref(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test repository tree retrieval with default ref."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute without specifying ref
    await get_repository_tree(project_id="test-project", ctx=mock_context)

    # Verify ref defaults to 'main'
    mock_project = mock_gitlab_client.projects.get.return_value
    # Check the arguments used in the call
    call_kwargs = mock_project.repository_tree.call_args[1]
    assert call_kwargs["ref"] == "main"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_repository_tree.client_factory")
async def test_get_repository_tree_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await get_repository_tree(project_id="nonexistent", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.repository.get_repository_tree.client_factory")
async def test_get_repository_tree_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test repository tree retrieval in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await get_repository_tree(project_id="test-project", ctx=ctx)

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
