"""Retry pipeline tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def retry_pipeline(
    project_id: str,
    pipeline_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Retry a failed pipeline in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        pipeline_id: Pipeline ID to retry
        ctx: FastMCP context (auto-injected)

    Returns:
        Pipeline details after retry

    Raises:
        ValueError: If project or pipeline not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_retry_pipeline() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get pipeline
        try:
            pipeline = project.pipelines.get(pipeline_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Pipeline {pipeline_id} not found") from e

        # 5. Retry pipeline
        pipeline.retry()

        # 6. Return serialized response
        return {
            "id": pipeline.id,
            "status": pipeline.status,
            "ref": pipeline.ref,
            "sha": pipeline.sha,
            "web_url": pipeline.web_url,
            "message": "Pipeline retried successfully",
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_retry_pipeline)
