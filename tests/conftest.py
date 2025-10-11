"""Shared test fixtures and configuration."""

import pytest


@pytest.fixture
def gitlab_api_base_url() -> str:
    """GitLab API base URL for tests."""
    return "https://gitlab.com/api/v4"
