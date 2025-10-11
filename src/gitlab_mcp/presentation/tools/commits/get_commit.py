"""Get details of a specific commit."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_commit(
    project_id: str,
    commit_sha: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific commit in a GitLab repository.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        commit_sha: Commit SHA, branch name, or tag name
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing detailed commit information including:
        - id: Full commit SHA
        - short_id: Short commit SHA
        - title: Commit title (first line of message)
        - message: Full commit message
        - author_name: Name of the author
        - author_email: Email of the author
        - authored_date: When the commit was authored
        - committer_name: Name of the committer
        - committer_email: Email of the committer
        - committed_date: When the commit was committed
        - parent_ids: List of parent commit SHAs
        - stats: Commit statistics (additions, deletions, total)
        - web_url: URL to view commit in GitLab
        - last_pipeline: Information about the last CI/CD pipeline (if available)

    Example:
        >>> commit = await get_commit("gitlab-org/gitlab", "a1b2c3d4")
        >>> commit = await get_commit("123", "main")
        >>> commit = await get_commit("my-org/my-project", "v1.0.0")
    """

    def _sync_get_commit() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the commit
        try:
            commit = project.commits.get(commit_sha)
        except Exception as e:
            raise ValueError(f"Commit '{commit_sha}' not found: {e}")

        # Serialize commit details
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

        # Add stats if available
        if hasattr(commit, "stats"):
            commit_data["stats"] = {
                "additions": getattr(commit.stats, "additions", 0),
                "deletions": getattr(commit.stats, "deletions", 0),
                "total": getattr(commit.stats, "total", 0),
            }

        # Add last pipeline if available
        if hasattr(commit, "last_pipeline") and commit.last_pipeline:
            commit_data["last_pipeline"] = {
                "id": getattr(commit.last_pipeline, "id", None),
                "ref": getattr(commit.last_pipeline, "ref", None),
                "sha": getattr(commit.last_pipeline, "sha", None),
                "status": getattr(commit.last_pipeline, "status", None),
                "web_url": getattr(commit.last_pipeline, "web_url", None),
            }

        return commit_data

    return await asyncio.to_thread(_sync_get_commit)
