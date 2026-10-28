"""General utility tools for the AURELION Manager MCP server."""

import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from aurelion_manager_mcp import client, versioning


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


async def get_version() -> str:
    """Retrieve the AURELION Manager application version string.

    Returns the version of the running AURELION Manager instance.
    Useful for compatibility checks and support diagnostics.
    """
    result = await client.api_request("GET", "/general/version")
    if isinstance(result, str):
        return json.dumps({"version": result}, indent=2)
    if result.get("error", {}).get("http_status") == 404:
        return json.dumps(
            {
                "version": versioning.format_version(versioning.V26_1),
                "note": "Inferred: AURELION Manager 26.1 has no version endpoint.",
            },
            indent=2,
        )
    return json.dumps(result, indent=2)


async def get_log_file_path() -> str:
    """Retrieve the absolute path to the merged AURELION toolchain log file.

    The log file aggregates log output from all AURELION components and is
    useful for diagnosing synchronization errors, connectivity issues, and
    runtime exceptions.

    Returns an object with a 'logFilePath' field containing the absolute path.

    Requires AURELION Manager 26.2 or newer.
    """
    if error := await versioning.require_version(versioning.V26_2, "get_log_file_path"):
        return json.dumps(error, indent=2)
    result = await client.api_request("GET", "/general/settings/log")
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all general tools with the given FastMCP instance."""
    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )

    mcp.tool(annotations=_read)(get_version)
    mcp.tool(annotations=_read)(get_log_file_path)
