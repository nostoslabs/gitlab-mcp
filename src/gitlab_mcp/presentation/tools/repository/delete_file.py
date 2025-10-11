"""Delete file tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def delete_file(
    project_id: str,
    file_path: str,
    branch: str,
    commit_message: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a file from a GitLab repository.

    Args:
        project_id: GitLab project ID or namespace/project path
        file_path: Path to file in repository
        branch: Branch name to commit deletion to
        commit_message: Commit message for the deletion
        ctx: FastMCP context (auto-injected)

    Returns:
        Deletion details including file_path, branch, deleted status, and commit_id

    Raises:
        ValueError: If project or file not found or token missing
        gitlab.exceptions.GitlabDeleteError: If file deletion fails
    """

    def _sync_delete() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get file and delete it
        try:
            f = project.files.get(file_path=file_path, ref=branch)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"File {file_path} not found in branch {branch}") from e

        # Delete the file
        f.delete(branch=branch, commit_message=commit_message)

        # 5. Return serialized response
        return {
            "file_path": file_path,
            "branch": branch,
            "deleted": True,
            "commit_id": f.last_commit_id,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_delete)
