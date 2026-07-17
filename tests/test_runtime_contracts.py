"""Tests for packaging and runtime seams."""

import importlib
from importlib import metadata
import runpy
from pathlib import Path
import tomllib
from unittest.mock import patch

import httpx
import pytest

from aurelion_manager_mcp import __version__
from aurelion_manager_mcp.client import (
    API_BASE_PATH,
    AurelionManagerClient,
    AurelionManagerClientConfig,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_package_modules_import_without_src_namespace() -> None:
    """The installed package interface must not depend on the src package name."""
    importlib.import_module("aurelion_manager_mcp.server")
    importlib.import_module("aurelion_manager_mcp.tools.vehicles")


def test_console_entry_point_targets_package_module() -> None:
    entry_points = metadata.entry_points(group="console_scripts")
    script = next(ep for ep in entry_points if ep.name == "aurelion-manager-mcp")

    assert script.value == "aurelion_manager_mcp.server:main"


def test_package_version_matches_project_metadata() -> None:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())["project"]

    assert __version__ == project["version"]
    assert metadata.version("aurelion-manager-mcp") == project["version"]
    assert project["requires-python"] == ">=3.12"


def test_missing_package_metadata_fails_fast() -> None:
    with patch(
        "importlib.metadata.version",
        side_effect=metadata.PackageNotFoundError("aurelion-manager-mcp"),
    ):
        with pytest.raises(metadata.PackageNotFoundError):
            runpy.run_path(str(PROJECT_ROOT / "src" / "aurelion_manager_mcp" / "__init__.py"))


def test_client_builds_urls_from_injected_config() -> None:
    api_client = AurelionManagerClient(
        AurelionManagerClientConfig(base_url="http://manager.example:8584/")
    )

    assert api_client.build_url("/general/version") == (
        f"http://manager.example:8584{API_BASE_PATH}/general/version"
    )


async def test_client_accepts_injected_http_adapter() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"url": str(request.url)})
    )
    async with httpx.AsyncClient(transport=transport) as http_client:
        api_client = AurelionManagerClient(
            AurelionManagerClientConfig(base_url="http://manager.example:8584"),
            http_client=http_client,
        )

        result = await api_client.request("GET", "/general/version")

    assert result == {
        "url": f"http://manager.example:8584{API_BASE_PATH}/general/version"
    }


def test_release_workflow_uses_pyinstaller_spec() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text()

    assert "packaging\\pyinstaller.spec" in workflow
    assert "src\\aurelion_manager_mcp\\server.py" not in workflow


def test_pyinstaller_spec_points_at_project_src_tree() -> None:
    spec = (PROJECT_ROOT / "packaging" / "pyinstaller.spec").read_text()

    assert "project_root = Path(SPECPATH).parent" in spec
    assert 'src_root = project_root / "src"' in spec
    assert 'name="aurelion-manager-mcp"' in spec
