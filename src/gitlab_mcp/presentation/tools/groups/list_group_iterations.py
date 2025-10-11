"""List iterations in a GitLab group."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_group_iterations(
    group_id: str,
    state: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List iterations in a GitLab group.

     Iterations are time-boxed periods for planning and tracking work (like sprints in Scrum).
    This feature is available in GitLab Premium and above.

    Args:
        group_id: Group ID or path (e.g., "gitlab-org" or "123")
        state: Filter by state ('opened', 'closed', 'all')
        page: Page number for pagination (default: 1)
        per_page: Number of iterations per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - iterations: List of iteration objects with id, title, state, dates
        - total_results: Total number of iterations returned

    Example:
        >>> result = await list_group_iterations("my-group")
        >>> result = await list_group_iterations("my-group", state="opened")
    """

    def _sync_list_group_iterations() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the group
        try:
            group = gl.groups.get(group_id)
        except Exception as e:
            raise ValueError(f"Group '{group_id}' not found: {e}")

        # Build filter parameters
        kwargs: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if state:
            kwargs["state"] = state

        # Get iterations (this feature requires GitLab Premium)
        try:
            iterations_list = group.iterations.list(**kwargs)
        except AttributeError:
            # If iterations are not available (e.g., GitLab CE or insufficient permissions)
            return {
                "iterations": [],
                "total_results": 0,
                "message": "Iterations feature not available. Requires GitLab Premium or above.",
            }
        except Exception as e:
            raise ValueError(f"Failed to retrieve iterations: {e}")

        # Serialize iterations
        iterations = []
        for iteration in iterations_list:
            iteration_data = {
                "id": iteration.id,
                "iid": getattr(iteration, "iid", None),
                "title": getattr(iteration, "title", None),
                "description": getattr(iteration, "description", None),
                "state": getattr(iteration, "state", None),
                "created_at": getattr(iteration, "created_at", None),
                "updated_at": getattr(iteration, "updated_at", None),
                "start_date": getattr(iteration, "start_date", None),
                "due_date": getattr(iteration, "due_date", None),
                "web_url": getattr(iteration, "web_url", None),
            }
            iterations.append(iteration_data)

        return {
            "iterations": iterations,
            "total_results": len(iterations),
        }

    return await asyncio.to_thread(_sync_list_group_iterations)
