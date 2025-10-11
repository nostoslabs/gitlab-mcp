"""Tests for GitLab Settings configuration."""

import pytest


class TestGitLabSettings:
    """Test suite for GitLab Settings using Pydantic."""

    def test_settings_token_optional_in_multi_tenant_mode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that GITLAB_PERSONAL_ACCESS_TOKEN is optional in multi-tenant mode."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        # Clear token and enable multi-tenant mode
        monkeypatch.delenv("GITLAB_PERSONAL_ACCESS_TOKEN", raising=False)
        monkeypatch.setenv("MULTI_TENANT_MODE", "true")

        # Should not raise - token is optional in multi-tenant mode
        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.multi_tenant_mode is True
        assert settings.gitlab_personal_access_token is None

    def test_settings_multi_tenant_mode_defaults_to_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that multi_tenant_mode defaults to False."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.multi_tenant_mode is False

    def test_settings_single_tenant_mode_with_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test single-tenant mode works with token (backward compatibility)."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        test_token = "glpat-test-token-123"
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", test_token)
        monkeypatch.setenv("MULTI_TENANT_MODE", "false")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.multi_tenant_mode is False
        assert settings.gitlab_personal_access_token == test_token

    def test_settings_loads_required_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads GITLAB_PERSONAL_ACCESS_TOKEN from environment."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        test_token = "glpat-test-token-123"
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", test_token)

        settings = GitLabSettings()
        assert settings.gitlab_personal_access_token == test_token

    def test_settings_uses_default_api_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that GITLAB_API_URL defaults to https://gitlab.com (python-gitlab adds /api/v4)."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_api_url == "https://gitlab.com"

    def test_settings_loads_custom_api_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads custom GITLAB_API_URL from environment."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        custom_url = "https://gitlab.example.com/api/v4"
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("GITLAB_API_URL", custom_url)

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_api_url == custom_url

    def test_settings_loads_project_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads GITLAB_PROJECT_ID as optional field."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("GITLAB_PROJECT_ID", "123")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_project_id == "123"

    def test_settings_project_id_is_optional(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that GITLAB_PROJECT_ID is optional."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_project_id is None

    def test_settings_loads_allowed_project_ids(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads GITLAB_ALLOWED_PROJECT_IDS as comma-separated list."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("GITLAB_ALLOWED_PROJECT_IDS", "123,456,789")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_allowed_project_ids == ["123", "456", "789"]

    def test_settings_allowed_project_ids_is_optional(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that GITLAB_ALLOWED_PROJECT_IDS is optional."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_allowed_project_ids is None

    def test_settings_loads_read_only_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads GITLAB_READ_ONLY_MODE boolean flag."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("GITLAB_READ_ONLY_MODE", "true")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_read_only_mode is True

    def test_settings_read_only_mode_defaults_to_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that GITLAB_READ_ONLY_MODE defaults to False."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_read_only_mode is False

    def test_settings_loads_denied_tools_regex(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads GITLAB_DENIED_TOOLS_REGEX pattern."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        regex_pattern = r"^(delete|remove).*"
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("GITLAB_DENIED_TOOLS_REGEX", regex_pattern)

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_denied_tools_regex == regex_pattern

    def test_settings_denied_tools_regex_is_optional(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that GITLAB_DENIED_TOOLS_REGEX is optional."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_denied_tools_regex is None

    def test_settings_loads_feature_flags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads feature flags (wiki, milestone, pipeline)."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("USE_GITLAB_WIKI", "true")
        monkeypatch.setenv("USE_MILESTONE", "false")
        monkeypatch.setenv("USE_PIPELINE", "true")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.use_gitlab_wiki is True
        assert settings.use_milestone is False
        assert settings.use_pipeline is True

    def test_settings_feature_flags_default_to_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that feature flags default to True when not set."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.use_gitlab_wiki is True
        assert settings.use_milestone is True
        assert settings.use_pipeline is True

    def test_settings_loads_transport_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads transport configuration (SSE, HTTP, host, port)."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("SSE", "true")
        monkeypatch.setenv("STREAMABLE_HTTP", "false")
        monkeypatch.setenv("HOST", "0.0.0.0")
        monkeypatch.setenv("PORT", "8080")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.sse is True
        assert settings.streamable_http is False
        assert settings.host == "0.0.0.0"
        assert settings.port == 8080

    def test_settings_transport_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that transport settings have sensible defaults."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.sse is False
        assert settings.streamable_http is False
        assert settings.host == "localhost"
        assert settings.port == 3000

    def test_settings_loads_proxy_configuration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads proxy configuration."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.com:8080")
        monkeypatch.setenv("HTTPS_PROXY", "https://proxy.example.com:8443")
        monkeypatch.setenv("NO_PROXY", "localhost,127.0.0.1")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.http_proxy == "http://proxy.example.com:8080"
        assert settings.https_proxy == "https://proxy.example.com:8443"
        assert settings.no_proxy == "localhost,127.0.0.1"

    def test_settings_proxy_is_optional(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that proxy settings are optional."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.http_proxy is None
        assert settings.https_proxy is None
        assert settings.no_proxy is None

    def test_settings_loads_auth_cookie_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads GITLAB_AUTH_COOKIE_PATH."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        cookie_path = "/path/to/cookies.txt"
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("GITLAB_AUTH_COOKIE_PATH", cookie_path)

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_auth_cookie_path == cookie_path

    def test_settings_auth_cookie_path_is_optional(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that GITLAB_AUTH_COOKIE_PATH is optional."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_auth_cookie_path is None

    def test_settings_loads_commit_files_per_page(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that settings loads GITLAB_COMMIT_FILES_PER_PAGE with default 20."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("GITLAB_COMMIT_FILES_PER_PAGE", "50")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_commit_files_per_page == 50

    def test_settings_commit_files_per_page_defaults_to_20(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that GITLAB_COMMIT_FILES_PER_PAGE defaults to 20."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "test-token")

        settings = GitLabSettings(_env_file=None)  # type: ignore
        assert settings.gitlab_commit_files_per_page == 20

    def test_settings_validates_all_fields_together(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that all settings can be loaded together."""
        from gitlab_mcp.infrastructure.config.settings import GitLabSettings

        # Set all environment variables
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "glpat-test-token")
        monkeypatch.setenv("GITLAB_API_URL", "https://gitlab.example.com/api/v4")
        monkeypatch.setenv("GITLAB_PROJECT_ID", "42")
        monkeypatch.setenv("GITLAB_ALLOWED_PROJECT_IDS", "1,2,3")
        monkeypatch.setenv("GITLAB_READ_ONLY_MODE", "true")
        monkeypatch.setenv("GITLAB_DENIED_TOOLS_REGEX", r"^delete.*")
        monkeypatch.setenv("USE_GITLAB_WIKI", "false")
        monkeypatch.setenv("USE_MILESTONE", "true")
        monkeypatch.setenv("USE_PIPELINE", "false")
        monkeypatch.setenv("SSE", "true")
        monkeypatch.setenv("STREAMABLE_HTTP", "true")
        monkeypatch.setenv("HOST", "0.0.0.0")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("HTTP_PROXY", "http://proxy:8080")
        monkeypatch.setenv("HTTPS_PROXY", "https://proxy:8443")
        monkeypatch.setenv("NO_PROXY", "localhost")
        monkeypatch.setenv("GITLAB_AUTH_COOKIE_PATH", "/cookies.txt")
        monkeypatch.setenv("GITLAB_COMMIT_FILES_PER_PAGE", "100")

        settings = GitLabSettings(_env_file=None)  # type: ignore

        # Verify all settings are loaded correctly
        assert settings.gitlab_personal_access_token == "glpat-test-token"
        assert settings.gitlab_api_url == "https://gitlab.example.com/api/v4"
        assert settings.gitlab_project_id == "42"
        assert settings.gitlab_allowed_project_ids == ["1", "2", "3"]
        assert settings.gitlab_read_only_mode is True
        assert settings.gitlab_denied_tools_regex == r"^delete.*"
        assert settings.use_gitlab_wiki is False
        assert settings.use_milestone is True
        assert settings.use_pipeline is False
        assert settings.sse is True
        assert settings.streamable_http is True
        assert settings.host == "0.0.0.0"
        assert settings.port == 9000
        assert settings.http_proxy == "http://proxy:8080"
        assert settings.https_proxy == "https://proxy:8443"
        assert settings.no_proxy == "localhost"
        assert settings.gitlab_auth_cookie_path == "/cookies.txt"
        assert settings.gitlab_commit_files_per_page == 100
