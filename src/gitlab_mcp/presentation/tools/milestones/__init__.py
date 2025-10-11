"""Milestone management tools for GitLab MCP."""

from .add_issue_to_milestone import add_issue_to_milestone
from .close_milestone import close_milestone
from .create_milestone import create_milestone
from .delete_milestone import delete_milestone
from .get_milestone import get_milestone
from .get_milestone_burndown import get_milestone_burndown
from .list_milestone_issues import list_milestone_issues
from .list_milestone_merge_requests import list_milestone_merge_requests
from .list_milestones import list_milestones
from .remove_issue_from_milestone import remove_issue_from_milestone
from .update_milestone import update_milestone

__all__ = [
    "add_issue_to_milestone",
    "close_milestone",
    "create_milestone",
    "delete_milestone",
    "get_milestone",
    "get_milestone_burndown",
    "list_milestone_issues",
    "list_milestone_merge_requests",
    "list_milestones",
    "remove_issue_from_milestone",
    "update_milestone",
]
