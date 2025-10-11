"""Get repository tree tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_repository_tree(
    project_id: str,
    path: str = "",
    ref: str = "main",
    recursive: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get repository tree (list of files and directories).

    Args:
        project_id: GitLab project ID or namespace/project path
        path: Path inside repository (empty string for root)
        ref: Branch, tag, or commit SHA (defaults to 'main')
        recursive: Get tree recursively (defaults to False)
        ctx: FastMCP context (auto-injected)

    Returns:
        Repository tree with list of files and directories

    Raises:
        ValueError: If project not found or token missing
        gitlab.exceptions.GitlabGetError: If tree retrieval fails
    """

    def _sync_get_tree() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get repository tree
        tree = project.repository_tree(path=path, ref=ref, recursive=recursive)

        # 5. Return serialized response
        return {
            "tree": [
                {
                    "id": item.id,  # type: ignore[attr-defined]
                    "name": item.name,  # type: ignore[attr-defined]
                    "type": item.type,  # type: ignore[attr-defined]
                    "path": item.path,  # type: ignore[attr-defined]
                    "mode": item.mode,  # type: ignore[attr-defined]
                }
                for item in tree
            ]
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_get_tree)
