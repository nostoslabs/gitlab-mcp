"""Create or update file tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_or_update_file(
    project_id: str,
    file_path: str,
    content: str,
    branch: str,
    commit_message: str,
    encoding: str = "text",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create or update a file in a GitLab repository.

    Args:
        project_id: GitLab project ID or namespace/project path
        file_path: Path to file in repository
        content: File content (text or base64 encoded)
        branch: Branch name to commit to
        commit_message: Commit message for the change
        encoding: Content encoding ('text' or 'base64', defaults to 'text')
        ctx: FastMCP context (auto-injected)

    Returns:
        File details including file_path, branch, action (created/updated),
        commit_id, and content_sha256

    Raises:
        ValueError: If project not found or token missing
        gitlab.exceptions.GitlabCreateError: If file creation fails
    """

    def _sync_create_or_update() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Check if file exists
        action = ""
        try:
            # File exists - update it
            f = project.files.get(file_path=file_path, ref=branch)
            f.content = content
            f.save(branch=branch, commit_message=commit_message)
            action = "updated"
        except gitlab.exceptions.GitlabGetError:
            # File doesn't exist - create it
            f = project.files.create(
                {
                    "file_path": file_path,
                    "branch": branch,
                    "content": content,
                    "commit_message": commit_message,
                    "encoding": encoding,
                }
            )
            action = "created"

        # 5. Return serialized response
        return {
            "file_path": f.file_path,
            "branch": branch,
            "action": action,
            "commit_id": f.last_commit_id,
            "content_sha256": f.content_sha256,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_create_or_update)
