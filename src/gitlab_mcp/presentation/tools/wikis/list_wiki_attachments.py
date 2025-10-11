"""List wiki attachments tool."""

import asyncio
import re
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


def _parse_attachments_from_markdown(content: str) -> list[dict[str, str]]:
    """Parse attachment references from markdown content.

    Args:
        content: Markdown content to parse

    Returns:
        List of attachment dictionaries with url, filename, and metadata
    """
    attachments = []

    # Match markdown images: ![alt text](url)
    image_pattern = r"!\[(.*?)\]\((/uploads/[^)]+)\)"
    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1)
        url = match.group(2)
        filename = url.split("/")[-1]
        attachments.append(
            {
                "url": url,
                "filename": filename,
                "alt_text": alt_text,
            }
        )

    # Match markdown links to uploads: [text](/uploads/...)
    link_pattern = r"\[(.*?)\]\((/uploads/[^)]+)\)"
    for match in re.finditer(link_pattern, content):
        link_text = match.group(1)
        url = match.group(2)
        filename = url.split("/")[-1]

        # Skip if already added as image
        if not any(att["url"] == url for att in attachments):
            attachments.append(
                {
                    "url": url,
                    "filename": filename,
                    "link_text": link_text,
                }
            )

    return attachments


async def list_wiki_attachments(
    project_id: str,
    slug: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List attachments for a wiki page in a GitLab project.

    This tool parses the wiki page content to find attachment references
    (images and file links using /uploads/ URLs).

    Args:
        project_id: GitLab project ID or namespace/project path
        slug: Wiki page slug (URL-friendly identifier)
        ctx: FastMCP context (auto-injected)

    Returns:
        List of attachments found in the wiki page content

    Raises:
        ValueError: If project or wiki page not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_list_wiki_attachments() -> dict[str, Any]:
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

        # 5. Parse attachments from content
        attachments = _parse_attachments_from_markdown(wiki.content)

        # 6. Return serialized response
        return {
            "attachments": attachments,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list_wiki_attachments)
