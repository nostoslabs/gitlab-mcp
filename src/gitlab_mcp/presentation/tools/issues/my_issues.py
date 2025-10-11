"""List issues assigned to the authenticated user in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def my_issues(
    state: str = "opened",
    labels: str | None = None,
    milestone: str | None = None,
    order_by: str = "created_at",
    sort: str = "desc",
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List issues assigned to the authenticated user across all projects.

    Args:
        state: Issue state ('opened', 'closed', or 'all')
        labels: Comma-separated label names to filter by
        milestone: Milestone title to filter by
        order_by: Order by field ('created_at', 'updated_at', 'priority', 'due_date')
        sort: Sort order ('asc' or 'desc')
        page: Page number for pagination (default: 1)
        per_page: Number of issues per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing list of issues assigned to the user

    Example:
        >>> result = await my_issues(state="opened", labels="bug,urgent")
    """

    def _sync_my_issues() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Build query parameters
        query_params: dict[str, Any] = {
            "state": state,
            "scope": "assigned_to_me",
            "order_by": order_by,
            "sort": sort,
            "page": page,
            "per_page": per_page,
        }

        if labels:
            query_params["labels"] = labels
        if milestone:
            query_params["milestone"] = milestone

        # Get issues assigned to current user
        try:
            issues_list = gl.issues.list(**query_params, get_all=False)
        except Exception as e:
            raise ValueError(f"Failed to fetch issues: {e}")

        # Serialize issues
        issues_data = []
        for issue in issues_list:
            issues_data.append(
                {
                    "iid": issue.iid,
                    "id": issue.id,
                    "title": issue.title,
                    "description": getattr(issue, "description", None),
                    "state": issue.state,
                    "labels": getattr(issue, "labels", []),
                    "author": {
                        "id": (
                            getattr(issue.author, "id", None) if hasattr(issue, "author") else None
                        ),
                        "username": (
                            getattr(issue.author, "username", None)
                            if hasattr(issue, "author")
                            else None
                        ),
                    },
                    "assignees": (
                        [
                            {"id": assignee.get("id"), "username": assignee.get("username")}
                            for assignee in getattr(issue, "assignees", [])
                        ]
                        if hasattr(issue, "assignees") and issue.assignees
                        else []
                    ),
                    "milestone": (
                        {
                            "id": (
                                getattr(issue.milestone, "id", None)
                                if hasattr(issue, "milestone") and issue.milestone
                                else None
                            ),
                            "title": (
                                getattr(issue.milestone, "title", None)
                                if hasattr(issue, "milestone") and issue.milestone
                                else None
                            ),
                        }
                        if hasattr(issue, "milestone") and issue.milestone
                        else None
                    ),
                    "project_id": issue.project_id,
                    "web_url": getattr(issue, "web_url", None),
                    "created_at": getattr(issue, "created_at", None),
                    "updated_at": getattr(issue, "updated_at", None),
                    "due_date": getattr(issue, "due_date", None),
                }
            )

        return {
            "issues": issues_data,
            "total_results": len(issues_data),
            "page": page,
            "per_page": per_page,
            "state": state,
        }

    return await asyncio.to_thread(_sync_my_issues)
