"""Upload wiki attachment tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def upload_wiki_attachment(
    project_id: str,
    filename: str,
    filepath: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Upload an attachment to a GitLab project for use in wiki pages.

    Args:
        project_id: GitLab project ID or namespace/project path
        filename: Name of the file to upload
        filepath: Local path to the file to upload
        ctx: FastMCP context (auto-injected)

    Returns:
        Upload result with URL, alt text, and markdown

    Raises:
        ValueError: If project not found or upload fails
        gitlab.exceptions.GitlabUploadError: If upload fails
    """

    def _sync_upload_wiki_attachment() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Upload file
        try:
            result = project.upload(filename, filepath=filepath)
        except gitlab.exceptions.GitlabUploadError as e:
            raise ValueError(f"Failed to upload attachment: {e}") from e

        # 5. Return serialized response
        return {
            "url": result["url"],
            "alt": result["alt"],
            "markdown": result["markdown"],
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_upload_wiki_attachment)
