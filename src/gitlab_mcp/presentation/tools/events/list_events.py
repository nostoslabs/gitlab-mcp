"""List events for the authenticated user."""

import asyncio
from typing import Any

from fastmcp import Context
from gitlab_mcp.presentation.tools.common.helpers import get_user_context
from gitlab_mcp.services.gitlab_client_factory import GitLabClientFactory

# Module-level instances (will be injected by server)
client_factory = GitLabClientFactory()


async def list_events(
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

    Returns activity feed including:
    - Push events
    - Issue events (opened, closed, commented)
    - Merge request events
    - Comment events
    - Project events
    - Wiki events

    Args:
         action: Filter events by action (e.g., created, updated, closed, pushed, commented)
         target_type: Filter events by target type (e.g., issue, milestone, merge_request)
        before: Filter events before this date (ISO 8601 format: YYYY-MM-DD)
        after: Filter events after this date (ISO 8601 format: YYYY-MM-DD)
        sort: Sort order (asc or desc, default: desc)
        page: Page number for pagination (default: 1)
        per_page: Number of events per page (default: 20, max: 100)
        ctx: FastMCP context for multi-tenant support

    Returns:
        Dictionary containing:
        - events: List of event objects
        - total_results: Total number of events returned

    Example:
        >>> events = await list_events(action="pushed", per_page=10)
        >>> events = await list_events(target_type="issue", after="2024-01-01")
        >>> events = await list_events(before="2024-12-31", sort="asc")
    """

    def _sync_list_events() -> dict[str, Any]:
        user_ctx = get_user_context(ctx)
        gl = client_factory.get_client(user_ctx)

        # Build filter parameters
        kwargs: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if action:
            kwargs["action"] = action
        if target_type:
            kwargs["target_type"] = target_type
        if before:
            kwargs["before"] = before
        if after:
            kwargs["after"] = after
        if sort:
            kwargs["sort"] = sort

        # Get events for the authenticated user
        events_list = gl.events.list(**kwargs)

        # Serialize events
        events = []
        for event in events_list:
            event_data = {
                "id": event.id,
                "action_name": getattr(event, "action_name", None),
                "target_type": getattr(event, "target_type", None),
                "target_id": getattr(event, "target_id", None),
                "target_iid": getattr(event, "target_iid", None),
                "target_title": getattr(event, "target_title", None),
                "created_at": getattr(event, "created_at", None),
                "author": {},
                "project_id": getattr(event, "project_id", None),
                "push_data": None,
            }

            # Add author information
            if hasattr(event, "author") and event.author:
                event_data["author"] = {
                    "id": getattr(event.author, "id", None),
                    "username": getattr(event.author, "username", None),
                    "name": getattr(event.author, "name", None),
                    "avatar_url": getattr(event.author, "avatar_url", None),
                    "web_url": getattr(event.author, "web_url", None),
                }

            # Add push data if available
            if hasattr(event, "push_data") and event.push_data:
                event_data["push_data"] = {
                    "commit_count": getattr(event.push_data, "commit_count", None),
                    "action": getattr(event.push_data, "action", None),
                    "ref_type": getattr(event.push_data, "ref_type", None),
                    "commit_from": getattr(event.push_data, "commit_from", None),
                    "commit_to": getattr(event.push_data, "commit_to", None),
                    "ref": getattr(event.push_data, "ref", None),
                }

            # Add note data if available (for comment events)
            if hasattr(event, "note") and event.note:
                event_data["note"] = {
                    "id": getattr(event.note, "id", None),
                    "body": getattr(event.note, "body", None),
                    "noteable_type": getattr(event.note, "noteable_type", None),
                    "noteable_id": getattr(event.note, "noteable_id", None),
                }

            events.append(event_data)

        return {
            "events": events,
            "total_results": len(events),
        }

    return await asyncio.to_thread(_sync_list_events)
