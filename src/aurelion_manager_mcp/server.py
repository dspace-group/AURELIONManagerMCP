"""AURELION Manager MCP Server — entry point."""

import json
import logging

from mcp.server.fastmcp import FastMCP

from aurelion_manager_mcp import client
from aurelion_manager_mcp.tools import (
    vehicles,
)
from aurelion_manager_mcp.tools import general, projects, scenarios, sensors, simulation, systems

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "aurelion-manager",
    instructions=(
        "This MCP server exposes the AURELION Manager REST API (v1.0.0). "
        "AURELION Manager is a dSPACE application for configuring and controlling "
        "AURELION sensor simulation systems used in HIL and SIL testing.\n\n"
        "Key concepts:\n"
        "- **Scenario**: Defines the 3D environment and driving situation "
        "(ModelDesk-driven or OpenSCENARIO .xosc file).\n"
        "- **Sensor**: A sensor definition (CAMERA, RADAR, LIDAR, ULTRASONIC, INFRARED) "
        "with a configuration file.\n"
        "- **Vehicle**: The ego-vehicle body with sensor instances attached.\n"
        "- **System**: Bundles AURELION instances, a model simulator (VEOS/SCALEXIO), "
        "an SD Broker, and a vehicle into a runnable simulation configuration.\n\n"
        "Typical workflow: open_project → list/create artifacts → "
        "check_simulation_preconditions → synchronize_simulation → "
        "control_scenario_state(Running).\n\n"
        f"Connected to AURELIONManager at: {client.get_configured_base_url()} "
        "(override with the AURELION_MANAGER_API_URL environment variable).\n\n"
        "If you receive a NO_OPEN_PROJECT error, call open_project first."
    ),
)

# ── Register tool groups ────────────────────────────────────────────────────
vehicles.register_tools(mcp)
sensors.register_tools(mcp)
scenarios.register_tools(mcp)
systems.register_tools(mcp)
simulation.register_tools(mcp)
projects.register_tools(mcp)
general.register_tools(mcp)


# ── Resources ───────────────────────────────────────────────────────────────


@mcp.resource(
    "aurelionmgr://vehicles",
    title="All Vehicles",
    mime_type="application/json",
)
async def resource_all_vehicles() -> str:
    """All vehicles in the currently open AURELION Manager project."""
    result = await client.api_request("GET", "/vehicles")
    return json.dumps(result, indent=2)


@mcp.resource(
    "aurelionmgr://vehicles/{vehicle_id}",
    title="Vehicle",
    mime_type="application/json",
)
async def resource_vehicle(vehicle_id: str) -> str:
    """A specific vehicle by ID."""
    result = await client.api_request("GET", f"/vehicles/{vehicle_id}")
    return json.dumps(result, indent=2)


@mcp.resource(
    "aurelionmgr://sensors",
    title="All Sensors",
    mime_type="application/json",
)
async def resource_all_sensors() -> str:
    """All sensors in the currently open AURELION Manager project."""
    result = await client.api_request("GET", "/sensors")
    return json.dumps(result, indent=2)


@mcp.resource(
    "aurelionmgr://sensors/{sensor_id}",
    title="Sensor",
    mime_type="application/json",
)
async def resource_sensor(sensor_id: str) -> str:
    """A specific sensor by ID."""
    result = await client.api_request("GET", f"/sensors/{sensor_id}")
    return json.dumps(result, indent=2)


@mcp.resource(
    "aurelionmgr://scenarios",
    title="All Scenarios",
    mime_type="application/json",
)
async def resource_all_scenarios() -> str:
    """All scenarios in the currently open AURELION Manager project."""
    result = await client.api_request("GET", "/scenarios")
    return json.dumps(result, indent=2)


@mcp.resource(
    "aurelionmgr://scenarios/{scenario_id}",
    title="Scenario",
    mime_type="application/json",
)
async def resource_scenario(scenario_id: str) -> str:
    """A specific scenario by ID."""
    result = await client.api_request("GET", f"/scenarios/{scenario_id}")
    return json.dumps(result, indent=2)


@mcp.resource(
    "aurelionmgr://systems",
    title="All Systems",
    mime_type="application/json",
)
async def resource_all_systems() -> str:
    """All simulation systems in the currently open AURELION Manager project."""
    result = await client.api_request("GET", "/systems")
    return json.dumps(result, indent=2)


