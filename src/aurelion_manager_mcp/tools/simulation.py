"""Simulation control tools for the AURELION Manager MCP server."""

import json
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from aurelion_manager_mcp import client, versioning
from aurelion_manager_mcp.tools.schemas.simulation import (
    ApplicationSynchronizationSettings,
    AsmGtVisualizationSettings,
    RoadAndSceneryGeneratorSettings,
    ScenarioControlSettings,
    SimulationHook,
)



# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class SynchronizeSimulationInput(BaseModel):
    system_id: str | None = Field(
        None,
        description=(
            "ID of the simulation system to synchronize with. "
            "If omitted, the most recently used system is reused. "
            "Obtain IDs from list_systems. Example: 'sys-abc-def-1234'"
        ),
    )
    scenario_id: str | None = Field(
        None,
        description=(
            "ID of the scenario to synchronize with. "
            "If omitted, the most recently used scenario is reused. "
            "Obtain IDs from list_scenarios. Example: 'scn-xyz-789'"
        ),
    )
    autostart: bool = Field(
        False,
        description=(
            "Automatically start the scenario after synchronization completes. "
            "Default: false. Example: true"
        ),
    )
    asm_gt_bounding_boxes: bool = Field(
        False,
        description="Show ASM ground truth bounding boxes in AURELION. Default: false.",
    )
    asm_gt_sensor_points: bool = Field(
        False,
        description="Show ASM ground truth sensor points in AURELION. Default: false.",
    )
    asm_gt_lane_arrows: bool = Field(
        False,
        description="Show ASM ground truth lane arrows in AURELION. Default: false.",
    )
    asm_gt_sensor_cones: bool = Field(
        False,
        description="Show ASM ground truth sensor cones in AURELION. Default: false.",
    )
    scenario_parameter_values: dict[str, str] | None = Field(
        None,
        description=(
            "OpenSCENARIO parameter overrides (key = parameter name, value = string value). "
            "Use get_scenario_parameters to discover available parameters. "
            "Example: {'Ego_Speed': '80', 'TrafficDensity': 'high'}"
        ),
    )


class CheckPreconditionsInput(BaseModel):
    system_id: str = Field(
        ...,
        description=(
            "ID of the system to check preconditions for. "
            "Obtain from list_systems. Example: 'sys-abc-def-1234'"
        ),
    )
    scenario_id: str = Field(
        ...,
        description=(
            "ID of the scenario to check preconditions for. "
            "Obtain from list_scenarios. Example: 'scn-xyz-789'"
        ),
    )


class ControlScenarioStateInput(BaseModel):
    state: Literal["Running", "Stopped", "Reset"] = Field(
        ...,
        description=(
            "Desired scenario state. "
            "'Running' starts or resumes the simulation scenario. "
            "'Stopped' pauses the running simulation. "
            "'Reset' returns the scenario to its initial state. "
            "Example: 'Running'"
        ),
    )


class UpdateSynchronizationSettingsInput(BaseModel):
    asm_gt_visualization: AsmGtVisualizationSettings | None = Field(
        None,
        description=(
            "ASM ground-truth visualization during synchronization. "
            "Example: {'sensorCones': false, 'laneArrows': true, "
            "'sensorPoints': false, 'boundingBoxes': true}"
        ),
    )
    scenario_control: ScenarioControlSettings | None = Field(
        None,
        description="Scenario control during synchronization. Example: {'autostart': true}",
    )
    road_and_scenery_generator: RoadAndSceneryGeneratorSettings | None = Field(
        None,
        description=(
            "Road and Scenery Generator settings. "
            "Example: {'configPath': 'C:/RSG/config.json'}"
        ),
    )
    application: ApplicationSynchronizationSettings | None = Field(
        None,
        description=(
            "Application behavior during synchronization. "
            "Example: {'downloadWhenDifferent': true}"
        ),
    )


class SetSimulationHooksInput(BaseModel):
    hooks: list[SimulationHook] = Field(
        ...,
        description=(
            "Hooks with their desired enabled state. Use get_simulation_hooks to "
            "discover the available hook paths. "
            "Example: [{'path': '<path-from-get_simulation_hooks>', 'isEnabled': true}]"
        ),
    )


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


async def get_simulation_state() -> str:
    """Retrieve the current simulation state and configuration from AURELION Manager.

    Returns details about the currently loaded system and scenario, the
    synchronization progress, and configuration applied to the AURELION instances.
    AURELION Manager 26.3 and newer also report 'synchronizationStatus'
    ('Synchronized' or 'Not_Synchronized').
    Use get_simulation_diagnostics for connectivity status of individual components.

    Requires AURELION Manager 26.2 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    """
    if error := await versioning.require_version(versioning.V26_2, "get_simulation_state"):
        return json.dumps(error, indent=2)
    result = await client.api_request("GET", "/simulation/state")
    return json.dumps(result, indent=2)


