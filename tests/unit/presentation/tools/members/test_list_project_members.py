"""Tests for list_project_members tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.members.list_project_members import list_project_members


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
    mock_member1 = Mock()
    mock_member2 = Mock()

    # Setup mock member attributes
    # Member 1: Maintainer
    mock_member1.id = 1
    mock_member1.username = "alice"
    mock_member1.name = "Alice Smith"
    mock_member1.email = "alice@example.com"
    mock_member1.state = "active"
    mock_member1.avatar_url = "https://gitlab.com/uploads/user/avatar/1.png"
    mock_member1.web_url = "https://gitlab.com/alice"
    mock_member1.access_level = 40  # Maintainer
    mock_member1.expires_at = None

    # Member 2: Developer
    mock_member2.id = 2
    mock_member2.username = "bob"
    mock_member2.name = "Bob Johnson"
    mock_member2.email = "bob@example.com"
    mock_member2.state = "active"
    mock_member2.avatar_url = "https://gitlab.com/uploads/user/avatar/2.png"
    mock_member2.web_url = "https://gitlab.com/bob"
    mock_member2.access_level = 30  # Developer
    mock_member2.expires_at = "2025-12-31"

    # Chain mocks
    mock_project.members.list.return_value = [mock_member1, mock_member2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.members.list_project_members.client_factory")
async def test_list_project_members_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful project members listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_project_members(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 2
    assert len(result["members"]) == 2
    assert result["members"][0]["username"] == "alice"
    assert result["members"][0]["access_level"] == 40  # Maintainer
    assert result["members"][1]["username"] == "bob"
    assert result["members"][1]["access_level"] == 30  # Developer

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.members.list.assert_called_once_with(page=1, per_page=20)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.members.list_project_members.client_factory")
async def test_list_project_members_with_pagination(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test project members listing with pagination."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    _result = await list_project_members(
        project_id="test-project",
        page=2,
        per_page=50,
        ctx=mock_context,
    )

    # Verify pagination parameters were passed
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.members.list.assert_called_once_with(page=2, per_page=50)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.members.list_project_members.client_factory")
async def test_list_project_members_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test project members listing with no results."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make mock return empty list
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.members.list.return_value = []

    # Execute
    result = await list_project_members(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 0
    assert len(result["members"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.members.list_project_members.client_factory")
async def test_list_project_members_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_project_members(
            project_id="missing-project",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.members.list_project_members.client_factory")
async def test_list_project_members_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test listing project members in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await list_project_members(
        project_id="test-project",
        ctx=ctx,
    )

    # Verify result
    assert result["total_results"] == 2

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