@mcp.resource(
    "aurelionmgr://systems/{system_id}",
    title="System",
    mime_type="application/json",
)
async def resource_system(system_id: str) -> str:
    """A specific simulation system by ID."""
    result = await client.api_request("GET", f"/systems/{system_id}")
    return json.dumps(result, indent=2)


@mcp.resource(
    "aurelionmgr://simulation/state",
    title="Simulation State",
    mime_type="application/json",
)
async def resource_simulation_state() -> str:
    """Current simulation state and configuration."""
    result = await client.api_request("GET", "/simulation/state")
    return json.dumps(result, indent=2)


# ── Prompts ─────────────────────────────────────────────────────────────────


@mcp.prompt()
def configure_simulation(
    system_name: str = "",
    scenario_name: str = "",
) -> str:
    """Guided workflow for configuring and starting an AURELION simulation.

    Walks through: open project → select system and scenario →
    check preconditions → synchronize → start scenario.
    """
    context = ""
    if system_name:
        context += f" using system '{system_name}'"
    if scenario_name:
        context += f" with scenario '{scenario_name}'"
    return f"""# Configure and Start an AURELION Simulation{context}

Follow these steps to configure and start a simulation in AURELION Manager:

## Step 1 — Verify Project
Call `get_current_project` to confirm which project is open.
If no project is open, call `open_project` with the absolute folder path.

## Step 2 — Select Resources
- Call `list_systems` to see available simulation systems.
- Call `list_scenarios` to see available scenarios.
- Note the `id` of your target system and scenario.

## Step 3 — Check Preconditions
Call `check_simulation_preconditions(system_id=<id>, scenario_id=<id>)`.
Review any errors (blocking) and warnings (non-blocking).
All errors must be resolved before synchronizing.

## Step 4 — Synchronize
Call `synchronize_simulation(system_id=<id>, scenario_id=<id>)`.
This pushes the configuration to all connected AURELION instances.
Optionally set `autostart=true` to start automatically after sync.

## Step 5 — Start the Scenario
If autostart was false, call `control_scenario_state(state='Running')`.

## Monitoring
- `get_simulation_diagnostics` — connectivity status of all components
- `get_simulation_state` — currently loaded system and scenario
- `get_scenario_state` — current playback state and simulation time

## Stopping
- `control_scenario_state(state='Stopped')` — pause the simulation
- `control_scenario_state(state='Reset')` — return to initial state
- `reset_simulation` — unload the synchronization entirely
"""


@mcp.prompt()
def create_sensor_workflow(sensor_type: str = "CAMERA") -> str:
    """Guided workflow for creating a sensor and integrating it into a vehicle and system.

    Covers: create sensor → create/update vehicle with sensor instance →
    assign vehicle to system.
    """
    return f"""# Create a {sensor_type} Sensor and Assign to a Vehicle

## Step 1 — Create the Sensor
Call `create_sensor` with:
- `name`: Descriptive name, e.g. 'Front {sensor_type} Sensor'
- `description`: What this sensor does
- `sensor_type`: '{sensor_type}'
- `config_file`: Absolute path to the sensor configuration file

Note the `id` in the response — you need it in Step 3.

## Step 2 — Select or Create a Vehicle
Call `list_vehicles` to see existing vehicles.
If no suitable vehicle exists, call `create_vehicle` with at minimum:
- `name`, `description`, and a `components` array with the vehicle body parts.

Note the `id` and the component `id` values.

## Step 3 — Add Sensor Instance to Vehicle
Call `update_vehicle` with the full vehicle data from `get_vehicle`,
adding an entry to `sensor_instances`:
```json
{{
  "id": "<new-unique-id>",
  "name": "Front {sensor_type}",
  "sensorId": "<sensor-id-from-step-1>",
  "enable": true,
  "sensorNumber": 1,
  "vehicleComponentId": "<matching-component-id>",
  "position": {{"x": 2.5, "y": 0.0, "z": 1.2}},
  "rotation": {{"pitch": 0.0, "yaw": 0.0, "roll": 0.0}},
  "isValid": true
}}
```

## Step 4 — Assign Vehicle to a System
Call `update_system` with the system data from `get_system`,
setting `vehicle` to: `{{"id": "<vehicle-id>", "name": "<vehicle-name>"}}`

## Step 5 — Verify
Call `check_simulation_preconditions` to confirm the configuration is valid,
then proceed with `synchronize_simulation`.
"""


# ── Entry point ─────────────────────────────────────────────────────────────


def main() -> None:
    """Start the AURELION Manager MCP server on stdio transport."""
    logging.basicConfig(level=logging.WARNING)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
