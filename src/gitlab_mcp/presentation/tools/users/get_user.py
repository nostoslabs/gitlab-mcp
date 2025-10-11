"""Get user tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_user(
    username: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific GitLab user by username.

    Performs case-insensitive username matching.

    Args:
        username: Username to search for (case-insensitive)
        ctx: FastMCP context (auto-injected)

    Returns:
        Dictionary containing user details:
        - id: User ID
        - username: Username
        - name: Full name
        - email: Email address
        - avatar_url: Profile picture URL
        - web_url: Profile URL
        - state: Account state (active, blocked, etc.)
        - created_at: Account creation date
        - bio: User biography
        - location: User location
        - public_email: Public email
        - skype: Skype username
        - linkedin: LinkedIn profile
        - twitter: Twitter username
        - website_url: Personal website
        - organization: Organization name

    Raises:
        ValueError: If user not found or search fails
        gitlab.exceptions.GitlabGetError: If retrieval fails

    Example:
        # Get user by username (case-insensitive)
        user = await get_user(username="johndoe")
    """

    def _sync_get_user() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Search for user by username (case-insensitive)
        try:
            users_list = gl.users.list(username=username)
        except gitlab.exceptions.GitlabListError as e:
            raise ValueError(f"Failed to search for user '{username}': {e}") from e

        # 4. GitLab API returns array of users matching the username
        if not users_list or len(users_list) == 0:
            raise ValueError(f"User '{username}' not found")

        # 5. Find exact match (case-insensitive)
        user = None
        username_lower = username.lower()
        for u in users_list:
            if u.username.lower() == username_lower:
                user = u
                break

        if user is None:
            raise ValueError(f"No exact match found for username '{username}'")

        # 6. Serialize user details
        return {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": getattr(user, "email", None),
            "avatar_url": getattr(user, "avatar_url", None),
            "web_url": getattr(user, "web_url", None),
            "state": getattr(user, "state", None),
            "created_at": getattr(user, "created_at", None),
            "bio": getattr(user, "bio", None),
            "location": getattr(user, "location", None),
            "public_email": getattr(user, "public_email", None),
            "skype": getattr(user, "skype", None),
            "linkedin": getattr(user, "linkedin", None),
            "twitter": getattr(user, "twitter", None),
            "website_url": getattr(user, "website_url", None),
            "organization": getattr(user, "organization", None),
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_get_user)
