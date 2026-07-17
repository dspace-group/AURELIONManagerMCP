"""Scenario tools for the AURELION Manager MCP server."""

import json
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from aurelion_manager_mcp import client


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class GetScenarioInput(BaseModel):
    scenario_id: str = Field(
        ...,
        description=(
            "Unique identifier of the scenario to retrieve. "
            "Obtain this ID from list_scenarios. "
            "Example: 'scn-abc-def-1234'"
        ),
    )


class CreateScenarioInput(BaseModel):
    name: str = Field(
        ...,
        description="Display name of the scenario. Example: 'Highway Merge Test'",
    )
    description: str = Field(
        ...,
        description=(
            "Human-readable description of the scenario. "
            "Example: 'Tests ego-vehicle merging onto a motorway at 80 km/h'"
        ),
    )
    scenario_type: Literal["ModelDesk", "OpenScenario"] = Field(
        ...,
        description=(
            "Scenario type. 'ModelDesk' for ASM/ModelDesk-driven scenarios "
            "(traffic and vehicle behaviour defined in ModelDesk parameter sets). "
            "'OpenScenario' for ASAM OpenSCENARIO (.xosc) file-based scenarios. "
            "Example: 'OpenScenario'"
        ),
    )
    xosc_path: str | None = Field(
        None,
        description=(
            "Absolute path to the .xosc file. Required when scenario_type is 'OpenScenario'. "
            "Example: 'C:/Scenarios/highway_merge.xosc'"
        ),
    )
    image_file: str | None = Field(
        None,
        description=(
            "Optional path to the scenario thumbnail image. "
            "Example: 'images/highway_merge.png'"
        ),
    )
    scenery: dict[str, Any] | None = Field(
        None,
        description=(
            "3D scenery configuration. The 'selection' key determines the type: "
            "'rsg' — standard RSG road scene (no extra fields required), "
            "'aur' — custom AURELION scene (requires 'scene': {'name': str, 'path': str}), "
            "'glb' — GLB 3D model file (requires 'path': str). "
            "Example RSG: {'selection': 'rsg'}. "
            "Example AUR: {'selection': 'aur', 'scene': {'name': 'CityLoop', 'path': 'scenes/city_loop.umap'}}. "
            "Example GLB: {'selection': 'glb', 'path': 'models/highway.glb'}"
        ),
    )


class UpdateScenarioInput(BaseModel):
    scenario_id: str = Field(
        ...,
        description=(
            "ID of the scenario to update. Obtain from list_scenarios. "
            "Example: 'scn-abc-def-1234'"
        ),
    )
    name: str = Field(
        ...,
        description="Updated scenario name. Example: 'Highway Merge Test v2'",
    )
    description: str = Field(
        ...,
        description="Updated description. Example: 'Updated — increased traffic density'",
    )
    scenario_type: Literal["ModelDesk", "OpenScenario"] = Field(
        ...,
        description=(
            "Scenario type: 'ModelDesk' or 'OpenScenario'. "
            "Example: 'OpenScenario'"
        ),
    )
    xosc_path: str | None = Field(
        None,
        description=(
            "Path to the updated .xosc file (OpenScenario type only). "
            "Example: 'C:/Scenarios/highway_merge_v2.xosc'"
        ),
    )
    image_file: str | None = Field(
        None,
        description="Optional updated thumbnail image path.",
    )
    scenery: dict[str, Any] | None = Field(
        None,
        description="Updated scenery configuration. Same schema as in create_scenario.",
    )


class DeleteScenarioInput(BaseModel):
    scenario_id: str = Field(
        ...,
        description=(
            "ID of the scenario to permanently delete. Obtain from list_scenarios. "
            "Example: 'scn-abc-def-1234'"
        ),
    )


class GetScenarioParametersInput(BaseModel):
    scenario_id: str = Field(
        ...,
        description=(
            "ID of the OpenScenario scenario to retrieve parameters for. "
            "Only applicable to 'OpenScenario' type scenarios. "
            "Example: 'scn-abc-def-1234'"
        ),
    )


class GetScenarioValidationInput(BaseModel):
    scenario_id: str = Field(
        ...,
        description=(
            "ID of the OpenScenario scenario to validate. "
            "Only applicable to 'OpenScenario' type scenarios. "
            "Example: 'scn-abc-def-1234'"
        ),
    )


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


