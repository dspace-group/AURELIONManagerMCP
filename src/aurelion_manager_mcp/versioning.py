"""AURELION Manager version detection and per-version request models.

Request models exist once per AURELION Manager version that changed them; newer
versions subclass older ones. Tools expose the newest models to the LLM and
validate each request against the models of the connected version before sending.
"""

import re
import time
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from aurelion_manager_mcp import client

Version = tuple[int, int]

V26_1: Version = (26, 1)
V26_2: Version = (26, 2)
V26_3: Version = (26, 3)
SUPPORTED_VERSIONS = (V26_1, V26_2, V26_3)

_CACHE_TTL_SECONDS = 60.0

_cache: tuple[str, Version, float] | None = None


def parse_version(text: str) -> Version | None:
    """Extract the ``major.minor`` part of an AURELION Manager version string."""
    match = re.search(r"(\d+)\.(\d+)", text)
    return (int(match[1]), int(match[2])) if match else None


def format_version(version: Version) -> str:
    return f"{version[0]}.{version[1]}"


def clear_version_cache() -> None:
    global _cache
    _cache = None


def _error(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "type": "permanent"}}


async def get_manager_version() -> Version | dict[str, Any]:
    """Return the connected ``(major, minor)`` version, or an error dict."""
    global _cache
    base_url = client.get_configured_base_url()
    now = time.monotonic()
    if _cache is not None and _cache[0] == base_url and now - _cache[2] < _CACHE_TTL_SECONDS:
        return _cache[1]

    result = await client.api_request("GET", "/general/version")
    if isinstance(result, dict) and "error" in result:
        if result["error"].get("http_status") != 404:
            return result
        # 26.1 is the only supported version without a version endpoint.
        version = V26_1
    else:
        parsed = parse_version(str(result))
        if parsed is None:
            return _error(
                "UNKNOWN_MANAGER_VERSION",
                f"Could not determine the AURELION Manager version from {result!r}.",
            )
        version = parsed
    if version < SUPPORTED_VERSIONS[0]:
        return _error(
            "UNSUPPORTED_MANAGER_VERSION",
            f"AURELION Manager {format_version(version)} is not supported. This MCP server "
            f"requires AURELION Manager {format_version(SUPPORTED_VERSIONS[0])} or newer.",
        )
    _cache = (base_url, version, now)
    return version


async def require_version(minimum: Version, feature: str) -> dict[str, Any] | None:
    """Return an error dict if the connected manager is older than ``minimum``."""
    version = await get_manager_version()
    if isinstance(version, dict):
        return version
    if version >= minimum:
        return None
    return _error(
        "UNSUPPORTED_BY_MANAGER_VERSION",
        f"'{feature}' requires AURELION Manager {format_version(minimum)} or newer; "
        f"the connected AURELION Manager is {format_version(version)}.",
    )


async def adapt_body(
    models: Mapping[Version, type[BaseModel]], body: dict[str, Any]
) -> dict[str, Any]:
    """Validate ``body`` against the connected version's model and return the body to send.

    ``models`` maps the version that introduced a model to the model. Returns an
    error dict if the version cannot be determined or does not accept the body.
    """
    version = await get_manager_version()
    if isinstance(version, dict):
        return version
    model = models[max(v for v in models if v <= version)]
    try:
        adapted = model.model_validate(body)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors()
        )
        return _error(
            "UNSUPPORTED_BY_MANAGER_VERSION",
            f"The connected AURELION Manager {format_version(version)} does not accept this "
            f"request: {problems}. Remove or change these values, or upgrade AURELION Manager.",
        )
    return adapted.model_dump(mode="json", exclude_none=True)
