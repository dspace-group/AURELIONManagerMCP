"""Sensor tools for the AURELION Manager MCP server."""

import json
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from aurelion_manager_mcp import client


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class GetSensorInput(BaseModel):
    sensor_id: str = Field(
        ...,
        description=(
            "Unique identifier of the sensor to retrieve. "
            "Obtain this ID from list_sensors. "
            "Example: 'cam-abc-def-1234'"
        ),
    )


class CreateSensorInput(BaseModel):
    name: str = Field(
        ...,
        description="Display name of the sensor. Example: 'Front Camera 2MP'",
    )
    description: str = Field(
        ...,
        description=(
            "Human-readable description of the sensor. "
            "Example: '2 megapixel front-facing camera for lane detection'"
        ),
    )
    sensor_type: Literal["CAMERA", "RADAR", "LIDAR", "ULTRASONIC", "INFRARED"] = Field(
        ...,
        description=(
            "Sensor type. Must be one of: 'CAMERA', 'RADAR', 'LIDAR', 'ULTRASONIC', 'INFRARED'. "
            "Example: 'CAMERA'"
        ),
    )
    config_file: str = Field(
        ...,
        description=(
            "Absolute or relative path to the sensor configuration file. "
            "Example: 'C:/Sensors/Configs/front_camera.yaml'"
        ),
    )
    image_file: str | None = Field(
        None,
        description=(
            "Optional path to the sensor thumbnail image. "
            "Example: 'images/camera_icon.png'"
        ),
    )
    additional_files_directory: str | None = Field(
        None,
        description=(
            "Optional path to a directory containing additional sensor support files. "
            "Example: 'C:/Sensors/camera_extras'"
        ),
    )
    tags: list[str] | None = Field(
        None,
        description=(
            "Optional tag names for filtering and categorisation. "
            "Example: ['camera', '2mp', 'front']"
        ),
    )


class UpdateSensorInput(BaseModel):
    sensor_id: str = Field(
        ...,
        description=(
            "ID of the sensor to update. Obtain from list_sensors. "
            "Example: 'cam-abc-def-1234'"
        ),
    )
    name: str = Field(
        ...,
        description="Updated sensor name. Example: 'Front Camera 4MP'",
    )
    description: str = Field(
        ...,
        description="Updated description. Example: 'Upgraded to 4MP resolution'",
    )
    sensor_type: Literal["CAMERA", "RADAR", "LIDAR", "ULTRASONIC", "INFRARED"] = Field(
        ...,
        description=(
            "Sensor type. Must be one of: 'CAMERA', 'RADAR', 'LIDAR', 'ULTRASONIC', 'INFRARED'. "
            "Example: 'CAMERA'"
        ),
    )
    config_file: str = Field(
        ...,
        description=(
            "Path to the updated sensor configuration file. "
            "Example: 'C:/Sensors/Configs/front_camera_v2.yaml'"
        ),
    )
    image_file: str | None = Field(
        None,
        description="Optional updated thumbnail image path. Example: 'images/camera_v2.png'",
    )
    additional_files_directory: str | None = Field(
        None,
        description="Optional updated additional files directory path.",
    )
    tags: list[str] | None = Field(
        None,
        description="Optional updated tag names. Example: ['camera', '4mp']",
    )


class DeleteSensorInput(BaseModel):
    sensor_id: str = Field(
        ...,
        description=(
            "ID of the sensor to permanently delete. Obtain from list_sensors. "
            "Example: 'cam-abc-def-1234'"
        ),
    )


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


async def list_sensors() -> str:
    """List all sensors defined in the currently open AURELION Manager project.

    Returns a JSON array of sensor objects. Each sensor has 'id', 'name',
    'description', 'type', and 'configFile'. Use get_sensor to retrieve the
    full details of a specific sensor.

    Precondition: A project must be open. Use open_project first if needed.
    """
    result = await client.api_request("GET", "/sensors")
    return json.dumps(result, indent=2)


async def get_sensor(input: GetSensorInput) -> str:
    """Retrieve the full configuration of a specific sensor by its ID.

    Returns the complete sensor object including config file path, type, tags,
    and image. Use list_sensors to discover available sensor IDs.

    Precondition: A project must be open. Use open_project first if needed.
    """
    result = await client.api_request("GET", f"/sensors/{input.sensor_id}")
    return json.dumps(result, indent=2)


async def create_sensor(input: CreateSensorInput) -> str:
    """Create a new sensor in the currently open AURELION Manager project.

    A sensor definition specifies the sensor type and its configuration file.
    After creation, the sensor can be referenced in vehicle configurations via
    sensor instances. The returned object includes the auto-generated 'id'.

    WARNING: This operation is not idempotent. Multiple calls with the same
    arguments will create duplicate sensors.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: The config_file path must point to a valid sensor config file.
    """
    body: dict[str, Any] = {
        "name": input.name,
        "description": input.description,
        "type": input.sensor_type,
        "configFile": input.config_file,
    }
    if input.image_file is not None:
        body["imageFile"] = input.image_file
    if input.additional_files_directory is not None:
        body["additionalFilesDirectory"] = input.additional_files_directory
    if input.tags is not None:
        body["tags"] = [{"name": tag} for tag in input.tags]
    result = await client.api_request("POST", "/sensors", json_body=body)
    return json.dumps(result, indent=2)


async def update_sensor(input: UpdateSensorInput) -> str:
    """Update an existing sensor in the currently open AURELION Manager project.

    Performs a full replacement of the sensor configuration. All required fields
    must be provided even if unchanged. Use get_sensor to retrieve the current
    configuration before making targeted updates.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: sensor_id must refer to an existing sensor (use list_sensors).
    """
    body: dict[str, Any] = {
        "id": input.sensor_id,
        "name": input.name,
        "description": input.description,
        "type": input.sensor_type,
        "configFile": input.config_file,
    }
    if input.image_file is not None:
        body["imageFile"] = input.image_file
    if input.additional_files_directory is not None:
        body["additionalFilesDirectory"] = input.additional_files_directory
    if input.tags is not None:
        body["tags"] = [{"name": tag} for tag in input.tags]
    result = await client.api_request(
        "PUT", f"/sensors/{input.sensor_id}", json_body=body
    )
    return json.dumps(result, indent=2)


async def delete_sensor(input: DeleteSensorInput) -> str:
    """Permanently delete a sensor from the currently open AURELION Manager project.

    Any vehicles that reference this sensor via sensor instances must be updated
    afterwards. This operation cannot be undone through the API.

    Precondition: A project must be open. Use open_project first if needed.
    Precondition: sensor_id must refer to an existing sensor.
    """
    result = await client.api_request("DELETE", f"/sensors/{input.sensor_id}")
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all sensor tools with the given FastMCP instance."""
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

    mcp.tool(annotations=_read)(list_sensors)
    mcp.tool(annotations=_read)(get_sensor)
    mcp.tool(annotations=_create)(create_sensor)
    mcp.tool(annotations=_update)(update_sensor)
    mcp.tool(annotations=_delete)(delete_sensor)
