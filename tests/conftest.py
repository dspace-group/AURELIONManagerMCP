"""Shared test fixtures for AURELION Manager MCP server tests."""

import pytest

from aurelion_manager_mcp import client, versioning


@pytest.fixture(autouse=True)
def _clear_version_cache():
    versioning.clear_version_cache()
    yield
    versioning.clear_version_cache()


@pytest.fixture
def manager_version(httpx_mock) -> None:
    """Let the mocked AURELION Manager report the newest supported version."""
    httpx_mock.add_response(
        method="GET",
        url=f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}/general/version",
        json="26.3.0",
        is_optional=True,
        is_reusable=True,
    )


@pytest.fixture
def base_url() -> str:
    """Base URL prefix used when registering httpx mock responses."""
    return f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}"
