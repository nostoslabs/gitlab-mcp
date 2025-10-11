"""Tests for GitLab client factory."""

from unittest.mock import Mock, patch

import pytest
from gitlab_mcp.services.gitlab_client_factory import (
    GitLabClientFactory,
    UserContext,
)


@pytest.fixture
def factory() -> GitLabClientFactory:
    """Create client factory."""
    return GitLabClientFactory()


@pytest.fixture
def user_context() -> UserContext:
    """Create test user context."""
    return UserContext(
        user_id="test_user",
        gitlab_token="test_token",
        gitlab_url="https://gitlab.example.com",
    )


@patch("gitlab.Gitlab")
def test_get_client_creates_new(
    mock_gitlab_class: Mock, factory: GitLabClientFactory, user_context: UserContext
) -> None:
    """Factory creates new client for first request."""
    mock_client = Mock()
    mock_gitlab_class.return_value = mock_client

    client = factory.get_client(user_context)

    assert client == mock_client
    mock_gitlab_class.assert_called_once_with(
        url="https://gitlab.example.com",
        private_token="test_token",
        retry_transient_errors=True,
    )


@patch("gitlab.Gitlab")
def test_get_client_returns_cached(
    mock_gitlab_class: Mock, factory: GitLabClientFactory, user_context: UserContext
) -> None:
    """Factory returns cached client for subsequent requests."""
    mock_client = Mock()
    mock_gitlab_class.return_value = mock_client

    # First call - creates client
    client1 = factory.get_client(user_context)
    # Second call - returns cached
    client2 = factory.get_client(user_context)

    assert client1 is client2
    mock_gitlab_class.assert_called_once()  # Only called once


@patch("gitlab.Gitlab")
def test_clear_user_removes_clients(mock_gitlab_class: Mock, factory: GitLabClientFactory) -> None:
    """clear_user removes all clients for user."""
    ctx1 = UserContext("user1", "token1", "https://gitlab.com")
    ctx2 = UserContext("user1", "token1", "https://gitlab.example.com")
    ctx3 = UserContext("user2", "token2", "https://gitlab.com")

    # Create clients for multiple users
    factory.get_client(ctx1)
    factory.get_client(ctx2)
    factory.get_client(ctx3)

    # Clear user1
    factory.clear_user("user1")

    # Verify user1 clients removed, user2 remains
    stats = factory.get_stats()
    assert stats["total_clients"] == 1


@patch("gitlab.Gitlab")
def test_clear_all_removes_all(
    mock_gitlab_class: Mock, factory: GitLabClientFactory, user_context: UserContext
) -> None:
    """clear_all removes all cached clients."""
    factory.get_client(user_context)
    factory.clear_all()

    stats = factory.get_stats()
    assert stats["total_clients"] == 0
