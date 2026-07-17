"""Unit tests for sensor tools."""

import json

import httpx
from aurelion_manager_mcp import client
from aurelion_manager_mcp.tools.sensors import (
    CreateSensorInput,
    DeleteSensorInput,
    GetSensorInput,
    UpdateSensorInput,
    create_sensor,
    delete_sensor,
    get_sensor,
    list_sensors,
    update_sensor,
)

BASE = f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}"

SAMPLE_SENSOR = {
    "id": "cam-abc-123",
    "name": "Front Camera",
    "description": "Front-facing camera sensor",
    "type": "CAMERA",
    "configFile": "C:/Sensors/front_camera.yaml",
}


# ---------------------------------------------------------------------------
# list_sensors
# ---------------------------------------------------------------------------


async def test_list_sensors_success(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/sensors", json=[SAMPLE_SENSOR])
    result = json.loads(await list_sensors())
    assert result == [SAMPLE_SENSOR]


async def test_list_sensors_no_project(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/sensors", status_code=412)
    result = json.loads(await list_sensors())
    assert result["error"]["code"] == "NO_OPEN_PROJECT"
    assert result["error"]["type"] == "permanent"


async def test_list_sensors_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("Refused"))
    result = json.loads(await list_sensors())
    assert result["error"]["code"] == "CONNECTION_ERROR"
    assert result["error"]["type"] == "transient"


# ---------------------------------------------------------------------------
# get_sensor
# ---------------------------------------------------------------------------


async def test_get_sensor_success(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/sensors/cam-abc-123", json=SAMPLE_SENSOR
    )
    result = json.loads(await get_sensor(GetSensorInput(sensor_id="cam-abc-123")))
    assert result["id"] == "cam-abc-123"
    assert result["type"] == "CAMERA"


async def test_get_sensor_not_found(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/sensors/no-such", status_code=404
    )
    result = json.loads(await get_sensor(GetSensorInput(sensor_id="no-such")))
    assert result["error"]["type"] == "permanent"


# ---------------------------------------------------------------------------
# create_sensor
# ---------------------------------------------------------------------------


async def test_create_sensor_success(httpx_mock):
    created = {**SAMPLE_SENSOR, "id": "cam-new-456"}
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/sensors", status_code=201, json=created
    )
    result = json.loads(
        await create_sensor(
            CreateSensorInput(
                name="Front Camera",
                description="Test sensor",
                sensor_type="CAMERA",
                config_file="C:/Sensors/cam.yaml",
            )
        )
    )
    assert result["id"] == "cam-new-456"


async def test_create_radar_sensor(httpx_mock):
    created = {**SAMPLE_SENSOR, "id": "rad-new-789", "type": "RADAR"}
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/sensors", status_code=201, json=created
    )
    result = json.loads(
        await create_sensor(
            CreateSensorInput(
                name="Front Radar",
                description="Radar sensor",
                sensor_type="RADAR",
                config_file="C:/Sensors/radar.yaml",
                tags=["radar", "front"],
            )
        )
    )
    assert result["type"] == "RADAR"


# ---------------------------------------------------------------------------
# update_sensor
# ---------------------------------------------------------------------------


async def test_update_sensor_success(httpx_mock):
    updated = {**SAMPLE_SENSOR, "name": "Updated Camera"}
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/sensors/cam-abc-123", json=updated
    )
    result = json.loads(
        await update_sensor(
            UpdateSensorInput(
                sensor_id="cam-abc-123",
                name="Updated Camera",
                description="Updated description",
                sensor_type="CAMERA",
                config_file="C:/Sensors/cam_v2.yaml",
            )
        )
    )
    assert result["name"] == "Updated Camera"


# ---------------------------------------------------------------------------
# delete_sensor
# ---------------------------------------------------------------------------


async def test_delete_sensor_success(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE}/sensors/cam-abc-123", status_code=200
    )
    result = json.loads(await delete_sensor(DeleteSensorInput(sensor_id="cam-abc-123")))
    assert "error" not in result


async def test_delete_sensor_server_error(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE}/sensors/cam-abc-123", status_code=500
    )
    result = json.loads(await delete_sensor(DeleteSensorInput(sensor_id="cam-abc-123")))
    assert result["error"]["type"] == "transient"
