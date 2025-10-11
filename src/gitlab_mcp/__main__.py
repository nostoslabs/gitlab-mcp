"""Entry point for GitLab MCP server."""

from gitlab_mcp.server import mcp


def main() -> None:
    """Run the GitLab MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
