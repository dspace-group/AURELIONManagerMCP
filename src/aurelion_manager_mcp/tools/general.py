"""General utility tools for the AURELION Manager MCP server."""

import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from aurelion_manager_mcp import client


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
    return json.dumps(result, indent=2)


async def get_log_file_path() -> str:
    """Retrieve the absolute path to the merged AURELION toolchain log file.

    The log file aggregates log output from all AURELION components and is
    useful for diagnosing synchronization errors, connectivity issues, and
    runtime exceptions.

    Returns an object with a 'logFilePath' field containing the absolute path.
    """
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
