"""Async HTTP client for the AURELION Manager REST API (v1.0.0)."""

from dataclasses import dataclass
import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_AURELION_MANAGER_API_URL: str = "http://localhost:8584"
AURELION_MANAGER_API_URL: str = os.environ.get(
    "AURELION_MANAGER_API_URL", DEFAULT_AURELION_MANAGER_API_URL
)
API_BASE_PATH: str = "/api/aurelionmanager/v1.0"

_PERMANENT_STATUS_CODES: frozenset[int] = frozenset({400, 404, 409, 412, 422})
_REQUEST_TIMEOUT: float = 30.0


@dataclass(frozen=True)
class AurelionManagerClientConfig:
    """Configuration for the AURELION Manager HTTP adapter."""

    base_url: str = DEFAULT_AURELION_MANAGER_API_URL
    api_base_path: str = API_BASE_PATH
    timeout: float = _REQUEST_TIMEOUT


def get_configured_base_url() -> str:
    """Return the configured AURELION Manager base URL."""
    return os.environ.get("AURELION_MANAGER_API_URL", DEFAULT_AURELION_MANAGER_API_URL)


def _classify_status(status_code: int) -> str:
    return "permanent" if status_code in _PERMANENT_STATUS_CODES else "transient"


class AurelionManagerClient:
    """HTTP adapter for the AURELION Manager REST API."""

    def __init__(
        self,
        config: AurelionManagerClientConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config or AurelionManagerClientConfig(
            base_url=get_configured_base_url()
        )
        self._http_client = http_client

    def build_url(self, path: str) -> str:
        """Build an absolute AURELION Manager REST API URL."""
        return f"{self.config.base_url.rstrip('/')}{self.config.api_base_path}{path}"

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an async HTTP request against the AURELION Manager API.

        Returns the parsed JSON response on success, or a dict with an
        ``"error"`` key on failure.  The ``error.type`` field is either
        ``"transient"`` (network/5xx — safe to retry) or ``"permanent"``
        (4xx — do not retry without fixing the input).
        """
        url = self.build_url(path)
        kwargs: dict[str, Any] = {"timeout": self.config.timeout}
        if json_body is not None:
            kwargs["json"] = json_body
        if params:
            kwargs["params"] = params

        try:
            if self._http_client is not None:
                response = await self._http_client.request(method, url, **kwargs)
            else:
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.request(method, url, **kwargs)
        except httpx.TimeoutException:
            logger.warning("Request timeout: %s %s", method, url)
            return {
                "error": {
                    "code": "TIMEOUT",
                    "message": (
                        f"Request to AURELIONManager timed out after {self.config.timeout}s. "
                        "Check that the manager is running and responsive."
                    ),
                    "type": "transient",
                }
            }
        except httpx.ConnectError:
            logger.error("Connection error: %s %s", method, url)
            return {
                "error": {
                    "code": "CONNECTION_ERROR",
                    "message": (
                        f"Cannot connect to AURELIONManager at {self.config.base_url}. "
                        "Ensure the manager is running and AURELION_MANAGER_API_URL is configured correctly."
                    ),
                    "type": "transient",
                }
            }
        except httpx.RequestError as exc:
            logger.error("Request error: %s %s — %s", method, url, exc)
            return {
                "error": {
                    "code": "REQUEST_ERROR",
                    "message": str(exc),
                    "type": "transient",
                }
            }

        logger.debug("HTTP %s %s → %d", method, url, response.status_code)

        if response.is_success:
            if response.status_code == 204 or not response.content:
                return {"success": True}
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"success": True, "body": response.text}

        if response.status_code == 412:
            return {
                "error": {
                    "code": "NO_OPEN_PROJECT",
                    "message": (
                        "No project is currently open in AURELIONManager. "
                        "Use the open_project tool to open a project folder first."
                    ),
                    "type": "permanent",
                    "http_status": 412,
                }
            }

        error_type = _classify_status(response.status_code)
        try:
            detail: Any = response.json()
        except json.JSONDecodeError:
            detail = response.text

        return {
            "error": {
                "code": f"HTTP_{response.status_code}",
                "message": f"HTTP {response.status_code}: {detail}",
                "type": error_type,
                "http_status": response.status_code,
            }
        }


async def api_request(
    method: str,
    path: str,
    *,
    json_body: Any = None,
    params: dict[str, Any] | None = None,
) -> Any:
    """Execute a request using the environment-configured default client."""
    return await AurelionManagerClient().request(
        method,
        path,
        json_body=json_body,
        params=params,
    )
