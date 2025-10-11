"""Tests for list_labels tool."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.presentation.tools.labels.list_labels import list_labels


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
    mock_label1 = Mock()
    mock_label2 = Mock()

    # Setup mock label attributes
    mock_label1.id = 1
    mock_label1.name = "bug"
    mock_label1.color = "#FF0000"
    mock_label1.description = "Bug reports"
    mock_label1.open_issues_count = 5
    mock_label1.closed_issues_count = 10
    mock_label1.open_merge_requests_count = 2

    mock_label2.id = 2
    mock_label2.name = "feature"
    mock_label2.color = "#00FF00"
    mock_label2.description = "New features"
    mock_label2.open_issues_count = 3
    mock_label2.closed_issues_count = 7
    mock_label2.open_merge_requests_count = 1

    # Chain mocks
    mock_project.labels.list.return_value = [mock_label1, mock_label2]
    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.list_labels.client_factory")
async def test_list_labels_success(mock_factory, mock_settings, mock_context, mock_gitlab_client):
    """Test successful label listing."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Execute
    result = await list_labels(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 2
    assert len(result["labels"]) == 2
    assert result["labels"][0]["name"] == "bug"
    assert result["labels"][0]["color"] == "#FF0000"
    assert result["labels"][1]["name"] == "feature"

    # Verify python-gitlab was called correctly
    mock_gitlab_client.projects.get.assert_called_once_with("test-project")
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.list.assert_called_once_with()


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.list_labels.client_factory")
async def test_list_labels_with_search(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test label listing with search filter."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make mock return only one label matching search
    mock_label = Mock()
    mock_label.id = 1
    mock_label.name = "bug"
    mock_label.color = "#FF0000"
    mock_label.description = "Bug reports"
    mock_label.open_issues_count = 5
    mock_label.closed_issues_count = 10
    mock_label.open_merge_requests_count = 2

    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.list.return_value = [mock_label]

    # Execute
    result = await list_labels(
        project_id="test-project",
        search="bug",
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 1
    assert result["labels"][0]["name"] == "bug"

    # Verify search parameter was passed
    mock_project.labels.list.assert_called_once_with(search="bug")


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.list_labels.client_factory")
async def test_list_labels_empty_result(
    mock_factory, mock_settings, mock_context, mock_gitlab_client
):
    """Test label listing with no results."""
    # Setup
    mock_settings.multi_tenant_mode = True
    mock_factory.get_client.return_value = mock_gitlab_client

    # Make mock return empty list
    mock_project = mock_gitlab_client.projects.get.return_value
    mock_project.labels.list.return_value = []

    # Execute
    result = await list_labels(
        project_id="test-project",
        ctx=mock_context,
    )

    # Verify result
    assert result["total_results"] == 0
    assert len(result["labels"]) == 0


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.list_labels.client_factory")
async def test_list_labels_project_not_found(mock_factory, mock_settings, mock_context):
    """Test error when project doesn't exist."""
    import gitlab

    # Setup
    mock_settings.multi_tenant_mode = True

    mock_gl = Mock()
    mock_gl.projects.get.side_effect = gitlab.exceptions.GitlabGetError("Not found")
    mock_factory.get_client.return_value = mock_gl

    with pytest.raises(ValueError, match="Project .* not found"):
        await list_labels(
            project_id="missing-project",
            ctx=mock_context,
        )


@pytest.mark.asyncio
@patch("gitlab_mcp.presentation.tools.common.helpers.settings")
@patch("gitlab_mcp.presentation.tools.labels.list_labels.client_factory")
async def test_list_labels_single_tenant_mode(mock_factory, mock_settings, mock_gitlab_client):
    """Test listing labels in single-tenant mode."""
    # Setup single-tenant mode
    mock_settings.multi_tenant_mode = False
    mock_settings.gitlab_personal_access_token = "single_tenant_token"
    mock_settings.gitlab_api_url = "https://gitlab.com"

    mock_factory.get_client.return_value = mock_gitlab_client

    # Create context without headers (single-tenant doesn't use them)
    ctx = Mock()
    ctx.request.headers = {}

    # Execute
    result = await list_labels(
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
