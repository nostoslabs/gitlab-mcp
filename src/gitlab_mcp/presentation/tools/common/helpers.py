"""Shared helper functions for MCP tools."""

from fastmcp import Context
from gitlab_mcp.infrastructure.config.settings import GitLabSettings
from gitlab_mcp.services.gitlab_client_factory import UserContext

# Module-level instances (will be injected by server)
settings = GitLabSettings()


def get_user_context(ctx: Context | None) -> UserContext:
    """Extract user context from FastMCP context.

    In multi-tenant mode, extracts user credentials from request headers.
    In single-tenant mode, uses default credentials from settings.

    Args:
        ctx: FastMCP context (may be None in single-tenant mode)

    Returns:
        UserContext with user ID and GitLab credentials

    Raises:
        ValueError: In multi-tenant mode if required headers are missing
    """
    if settings.multi_tenant_mode:
        # Multi-tenant: Extract from headers
        if ctx is None:
            raise ValueError("Context required in multi-tenant mode")

        user_id = ctx.request.headers.get("X-User-ID", "anonymous")  # type: ignore[attr-defined]
        gitlab_token = ctx.request.headers.get("X-GitLab-Token")  # type: ignore[attr-defined]
        gitlab_url = ctx.request.headers.get("X-GitLab-URL", settings.gitlab_api_url)  # type: ignore[attr-defined]

        if not gitlab_token:
            raise ValueError("GitLab token required in multi-tenant mode")

        return UserContext(
            user_id=user_id,
            gitlab_token=gitlab_token,
            gitlab_url=gitlab_url,
        )
    else:
        # Single-tenant mode - use default token
        if not settings.gitlab_personal_access_token:
            raise ValueError("GITLAB_PERSONAL_ACCESS_TOKEN not configured")

        return UserContext(
            user_id="default",
            gitlab_token=settings.gitlab_personal_access_token,
            gitlab_url=settings.gitlab_api_url,
        )
