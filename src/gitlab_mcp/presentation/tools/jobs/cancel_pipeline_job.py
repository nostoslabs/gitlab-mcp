"""Cancel a running pipeline job in GitLab."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def cancel_pipeline_job(
    project_id: str,
    job_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Cancel a running pipeline job.

    This will stop a job that is currently running or pending.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        job_id: Job ID to cancel
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - id: Job ID
        - name: Job name
        - status: Job status (should change to 'canceled')
        - stage: Pipeline stage
        - created_at: Job creation timestamp
        - finished_at: Job finish timestamp
        - web_url: Web URL to the job

    Example:
        >>> result = await cancel_pipeline_job("my-project", 12345)
    """

    def _sync_cancel_pipeline_job() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Get the project
        try:
            project = gl.projects.get(project_id)
        except Exception as e:
            raise ValueError(f"Project '{project_id}' not found: {e}")

        # Get the job
        try:
            job = project.jobs.get(job_id)
        except Exception as e:
            raise ValueError(f"Job '{job_id}' not found: {e}")

        # Cancel the job
        try:
            job.cancel()
            # Refresh job to get updated status
            job = project.jobs.get(job_id)
        except Exception as e:
            raise ValueError(f"Failed to cancel job '{job_id}': {e}")

        # Serialize job
        return {
            "id": job.id,
            "name": job.name,
            "status": job.status,
            "stage": getattr(job, "stage", None),
            "ref": getattr(job, "ref", None),
            "created_at": getattr(job, "created_at", None),
            "started_at": getattr(job, "started_at", None),
            "finished_at": getattr(job, "finished_at", None),
            "duration": getattr(job, "duration", None),
            "web_url": getattr(job, "web_url", None),
            "pipeline": {
                "id": getattr(job, "pipeline", {}).get("id") if hasattr(job, "pipeline") else None,
            },
        }

    return await asyncio.to_thread(_sync_cancel_pipeline_job)
