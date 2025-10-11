"""Tests for list_milestone_issues tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.milestones.list_milestone_issues import list_milestone_issues


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

    # Setup mock milestone
    mock_milestone = Mock()
    mock_milestone.id = 1

    # Setup mock issues
    mock_issue1 = Mock()
    mock_issue1.id = 101
    mock_issue1.iid = 1
    mock_issue1.title = "Bug in feature X"
    mock_issue1.state = "opened"
    mock_issue1.web_url = "https://gitlab.example.com/project/-/issues/1"

    mock_issue2 = Mock()
    mock_issue2.id = 102
    mock_issue2.iid = 2
    mock_issue2.title = "Implement feature Y"
    mock_issue2.state = "closed"
    mock_issue2.web_url = "https://gitlab.example.com/project/-/issues/2"

    # Chain mocks
    mock_milestone.issues.return_value = [mock_issue1, mock_issue2]
    mock_project.milestones.get.return_value = mock_milestone
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_issues.client_factory")
async def test_list_milestone_issues_success(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test successful listing of milestone issues."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_milestone_issues(
        project_id="test-project",
        milestone_id=1,
        ctx=mock_context,
    )

    # Verify result
    assert len(result["issues"]) == 2
    assert result["issues"][0]["id"] == 101
    assert result["issues"][0]["title"] == "Bug in feature X"
    assert result["issues"][1]["id"] == 102
    assert result["issues"][1]["title"] == "Implement feature Y"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.milestones.get.assert_called_once_with(1)
    mock_milestone = mock_project.milestones.get.return_value
    mock_milestone.issues.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_issues.client_factory")
async def test_list_milestone_issues_empty(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test milestone with no issues."""
    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    # Return empty list
    mock_milestone = mock_gitlab_client.projects.get.return_value.milestones.get.return_value
    mock_milestone.issues.return_value = []

    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_milestone_issues(
        project_id="test-project",
        milestone_id=1,
        ctx=mock_context,
    )

    # Verify empty result
    assert result["issues"] == []


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_issues.client_factory")
async def test_list_milestone_issues_milestone_not_found(mock_factory, mock_settings, mock_context):
    """Test error when milestone doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.milestones.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Milestone .* not found"):
        await list_milestone_issues(
            project_id="test-project",
            milestone_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_issues.client_factory")
async def test_list_milestone_issues_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup multi-tenant mode
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_milestone_issues(
            project_id="nonexistent",
            milestone_id=1,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.milestones.list_milestone_issues.client_factory")
async def test_list_milestone_issues_single_tenant_mode(
    mock_factory, mock_settings, mock_gitlab_client
):
    """Test listing issues in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    await list_milestone_issues(
        project_id="test-project",
        milestone_id=1,
        ctx=ctx,
    )

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
