"""List commits in a GitLab repository."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_commits(
    project_id: str,
    ref_name: str | None = None,
    since: str | None = None,
    until: str | None = None,
    path: str | None = None,
    all: bool = False,
    with_stats: bool = False,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List commits in a GitLab repository.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
         ref_name: Branch, tag, or commit SHA to list commits from (defaults to default branch)
        since: Only commits after this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
        until: Only commits before this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
        path: File path to filter commits that modified this path
        all: Retrieve all commits (default: False)
        with_stats: Include commit stats (additions, deletions, total changes)
        page: Page number for pagination (default: 1)
        per_page: Number of commits per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - commits: List of commit objects
        - total_results: Total number of commits returned

    Example:
        >>> commits = await list_commits("gitlab-org/gitlab", ref_name="main", per_page=10)
        >>> commits = await list_commits("123", since="2024-01-01", with_stats=True)
        >>> commits = await list_commits("my-org/my-project", path="src/main.py")
    """

    def _sync_list_commits() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Build filter parameters
        kwargs: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if ref_name:
            kwargs["ref_name"] = ref_name
        if since:
            kwargs["since"] = since
        if until:
            kwargs["until"] = until
        if path:
            kwargs["path"] = path
        if all:
            kwargs["all"] = True
        if with_stats:
            kwargs["with_stats"] = True

        # List commits
        commits_list = project.commits.list(**kwargs)

        # Serialize commits
        commits = []
        for commit in commits_list:
            commit_data = {
                "id": commit.id,
                "short_id": commit.short_id,
                "title": getattr(commit, "title", None),
                "message": getattr(commit, "message", None),
                "author_name": getattr(commit, "author_name", None),
                "author_email": getattr(commit, "author_email", None),
                "authored_date": getattr(commit, "authored_date", None),
                "committer_name": getattr(commit, "committer_name", None),
                "committer_email": getattr(commit, "committer_email", None),
                "committed_date": getattr(commit, "committed_date", None),
                "created_at": getattr(commit, "created_at", None),
                "parent_ids": getattr(commit, "parent_ids", []),
                "web_url": getattr(commit, "web_url", None),
            }

            # Add stats if requested
            if with_stats and hasattr(commit, "stats"):
                commit_data["stats"] = {
                    "additions": getattr(commit.stats, "additions", 0),
                    "deletions": getattr(commit.stats, "deletions", 0),
                    "total": getattr(commit.stats, "total", 0),
                }

            commits.append(commit_data)

        return {
            "commits": commits,
            "total_results": len(commits),
        }

    return await asyncio.to_thread(_sync_list_commits)
