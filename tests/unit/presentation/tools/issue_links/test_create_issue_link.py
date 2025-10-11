"""Tests for create_issue_link tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.issue_links.create_issue_link import create_issue_link


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
    mock_target_project = Mock()
    mock_issue = Mock()
    mock_link = Mock()

    # Setup mock objects
    mock_project.id = 100
    mock_target_project.id = 200
    mock_issue.iid = 42
    mock_issue.title = "Source issue title"

    # Setup mock link attributes
    mock_link.id = 999
    mock_link.link_type = "relates_to"
    mock_link.created_at = "2025-01-15T12:00:00Z"

    # Chain mocks
    mock_issue.links.create.return_value = mock_link
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.side_effect = (
        lambda pid: mock_project if pid == "source-project" else mock_target_project
    )

    # Store references for test access
    mock_gl._source_project = mock_project
    mock_gl._target_project = mock_target_project
    mock_gl._issue = mock_issue
    mock_gl._link = mock_link

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.create_issue_link.client_factory")
async def test_create_issue_link_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful issue link creation."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_issue_link(
        project_id="source-project",
        issue_iid=42,
        target_project_id="target-project",
        target_issue_iid=100,
        link_type="relates_to",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 999
    assert result["source_issue"]["iid"] == 42
    assert result["source_issue"]["project_id"] == 100
    assert result["target_issue"]["iid"] == 100
    assert result["target_issue"]["project_id"] == 200
    assert result["link_type"] == "relates_to"

    # Verify python-gitlab was called correctly
    mock_issue = mock_gitlab_client._issue
    call_args = mock_issue.links.create.call_args[0][0]
    assert call_args["target_project_id"] == 200
    assert call_args["target_issue_iid"] == 100


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.create_issue_link.client_factory")
async def test_create_issue_link_with_blocks_type(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test issue link creation with 'blocks' link type."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Update mock to return blocks link type
    mock_link = mock_gitlab_client._link
    mock_link.link_type = "blocks"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_issue_link(
        project_id="source-project",
        issue_iid=42,
        target_project_id="target-project",
        target_issue_iid=100,
        link_type="blocks",
        ctx=mock_context,
    )

    # Verify link type was included in the request
    mock_issue = mock_gitlab_client._issue
    call_args = mock_issue.links.create.call_args[0][0]
    assert call_args["link_type"] == "blocks"
    assert result["link_type"] == "blocks"


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.create_issue_link.client_factory")
async def test_create_issue_link_source_issue_not_found(mock_factory, mock_settings, mock_context):
    """Test error when source issue doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.issues.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Source issue .* not found"):
        await create_issue_link(
            project_id="source-project",
            issue_iid=999,
            target_project_id="target-project",
            target_issue_iid=100,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.create_issue_link.client_factory")
async def test_create_issue_link_target_project_not_found(
    mock_factory, mock_settings, mock_context
):
    """Test error when target project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_issue = Mock()

    # Source project and issue exist, but target project doesn't
    mock_project.issues.get.return_value = mock_issue

    def get_project_side_effect(pid):
        if pid == "source-project":
            return mock_project
        raise gitlab.exceptions.GitlabGetError("Not found")

    mock_gl.projects.get.side_effect = get_project_side_effect
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Target project .* not found"):
        await create_issue_link(
            project_id="source-project",
            issue_iid=42,
            target_project_id="missing-project",
            target_issue_iid=100,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.create_issue_link.client_factory")
async def test_create_issue_link_creation_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when link creation fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make create raise error
    mock_issue = mock_gitlab_client._issue
    mock_issue.links.create.side_effect = Exception("Permission denied")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to create issue link"):
        await create_issue_link(
            project_id="source-project",
            issue_iid=42,
            target_project_id="target-project",
            target_issue_iid=100,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.create_issue_link.client_factory")
async def test_create_issue_link_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test creating issue link in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await create_issue_link(
        project_id="source-project",
        issue_iid=42,
        target_project_id="target-project",
        target_issue_iid=100,
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 999

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
