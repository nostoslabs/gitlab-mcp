"""Create wiki page tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_wiki_page(
    project_id: str,
    title: str,
    content: str,
    format: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new wiki page in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        title: Wiki page title
        content: Wiki page content
        format: Optional content format (markdown, rdoc, asciidoc, org)
        ctx: FastMCP context (auto-injected)

    Returns:
        Created wiki page details

    Raises:
        ValueError: If project not found or creation fails
        gitlab.exceptions.GitlabCreateError: If creation fails
    """

    def _sync_create_wiki_page() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Create wiki page
        wiki_data: dict[str, Any] = {
            "title": title,
            "content": content,
        }
        if format:
            wiki_data["format"] = format

        try:
            wiki = project.wikis.create(wiki_data)
        except gitlab.exceptions.GitlabCreateError as e:
            raise ValueError(f"Failed to create wiki page: {e}") from e

        # 5. Return serialized response
        return {
            "slug": wiki.slug,
            "title": wiki.title,
            "format": wiki.format,
            "content": wiki.content,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_create_wiki_page)
