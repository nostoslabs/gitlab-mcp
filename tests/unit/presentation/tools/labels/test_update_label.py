"""Tests for update_label tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.labels.update_label import update_label


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
    mock_label.color = "#00FF00"
    mock_label.description = "Updated description"
    mock_label.priority = 2
    mock_label.open_issues_count = 3
    mock_label.closed_issues_count = 7
    mock_label.open_merge_requests_count = 1
    mock_label.subscribed = False

    # Chain mocks
    mock_project.labels.get.return_value = mock_label
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.update_label.client_factory")
async def test_update_label_color(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test updating label color."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await update_label(
        project_id="test-project",
        label_name="bug",
        color="#00FF00",
        ctx=mock_context,
    )

    # Verify result
    assert result["id"] == 1
    assert result["color"] == "#00FF00"

    # Verify save was called
    mock_label = mock_gitlab_client.projects.get.return_value.labels.get.return_value
    mock_label.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.update_label.client_factory")
async def test_update_label_rename(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test renaming a label."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await update_label(
        project_id="test-project",
        label_name="bug",
        new_name="defect",
        ctx=mock_context,
    )

    # Verify new_name was set
    mock_label = mock_gitlab_client.projects.get.return_value.labels.get.return_value
    assert mock_label.new_name == "defect"
    mock_label.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.update_label.client_factory")
async def test_update_label_multiple_fields(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test updating multiple label fields."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    await update_label(
        project_id="test-project",
        label_name="bug",
        color="#0000FF",
        description="Critical bugs",
        priority=3,
        ctx=mock_context,
    )

    # Verify all fields were set
    mock_label = mock_gitlab_client.projects.get.return_value.labels.get.return_value
    assert mock_label.color == "#0000FF"
    assert mock_label.description == "Critical bugs"
    assert mock_label.priority == 3
    mock_label.save.assert_called_once()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.update_label.client_factory")
async def test_update_label_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await update_label(
            project_id="nonexistent",
            label_name="bug",
            color="#FF0000",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.update_label.client_factory")
async def test_update_label_not_found(
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
        await update_label(
            project_id="test-project",
            label_name="nonexistent",
            color="#FF0000",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.update_label.client_factory")
async def test_update_label_save_error(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test error when save fails."""
    # Setup
    mock_settings.multi_tenant_mode = True

    # Make save raise error
    mock_label = mock_gitlab_client.projects.get.return_value.labels.get.return_value
    mock_label.save.side_effect = Exception("Permission denied")

    mock_factory.get_client.return_value = mock_gitlab_client

    with pytest.raises(ValueError, match="Failed to update label"):
        await update_label(
            project_id="test-project",
            label_name="bug",
            color="#FF0000",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.update_label.client_factory")
async def test_update_label_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test updating label in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await update_label(
        project_id="test-project",
        label_name="bug",
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
