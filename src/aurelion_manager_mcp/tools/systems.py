"""System tools for the AURELION Manager MCP server."""

import json
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from aurelion_manager_mcp import client
from aurelion_manager_mcp.tools.schemas import (
    ModelApplication,
    ModelSimulator,
    SdBroker,
    SystemAurelionInstance,
    VehicleReference,
)


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class GetSystemInput(BaseModel):
    system_id: str = Field(
        ...,
        description=(
            "Unique identifier of the simulation system to retrieve. "
            "Obtain this ID from list_systems. "
            "Example: 'sys-abc-def-1234'"
        ),
    )


class CreateSystemInput(BaseModel):
    name: str = Field(
        ...,
        description="Display name of the simulation system. Example: 'ASM Highway Test System'",
    )
    description: str = Field(
        ...,
        description=(
            "Human-readable description of the system. "
            "Example: 'System for ASM-based highway test scenarios on VEOS'"
        ),
    )
    system_type: Literal["ASM", "Replay"] = Field(
        ...,
        description=(
            "System type. 'ASM' for live ASM simulation (requires a running model simulator). "
            "'Replay' for prerecorded simulation data playback. "
            "Example: 'ASM'"
        ),
    )
    model_simulator: ModelSimulator = Field(
        ...,
        description=(
            "Model simulator configuration. Required fields: "
            "'type' ('VEOS' or 'SCALEXIO'), "
            "'host' (IP address or hostname of the simulation platform), "
            "'modelConfiguration' (object with paths: "
            "'pathScenarioStart', 'pathScenarioStop', 'pathScenarioState', "
            "'pathScenarioTime', 'pathScenarioReset' — these are model variable paths). "
            "Optional: 'motionData' ({'host': str, 'port': int}), "
            "'advancedPortConfiguration' ({'customDataPorts': [], 'clifPort': int}). "
            "Example: {'type': 'VEOS', 'host': '127.0.0.1', "
            "'modelConfiguration': {'pathScenarioStart': '/Model/start', "
            "'pathScenarioStop': '/Model/stop', 'pathScenarioState': '/Model/state', "
            "'pathScenarioTime': '/Model/time', 'pathScenarioReset': '/Model/reset'}}"
        ),
    )
    sd_broker: SdBroker = Field(
        ...,
        description=(
            "Simulation Data Broker (SdBroker) connection configuration. "
            "Required fields: 'ip' (string), 'publisherPort' (integer), "
            "'registerPort' (integer), 'api' ({'host': string, 'port': integer}). "
            "Example: {'ip': '127.0.0.1', 'publisherPort': 5557, "
            "'registerPort': 5556, 'api': {'host': '127.0.0.1', 'port': 8080}}"
        ),
    )
    aurelion_instances: list[SystemAurelionInstance] = Field(
        default_factory=list,
        description=(
            "List of AURELION instance configurations. Each instance needs 'name' and 'host' "
            "plus the relevant port configuration for SensorSim PCs. "
            "Example: [{'name': 'AUR-Instance-1', 'host': '192.168.1.100'}]"
        ),
    )
    sut_control_sim_frequency: float = Field(
        50.0,
        description=(
            "SUT (System Under Test) control simulation frequency in Hz. "
            "Example: 50.0"
        ),
    )
    enable_suts: bool = Field(
        False,
        description="Enable SUT (V-ESI) integration. Default: false. Example: false",
    )
    num_suts: int = Field(
        0,
        description="Number of SUTs in this system configuration. Default: 0. Example: 1",
    )
    hide_ego_from_sensors: bool = Field(
        False,
        description=(
            "If true, the ego-vehicle mesh is excluded from sensor simulation "
            "(useful to prevent self-occlusion). Default: false."
        ),
    )
    vehicle: VehicleReference | None = Field(
        None,
        description=(
            "Vehicle reference to assign to this system. "
            "Provide {'id': str, 'name': str}. "
            "Obtain IDs from list_vehicles. "
            "Example: {'id': 'veh-abc-123', 'name': 'Sedan Front Camera'}"
        ),
    )
    application: ModelApplication | None = Field(
        None,
        description=(
            "Optional application (MA) configuration. "
            "Fields: 'maPortConfigPath' (string), 'filepath' (string). "
            "Example: {'maPortConfigPath': 'C:/MA/ports.xml', 'filepath': 'C:/MA/app.exe'}"
        ),
    )


class UpdateSystemInput(BaseModel):
    system_id: str = Field(
        ...,
        description=(
            "ID of the simulation system to update. Obtain from list_systems. "
            "Example: 'sys-abc-def-1234'"
        ),
    )
    name: str = Field(
        ...,
        description="Updated system name. Example: 'ASM Highway Test System v2'",
    )
    description: str = Field(
        ...,
        description="Updated description.",
    )
    system_type: Literal["ASM", "Replay"] = Field(
        ...,
        description="System type: 'ASM' or 'Replay'. Example: 'ASM'",
    )
    model_simulator: ModelSimulator = Field(
        ...,
        description="Updated model simulator config. Same schema as in create_system.",
    )
    sd_broker: SdBroker = Field(
        ...,
        description="Updated SD Broker config. Same schema as in create_system.",
    )
    aurelion_instances: list[SystemAurelionInstance] = Field(
        default_factory=list,
        description="Updated AURELION instances list.",
    )
    sut_control_sim_frequency: float = Field(
        50.0,
        description="Updated SUT frequency in Hz. Example: 50.0",
    )
    enable_suts: bool = Field(False, description="Updated SUT enable flag.")
    num_suts: int = Field(0, description="Updated number of SUTs.")
    hide_ego_from_sensors: bool = Field(
        False, description="Updated hide-ego-from-sensors flag."
    )
    vehicle: VehicleReference | None = Field(
        None,
        description=(
            "Updated vehicle reference {'id': str, 'name': str}. "
            "Example: {'id': 'veh-abc-123', 'name': 'Sedan Front Camera'}"
        ),
    )
    application: ModelApplication | None = Field(
        None,
        description="Updated application (MA) configuration.",
    )


