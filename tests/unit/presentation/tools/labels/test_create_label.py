"""Tests for create_label tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.labels.create_label import create_label


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
    mock_label.id = 1
    mock_label.name = "bug"
    mock_label.color = "#FF0000"
    mock_label.description = "Bug tracking label"
    mock_label.priority = 1
    mock_label.open_issues_count = 5
    mock_label.closed_issues_count = 10
    mock_label.open_merge_requests_count = 2
    mock_label.subscribed = False

    # Chain mocks
    mock_project.labels.create.return_value = mock_label
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.create_label.client_factory")
async def test_create_label_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful label creation."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await create_label(
        project_id="test-project",
        name="bug",
        color="#FF0000",
        description="Bug tracking label",
        priority=1,
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 1
    assert result["name"] == "bug"
    assert result["color"] == "#FF0000"
    assert result["description"] == "Bug tracking label"
    assert result["priority"] == 1
    assert result["open_issues_count"] == 5
    assert result["closed_issues_count"] == 10

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.create.assert_called_once_with(
        {
            "name": "bug",
            "color": "#FF0000",
            "description": "Bug tracking label",
            "priority": 1,
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.create_label.client_factory")
async def test_create_label_minimal(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test label creation with minimal parameters."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute with only required parameters
    await create_label(
        project_id="test-project",
        name="feature",
        color="#00FF00",
        ctx=mock_context,
    )

    # Verify python-gitlab was called with minimal data
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.create.assert_called_once_with(
        {
            "name": "feature",
            "color": "#00FF00",
        }
    )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.create_label.client_factory")
async def test_create_label_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await create_label(
            project_id="nonexistent",
            name="bug",
            color="#FF0000",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.create_label.client_factory")
async def test_create_label_creation_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when label creation fails."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    # Make labels.create raise error
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.create.side_effect = gitlab.exceptions.GitlabCreateError(
        "Label already exists"
    )

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to create label"):
        await create_label(
            project_id="test-project",
            name="duplicate",
            color="#FF0000",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.create_label.client_factory")
async def test_create_label_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test label creation in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await create_label(
        project_id="test-project",
        name="bug",
        color="#FF0000",
        ctx=ctx,
    )

    # Verify result
    assert result["id"] == 1

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
