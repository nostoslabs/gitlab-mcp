"""GitLab MCP Server - FastMCP server instance and tool registration."""

from collections.abc import Callable
from typing import Any

from fastmcp import Context, FastMCP

# Import settings
from gitlab_mcp.infrastructure.config.settings import GitLabSettings

# Import branch tools
from gitlab_mcp.presentation.tools.branches.create_branch import create_branch
from gitlab_mcp.presentation.tools.branches.delete_branch import delete_branch
from gitlab_mcp.presentation.tools.branches.list_branches import list_branches

# Import commit tools
from gitlab_mcp.presentation.tools.commits.get_commit import get_commit
from gitlab_mcp.presentation.tools.commits.get_commit_diff import get_commit_diff
from gitlab_mcp.presentation.tools.commits.list_commits import list_commits

# Import discussion tools
from gitlab_mcp.presentation.tools.discussions.create_issue_note import create_issue_note
from gitlab_mcp.presentation.tools.discussions.create_merge_request_note import (
    create_merge_request_note,
)
from gitlab_mcp.presentation.tools.discussions.list_issue_discussions import (
    list_issue_discussions,
)
from gitlab_mcp.presentation.tools.discussions.list_merge_request_discussions import (
    list_merge_request_discussions,
)
from gitlab_mcp.presentation.tools.discussions.update_issue_note import update_issue_note

# Import draft note tools
from gitlab_mcp.presentation.tools.draft_notes.create_draft_note import create_draft_note
from gitlab_mcp.presentation.tools.draft_notes.delete_draft_note import delete_draft_note
from gitlab_mcp.presentation.tools.draft_notes.get_draft_note import get_draft_note
from gitlab_mcp.presentation.tools.draft_notes.list_draft_notes import list_draft_notes
from gitlab_mcp.presentation.tools.draft_notes.publish_draft_note import publish_draft_note
from gitlab_mcp.presentation.tools.draft_notes.update_draft_note import update_draft_note

# Import event tools
from gitlab_mcp.presentation.tools.events.get_project_events import get_project_events
from gitlab_mcp.presentation.tools.events.list_events import list_events

# Import group tools
from gitlab_mcp.presentation.tools.groups.list_group_iterations import (
    list_group_iterations,
)
from gitlab_mcp.presentation.tools.groups.list_group_projects import list_group_projects

# Import issue link tools
from gitlab_mcp.presentation.tools.issue_links.create_issue_link import create_issue_link
from gitlab_mcp.presentation.tools.issue_links.delete_issue_link import delete_issue_link
from gitlab_mcp.presentation.tools.issue_links.get_issue_link import get_issue_link
from gitlab_mcp.presentation.tools.issue_links.list_issue_links import list_issue_links

# Import issue tools
from gitlab_mcp.presentation.tools.issues.create_issue import create_issue
from gitlab_mcp.presentation.tools.issues.delete_issue import delete_issue
from gitlab_mcp.presentation.tools.issues.get_issue import get_issue
from gitlab_mcp.presentation.tools.issues.list_issues import list_issues
from gitlab_mcp.presentation.tools.issues.my_issues import my_issues
from gitlab_mcp.presentation.tools.issues.update_issue import update_issue

# Import job tools
from gitlab_mcp.presentation.tools.jobs.cancel_pipeline_job import cancel_pipeline_job
from gitlab_mcp.presentation.tools.jobs.play_pipeline_job import play_pipeline_job

# Import label tools
from gitlab_mcp.presentation.tools.labels.create_label import create_label
from gitlab_mcp.presentation.tools.labels.delete_label import delete_label
from gitlab_mcp.presentation.tools.labels.get_label import get_label
from gitlab_mcp.presentation.tools.labels.list_labels import list_labels
from gitlab_mcp.presentation.tools.labels.update_label import update_label

# Import member tools
from gitlab_mcp.presentation.tools.members.list_project_members import (
    list_project_members,
)

# Import merge request tools
from gitlab_mcp.presentation.tools.merge_requests.approve_merge_request import (
    approve_merge_request,
)
from gitlab_mcp.presentation.tools.merge_requests.create_merge_request import (
    create_merge_request,
)
from gitlab_mcp.presentation.tools.merge_requests.get_branch_diffs import (
    get_branch_diffs,
)
from gitlab_mcp.presentation.tools.merge_requests.get_merge_request import (
    get_merge_request,
)
from gitlab_mcp.presentation.tools.merge_requests.get_merge_request_diffs import (
    get_merge_request_diffs,
)
from gitlab_mcp.presentation.tools.merge_requests.list_merge_request_diffs import (
    list_merge_request_diffs,
)
from gitlab_mcp.presentation.tools.merge_requests.list_merge_requests import (
    list_merge_requests,
)
from gitlab_mcp.presentation.tools.merge_requests.merge_merge_request import (
    merge_merge_request,
)
from gitlab_mcp.presentation.tools.merge_requests.update_merge_request import (
    update_merge_request,
)

# Import milestone tools
from gitlab_mcp.presentation.tools.milestones.add_issue_to_milestone import (
    add_issue_to_milestone,
)
from gitlab_mcp.presentation.tools.milestones.close_milestone import close_milestone
from gitlab_mcp.presentation.tools.milestones.create_milestone import create_milestone
from gitlab_mcp.presentation.tools.milestones.delete_milestone import delete_milestone
from gitlab_mcp.presentation.tools.milestones.get_milestone import get_milestone
from gitlab_mcp.presentation.tools.milestones.get_milestone_burndown import (
    get_milestone_burndown,
)
from gitlab_mcp.presentation.tools.milestones.list_milestone_issues import (
    list_milestone_issues,
)
from gitlab_mcp.presentation.tools.milestones.list_milestone_merge_requests import (
    list_milestone_merge_requests,
)
from gitlab_mcp.presentation.tools.milestones.list_milestones import list_milestones
from gitlab_mcp.presentation.tools.milestones.remove_issue_from_milestone import (
    remove_issue_from_milestone,
)
from gitlab_mcp.presentation.tools.milestones.update_milestone import update_milestone

