"""Multi-tenant GitLab client factory."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import gitlab


@dataclass
class UserContext:
    """User context for multi-tenant operations.

    Attributes:
        user_id: Unique identifier for the user
        gitlab_token: GitLab personal access token
        gitlab_url: GitLab instance URL (defaults to GitLab.com)
    """

    user_id: str
    gitlab_token: str
    gitlab_url: str = "https://gitlab.com"


class GitLabClientFactory:
    """Thread-safe factory for creating and caching per-user GitLab clients.

    Each user gets their own gitlab.Gitlab instance to ensure:
    - Separate authentication
    - Thread-safe operations
    - Isolated HTTP sessions

    Example:
        >>> factory = GitLabClientFactory()
        >>> ctx = UserContext(user_id="user1", gitlab_token="token")
        >>> client = factory.get_client(ctx)
        >>> project = client.projects.get("project_id")
    """

    def __init__(self) -> None:
        """Initialize the factory with empty client cache."""
        self._clients: dict[str, gitlab.Gitlab] = {}
        self._lock = Lock()

    def get_client(self, context: UserContext | None = None) -> gitlab.Gitlab:
        """Get or create GitLab client for the given user context.

        Args:
            context: User context with credentials and GitLab URL.
                     If None, uses default settings from environment.

        Returns:
            gitlab.Gitlab instance configured for the user

        Note:
            Clients are cached by user_id:gitlab_url to avoid
            recreating connections for the same user.
        """
        # Import gitlab here to avoid module-level import issues
        import gitlab

        # If no context provided, use default client (single-tenant mode)
        if context is None:
            cache_key = "default"
            with self._lock:
                if cache_key not in self._clients:
                    from gitlab_mcp.infrastructure.config.settings import GitLabSettings

                    settings = GitLabSettings()

                    if not settings.gitlab_personal_access_token:
                        raise ValueError("GITLAB_PERSONAL_ACCESS_TOKEN not set in environment")

                    self._clients[cache_key] = gitlab.Gitlab(
                        url=settings.gitlab_api_url,
                        private_token=settings.gitlab_personal_access_token,
                        retry_transient_errors=True,
                    )
                return self._clients[cache_key]

        # Multi-tenant mode with user context
        cache_key = f"{context.user_id}:{context.gitlab_url}"

        with self._lock:
            if cache_key not in self._clients:
                self._clients[cache_key] = gitlab.Gitlab(
                    url=context.gitlab_url,
                    private_token=context.gitlab_token,
                    retry_transient_errors=True,  # Auto-retry on network issues
                )
            return self._clients[cache_key]

    def clear_user(self, user_id: str) -> None:
        """Remove all cached clients for a specific user.

        Args:
            user_id: User identifier to clear

        Use this when:
        - User logs out
        - Token is refreshed/revoked
        - User's credentials change

        TODO: Expose as admin tool for cache management.
        Currently only used in tests.
        """
        with self._lock:
            keys_to_remove = [k for k in self._clients if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self._clients[key]

    def clear_all(self) -> None:
        """Clear all cached clients.

        Use this when:
        - Server shutdown
        - Memory cleanup needed

        TODO: Expose as admin tool for cache management.
        Currently only used in tests.
        """
        with self._lock:
            self._clients.clear()

    def get_stats(self) -> dict[str, int]:
        """Get statistics about cached clients.

        Returns:
            Dictionary with client count

        TODO: Expose as monitoring tool.
        Currently only used in tests.
        """
        with self._lock:
            return {"total_clients": len(self._clients)}
