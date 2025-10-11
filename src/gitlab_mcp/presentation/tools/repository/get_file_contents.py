"""Get file contents tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_file_contents(
    project_id: str,
    file_path: str,
    ref: str = "main",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get file contents from a GitLab repository.

    Args:
        project_id: GitLab project ID or namespace/project path
        file_path: Path to file in repository
        ref: Branch, tag, or commit SHA (defaults to 'main')
        ctx: FastMCP context (auto-injected)

    Returns:
        File details including content (base64 encoded), size, blob_id, etc.

    Raises:
        ValueError: If project or file not found or token missing
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_get_file() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get file from repository
        try:
            file = project.files.get(file_path=file_path, ref=ref)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"File {file_path} not found in ref {ref}") from e

        # 5. Return serialized response
        return {
            "file_path": file.file_path,
            "file_name": file.file_name,
            "size": file.size,
            "encoding": file.encoding,
            "content": file.content,
            "content_sha256": file.content_sha256,
            "ref": file.ref,
            "blob_id": file.blob_id,
            "commit_id": file.last_commit_id,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_get_file)
