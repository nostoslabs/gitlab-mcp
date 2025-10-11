"""Get the diff for a specific commit."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_commit_diff(
    project_id: str,
    commit_sha: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get the diff for a specific commit in a GitLab repository.

    Returns the changes introduced by the commit, showing additions and deletions
    for each modified file.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        commit_sha: Commit SHA, branch name, or tag name
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - commit_sha: The commit SHA
        - diffs: List of diff objects, each containing:
          - old_path: Path to the file before the change
          - new_path: Path to the file after the change
          - a_mode: File mode before the change
          - b_mode: File mode after the change
          - new_file: Whether this is a newly created file
          - renamed_file: Whether the file was renamed
          - deleted_file: Whether the file was deleted
          - diff: The actual diff content showing changes

    Example:
        >>> diff = await get_commit_diff("gitlab-org/gitlab", "a1b2c3d4")
        >>> diff = await get_commit_diff("123", "main")
        >>> diff = await get_commit_diff("my-org/my-project", "feature-branch")
    """

    def _sync_get_commit_diff() -> dict[str, Any]:
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

        # Get commit diffs
        try:
            diffs_list = commit.diff()
        except Exception as e:
            raise ValueError(f"Failed to get diff for commit '{commit_sha}': {e}")

        # Serialize diffs
        diffs = []
        for diff_item in diffs_list:
            diff_data = {
                "old_path": getattr(diff_item, "old_path", None),
                "new_path": getattr(diff_item, "new_path", None),
                "a_mode": getattr(diff_item, "a_mode", None),
                "b_mode": getattr(diff_item, "b_mode", None),
                "new_file": getattr(diff_item, "new_file", False),
                "renamed_file": getattr(diff_item, "renamed_file", False),
                "deleted_file": getattr(diff_item, "deleted_file", False),
                "diff": getattr(diff_item, "diff", ""),
            }
            diffs.append(diff_data)

        return {
            "commit_sha": commit_sha,
            "diffs": diffs,
            "total_diffs": len(diffs),
        }

    return await asyncio.to_thread(_sync_get_commit_diff)
