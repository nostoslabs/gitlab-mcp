"""Merge request tools for GitLab MCP server."""

from .approve_merge_request import approve_merge_request
from .create_merge_request import create_merge_request
from .get_branch_diffs import get_branch_diffs
from .get_merge_request import get_merge_request
from .get_merge_request_diffs import get_merge_request_diffs
from .list_merge_request_diffs import list_merge_request_diffs
from .list_merge_requests import list_merge_requests
from .merge_merge_request import merge_merge_request
from .update_merge_request import update_merge_request

__all__ = [
    "approve_merge_request",
    "create_merge_request",
    "get_branch_diffs",
    "get_merge_request",
    "get_merge_request_diffs",
    "list_merge_request_diffs",
    "list_merge_requests",
    "merge_merge_request",
    "update_merge_request",
]
