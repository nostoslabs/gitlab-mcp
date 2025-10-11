"""Create pipeline tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def create_pipeline(
    project_id: str,
    ref: str,
    variables: list[dict[str, str]] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new pipeline run in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        ref: Branch or tag name to run the pipeline on
        variables: Optional list of pipeline variables (each dict with 'key' and 'value')
        ctx: FastMCP context (auto-injected)

    Returns:
        Created pipeline details

    Raises:
        ValueError: If project not found or pipeline creation fails
        gitlab.exceptions.GitlabCreateError: If creation fails
    """

    def _sync_create_pipeline() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Create pipeline
        create_data: dict[str, Any] = {"ref": ref}
        if variables:
            create_data["variables"] = variables

        try:
            pipeline = project.pipelines.create(create_data)
        except gitlab.exceptions.GitlabCreateError as e:
            raise ValueError(f"Failed to create pipeline on ref {ref}: {e}") from e

        # 5. Return serialized response
        return {
            "id": pipeline.id,
            "iid": pipeline.iid,
            "status": pipeline.status,
            "ref": pipeline.ref,
            "sha": pipeline.sha,
            "web_url": pipeline.web_url,
            "created_at": pipeline.created_at,
            "updated_at": pipeline.updated_at,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_create_pipeline)
