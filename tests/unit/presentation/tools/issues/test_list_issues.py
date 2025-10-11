"""Tests for list_issues tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.issues.list_issues import list_issues


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

    # Create mock issues
    mock_issue1 = Mock()
    mock_issue1.id = 1
    mock_issue1.iid = 100
    mock_issue1.title = "First Issue"
    mock_issue1.state = "opened"
    mock_issue1.labels = ["bug"]
    mock_issue1.web_url = "https://gitlab.example.com/project/-/issues/100"

    mock_issue2 = Mock()
    mock_issue2.id = 2
    mock_issue2.iid = 101
    mock_issue2.title = "Second Issue"
    mock_issue2.state = "closed"
    mock_issue2.labels = ["feature"]
    mock_issue2.web_url = "https://gitlab.example.com/project/-/issues/101"

    # Chain mocks
    mock_project.issues.list.return_value = [mock_issue1, mock_issue2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.list_issues.client_factory")
async def test_list_issues_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful issue listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_issues(project_id="test-project", ctx=mock_context)

    # Verify result structure
    assert "issues" in result
    assert "total" in result
    assert "page" in result
    assert "per_page" in result

    # Verify issues
    assert len(result["issues"]) == 2
    assert result["issues"][0]["iid"] == 100
    assert result["issues"][0]["title"] == "First Issue"
    assert result["issues"][0]["state"] == "opened"
    assert result["issues"][1]["iid"] == 101
    assert result["issues"][1]["title"] == "Second Issue"

    # Verify pagination
    assert result["total"] == 2
    assert result["page"] == 1
    assert result["per_page"] == 20

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.list.assert_called_once_with(page=1, per_page=20)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.list_issues.client_factory")
async def test_list_issues_with_filters(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test issue listing with filters."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await list_issues(
        project_id="test-project",
        state="opened",
        labels=["bug", "critical"],
        search="database",
        page=2,
        per_page=10,
        ctx=mock_context,
    )

    # Verify python-gitlab was called with filters
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.issues.list.assert_called_once_with(
        page=2, per_page=10, state="opened", labels="bug,critical", search="database"
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.list_issues.client_factory")
async def test_list_issues_empty_result(mock_factory, mock_settings, mock_context):
    """Test listing when no issues exist."""
    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.issues.list.return_value = []
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    # Execute
    result = await list_issues(project_id="test-project", ctx=mock_context)

    # Verify
    assert result["total"] == 0
    assert len(result["issues"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.list_issues.client_factory")
async def test_list_issues_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_issues(project_id="nonexistent", ctx=mock_context)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.issues.list_issues.client_factory")
async def test_list_issues_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test issue listing in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await list_issues(project_id="test-project", ctx=ctx)

    # Verify
    assert len(result["issues"]) == 2

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
