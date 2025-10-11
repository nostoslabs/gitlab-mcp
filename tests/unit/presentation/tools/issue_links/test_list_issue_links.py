"""Tests for list_issue_links tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.issue_links.list_issue_links import list_issue_links


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
    mock_issue = Mock()
    mock_link1 = Mock()
    mock_link2 = Mock()

    # Setup mock link attributes
    mock_link1.id = 100
    mock_link1.iid = 10
    mock_link1.title = "Related issue 1"
    mock_link1.state = "opened"
    mock_link1.project_id = 200
    mock_link1.web_url = "https://gitlab.com/project/issue/10"
    mock_link1.link_type = "relates_to"

    mock_link2.id = 101
    mock_link2.iid = 11
    mock_link2.title = "Blocking issue"
    mock_link2.state = "opened"
    mock_link2.project_id = 200
    mock_link2.web_url = "https://gitlab.com/project/issue/11"
    mock_link2.link_type = "blocks"

    # Chain mocks
    mock_issue.links.list.return_value = [mock_link1, mock_link2]
    mock_project.issues.get.return_value = mock_issue
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.list_issue_links.client_factory")
async def test_list_issue_links_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful issue links listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_issue_links(
        project_id="test-project",
        issue_iid=42,
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 2
    assert len(result["links"]) == 2
    assert result["links"][0]["id"] == 100
    assert result["links"][0]["title"] == "Related issue 1"
    assert result["links"][0]["link_type"] == "relates_to"
    assert result["links"][1]["link_type"] == "blocks"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.get.assert_called_once_with(42)
    mock_issue = mock_project.issues.get.return_value
    mock_issue.links.list.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.list_issue_links.client_factory")
async def test_list_issue_links_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test issue links listing with no results."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make mock return empty list
    mock_issue = mock_gitlab_client.projects.get.return_value.issues.get.return_value
    mock_issue.links.list.return_value = []

    # Execute
    result = await list_issue_links(
        project_id="test-project",
        issue_iid=42,
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 0
    assert len(result["links"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.list_issue_links.client_factory")
async def test_list_issue_links_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_issue_links(
            project_id="missing-project",
            issue_iid=42,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.list_issue_links.client_factory")
async def test_list_issue_links_issue_not_found(mock_factory, mock_settings, mock_context):
    """Test error when issue doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.issues.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Issue .* not found"):
        await list_issue_links(
            project_id="test-project",
            issue_iid=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issue_links.list_issue_links.client_factory")
async def test_list_issue_links_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test listing issue links in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await list_issue_links(
        project_id="test-project",
        issue_iid=42,
        ctx=ctx,
    )

    # Verify result
    assert result["total_results"] == 2

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
