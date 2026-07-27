"""Vehicle tools for the AURELION Manager MCP server."""

import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from aurelion_manager_mcp import client
from aurelion_manager_mcp.tools.schemas import ApiVehicleComponent, SensorInstance


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class GetVehicleInput(BaseModel):
    vehicle_id: str = Field(
        ...,
        description=(
            "Unique identifier of the vehicle to retrieve. "
            "Obtain this ID from list_vehicles. "
            "Example: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'"
        ),
    )


class CreateVehicleInput(BaseModel):
    name: str = Field(
        ...,
        description="Display name of the vehicle. Example: 'Sedan Front Camera'",
    )
    description: str = Field(
        ...,
        description=(
            "Human-readable description of this vehicle configuration. "
            "Example: 'Test vehicle with a single front-facing camera on the roof'"
        ),
    )
    components: list[ApiVehicleComponent] = Field(
        default_factory=list,
        description=(
            "Vehicle body components. Each object requires at minimum 'name' (string) and 'id' (string). "
            "Optional fields: 'assetPath', 'model3d', 'mappingFile', 'baseDataStream', "
            "'dataStreams', 'sensorMountingObjects'. "
            "Example: [{'id': 'body-01', 'name': 'BodyShell', "
            "'assetPath': 'vehicles/sedan/body.uasset', "
            "'sensorMountingObjects': ['roof', 'front_bumper']}]"
        ),
    )
    sensor_instances: list[SensorInstance] = Field(
        default_factory=list,
        description=(
            "Sensor instances attached to this vehicle. Required fields per instance: "
            "'id' (string), 'name' (string), "
            "'sensorId' (ID of an existing sensor — obtain from list_sensors), "
            "'enable' (boolean), 'sensorNumber' (integer), "
            "'vehicleComponentId' (must match a component 'id' in the components list), "
            "'position' ({'x': float, 'y': float, 'z': float} in metres relative to vehicle origin), "
            "'rotation' ({'pitch': float, 'yaw': float, 'roll': float} in degrees), "
            "'isValid' (boolean). "
            "Example: [{'id': 'si-01', 'name': 'Front Camera', 'sensorId': 'cam-abc-123', "
            "'enable': true, 'sensorNumber': 1, 'vehicleComponentId': 'body-01', "
            "'position': {'x': 2.5, 'y': 0.0, 'z': 1.2}, "
            "'rotation': {'pitch': 0.0, 'yaw': 0.0, 'roll': 0.0}, 'isValid': true}]"
        ),
    )
    image_file: str | None = Field(
        None,
        description=(
            "Optional relative path to the vehicle thumbnail image. "
            "Example: 'images/sedan.png'"
        ),
    )
    tags: list[str] | None = Field(
        None,
        description=(
            "Optional tag names for filtering and categorisation. "
            "Example: ['camera', 'sedan', 'test']"
        ),
    )


class UpdateVehicleInput(BaseModel):
    vehicle_id: str = Field(
        ...,
        description=(
            "ID of the vehicle to update. Obtain from list_vehicles. "
            "Example: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'"
        ),
    )
    name: str = Field(
        ...,
        description="Updated vehicle name. Example: 'Sedan Front Camera v2'",
    )
    description: str = Field(
        ...,
        description="Updated description. Example: 'Updated — rear camera added'",
    )
    components: list[ApiVehicleComponent] = Field(
        default_factory=list,
        description=(
            "Updated components list. Same schema as in create_vehicle. "
            "Example: [{'id': 'body-01', 'name': 'BodyShell'}]"
        ),
    )
    sensor_instances: list[SensorInstance] = Field(
        default_factory=list,
        description="Updated sensor instances. Same schema as in create_vehicle.",
    )
    image_file: str | None = Field(
        None,
        description="Optional updated thumbnail image path. Example: 'images/sedan_v2.png'",
    )
    tags: list[str] | None = Field(
        None,
        description="Optional updated tag names. Example: ['camera', 'radar']",
    )