async def get_simulation_diagnostics() -> str:
    """Retrieve a full diagnostics summary of all simulation components.

    Returns the connection and status information for: AURELION instances,
    ModelDesk, SensorPlatformService, Simulation Data Broker, Simulation Data
    Player, system state, scenario state, and synced configuration.

    Use this tool to diagnose why a synchronization failed or to verify that
    all components are connected and ready before synchronizing.

    Precondition: A project must be open. Use open_project first if needed.
    """
    result = await client.api_request("GET", "/simulation/diagnostics")
    return json.dumps(result, indent=2)


async def check_simulation_preconditions(input: CheckPreconditionsInput) -> str:
    """Check whether all preconditions are met before synchronizing a system and scenario.

    Returns a result object with: 'conditionsMet' (boolean), 'errors' (list of
    blocking error messages), and 'warnings' (list of non-blocking warnings).

    Always call this tool before synchronize_simulation to catch configuration
    issues early. All errors must be resolved before synchronization can succeed.

    Requires AURELION Manager 26.2 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    """
    if error := await versioning.require_version(
        versioning.V26_2, "check_simulation_preconditions"
    ):
        return json.dumps(error, indent=2)
    result = await client.api_request(
        "GET",
        f"/simulation/preconditions/{input.system_id}/{input.scenario_id}",
    )
    return json.dumps(result, indent=2)


async def synchronize_simulation(input: SynchronizeSimulationInput) -> str:
    """Synchronize the AURELION Manager configuration with all AURELION instances.

    Pushes the selected system and scenario configuration to every AURELION
    instance in the system. This is required before starting a simulation.

    If system_id and scenario_id are provided, synchronizes with that specific
    combination. If omitted, the most recently used system and scenario are reused.

    Use check_simulation_preconditions first to verify the setup is valid.
    After synchronization, call control_scenario_state(state='Running') to start.

    WARNING: This operation is NOT idempotent. Each call initiates a new
    synchronization process and re-pushes configuration to all AURELION instances.
    Do not call repeatedly without intention.

    Requires AURELION Manager 26.2 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    Precondition: All preconditions must be met (use check_simulation_preconditions).
    """
    if error := await versioning.require_version(versioning.V26_2, "synchronize_simulation"):
        return json.dumps(error, indent=2)
    sync_props: dict[str, Any] = {
        "autostart": input.autostart,
        "asmGtBoundingBoxes": input.asm_gt_bounding_boxes,
        "asmGtSensorPoints": input.asm_gt_sensor_points,
        "asmGtLaneArrows": input.asm_gt_lane_arrows,
        "asmGtSensorCones": input.asm_gt_sensor_cones,
    }
    if input.scenario_parameter_values:
        sync_props["scenario"] = {"parameterValues": input.scenario_parameter_values}

    if input.system_id and input.scenario_id:
        path = f"/simulation/synchronize/{input.system_id}/{input.scenario_id}"
    else:
        path = "/simulation/synchronize"

    result = await client.api_request("POST", path, json_body=sync_props)
    return json.dumps(result, indent=2)


async def reset_simulation() -> str:
    """Reset the current simulation system in AURELION Manager.

    Resets the synchronization state, returning the system to an unsynced
    configuration. After reset, a new synchronize_simulation call is required
    before the simulation can be started again.

    Requires AURELION Manager 26.2 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    """
    if error := await versioning.require_version(versioning.V26_2, "reset_simulation"):
        return json.dumps(error, indent=2)
    result = await client.api_request("PUT", "/simulation/reset")
    return json.dumps(result, indent=2)


async def cancel_synchronization() -> str:
    """Cancel an in-progress synchronization process.

    Stops an ongoing synchronization. Safe to call if synchronization is taking
    too long or if a configuration error was detected mid-process.

    Requires AURELION Manager 26.2 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    """
    if error := await versioning.require_version(versioning.V26_2, "cancel_synchronization"):
        return json.dumps(error, indent=2)
    result = await client.api_request("PUT", "/simulation/cancel")
    return json.dumps(result, indent=2)


async def get_scenario_state() -> str:
    """Retrieve the current scenario playback state and simulation time.

    Returns the scenario state ('Running', 'Stopped', 'Reset', or 'Disconnected')
    and the current simulation time in seconds.

    Use this tool to monitor whether the scenario is actively running or has
    been stopped. Use control_scenario_state to change the state.

    Requires AURELION Manager 26.2 or newer.
    Precondition: A project must be open and simulation must be synchronized.
    """
    if error := await versioning.require_version(versioning.V26_2, "get_scenario_state"):
        return json.dumps(error, indent=2)
    result = await client.api_request("GET", "/scenario-state")
    return json.dumps(result, indent=2)