async def list_scenarios() -> str:
    """List all scenarios defined in the currently open AURELION Manager project.

    Returns a JSON array of scenario objects. Each scenario includes 'id', 'name',
    'description', and 'type' ('ModelDesk', 'OpenScenario', or 'Replay').
    Use get_scenario for full details of a specific scenario.

    Precondition: A project must be open. Use open_project first if needed.
    """
    result = await client.api_request("GET", "/scenarios")
    return json.dumps(result, indent=2)


async def get_scenario(input: GetScenarioInput) -> str:
    """Retrieve the full configuration of a specific scenario by its ID.

    Returns the complete scenario object including type, scenery configuration,
    and (for OpenScenario types) the xosc file path. Use list_scenarios to
    discover available scenario IDs.

    Precondition: A project must be open. Use open_project first if needed.
    """
    result = await client.api_request("GET", f"/scenarios/{input.scenario_id}")
    return json.dumps(result, indent=2)


async def create_scenario(input: CreateScenarioInput) -> str:
    """Create a new scenario in the currently open AURELION Manager project.

    A scenario defines the 3D environment (scenery) and the driving situation
    (vehicle and traffic behaviour). The returned object includes the
    auto-generated 'id' which is needed for synchronization.

    WARNING: This operation is not idempotent. Multiple calls with the same
    arguments will create duplicate scenarios.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: For OpenScenario type, xosc_path must point to a valid .xosc file.
    """
    body: dict[str, Any] = {
        "name": input.name,
        "description": input.description,
        "type": input.scenario_type,
    }
    if input.xosc_path is not None:
        body["xoscPath"] = input.xosc_path
    if input.image_file is not None:
        body["imageFile"] = input.image_file
    if input.scenery is not None:
        body["scenery"] = input.scenery
    result = await client.api_request("POST", "/scenarios", json_body=body)
    return json.dumps(result, indent=2)


async def update_scenario(input: UpdateScenarioInput) -> str:
    """Update an existing scenario in the currently open AURELION Manager project.

    Performs a full replacement of the scenario configuration. All required fields
    must be provided even if unchanged. Use get_scenario to retrieve the current
    configuration before making targeted updates.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: scenario_id must refer to an existing scenario.
    """
    body: dict[str, Any] = {
        "id": input.scenario_id,
        "name": input.name,
        "description": input.description,
        "type": input.scenario_type,
    }
    if input.xosc_path is not None:
        body["xoscPath"] = input.xosc_path
    if input.image_file is not None:
        body["imageFile"] = input.image_file
    if input.scenery is not None:
        body["scenery"] = input.scenery
    result = await client.api_request(
        "PUT", f"/scenarios/{input.scenario_id}", json_body=body
    )
    return json.dumps(result, indent=2)


async def delete_scenario(input: DeleteScenarioInput) -> str:
    """Permanently delete a scenario from the currently open AURELION Manager project.

    This operation cannot be undone through the API.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: scenario_id must refer to an existing scenario.
    """
    result = await client.api_request("DELETE", f"/scenarios/{input.scenario_id}")
    return json.dumps(result, indent=2)


async def get_scenario_parameters(input: GetScenarioParametersInput) -> str:
    """Retrieve the OpenSCENARIO parameter declarations for a scenario.

    Returns the list of ParameterDeclaration objects for an OpenScenario-type
    scenario. These parameters can be overridden at synchronization time via
    the synchronize_simulation tool's scenario_parameter_values argument.

    Use this tool before synchronizing to understand what parameters are
    available for a given scenario.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: The scenario must be of type 'OpenScenario'.
    """
    result = await client.api_request(
        "GET", f"/scenarios/{input.scenario_id}/parameters"
    )
    return json.dumps(result, indent=2)


async def get_scenario_validation_result(input: GetScenarioValidationInput) -> str:
    """Validate an OpenSCENARIO scenario and retrieve the validation result.

    Returns whether the .xosc file is valid and lists any validation errors or
    warnings per file. Use this tool to diagnose scenario configuration issues
    before attempting synchronization.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: The scenario must be of type 'OpenScenario'.
    """
    result = await client.api_request(
        "GET", f"/scenarios/{input.scenario_id}/validation-result"
    )
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all scenario tools with the given FastMCP instance."""
    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    _create = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )
    _update = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )
    _delete = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )

    mcp.tool(annotations=_read)(list_scenarios)
    mcp.tool(annotations=_read)(get_scenario)
    mcp.tool(annotations=_create)(create_scenario)
    mcp.tool(annotations=_update)(update_scenario)
    mcp.tool(annotations=_delete)(delete_scenario)
    mcp.tool(annotations=_read)(get_scenario_parameters)
    mcp.tool(annotations=_read)(get_scenario_validation_result)
