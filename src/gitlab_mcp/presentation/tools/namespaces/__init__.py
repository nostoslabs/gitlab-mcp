"""Namespaces tools for GitLab MCP server."""

from .get_namespace import get_namespace
from .list_namespaces import list_namespaces
from .verify_namespace import verify_namespace

__all__ = ["get_namespace", "list_namespaces", "verify_namespace"]