class DeleteVehicleInput(BaseModel):
    vehicle_id: str = Field(
        ...,
        description=(
            "ID of the vehicle to permanently delete. Obtain from list_vehicles. "
            "Example: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'"
        ),
    )


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


async def list_vehicles() -> str:
    """List all vehicles defined in the currently open AURELION Manager project.

    Returns a JSON array of vehicle objects. Each vehicle includes 'id', 'name',
    'description', 'sensorInstances', and 'components'. Use get_vehicle to
    retrieve the full configuration of a specific vehicle by its ID.

    Precondition: A project must be open. Use open_project first if you receive
    a NO_OPEN_PROJECT error.
    """
    result = await client.api_request("GET", "/vehicles")
    return json.dumps(result, indent=2)


async def get_vehicle(input: GetVehicleInput) -> str:
    """Retrieve the full configuration of a specific vehicle by its ID.

    Returns the complete vehicle object including all sensor instances and
    body components. Use list_vehicles to discover available vehicle IDs.

    Precondition: A project must be open. Use open_project first if needed.
    """
    result = await client.api_request("GET", f"/vehicles/{input.vehicle_id}")
    return json.dumps(result, indent=2)


async def create_vehicle(input: CreateVehicleInput) -> str:
    """Create a new vehicle in the currently open AURELION Manager project.

    A vehicle defines the physical body components and the sensor configuration
    (sensor instances) of the ego-vehicle. The returned object includes the
    auto-generated 'id' which can be referenced when configuring simulation systems.

    WARNING: This operation is not idempotent. Multiple calls with the same
    arguments will create duplicate vehicles.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: 'sensorId' values in sensor_instances must refer to sensors
    that already exist (use list_sensors to verify).
    """
    body = {
        "name": input.name,
        "description": input.description,
        "components": [component.model_dump(exclude_none=True) for component in input.components],
        "sensorInstances": [
            sensor_instance.model_dump(exclude_none=True)
            for sensor_instance in input.sensor_instances
        ],
    }
    if input.image_file is not None:
        body["imageFile"] = input.image_file
    if input.tags is not None:
        body["tags"] = [{"name": tag} for tag in input.tags]
    result = await client.api_request("POST", "/vehicles", json_body=body)
    return json.dumps(result, indent=2)


async def update_vehicle(input: UpdateVehicleInput) -> str:
    """Update an existing vehicle in the currently open AURELION Manager project.

    Performs a full replacement of the vehicle configuration. All required fields
    must be provided even if unchanged. Use get_vehicle to retrieve the current
    configuration before making targeted updates.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: vehicle_id must refer to an existing vehicle (use list_vehicles).
    """
    body = {
        "id": input.vehicle_id,
        "name": input.name,
        "description": input.description,
        "components": [component.model_dump(exclude_none=True) for component in input.components],
        "sensorInstances": [
            sensor_instance.model_dump(exclude_none=True)
            for sensor_instance in input.sensor_instances
        ],
    }
    if input.image_file is not None:
        body["imageFile"] = input.image_file
    if input.tags is not None:
        body["tags"] = [{"name": tag} for tag in input.tags]
    result = await client.api_request(
        "PUT", f"/vehicles/{input.vehicle_id}", json_body=body
    )
    return json.dumps(result, indent=2)


async def delete_vehicle(input: DeleteVehicleInput) -> str:
    """Permanently delete a vehicle from the currently open AURELION Manager project.

    Any simulation systems that reference this vehicle must be updated afterwards.
    This operation cannot be undone through the API.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: vehicle_id must refer to an existing vehicle.
    """
    result = await client.api_request("DELETE", f"/vehicles/{input.vehicle_id}")
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all vehicle tools with the given FastMCP instance."""
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

    mcp.tool(annotations=_read)(list_vehicles)
    mcp.tool(annotations=_read)(get_vehicle)
    mcp.tool(annotations=_create)(create_vehicle)
    mcp.tool(annotations=_update)(update_vehicle)
    mcp.tool(annotations=_delete)(delete_vehicle)
