"""Project management tools for the AURELION Manager MCP server."""

import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from aurelion_manager_mcp import client


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class OpenProjectInput(BaseModel):
    project_folder: str = Field(
        ...,
        description=(
            "Absolute path to the AURELION Manager project folder to open. "
            "The folder must contain a valid AURELION Manager project. "
            "Example: 'C:/Users/UserName/Documents/AURELIONProjects/HighwayTest'"
        ),
    )


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


async def get_current_project() -> str:
    """Retrieve information about the currently open AURELION Manager project.

    Returns the project name, version, AURELION version, project folder path,
    and optional description. Returns a NO_OPEN_PROJECT error if no project
    is open.

    Use this tool to verify that the correct project is open before performing
    any operations on scenarios, sensors, vehicles, or systems.
    """
    result = await client.api_request("GET", "/projects/current-project")
    return json.dumps(result, indent=2)


async def open_project(input: OpenProjectInput) -> str:
    """Open an AURELION Manager project from a folder path.

    Switches the active project to the specified folder. All subsequent tool
    calls will operate on the newly opened project. If a different project was
    previously open, it will be replaced without warning.

    After opening a project, use list_scenarios, list_systems, list_vehicles,
    and list_sensors to explore its contents.

    Precondition: The project_folder must point to a valid AURELION Manager
    project directory that exists on the host running AURELION Manager.
    """
    body = {"projectFolder": input.project_folder}
    result = await client.api_request("PUT", "/projects/open-project", json_body=body)
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all project tools with the given FastMCP instance."""
    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    _open = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )

    mcp.tool(annotations=_read)(get_current_project)
    mcp.tool(annotations=_open)(open_project)
