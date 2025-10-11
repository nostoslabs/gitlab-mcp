"""Tests for list_branches tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.branches.list_branches import list_branches


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

    # Setup mock branches
    mock_branch1 = Mock()
    mock_branch1.name = "main"
    mock_branch1.commit = {"id": "abc123", "short_id": "abc123"}
    mock_branch1.merged = False
    mock_branch1.protected = True
    mock_branch1.developers_can_push = False
    mock_branch1.developers_can_merge = False
    mock_branch1.can_push = True
    mock_branch1.default = True
    mock_branch1.web_url = "https://gitlab.example.com/project/-/tree/main"

    mock_branch2 = Mock()
    mock_branch2.name = "feature-branch"
    mock_branch2.commit = {"id": "def456", "short_id": "def456"}
    mock_branch2.merged = False
    mock_branch2.protected = False
    mock_branch2.developers_can_push = True
    mock_branch2.developers_can_merge = True
    mock_branch2.can_push = True
    mock_branch2.default = False
    mock_branch2.web_url = "https://gitlab.example.com/project/-/tree/feature-branch"

    # Chain mocks
    mock_project.branches.list.return_value = [mock_branch1, mock_branch2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.list_branches.client_factory")
async def test_list_branches_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful branch listing."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_branches(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify result
    assert len(result["branches"]) == 2
    assert result["branches"][0]["name"] == "main"
    assert result["branches"][0]["default"]
    assert result["branches"][0]["protected"]
    assert result["branches"][1]["name"] == "feature-branch"
    assert not result["branches"][1]["default"]
    assert not result["branches"][1]["protected"]

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.branches.list.assert_called_once_with(all=True)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.list_branches.client_factory")
async def test_list_branches_with_search(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test branch listing with search filter."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with search
    await list_branches(
        project_id="test-project",
        search="feature",
        ctx=mock_context,
    )

    # Verify search parameter was passed
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.branches.list.assert_called_once_with(all=True, search="feature")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.list_branches.client_factory")
async def test_list_branches_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test branch listing with no branches."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return empty list
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.branches.list.return_value = []

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_branches(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify empty result
    assert result["branches"] == []


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.list_branches.client_factory")
async def test_list_branches_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_branches(
            project_id="nonexistent",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.list_branches.client_factory")
async def test_list_branches_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test branch listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_branches(
        project_id="test-project",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