async def control_scenario_state(input: ControlScenarioStateInput) -> str:
    """Start, stop, or reset the simulation scenario in AURELION.

    Changes the running state of the active simulation scenario:
    - 'Running': Starts or resumes the scenario execution.
    - 'Stopped': Pauses the running scenario at the current simulation time.
    - 'Reset': Returns the scenario to its initial state (time = 0).

    The simulation must be synchronized before the scenario can be started.
    Use synchronize_simulation first if get_simulation_state shows no active sync.

    Requires AURELION Manager 26.2 or newer.
    Precondition: A project must be open and simulation must be synchronized.
    """
    if error := await versioning.require_version(versioning.V26_2, "control_scenario_state"):
        return json.dumps(error, indent=2)
    result = await client.api_request(
        "PUT",
        "/scenario-state",
        json_body={"state": input.state},
    )
    return json.dumps(result, indent=2)


async def get_synchronization_settings() -> str:
    """Retrieve the settings persisted for subsequent synchronization operations.

    Returns ASM ground-truth visualization, scenario control (autostart),
    Road and Scenery Generator, and application settings.

    Requires AURELION Manager 26.3 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    """
    if error := await versioning.require_version(
        versioning.V26_3, "get_synchronization_settings"
    ):
        return json.dumps(error, indent=2)
    result = await client.api_request("GET", "/simulation/synchronization-settings")
    return json.dumps(result, indent=2)


async def update_synchronization_settings(input: UpdateSynchronizationSettingsInput) -> str:
    """Persist settings used by subsequent synchronization operations.

    Only the provided setting groups are sent. Use get_synchronization_settings
    to retrieve the current settings first.

    Requires AURELION Manager 26.3 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    """
    if error := await versioning.require_version(
        versioning.V26_3, "update_synchronization_settings"
    ):
        return json.dumps(error, indent=2)
    groups = {
        "asmGtVisualization": input.asm_gt_visualization,
        "scenarioControl": input.scenario_control,
        "roadAndSceneryGenerator": input.road_and_scenery_generator,
        "application": input.application,
    }
    body = {
        key: value.model_dump(exclude_none=True)
        for key, value in groups.items()
        if value is not None
    }
    result = await client.api_request(
        "PUT", "/simulation/synchronization-settings", json_body=body
    )
    return json.dumps(result, indent=2)


async def get_simulation_hooks() -> str:
    """Retrieve the synchronization hooks and whether each one is enabled.

    Returns a JSON array of {'path': str, 'isEnabled': bool}.

    Requires AURELION Manager 26.3 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    """
    if error := await versioning.require_version(versioning.V26_3, "get_simulation_hooks"):
        return json.dumps(error, indent=2)
    result = await client.api_request("GET", "/simulation/hooks")
    return json.dumps(result, indent=2)


async def set_simulation_hooks(input: SetSimulationHooksInput) -> str:
    """Enable or disable hooks for synchronization.

    Use get_simulation_hooks to discover the available hook paths.

    Requires AURELION Manager 26.3 or newer.
    Precondition: A project must be open. Use open_project first if needed.
    """
    if error := await versioning.require_version(versioning.V26_3, "set_simulation_hooks"):
        return json.dumps(error, indent=2)
    result = await client.api_request(
        "PUT",
        "/simulation/hooks",
        json_body=[hook.model_dump() for hook in input.hooks],
    )
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all simulation tools with the given FastMCP instance."""
    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    _sync = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,  # Not idempotent — replay risk documented in docstring
        openWorldHint=False,
    )
    _state_change = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )

    mcp.tool(annotations=_read)(get_simulation_state)
    mcp.tool(annotations=_read)(get_simulation_diagnostics)
    mcp.tool(annotations=_read)(check_simulation_preconditions)
    mcp.tool(annotations=_sync)(synchronize_simulation)
    mcp.tool(annotations=_state_change)(reset_simulation)
    mcp.tool(annotations=_state_change)(cancel_synchronization)
    mcp.tool(annotations=_read)(get_scenario_state)
    mcp.tool(annotations=_state_change)(control_scenario_state)
    mcp.tool(annotations=_read)(get_synchronization_settings)
    mcp.tool(annotations=_state_change)(update_synchronization_settings)
    mcp.tool(annotations=_read)(get_simulation_hooks)
    mcp.tool(annotations=_state_change)(set_simulation_hooks)
