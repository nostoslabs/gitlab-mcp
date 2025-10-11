"""Wiki tools for GitLab MCP server."""

from .create_wiki_page import create_wiki_page
from .delete_wiki_page import delete_wiki_page
from .get_wiki_page import get_wiki_page
from .list_wiki_attachments import list_wiki_attachments
from .list_wiki_pages import list_wiki_pages
from .update_wiki_page import update_wiki_page
from .upload_wiki_attachment import upload_wiki_attachment

__all__ = [
    "list_wiki_pages",
    "get_wiki_page",
    "create_wiki_page",
    "update_wiki_page",
    "delete_wiki_page",
    "list_wiki_attachments",
    "upload_wiki_attachment",
]
