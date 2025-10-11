"""Tests for get_label tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.labels.get_label import get_label


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
    mock_label = Mock()

    # Setup mock label attributes
    mock_label.id = 123
    mock_label.name = "bug"
    mock_label.color = "#FF0000"
    mock_label.description = "Bug reports"
    mock_label.open_issues_count = 5
    mock_label.closed_issues_count = 10
    mock_label.open_merge_requests_count = 2

    # Chain mocks
    mock_project.labels.get.return_value = mock_label
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.get_label.client_factory")
async def test_get_label_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful label retrieval."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await get_label(
        project_id="test-project",
        label_id=123,
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 123
    assert result["name"] == "bug"
    assert result["color"] == "#FF0000"
    assert result["description"] == "Bug reports"
    assert result["open_issues_count"] == 5
    assert result["closed_issues_count"] == 10

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.get.assert_called_once_with(123)


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.get_label.client_factory")
async def test_get_label_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await get_label(
            project_id="missing-project",
            label_id=123,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.get_label.client_factory")
async def test_get_label_not_found(mock_factory, mock_settings, mock_context):
    """Test error when label doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_project = Mock()
    mock_project.labels.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_gl.projects.get.return_value = mock_project
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Label .* not found"):
        await get_label(
            project_id="test-project",
            label_id=999,
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.get_label.client_factory")
async def test_get_label_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test getting label in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await get_label(
        project_id="test-project",
        label_id=123,
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 123

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