class DeleteSystemInput(BaseModel):
    system_id: str = Field(
        ...,
        description=(
            "ID of the simulation system to permanently delete. "
            "Obtain from list_systems. Example: 'sys-abc-def-1234'"
        ),
    )


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


async def list_systems() -> str:
    """List all simulation systems defined in the currently open AURELION Manager project.

    Returns a JSON array of system objects. Each system has 'id', 'name',
    'description', 'type' ('ASM' or 'Replay'), and connection configuration.
    A simulation system bundles the AURELION instances, model simulator,
    and vehicle configuration needed to run a simulation.

    Use get_system for the full configuration of a specific system.

    Precondition: A project must be open. Use open_project first if needed.
    """
    result = await client.api_request("GET", "/systems")
    return json.dumps(result, indent=2)


async def get_system(input: GetSystemInput) -> str:
    """Retrieve the full configuration of a specific simulation system by its ID.

    Returns the complete system object including model simulator settings,
    SD Broker configuration, AURELION instance list, and vehicle assignment.
    Use list_systems to discover available system IDs.

    Precondition: A project must be open. Use open_project first if needed.
    """
    result = await client.api_request("GET", f"/systems/{input.system_id}")
    return json.dumps(result, indent=2)


async def create_system(input: CreateSystemInput) -> str:
    """Create a new simulation system in the currently open AURELION Manager project.

    A simulation system defines all the connections and components needed to run
    a simulation: the model simulator (VEOS/SCALEXIO), the Simulation Data Broker,
    AURELION instances, and optionally a vehicle. The returned object includes
    the auto-generated 'id'.

    WARNING: This operation is not idempotent. Multiple calls with the same
    arguments will create duplicate systems.

    Precondition: A project must be open. Use open_project first if needed.
    """
    body: dict[str, Any] = {
        "name": input.name,
        "description": input.description,
        "type": input.system_type,
        "modelSimulator": input.model_simulator.model_dump(exclude_none=True),
        "sdBroker": input.sd_broker.model_dump(exclude_none=True),
        "aurelionInstances": [
            instance.model_dump(exclude_none=True)
            for instance in input.aurelion_instances
        ],
        "sutControlSimFrequency": input.sut_control_sim_frequency,
        "enableSuts": input.enable_suts,
        "numSuts": input.num_suts,
        "hideEgoFromSensors": input.hide_ego_from_sensors,
    }
    if input.vehicle is not None:
        body["vehicle"] = input.vehicle.model_dump(exclude_none=True)
    if input.application is not None:
        body["application"] = input.application.model_dump(exclude_none=True)
    result = await client.api_request("POST", "/systems", json_body=body)
    return json.dumps(result, indent=2)


async def update_system(input: UpdateSystemInput) -> str:
    """Update an existing simulation system in the currently open AURELION Manager project.

    Performs a full replacement of the system configuration. All required fields
    must be provided even if unchanged. Use get_system to retrieve the current
    configuration before making targeted updates.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: system_id must refer to an existing system (use list_systems).
    """
    body: dict[str, Any] = {
        "id": input.system_id,
        "name": input.name,
        "description": input.description,
        "type": input.system_type,
        "modelSimulator": input.model_simulator.model_dump(exclude_none=True),
        "sdBroker": input.sd_broker.model_dump(exclude_none=True),
        "aurelionInstances": [
            instance.model_dump(exclude_none=True)
            for instance in input.aurelion_instances
        ],
        "sutControlSimFrequency": input.sut_control_sim_frequency,
        "enableSuts": input.enable_suts,
        "numSuts": input.num_suts,
        "hideEgoFromSensors": input.hide_ego_from_sensors,
    }
    if input.vehicle is not None:
        body["vehicle"] = input.vehicle.model_dump(exclude_none=True)
    if input.application is not None:
        body["application"] = input.application.model_dump(exclude_none=True)
    result = await client.api_request(
        "PUT", f"/systems/{input.system_id}", json_body=body
    )
    return json.dumps(result, indent=2)


async def delete_system(input: DeleteSystemInput) -> str:
    """Permanently delete a simulation system from the currently open AURELION Manager project.

    This operation cannot be undone through the API.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: system_id must refer to an existing system.
    """
    result = await client.api_request("DELETE", f"/systems/{input.system_id}")
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all system tools with the given FastMCP instance."""
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

    mcp.tool(annotations=_read)(list_systems)
    mcp.tool(annotations=_read)(get_system)
    mcp.tool(annotations=_create)(create_system)
    mcp.tool(annotations=_update)(update_system)
    mcp.tool(annotations=_delete)(delete_system)
