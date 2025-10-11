"""List pipeline jobs tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_pipeline_jobs(
    project_id: str,
    pipeline_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all jobs in a pipeline.

    Args:
        project_id: GitLab project ID or namespace/project path
        pipeline_id: Pipeline ID
        ctx: FastMCP context (auto-injected)

    Returns:
        List of jobs in the pipeline

    Raises:
        ValueError: If project or pipeline not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_list_pipeline_jobs() -> dict[str, Any]:
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

        # 5. List jobs in pipeline
        jobs = pipeline.jobs.list(all=True)

        # 6. Return serialized response
        return {
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "stage": job.stage,
                    "ref": job.ref,
                    "created_at": job.created_at,
                    "started_at": job.started_at,
                    "finished_at": job.finished_at,
                    "duration": job.duration,
                    "web_url": job.web_url,
                }
                for job in jobs
            ]
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_list_pipeline_jobs)
