"""Shared test fixtures for AURELION Manager MCP server tests."""

import pytest

from aurelion_manager_mcp import client


@pytest.fixture
def base_url() -> str:
    """Base URL prefix used when registering httpx mock responses."""
    return f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}"