# Import namespace tools
from gitlab_mcp.presentation.tools.namespaces.get_namespace import get_namespace
from gitlab_mcp.presentation.tools.namespaces.list_namespaces import list_namespaces
from gitlab_mcp.presentation.tools.namespaces.verify_namespace import verify_namespace

# Import pipeline tools
from gitlab_mcp.presentation.tools.pipelines.cancel_pipeline import cancel_pipeline
from gitlab_mcp.presentation.tools.pipelines.create_pipeline import create_pipeline
from gitlab_mcp.presentation.tools.pipelines.get_pipeline import get_pipeline
from gitlab_mcp.presentation.tools.pipelines.get_pipeline_job_log import (
    get_pipeline_job_log,
)
from gitlab_mcp.presentation.tools.pipelines.list_pipeline_jobs import list_pipeline_jobs
from gitlab_mcp.presentation.tools.pipelines.list_pipelines import list_pipelines
from gitlab_mcp.presentation.tools.pipelines.retry_pipeline import retry_pipeline

# Import project tools
from gitlab_mcp.presentation.tools.projects.create_project import create_project
from gitlab_mcp.presentation.tools.projects.fork_project import fork_project
from gitlab_mcp.presentation.tools.projects.get_project import get_project
from gitlab_mcp.presentation.tools.projects.list_projects import list_projects
from gitlab_mcp.presentation.tools.projects.push_files import push_files
from gitlab_mcp.presentation.tools.projects.search_projects import search_projects

# Import repository tools
from gitlab_mcp.presentation.tools.repository.create_or_update_file import (
    create_or_update_file,
)
from gitlab_mcp.presentation.tools.repository.delete_file import delete_file
from gitlab_mcp.presentation.tools.repository.get_file_contents import get_file_contents
from gitlab_mcp.presentation.tools.repository.get_repository_tree import (
    get_repository_tree,
)

# Import user tools
from gitlab_mcp.presentation.tools.users.get_user import get_user
from gitlab_mcp.presentation.tools.users.list_users import list_users

# Import wiki tools
from gitlab_mcp.presentation.tools.wikis.create_wiki_page import create_wiki_page
from gitlab_mcp.presentation.tools.wikis.delete_wiki_page import delete_wiki_page
from gitlab_mcp.presentation.tools.wikis.get_wiki_page import get_wiki_page
from gitlab_mcp.presentation.tools.wikis.list_wiki_attachments import list_wiki_attachments
from gitlab_mcp.presentation.tools.wikis.list_wiki_pages import list_wiki_pages
from gitlab_mcp.presentation.tools.wikis.update_wiki_page import update_wiki_page
from gitlab_mcp.presentation.tools.wikis.upload_wiki_attachment import upload_wiki_attachment

# Load settings to check read-only mode
settings = GitLabSettings()

# Define read-only tools (tools that only read data, don't modify GitLab state)
READ_ONLY_TOOLS = [
    "gitlab_search_projects",
    "gitlab_get_file_contents",
    "gitlab_get_merge_request",
    "gitlab_get_merge_request_diffs",
    "gitlab_list_merge_request_diffs",
    "gitlab_get_branch_diffs",
    "gitlab_list_merge_request_discussions",
    "gitlab_list_issues",
    "gitlab_my_issues",
    "gitlab_list_merge_requests",
    "gitlab_get_issue",
    "gitlab_list_issue_links",
    "gitlab_list_issue_discussions",
    "gitlab_get_issue_link",
    "gitlab_list_namespaces",
    "gitlab_get_namespace",
    "gitlab_verify_namespace",
    "gitlab_get_project",
    "gitlab_list_projects",
    "gitlab_list_project_members",
    "gitlab_get_pipeline",
    "gitlab_list_pipelines",
    "gitlab_list_pipeline_jobs",
    "gitlab_get_pipeline_job_log",
    "gitlab_list_labels",
    "gitlab_get_label",
    "gitlab_list_group_projects",
    "gitlab_list_group_iterations",
    "gitlab_get_repository_tree",
    "gitlab_list_milestones",
    "gitlab_get_milestone",
    "gitlab_list_milestone_issues",
    "gitlab_list_milestone_merge_requests",
    "gitlab_get_milestone_burndown",
    "gitlab_list_wiki_pages",
    "gitlab_get_wiki_page",
    "gitlab_list_wiki_attachments",
    "gitlab_list_users",
    "gitlab_get_user",
    "gitlab_list_commits",
    "gitlab_get_commit",
    "gitlab_get_commit_diff",
    "gitlab_list_events",
    "gitlab_get_project_events",
    "gitlab_list_branches",
    "gitlab_list_draft_notes",
    "gitlab_get_draft_note",
]

# Create FastMCP server instance
mcp = FastMCP("GitLab MCP Server")


def should_register_tool(tool_name: str) -> bool:
    """Check if a tool should be registered based on read-only mode.

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if tool should be registered, False otherwise
    """
    if not settings.gitlab_read_only_mode:
        # Not in read-only mode, register all tools
        return True

    # In read-only mode, only register read-only tools
    return tool_name in READ_ONLY_TOOLS


