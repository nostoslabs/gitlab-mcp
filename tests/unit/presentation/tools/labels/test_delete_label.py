"""Tests for delete_label tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.labels.delete_label import delete_label


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

    # Chain mocks
    mock_project.labels.get.return_value = mock_label
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.delete_label.client_factory")
async def test_delete_label_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful label deletion."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await delete_label(
        project_id="test-project",
        label_name="old-label",
        ctx=mock_context,
    )

    # Verify result
    assert result["success"] is True
    assert result["deleted_label"] == "old-label"
    assert "deleted successfully" in result["message"]

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.get.assert_called_once_with("old-label")

    # Verify delete was called
    mock_label = mock_project.labels.get.return_value
    mock_label.delete.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.delete_label.client_factory")
async def test_delete_label_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await delete_label(
            project_id="nonexistent",
            label_name="bug",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.delete_label.client_factory")
async def test_delete_label_not_found(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when label doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    # Make labels.get raise error
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Label .* not found"):
        await delete_label(
            project_id="test-project",
            label_name="nonexistent",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.delete_label.client_factory")
async def test_delete_label_delete_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when deletion fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make delete raise error
    mock_label = mock_gitlab_client.projects.get.return_value.labels.get.return_value
    mock_label.delete.side_effect = Exception("Permission denied")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to delete label"):
        await delete_label(
            project_id="test-project",
            label_name="bug",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.delete_label.client_factory")
async def test_delete_label_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test deleting label in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await delete_label(
        project_id="test-project",
        label_name="old-label",
        ctx=ctx,
    )

    # Verify result
    assert result["success"] is True

    # Verify client factory was called with default user context
    user_ctx = mock_factory.get_client.call_args[0][0]
    assert user_ctx.user_id == "default"
    assert user_ctx.gitlab_token == "single_tenant_token"
    assert user_ctx.gitlab_url == "https://gitlab.com"
