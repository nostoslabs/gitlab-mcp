"""GitLab MCP Server configuration using Pydantic Settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitLabSettings(BaseSettings):
    """GitLab MCP Server settings loaded from environment variables.

    All settings are loaded from environment variables. Required fields will
    raise a ValidationError if not provided.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allow case-insensitive env var matching (GITLAB_* -> gitlab_*)
        extra="ignore",
        env_ignore_empty=True,
    )

    # Multi-tenant mode (NEW)
    multi_tenant_mode: bool = Field(
        default=False,
        description="Enable multi-tenant mode (users provide tokens via headers)",
    )

    # Authentication - Required in single-tenant, optional in multi-tenant
    gitlab_personal_access_token: str | None = Field(
        default=None,
        description="GitLab personal access token (required in single-tenant mode)",
    )

    # API configuration
    gitlab_api_url: str = Field(
        default="https://gitlab.com",
        description="GitLab API base URL (without /api/v4, python-gitlab adds it automatically)",
    )

    # Project control
    gitlab_project_id: str | None = Field(
        default=None,
        description="Default GitLab project ID",
    )

    gitlab_allowed_project_ids: list[str] | None = Field(
        default=None,
        description="Comma-separated list of allowed project IDs",
    )

    # Security settings
    gitlab_read_only_mode: bool = Field(
        default=False,
        description="Enable read-only mode to prevent write operations",
    )

    gitlab_denied_tools_regex: str | None = Field(
        default=None,
        description="Regular expression pattern to deny specific tools",
    )

    # Feature flags
    use_gitlab_wiki: bool = Field(
        default=True,
        description="Enable GitLab wiki functionality",
    )

    use_milestone: bool = Field(
        default=True,
        description="Enable milestone functionality",
    )

    use_pipeline: bool = Field(
        default=True,
        description="Enable pipeline functionality",
    )

    # Transport configuration
    sse: bool = Field(
        default=False,
        description="Enable Server-Sent Events transport",
    )

    streamable_http: bool = Field(
        default=False,
        description="Enable streamable HTTP transport",
    )

    host: str = Field(
        default="localhost",
        description="Server host address",
    )

    port: int = Field(
        default=3000,
        description="Server port number",
    )

    # Proxy configuration
    http_proxy: str | None = Field(
        default=None,
        description="HTTP proxy URL",
    )

    https_proxy: str | None = Field(
        default=None,
        description="HTTPS proxy URL",
    )

    no_proxy: str | None = Field(
        default=None,
        description="Comma-separated list of hosts to bypass proxy",
    )

    # Authentication
    gitlab_auth_cookie_path: str | None = Field(
        default=None,
        description="Path to GitLab authentication cookie file",
    )

    # Pagination
    gitlab_commit_files_per_page: int = Field(
        default=20,
        description="Number of commit files to fetch per page",
    )

    @field_validator("gitlab_allowed_project_ids", mode="before")
    @classmethod
    def parse_allowed_project_ids(cls, v: str | None) -> list[str] | None:
        """Parse comma-separated project IDs into a list.

        Args:
            v: Comma-separated string of project IDs or None

        Returns:
            List of project ID strings or None if input is None
        """
        if v is None or v == "":
            return None
        return [project_id.strip() for project_id in v.split(",")]