def conditional_tool(tool_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that conditionally registers a tool based on read-only mode.

    Args:
        tool_name: Name of the tool

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if should_register_tool(tool_name):
            return mcp.tool()(func)
        return func

    return decorator


# Register project tools
@conditional_tool("gitlab_list_projects")
async def gitlab_list_projects(
    search: str | None = None,
    owned: bool = False,
    starred: bool = False,
    visibility: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List GitLab projects with optional filters.

    Args:
        search: Search query
        owned: Only owned projects
        starred: Only starred projects
        visibility: Filter by visibility ('public', 'internal', 'private')
        page: Page number
        per_page: Results per page
    """
    return await list_projects(search, owned, starred, visibility, page, per_page, ctx)


@conditional_tool("gitlab_get_project")
async def gitlab_get_project(
    project_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific project by ID or path.

    Args:
        project_id: GitLab project ID or namespace/project path
    """
    return await get_project(project_id, ctx)


@conditional_tool("gitlab_search_projects")
async def gitlab_search_projects(
    search: str,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Search GitLab projects.

    Args:
        search: Search query (required)
        page: Page number
        per_page: Results per page
    """
    return await search_projects(search, page, per_page, ctx)


# Register user tools
@conditional_tool("gitlab_list_users")
async def gitlab_list_users(
    search: str | None = None,
    username: str | None = None,
    active: bool = True,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List or search GitLab users (case-insensitive).

    Args:
        search: Search query (searches username, name, email) - case-insensitive
        username: Filter by username (case-insensitive exact match)
        active: Only return active users (default: True)
        page: Page number
        per_page: Results per page
    """
    return await list_users(search, username, active, page, per_page, ctx)


@conditional_tool("gitlab_get_user")
async def gitlab_get_user(
    username: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific GitLab user by username (case-insensitive).

    Args:
        username: Username to search for (case-insensitive)
    """
    return await get_user(username, ctx)


# Register event tools
@conditional_tool("gitlab_list_events")
async def gitlab_list_events(
    action: str | None = None,
    target_type: str | None = None,
    before: str | None = None,
    after: str | None = None,
    sort: str = "desc",
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all events for the authenticated user.

    Returns activity feed including push events, issue events, merge request events,
    comments, and project events.

    Args:
        action: Filter events by action (e.g., created, updated, closed, pushed, commented)
        target_type: Filter events by target type (e.g., issue, milestone, merge_request)
       before: Filter events before this date (ISO 8601 format: YYYY-MM-DD)
       after: Filter events after this date (ISO 8601 format: YYYY-MM-DD)
       sort: Sort order (asc or desc, default: desc)
       page: Page number for pagination
       per_page: Number of events per page (max 100)
    """
    return await list_events(action, target_type, before, after, sort, page, per_page, ctx)


@conditional_tool("gitlab_get_project_events")
async def gitlab_get_project_events(
    project_id: str,
    action: str | None = None,
    target_type: str | None = None,
    before: str | None = None,
    after: str | None = None,
    sort: str = "desc",
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get events for a specific GitLab project.

    Returns activity feed for a project including push events, issue events,
     merge request events, comments, wiki events, and pipeline events.

     Args:
         project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
         action: Filter events by action (e.g., created, updated, closed, pushed, commented)
         target_type: Filter events by target type (e.g., issue, milestone, merge_request)
        before: Filter events before this date (ISO 8601 format: YYYY-MM-DD)
        after: Filter events after this date (ISO 8601 format: YYYY-MM-DD)
        sort: Sort order (asc or desc, default: desc)
        page: Page number for pagination
        per_page: Number of events per page (max 100)
    """
    return await get_project_events(
        project_id, action, target_type, before, after, sort, page, per_page, ctx
    )


# Register label tools
@conditional_tool("gitlab_list_labels")
async def gitlab_list_labels(
    project_id: str,
    search: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List labels in a GitLab project.

    Args:
        project_id: Project ID or path
        search: Optional search string to filter labels
    """
    return await list_labels(project_id, search, ctx)


@conditional_tool("gitlab_get_label")
async def gitlab_get_label(
    project_id: str,
    label_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific label.

    Args:
        project_id: Project ID or path
        label_id: Label ID
    """
    return await get_label(project_id, label_id, ctx)


# Register discussion tools
@conditional_tool("gitlab_list_issue_discussions")
async def gitlab_list_issue_discussions(
    project_id: str,
    issue_iid: int,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List discussions (comments) on a GitLab issue.

    Args:
        project_id: Project ID or path
        issue_iid: Issue IID
        page: Page number
        per_page: Results per page
    """
    return await list_issue_discussions(project_id, issue_iid, page, per_page, ctx)


@conditional_tool("gitlab_create_issue_note")
async def gitlab_create_issue_note(
    project_id: str,
    issue_iid: int,
    body: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a comment on a GitLab issue.

    Args:
        project_id: Project ID or path
        issue_iid: Issue IID
        body: Comment text (markdown supported)
    """
    return await create_issue_note(project_id, issue_iid, body, ctx)


@conditional_tool("gitlab_create_merge_request_note")
async def gitlab_create_merge_request_note(
    project_id: str,
    mr_iid: int,
    body: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a comment on a GitLab merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID
        body: Comment text (markdown supported)
    """
    return await create_merge_request_note(project_id, mr_iid, body, ctx)


# Register issue link tools
@conditional_tool("gitlab_list_issue_links")
async def gitlab_list_issue_links(
    project_id: str,
    issue_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all links for a GitLab issue.

    Args:
        project_id: Project ID or path
        issue_iid: Issue IID
    """
    return await list_issue_links(project_id, issue_iid, ctx)


@conditional_tool("gitlab_get_issue_link")
async def gitlab_get_issue_link(
    project_id: str,
    issue_iid: int,
    link_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific issue link.

    Args:
        project_id: Project ID or path
        issue_iid: Issue IID
        link_id: Link ID
    """
    return await get_issue_link(project_id, issue_iid, link_id, ctx)


# Register member tools
@conditional_tool("gitlab_list_project_members")
async def gitlab_list_project_members(
    project_id: str,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List members of a GitLab project with their access levels.

    Access levels: 10=Guest, 20=Reporter, 30=Developer, 40=Maintainer, 50=Owner

    Args:
        project_id: Project ID or path
        page: Page number
        per_page: Results per page
    """
    return await list_project_members(project_id, page, per_page, ctx)


# Register namespace tools
@conditional_tool("gitlab_list_namespaces")
async def gitlab_list_namespaces(
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List available namespaces in GitLab.

    Namespaces include user and group namespaces, used as the first part of project paths.

    Args:
        search: Optional search string to filter namespaces
        page: Page number
        per_page: Results per page
    """
    return await list_namespaces(search, page, per_page, ctx)


@conditional_tool("gitlab_get_namespace")
async def gitlab_get_namespace(
    namespace_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific namespace.

    Args:
        namespace_id: Namespace ID
    """
    return await get_namespace(namespace_id, ctx)


@conditional_tool("gitlab_verify_namespace")
async def gitlab_verify_namespace(
    namespace_path: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Verify if a namespace path is available or already taken.

    Args:
        namespace_path: Namespace path to check (e.g., "my-group")
    """
    return await verify_namespace(namespace_path, ctx)


# Register group tools
@conditional_tool("gitlab_list_group_projects")
async def gitlab_list_group_projects(
    group_id: str,
    archived: bool = False,
    visibility: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all projects in a GitLab group.

    Args:
        group_id: Group ID or path (e.g., "gitlab-org" or "123")
        archived: Include archived projects
        visibility: Filter by visibility ('public', 'internal', 'private')
        search: Search query to filter projects
        page: Page number
        per_page: Results per page
    """
    return await list_group_projects(group_id, archived, visibility, search, page, per_page, ctx)


@conditional_tool("gitlab_list_group_iterations")
async def gitlab_list_group_iterations(
    group_id: str,
    state: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List iterations in a GitLab group (Premium feature).

    Args:
        group_id: Group ID or path
        state: Filter by state ('opened', 'closed', 'all')
        page: Page number
        per_page: Results per page
    """
    return await list_group_iterations(group_id, state, page, per_page, ctx)


# Register job tools
@conditional_tool("gitlab_play_pipeline_job")
async def gitlab_play_pipeline_job(
    project_id: str,
    job_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Trigger (play) a manual pipeline job.

    Args:
        project_id: Project ID or path
        job_id: Job ID to trigger
    """
    return await play_pipeline_job(project_id, job_id, ctx)


@conditional_tool("gitlab_cancel_pipeline_job")
async def gitlab_cancel_pipeline_job(
    project_id: str,
    job_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Cancel a running pipeline job.

    Args:
        project_id: Project ID or path
        job_id: Job ID to cancel
    """
    return await cancel_pipeline_job(project_id, job_id, ctx)


# Register draft note tools
@conditional_tool("gitlab_list_draft_notes")
async def gitlab_list_draft_notes(
    project_id: str,
    mr_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List draft notes (unpublished comments) on a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID
    """
    return await list_draft_notes(project_id, mr_iid, ctx)


@conditional_tool("gitlab_get_draft_note")
async def gitlab_get_draft_note(
    project_id: str,
    mr_iid: int,
    draft_note_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific draft note on a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID
        draft_note_id: Draft note ID
    """
    return await get_draft_note(project_id, mr_iid, draft_note_id, ctx)


# Register issue tools
@conditional_tool("gitlab_list_issues")
async def gitlab_list_issues(
    project_id: str,
    state: str | None = None,
    labels: list[str] | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List issues in a project.

    Args:
        project_id: GitLab project ID or namespace/project path
        state: Filter by state ('opened', 'closed', 'all')
        labels: Filter by labels
        search: Search in title and description
        page: Page number (1-indexed)
        per_page: Results per page (max 100)
    """
    return await list_issues(project_id, state, labels, search, page, per_page, ctx)


@conditional_tool("gitlab_get_issue")
async def gitlab_get_issue(
    project_id: str,
    issue_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific issue by IID.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (project-scoped ID)
    """
    return await get_issue(project_id, issue_iid, ctx)


@conditional_tool("gitlab_create_issue")
async def gitlab_create_issue(
    project_id: str,
    title: str,
    description: str | None = None,
    labels: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new issue in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        title: Issue title (required)
        description: Issue description in markdown
        labels: List of label names to apply
    """
    return await create_issue(project_id, title, description, labels, ctx)


@conditional_tool("gitlab_update_issue")
async def gitlab_update_issue(
    project_id: str,
    issue_iid: int,
    title: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    state_event: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update an existing issue in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (project-scoped ID)
        title: New issue title
        description: New issue description in markdown
        labels: New list of label names (replaces existing)
        state_event: State transition ('close' or 'reopen')
    """
    return await update_issue(project_id, issue_iid, title, description, labels, state_event, ctx)


@conditional_tool("gitlab_delete_issue")
async def gitlab_delete_issue(
    project_id: str,
    issue_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete an issue from a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (project-scoped ID) to delete
    """
    return await delete_issue(project_id, issue_iid, ctx)


# Register merge request tools
@conditional_tool("gitlab_list_merge_requests")
async def gitlab_list_merge_requests(
    project_id: str,
    state: str | None = None,
    labels: list[str] | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List merge requests in a project.

    Args:
        project_id: GitLab project ID or path
        state: Filter by state ('opened', 'closed', 'merged', 'all')
        labels: Filter by labels
        search: Search in title and description
        page: Page number (1-indexed)
        per_page: Results per page (max 100)
    """
    return await list_merge_requests(project_id, state, labels, search, page, per_page, ctx)


@conditional_tool("gitlab_get_merge_request")
async def gitlab_get_merge_request(
    project_id: str,
    mr_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific merge request by IID.

    Args:
        project_id: GitLab project ID or path
        mr_iid: Merge request IID (project-scoped ID)
    """
    return await get_merge_request(project_id, mr_iid, ctx)


@conditional_tool("gitlab_create_merge_request")
async def gitlab_create_merge_request(
    project_id: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str | None = None,
    assignee_id: int | None = None,
    labels: list[str] | None = None,
    remove_source_branch: bool = False,
    squash: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new merge request.

    Args:
        project_id: GitLab project ID or namespace/project path
        source_branch: Source branch name
        target_branch: Target branch name
        title: MR title (required)
        description: MR description in markdown
        assignee_id: User ID to assign MR to
        labels: List of label names
        remove_source_branch: Delete source branch when merged
        squash: Squash commits when merging
    """
    return await create_merge_request(
        project_id,
        source_branch,
        target_branch,
        title,
        description,
        assignee_id,
        labels,
        remove_source_branch,
        squash,
        ctx,
    )


@conditional_tool("gitlab_merge_merge_request")
async def gitlab_merge_merge_request(
    project_id: str,
    mr_iid: int,
    merge_commit_message: str | None = None,
    should_remove_source_branch: bool = False,
    squash: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Merge a merge request.

    Args:
        project_id: GitLab project ID or path
        mr_iid: Merge request IID
        merge_commit_message: Custom merge commit message
        should_remove_source_branch: Delete source branch after merge
        squash: Squash commits when merging
    """
    return await merge_merge_request(
        project_id, mr_iid, merge_commit_message, should_remove_source_branch, squash, ctx
    )


@conditional_tool("gitlab_approve_merge_request")
async def gitlab_approve_merge_request(
    project_id: str,
    mr_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Approve a merge request.

    Args:
        project_id: GitLab project ID or path
        mr_iid: Merge request IID
    """
    return await approve_merge_request(project_id, mr_iid, ctx)


@conditional_tool("gitlab_get_merge_request_diffs")
async def gitlab_get_merge_request_diffs(
    project_id: str,
    mr_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get diffs for a specific merge request.

    Returns the changes introduced by the merge request, showing additions and
    deletions for each modified file.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        mr_iid: Merge request IID (project-scoped ID)
    """
    return await get_merge_request_diffs(project_id, mr_iid, ctx)


@conditional_tool("gitlab_list_merge_request_diffs")
async def gitlab_list_merge_request_diffs(
    project_id: str,
    mr_iid: int,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List diffs for a merge request with pagination.

    Returns the changes introduced by the merge request with pagination support
    for large merge requests.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        mr_iid: Merge request IID (project-scoped ID)
        page: Page number for pagination
        per_page: Number of diffs per page (max 100)
    """
    return await list_merge_request_diffs(project_id, mr_iid, page, per_page, ctx)


@conditional_tool("gitlab_get_branch_diffs")
async def gitlab_get_branch_diffs(
    project_id: str,
    from_branch: str,
    to_branch: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get diffs between two branches.

    Compares two branches and returns the changes, showing what would be merged
    if from_branch was merged into to_branch.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        from_branch: Source branch name
        to_branch: Target branch name
    """
    return await get_branch_diffs(project_id, from_branch, to_branch, ctx)


# Register repository tools
@conditional_tool("gitlab_get_file_contents")
async def gitlab_get_file_contents(
    project_id: str,
    file_path: str,
    ref: str = "main",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get file contents from a GitLab repository.

    Args:
        project_id: GitLab project ID or namespace/project path
        file_path: Path to file in repository
        ref: Branch, tag, or commit SHA (defaults to 'main')
    """
    return await get_file_contents(project_id, file_path, ref, ctx)


@conditional_tool("gitlab_create_or_update_file")
async def gitlab_create_or_update_file(
    project_id: str,
    file_path: str,
    content: str,
    branch: str,
    commit_message: str,
    encoding: str = "text",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create or update a file in a GitLab repository.

    Args:
        project_id: GitLab project ID or namespace/project path
        file_path: Path to file in repository
        content: File content (text or base64 encoded)
        branch: Branch name to commit to
        commit_message: Commit message for the change
        encoding: Content encoding ('text' or 'base64', defaults to 'text')
    """
    return await create_or_update_file(
        project_id, file_path, content, branch, commit_message, encoding, ctx
    )


@conditional_tool("gitlab_delete_file")
async def gitlab_delete_file(
    project_id: str,
    file_path: str,
    branch: str,
    commit_message: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a file from a GitLab repository.

    Args:
        project_id: GitLab project ID or namespace/project path
        file_path: Path to file in repository
        branch: Branch name to commit deletion to
        commit_message: Commit message for the deletion
    """
    return await delete_file(project_id, file_path, branch, commit_message, ctx)


@conditional_tool("gitlab_get_repository_tree")
async def gitlab_get_repository_tree(
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
    """
    return await get_repository_tree(project_id, path, ref, recursive, ctx)


# Register branch tools
@conditional_tool("gitlab_list_branches")
async def gitlab_list_branches(
    project_id: str,
    search: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all branches in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        search: Optional search string to filter branches
    """
    return await list_branches(project_id, search, ctx)


@conditional_tool("gitlab_create_branch")
async def gitlab_create_branch(
    project_id: str,
    branch: str,
    ref: str = "main",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new branch in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        branch: Name for the new branch
        ref: Source branch/commit for new branch (defaults to 'main')
    """
    return await create_branch(project_id, branch, ref, ctx)


@conditional_tool("gitlab_delete_branch")
async def gitlab_delete_branch(
    project_id: str,
    branch: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a branch from a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        branch: Name of the branch to delete
    """
    return await delete_branch(project_id, branch, ctx)


# Register commit tools
@conditional_tool("gitlab_list_commits")
async def gitlab_list_commits(
    project_id: str,
    ref_name: str | None = None,
    since: str | None = None,
    until: str | None = None,
    path: str | None = None,
    all: bool = False,
    with_stats: bool = False,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List commits in a GitLab repository.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        ref_name: Branch, tag, or commit SHA to list commits from
        since: Only commits after this date (ISO 8601 format)
        until: Only commits before this date (ISO 8601 format)
        path: File path to filter commits that modified this path
        all: Retrieve all commits (default: False)
        with_stats: Include commit stats (additions, deletions, total)
        page: Page number for pagination
        per_page: Number of commits per page (max 100)
    """
    return await list_commits(
        project_id, ref_name, since, until, path, all, with_stats, page, per_page, ctx
    )


@conditional_tool("gitlab_get_commit")
async def gitlab_get_commit(
    project_id: str,
    commit_sha: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific commit in a GitLab repository.

    Returns detailed information including author, committer, message, stats, and pipeline info.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        commit_sha: Commit SHA, branch name, or tag name
    """
    return await get_commit(project_id, commit_sha, ctx)


@conditional_tool("gitlab_get_commit_diff")
async def gitlab_get_commit_diff(
    project_id: str,
    commit_sha: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get the diff for a specific commit in a GitLab repository.

    Returns the changes introduced by the commit, showing additions and deletions
    for each modified file.

    Args:
        project_id: Project ID or path (e.g., "gitlab-org/gitlab" or "123")
        commit_sha: Commit SHA, branch name, or tag name
    """
    return await get_commit_diff(project_id, commit_sha, ctx)


# Register pipeline tools
@conditional_tool("gitlab_list_pipelines")
async def gitlab_list_pipelines(
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
    """
    return await list_pipelines(project_id, ref, status, ctx)


@conditional_tool("gitlab_get_pipeline")
async def gitlab_get_pipeline(
    project_id: str,
    pipeline_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get details of a specific pipeline in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        pipeline_id: Pipeline ID
    """
    return await get_pipeline(project_id, pipeline_id, ctx)


@conditional_tool("gitlab_create_pipeline")
async def gitlab_create_pipeline(
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
    """
    return await create_pipeline(project_id, ref, variables, ctx)


@conditional_tool("gitlab_retry_pipeline")
async def gitlab_retry_pipeline(
    project_id: str,
    pipeline_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Retry a failed pipeline in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        pipeline_id: Pipeline ID to retry
    """
    return await retry_pipeline(project_id, pipeline_id, ctx)


@conditional_tool("gitlab_cancel_pipeline")
async def gitlab_cancel_pipeline(
    project_id: str,
    pipeline_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Cancel a running pipeline in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        pipeline_id: Pipeline ID to cancel
    """
    return await cancel_pipeline(project_id, pipeline_id, ctx)


@conditional_tool("gitlab_list_pipeline_jobs")
async def gitlab_list_pipeline_jobs(
    project_id: str,
    pipeline_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all jobs in a pipeline.

    Args:
        project_id: GitLab project ID or namespace/project path
        pipeline_id: Pipeline ID
    """
    return await list_pipeline_jobs(project_id, pipeline_id, ctx)


@conditional_tool("gitlab_get_pipeline_job_log")
async def gitlab_get_pipeline_job_log(
    project_id: str,
    job_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get log output from a pipeline job.

    Args:
        project_id: GitLab project ID or namespace/project path
        job_id: Job ID
    """
    return await get_pipeline_job_log(project_id, job_id, ctx)


# Register wiki tools
@conditional_tool("gitlab_list_wiki_pages")
async def gitlab_list_wiki_pages(
    project_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all wiki pages in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
    """
    return await list_wiki_pages(project_id, ctx)


@conditional_tool("gitlab_get_wiki_page")
async def gitlab_get_wiki_page(
    project_id: str,
    slug: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific wiki page from a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        slug: Wiki page slug (URL-friendly identifier)
    """
    return await get_wiki_page(project_id, slug, ctx)


@conditional_tool("gitlab_create_wiki_page")
async def gitlab_create_wiki_page(
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
    """
    return await create_wiki_page(project_id, title, content, format, ctx)


@conditional_tool("gitlab_update_wiki_page")
async def gitlab_update_wiki_page(
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
    """
    return await update_wiki_page(project_id, slug, title, content, format, ctx)


@conditional_tool("gitlab_delete_wiki_page")
async def gitlab_delete_wiki_page(
    project_id: str,
    slug: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a wiki page from a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        slug: Wiki page slug (URL-friendly identifier)
    """
    return await delete_wiki_page(project_id, slug, ctx)


@conditional_tool("gitlab_list_wiki_attachments")
async def gitlab_list_wiki_attachments(
    project_id: str,
    slug: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List attachments for a wiki page in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        slug: Wiki page slug (URL-friendly identifier)
    """
    return await list_wiki_attachments(project_id, slug, ctx)


@conditional_tool("gitlab_upload_wiki_attachment")
async def gitlab_upload_wiki_attachment(
    project_id: str,
    filename: str,
    filepath: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Upload an attachment to a GitLab project for use in wiki pages.

    Args:
        project_id: GitLab project ID or namespace/project path
        filename: Name of the file to upload
        filepath: Local path to the file to upload
    """
    return await upload_wiki_attachment(project_id, filename, filepath, ctx)


# Register milestone tools
@conditional_tool("gitlab_list_milestones")
async def gitlab_list_milestones(
    project_id: str,
    state: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all milestones in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        state: Optional milestone state to filter by (active, closed)
    """
    return await list_milestones(project_id, state, ctx)


@conditional_tool("gitlab_get_milestone")
async def gitlab_get_milestone(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get a specific milestone by ID.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID to retrieve
    """
    return await get_milestone(project_id, milestone_id, ctx)


@conditional_tool("gitlab_create_milestone")
async def gitlab_create_milestone(
    project_id: str,
    title: str,
    description: str | None = None,
    due_date: str | None = None,
    start_date: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new milestone in a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        title: Milestone title
        description: Optional milestone description
        due_date: Optional due date in YYYY-MM-DD format
        start_date: Optional start date in YYYY-MM-DD format
    """
    return await create_milestone(project_id, title, description, due_date, start_date, ctx)


@conditional_tool("gitlab_update_milestone")
async def gitlab_update_milestone(
    project_id: str,
    milestone_id: int,
    title: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
    start_date: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update an existing milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID to update
        title: Optional new milestone title
        description: Optional new milestone description
        due_date: Optional new due date in YYYY-MM-DD format
        start_date: Optional new start date in YYYY-MM-DD format
    """
    return await update_milestone(
        project_id, milestone_id, title, description, due_date, start_date, ctx
    )


@conditional_tool("gitlab_close_milestone")
async def gitlab_close_milestone(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Close/archive a milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID to close
    """
    return await close_milestone(project_id, milestone_id, ctx)


@conditional_tool("gitlab_list_milestone_issues")
async def gitlab_list_milestone_issues(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all issues in a milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID to query
    """
    return await list_milestone_issues(project_id, milestone_id, ctx)


@conditional_tool("gitlab_list_milestone_merge_requests")
async def gitlab_list_milestone_merge_requests(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List all merge requests in a milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID to query
    """
    return await list_milestone_merge_requests(project_id, milestone_id, ctx)


@conditional_tool("gitlab_add_issue_to_milestone")
async def gitlab_add_issue_to_milestone(
    project_id: str,
    issue_iid: int,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Assign an issue to a milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (project-scoped issue number)
        milestone_id: Milestone ID to assign to
    """
    return await add_issue_to_milestone(project_id, issue_iid, milestone_id, ctx)


@conditional_tool("gitlab_remove_issue_from_milestone")
async def gitlab_remove_issue_from_milestone(
    project_id: str,
    issue_iid: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Remove an issue from its milestone.

    Args:
        project_id: GitLab project ID or namespace/project path
        issue_iid: Issue IID (project-scoped issue number)
    """
    return await remove_issue_from_milestone(project_id, issue_iid, ctx)


@conditional_tool("gitlab_get_milestone_burndown")
async def gitlab_get_milestone_burndown(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Get milestone burndown chart data and statistics.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID to query
    """
    return await get_milestone_burndown(project_id, milestone_id, ctx)


@conditional_tool("gitlab_delete_milestone")
async def gitlab_delete_milestone(
    project_id: str,
    milestone_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a milestone from a GitLab project.

    Args:
        project_id: GitLab project ID or namespace/project path
        milestone_id: Milestone ID to delete
    """
    return await delete_milestone(project_id, milestone_id, ctx)


# Register project creation/management tools
@conditional_tool("gitlab_create_project")
async def gitlab_create_project(
    name: str,
    description: str | None = None,
    visibility: str = "private",
    initialize_with_readme: bool = False,
    namespace_id: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new GitLab project.

    Args:
        name: Project name (required)
        description: Project description
        visibility: Project visibility ('private', 'internal', 'public')
        initialize_with_readme: Initialize project with README file
        namespace_id: Namespace ID (group or user namespace) to create project in
    """
    return await create_project(
        name, description, visibility, initialize_with_readme, namespace_id, ctx
    )


@conditional_tool("gitlab_fork_project")
async def gitlab_fork_project(
    project_id: str,
    namespace_id: int | None = None,
    name: str | None = None,
    path: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Fork a GitLab project to your account or specified namespace.

    Args:
        project_id: Source project ID or path to fork
        namespace_id: Target namespace ID (group or user) for the fork
        name: Name for the forked project (defaults to original name)
        path: Path for the forked project (defaults to original path)
    """
    return await fork_project(project_id, namespace_id, name, path, ctx)


@conditional_tool("gitlab_push_files")
async def gitlab_push_files(
    project_id: str,
    branch: str,
    commit_message: str,
    actions: list[dict[str, Any]],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Push multiple files to a GitLab project in a single commit.

    This allows creating, updating, or deleting multiple files atomically.

    Args:
        project_id: Project ID or path
        branch: Branch name to commit to
        commit_message: Commit message
        actions: List of file actions, each with:
            - action: 'create', 'update', 'delete', or 'move'
            - file_path: Path to the file
            - content: File content (for create/update, base64 encoded if binary)
            - encoding: 'text' or 'base64' (optional, default: 'text')
            - previous_path: Previous path (for move action)
    """
    return await push_files(project_id, branch, commit_message, actions, ctx)


# Register label CRUD tools
@conditional_tool("gitlab_create_label")
async def gitlab_create_label(
    project_id: str,
    name: str,
    color: str,
    description: str | None = None,
    priority: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a new label in a GitLab project.

    Args:
        project_id: Project ID or path
        name: Label name (required)
        color: Label color in hex format (e.g., '#FF0000')
        description: Label description
        priority: Label priority (integer)
    """
    return await create_label(project_id, name, color, description, priority, ctx)


@conditional_tool("gitlab_update_label")
async def gitlab_update_label(
    project_id: str,
    label_name: str,
    new_name: str | None = None,
    color: str | None = None,
    description: str | None = None,
    priority: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update an existing label in a GitLab project.

    Args:
        project_id: Project ID or path
        label_name: Current label name (required for identification)
        new_name: New label name (optional)
        color: New label color in hex format (e.g., '#FF0000')
        description: New label description
        priority: New label priority (integer)
    """
    return await update_label(project_id, label_name, new_name, color, description, priority, ctx)


@conditional_tool("gitlab_delete_label")
async def gitlab_delete_label(
    project_id: str,
    label_name: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a label from a GitLab project.

    Args:
        project_id: Project ID or path
        label_name: Label name to delete
    """
    return await delete_label(project_id, label_name, ctx)


# Register issue link CRUD tools
@conditional_tool("gitlab_create_issue_link")
async def gitlab_create_issue_link(
    project_id: str,
    issue_iid: int,
    target_project_id: str,
    target_issue_iid: int,
    link_type: str = "relates_to",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a link between two issues in GitLab.

    Args:
        project_id: Source project ID or path
        issue_iid: Source issue IID (internal ID)
        target_project_id: Target project ID or path
        target_issue_iid: Target issue IID
        link_type: Type of link ('relates_to', 'blocks', 'is_blocked_by')
    """
    return await create_issue_link(
        project_id, issue_iid, target_project_id, target_issue_iid, link_type, ctx
    )


@conditional_tool("gitlab_delete_issue_link")
async def gitlab_delete_issue_link(
    project_id: str,
    issue_iid: int,
    link_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a link between two issues in GitLab.

    Args:
        project_id: Source project ID or path
        issue_iid: Source issue IID (internal ID)
        link_id: Issue link ID to delete
    """
    return await delete_issue_link(project_id, issue_iid, link_id, ctx)


# Register draft note CRUD tools
@conditional_tool("gitlab_create_draft_note")
async def gitlab_create_draft_note(
    project_id: str,
    mr_iid: int,
    note: str,
    position: dict[str, Any] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Create a draft note (unpublished comment) on a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        note: Draft note content
        position: Position info for inline comments (optional)
    """
    return await create_draft_note(project_id, mr_iid, note, position, ctx)


@conditional_tool("gitlab_update_draft_note")
async def gitlab_update_draft_note(
    project_id: str,
    mr_iid: int,
    draft_note_id: int,
    note: str | None = None,
    position: dict[str, Any] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update a draft note (unpublished comment) on a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        draft_note_id: Draft note ID
        note: New draft note content
        position: New position info for inline comments (optional)
    """
    return await update_draft_note(project_id, mr_iid, draft_note_id, note, position, ctx)


@conditional_tool("gitlab_delete_draft_note")
async def gitlab_delete_draft_note(
    project_id: str,
    mr_iid: int,
    draft_note_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a draft note (unpublished comment) from a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        draft_note_id: Draft note ID to delete
    """
    return await delete_draft_note(project_id, mr_iid, draft_note_id, ctx)


@conditional_tool("gitlab_publish_draft_note")
async def gitlab_publish_draft_note(
    project_id: str,
    mr_iid: int,
    draft_note_id: int,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Publish a draft note (convert it to a regular comment).

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        draft_note_id: Draft note ID to publish
    """
    return await publish_draft_note(project_id, mr_iid, draft_note_id, ctx)


# Register MR/issue update tools
@conditional_tool("gitlab_update_merge_request")
async def gitlab_update_merge_request(
    project_id: str,
    mr_iid: int,
    title: str | None = None,
    description: str | None = None,
    state_event: str | None = None,
    target_branch: str | None = None,
    assignee_ids: list[int] | None = None,
    reviewer_ids: list[int] | None = None,
    labels: list[str] | None = None,
    milestone_id: int | None = None,
    remove_source_branch: bool | None = None,
    squash: bool | None = None,
    draft: bool | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update a merge request in GitLab.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        title: New merge request title
        description: New merge request description
        state_event: State change ('close', 'reopen', 'merge')
        target_branch: New target branch
        assignee_ids: List of assignee user IDs
        reviewer_ids: List of reviewer user IDs
        labels: List of label names
        milestone_id: Milestone ID
        remove_source_branch: Remove source branch after merge
        squash: Squash commits when merging
        draft: Mark as draft/WIP
    """
    return await update_merge_request(
        project_id,
        mr_iid,
        title,
        description,
        state_event,
        target_branch,
        assignee_ids,
        reviewer_ids,
        labels,
        milestone_id,
        remove_source_branch,
        squash,
        draft,
        ctx,
    )


@conditional_tool("gitlab_update_issue_note")
async def gitlab_update_issue_note(
    project_id: str,
    issue_iid: int,
    note_id: int,
    body: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Update a note/comment on an issue in GitLab.

    Args:
        project_id: Project ID or path
        issue_iid: Issue IID (internal ID)
        note_id: Note ID to update
        body: New note content
    """
    return await update_issue_note(project_id, issue_iid, note_id, body, ctx)


@conditional_tool("gitlab_list_merge_request_discussions")
async def gitlab_list_merge_request_discussions(
    project_id: str,
    mr_iid: int,
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List discussions (comment threads) on a merge request.

    Args:
        project_id: Project ID or path
        mr_iid: Merge request IID (internal ID)
        page: Page number for pagination (default: 1)
        per_page: Number of discussions per page (default: 20, max: 100)
    """
    return await list_merge_request_discussions(project_id, mr_iid, page, per_page, ctx)


# Register specialized query tools
@conditional_tool("gitlab_my_issues")
async def gitlab_my_issues(
    state: str = "opened",
    labels: str | None = None,
    milestone: str | None = None,
    order_by: str = "created_at",
    sort: str = "desc",
    page: int = 1,
    per_page: int = 20,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """List issues assigned to the authenticated user across all projects.

    Args:
        state: Issue state ('opened', 'closed', or 'all')
        labels: Comma-separated label names to filter by
        milestone: Milestone title to filter by
        order_by: Order by field ('created_at', 'updated_at', 'priority', 'due_date')
        sort: Sort order ('asc' or 'desc')
        page: Page number for pagination (default: 1)
        per_page: Number of issues per page (default: 20, max: 100)
    """
    return await my_issues(state, labels, milestone, order_by, sort, page, per_page, ctx)
