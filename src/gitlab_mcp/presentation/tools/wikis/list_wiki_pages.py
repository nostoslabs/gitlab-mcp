"""List wiki pages tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_wiki_pages(
    project_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all wiki pages in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        ctx: FastMCP context (auto-injected)

    Returns:
        List of wiki pages with their details

    Raises:
        ValueError: If project not found
        gitlab.exceptions.GitlabListError: If listing fails
    """

    def _sync_list_wiki_pages() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. List wiki pages
        wikis = project.wikis.list(all=True)

        # 5. Return serialized response
        return {
            "wiki_pages": [
                {
                    "slug": wiki.slug,
                    "title": wiki.title,
                    "format": wiki.format,
                    "content": wiki.content,
                }
                for wiki in wikis
            ]
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list_wiki_pages)
