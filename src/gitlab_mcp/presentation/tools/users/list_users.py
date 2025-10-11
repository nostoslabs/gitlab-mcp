"""List users tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_users(
    search: str | None = None,
    username: str | None = None,
    active: bool = True,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List or search GitLab users.

    Search is case-insensitive and searches across username, name, and email.
    The username parameter performs case-insensitive exact username matching.

    Args:
        search: Search query (searches username, name, email)
        username: Filter by username (case-insensitive exact match)
        active: Only return active users (default: True)
        page: Page number for pagination
        per_page: Results per page (default: 20, max: 100)
        ctx: FastMCP context (auto-injected)

    Returns:
        Dictionary containing:
        - users: List of user objects with id, username, name, email, etc.
        - total_results: Total number of users found

    Raises:
        ValueError: If search fails
        gitlab.exceptions.GitlabListError: If listing fails

    Example:
        # Search for users by name/email/username
        result = await list_users(search="john")

        # Get user by exact username (case-insensitive)
        result = await list_users(username="JohnDoe")
    """

    def _sync_list_users() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Build query parameters
        kwargs: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        # Add search parameter (case-insensitive)
        if search:
            kwargs["search"] = search

        # Add username parameter for exact match (case-insensitive)
        if username:
            kwargs["username"] = username

        # Add active filter
        if active:
            kwargs["active"] = True

        # 4. List users using python-gitlab
        try:
            users_list = gl.users.list(**kwargs)
        except gitlab.exceptions.GitlabListError as e:
            raise ValueError(f"Failed to list users: {e}") from e

        # 5. Serialize users
        users = []
        for user in users_list:
            users.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "email": getattr(user, "email", None),
                    "avatar_url": getattr(user, "avatar_url", None),
                    "web_url": getattr(user, "web_url", None),
                    "state": getattr(user, "state", None),
                    "created_at": getattr(user, "created_at", None),
                }
            )

        return {
            "users": users,
            "total_results": len(users),
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list_users)
