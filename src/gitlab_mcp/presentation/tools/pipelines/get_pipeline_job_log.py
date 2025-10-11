"""Get pipeline job log tool."""

import asyncio
from typing import Any

import gitlab
from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def get_pipeline_job_log(
    project_id: str,
    job_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get log output from a pipeline job.

    Args:
        project_id: GitLab project ID or namespace/project path
        job_id: Job ID
        ctx: FastMCP context (auto-injected)

    Returns:
        Job details and log output

    Raises:
        ValueError: If project or job not found
        gitlab.exceptions.GitlabGetError: If retrieval fails
    """

    def _sync_get_pipeline_job_log() -> dict[str, Any]:
        # 1. Get user context (multi-tenant) or use default
        user_ctx = get_user_context(ctx)

        # 2. Get GitLab client for this user
        gl = client_factory.get_client(user_ctx)

        # 3. Get project using python-gitlab
        try:
            project = gl.projects.get(project_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Project {project_id} not found") from e

        # 4. Get job
        try:
            job = project.jobs.get(job_id)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Job {job_id} not found") from e

        # 5. Get job log (trace)
        log_bytes = job.trace()
        log_text = log_bytes.decode("utf-8") if log_bytes else ""

        # 6. Return serialized response
        return {
            "job_id": job.id,
            "job_name": job.name,
            "status": job.status,
            "web_url": job.web_url,
            "log": log_text,
        }

    # Run sync code in thread pool (python-gitlab is sync, FastMCP is async)
    return await asyncio.to_thread(_sync_get_pipeline_job_log)
