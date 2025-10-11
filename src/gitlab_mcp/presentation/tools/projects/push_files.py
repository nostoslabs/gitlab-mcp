"""Push multiple files to a GitLab project in a single commit."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def push_files(
    project_id: str,
    branch: str,
    commit_message: str,
    actions: list[dict[str, Any]],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Push multiple files to a GitLab project in a single commit.

    This allows creating, updating, or deleting multiple files atomically.

    Args:
        project_id: Project ID or path
        branch: Branch name to commit to
        commit_message: Commit message
        actions: List of file actions, each with:
            - action: 'create', 'update', 'delete', or 'move'
            - file_path: Path to the file
            - content: File content (for create/update, base64 encoded if binary)
            - encoding: 'text' or 'base64' (optional, default: 'text')
            - previous_path: Previous path (for move action)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing commit details

    Example:
        >>> actions = [
        ...     {"action": "create", "file_path": "README.md", "content": "# Hello"},
        ...     {"action": "update", "file_path": "file.txt", "content": "Updated"},
        ... ]
        >>> result = await push_files("my-project", "main", "Add files", actions)
    """

    def _sync_push_files() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Create commit with multiple actions
        try:
            commit_data = {
                "branch": branch,
                "commit_message": commit_message,
                "actions": actions,
            }
            commit = project.commits.create(commit_data)
        except Exception as e:
            raise ValueError(f"Failed to push files: {e}")

        # Serialize commit
        return {
            "id": commit.id,
            "short_id": commit.short_id,
            "title": getattr(commit, "title", None),
            "message": commit.message,
            "author_name": getattr(commit, "author_name", None),
            "author_email": getattr(commit, "author_email", None),
            "created_at": getattr(commit, "created_at", None),
            "web_url": getattr(commit, "web_url", None),
            "stats": {
                "additions": (
                    getattr(commit, "stats", {}).get("additions", 0)
                    if hasattr(commit, "stats")
                    else 0
                ),
                "deletions": (
                    getattr(commit, "stats", {}).get("deletions", 0)
                    if hasattr(commit, "stats")
                    else 0
                ),
                "total": (
                    getattr(commit, "stats", {}).get("total", 0) if hasattr(commit, "stats") else 0
                ),
            },
        }

    return await asyncio.to_thread(_sync_push_files)
