"""Get diffs for a specific merge request."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_merge_request_diffs(
    project_id: str,
    mr_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get diffs for a specific merge request in a GitLab project.

    Returns the changes introduced by the merge request, showing additions and
    deletions for each modified file.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        mr_iid: Merge request IID (project-scoped ID)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - mr_iid: The merge request IID
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
        >>> diffs = await get_merge_request_diffs("gitlab-org/gitlab", 123)
        >>> diffs = await get_merge_request_diffs("my-org/my-project", 45)
    """

    def _sync_get_merge_request_diffs() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the merge request
        try:
            mr = project.mergerequests.get(mr_iid)
        except Exception as e:
            raise ValueError(f"Merge request !{mr_iid} not found: {e}")

        # Get merge request diffs
        try:
            diffs_list = mr.diffs.list(all=True)
        except Exception as e:
            raise ValueError(f"Failed to get diffs for merge request !{mr_iid}: {e}")

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
            "mr_iid": mr_iid,
            "diffs": diffs,
            "total_diffs": len(diffs),
        }

    return await asyncio.to_thread(_sync_get_merge_request_diffs)
