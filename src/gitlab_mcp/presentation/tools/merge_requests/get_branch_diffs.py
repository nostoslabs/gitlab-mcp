"""Get diffs between two branches."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_branch_diffs(
    project_id: str,
    from_branch: str,
    to_branch: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get diffs between two branches in a GitLab project.

    Compares two branches and returns the changes, showing what would be merged
    if from_branch was merged into to_branch.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        from_branch: Source branch name
        to_branch: Target branch name
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - from_branch: The source branch
        - to_branch: The target branch
        - commits: List of commits in from_branch not in to_branch
        - diffs: List of diff objects showing file changes

    Example:
        >>> diffs = await get_branch_diffs("gitlab-org/gitlab", "feature", "main")
        >>> diffs = await get_branch_diffs("123", "dev", "master")
    """

    def _sync_get_branch_diffs() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the comparison between branches
        try:
            comparison = project.repository_compare(
                from_=from_branch,
                to=to_branch,
            )
        except Exception as e:
            raise ValueError(f"Failed to compare branches '{from_branch}' and '{to_branch}': {e}")

        # Serialize commits
        commits = []
        if hasattr(comparison, "commits"):
            for commit in comparison["commits"]:
                commits.append(
                    {
                        "id": commit.get("id"),
                        "short_id": commit.get("short_id"),
                        "title": commit.get("title"),
                        "message": commit.get("message"),
                        "author_name": commit.get("author_name"),
                        "author_email": commit.get("author_email"),
                        "authored_date": commit.get("authored_date"),
                        "created_at": commit.get("created_at"),
                    }
                )

        # Serialize diffs
        diffs = []
        if hasattr(comparison, "diffs"):
            for diff_item in comparison["diffs"]:
                diffs.append(
                    {
                        "old_path": diff_item.get("old_path"),
                        "new_path": diff_item.get("new_path"),
                        "a_mode": diff_item.get("a_mode"),
                        "b_mode": diff_item.get("b_mode"),
                        "new_file": diff_item.get("new_file", False),
                        "renamed_file": diff_item.get("renamed_file", False),
                        "deleted_file": diff_item.get("deleted_file", False),
                        "diff": diff_item.get("diff", ""),
                    }
                )

        return {
            "from_branch": from_branch,
            "to_branch": to_branch,
            "commits": commits,
            "diffs": diffs,
            "total_commits": len(commits),
            "total_diffs": len(diffs),
        }

    return await asyncio.to_thread(_sync_get_branch_diffs)
