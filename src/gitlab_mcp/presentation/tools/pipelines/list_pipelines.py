"""List pipelines tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_pipelines(
    project_id: str,
    ref: str | None = None,
    status: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all pipelines in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        ref: Optional branch/tag name to filter by
        status: Optional pipeline status to filter by
            (running, pending, success, failed, canceled, skipped)
        ctx: FastMCP context (auto-injected)

    Returns:
        List of pipelines with their details

    Raises:
        ValueError: If project not found
        gitlab.exceptions.GitlabListError: If listing fails
    """

    def _sync_list_pipelines() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. List pipelines with optional filters
        list_kwargs: dict[str, Any] = {"all": True}
        if ref:
            list_kwargs["ref"] = ref
        if status:
            list_kwargs["status"] = status

        pipelines = project.pipelines.list(**list_kwargs)

        # 5. Return serialized response
        return {
            "pipelines": [
                {
                    "id": pipeline.id,
                    "iid": pipeline.iid,
                    "status": pipeline.status,
                    "ref": pipeline.ref,
                    "sha": pipeline.sha,
                    "web_url": pipeline.web_url,
                    "created_at": pipeline.created_at,
                    "updated_at": pipeline.updated_at,
                }
                for pipeline in pipelines
            ]
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list_pipelines)
