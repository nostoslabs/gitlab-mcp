"""Discussions tools for GitLab MCP server."""

from .create_issue_note import create_issue_note
from .create_merge_request_note import create_merge_request_note
from .list_issue_discussions import list_issue_discussions
from .list_merge_request_discussions import list_merge_request_discussions
from .update_issue_note import update_issue_note

__all__ = [
    "create_issue_note",
    "create_merge_request_note",
    "list_issue_discussions",
    "list_merge_request_discussions",
    "update_issue_note",
]
