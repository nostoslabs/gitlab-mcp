"""Update wiki page tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def update_wiki_page(
    project_id: str,
    slug: str,
    title: str | None = None,
    content: str | None = None,
    format: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update an existing wiki page in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        slug: Wiki page slug (URL-friendly identifier)
        title: Optional new title
        content: Optional new content
        format: Optional new format (markdown, rdoc, asciidoc, org)
        ctx: FastMCP context (auto-injected)

    Returns:
        Updated wiki page details

    Raises:
        ValueError: If project or wiki page not found, or update fails
        gitlab.exceptions.GitlabUpdateError: If update fails
    """

    def _sync_update_wiki_page() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get wiki page
        try:
            wiki = project.wikis.get(slug)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Wiki page {slug} not found in project {project_id}") from e

        # 5. Update fields if provided
        if title is not None:
            wiki.title = title
        if content is not None:
            wiki.content = content
        if format is not None:
            wiki.format = format

        # 6. Save changes
        try:
            wiki.save()
        except gitlab.exceptions.GitlabUpdateError as e:
            raise ValueError(f"Failed to update wiki page: {e}") from e

        # 7. Return serialized response
        return {
            "slug": wiki.slug,
            "title": wiki.title,
            "format": wiki.format,
            "content": wiki.content,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_update_wiki_page)
