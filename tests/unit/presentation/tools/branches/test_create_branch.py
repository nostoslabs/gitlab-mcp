"""Tests for create_branch tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.branches.create_branch import create_branch


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
    mock_branch = Mock()

    # Setup mock branch attributes
    mock_branch.name = "feature-branch"
    mock_branch.commit = {"id": "abc123", "web_url": "https://gitlab.example.com/commit/abc123"}
    mock_branch.merged = False
    mock_branch.protected = False
    mock_branch.developers_can_push = True
    mock_branch.developers_can_merge = True
    mock_branch.can_push = True
    mock_branch.default = False
    mock_branch.web_url = "https://gitlab.example.com/project/-/tree/feature-branch"

    # Chain mocks
    mock_project.branches.create.return_value = mock_branch
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.create_branch.client_factory")
async def test_create_branch_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful branch creation."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_branch(
        project_id="test-project",
        branch="feature-branch",
        ref="main",
        ctx=mock_context,
    )

    # Verify result
    assert result["name"] == "feature-branch"
    assert result["commit"]["id"] == "abc123"
    assert not result["merged"]
    assert not result["protected"]
    assert result["web_url"] == "https://gitlab.example.com/project/-/tree/feature-branch"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.branches.create.assert_called_once_with(
        {"branch": "feature-branch", "ref": "main"}
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.create_branch.client_factory")
async def test_create_branch_default_ref(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test branch creation with default ref."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute without specifying ref (should default to "main")
    await create_branch(
        project_id="test-project",
        branch="feature-branch",
        ctx=mock_context,
    )

    # Verify ref defaults to 'main'
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.branches.create.assert_called_once_with(
        {"branch": "feature-branch", "ref": "main"}
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.create_branch.client_factory")
async def test_create_branch_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_branch(
            project_id="nonexistent",
            branch="feature-branch",
            ref="main",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.create_branch.client_factory")
async def test_create_branch_creation_failed(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when branch creation fails."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Make branches.create raise GitlabCreateError
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.branches.create.side_effect = gitlab.exceptions.GitlabCreateError(
        "Branch already exists"
    )

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to create branch"):
        await create_branch(
            project_id="test-project",
            branch="existing-branch",
            ref="main",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.branches.create_branch.client_factory")
async def test_create_branch_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test branch creation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await create_branch(
        project_id="test-project",
        branch="feature-branch",
        ref="main",
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
