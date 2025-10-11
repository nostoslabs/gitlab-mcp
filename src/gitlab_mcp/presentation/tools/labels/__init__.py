"""Labels tools for GitLab MCP server."""

from .create_label import create_label
from .delete_label import delete_label
from .get_label import get_label
from .list_labels import list_labels
from .update_label import update_label

__all__ = [
    "create_label",
    "delete_label",
    "get_label",
    "list_labels",
    "update_label",
]
