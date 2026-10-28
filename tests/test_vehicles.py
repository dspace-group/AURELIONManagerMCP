"""Unit tests for vehicle tools."""

import json

import httpx
import pytest
from aurelion_manager_mcp import client
from aurelion_manager_mcp.tools.vehicles import (
    CreateVehicleInput,
    DeleteVehicleInput,
    GetVehicleInput,
    UpdateVehicleInput,
    create_vehicle,
    delete_vehicle,
    get_vehicle,
    list_vehicles,
    update_vehicle,
)

BASE = f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}"

pytestmark = pytest.mark.usefixtures("manager_version")

SAMPLE_VEHICLE = {
    "id": "veh-abc-123",
    "name": "Test Vehicle",
    "description": "A test vehicle",
    "sensorInstances": [],
    "components": [],
}


# ---------------------------------------------------------------------------
# list_vehicles
# ---------------------------------------------------------------------------


async def test_list_vehicles_success(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/vehicles", json=[SAMPLE_VEHICLE])
    result = json.loads(await list_vehicles())
    assert result == [SAMPLE_VEHICLE]


async def test_list_vehicles_no_project(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/vehicles", status_code=412)
    result = json.loads(await list_vehicles())
    assert result["error"]["code"] == "NO_OPEN_PROJECT"
    assert result["error"]["type"] == "permanent"


async def test_list_vehicles_server_error(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/vehicles", status_code=500)
    result = json.loads(await list_vehicles())
    assert result["error"]["type"] == "transient"


async def test_list_vehicles_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
    result = json.loads(await list_vehicles())
    assert result["error"]["code"] == "CONNECTION_ERROR"
    assert result["error"]["type"] == "transient"


async def test_list_vehicles_timeout(httpx_mock):
    httpx_mock.add_exception(httpx.TimeoutException("Timed out"))
    result = json.loads(await list_vehicles())
    assert result["error"]["code"] == "TIMEOUT"
    assert result["error"]["type"] == "transient"


# ---------------------------------------------------------------------------
# get_vehicle
# ---------------------------------------------------------------------------


async def test_get_vehicle_success(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/vehicles/veh-abc-123", json=SAMPLE_VEHICLE
    )
    result = json.loads(await get_vehicle(GetVehicleInput(vehicle_id="veh-abc-123")))
    assert result["id"] == "veh-abc-123"
    assert result["name"] == "Test Vehicle"


async def test_get_vehicle_not_found(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/vehicles/not-exists",
        status_code=404,
        json={"message": "Vehicle not found"},
    )
    result = json.loads(await get_vehicle(GetVehicleInput(vehicle_id="not-exists")))
    assert result["error"]["code"] == "HTTP_404"
    assert result["error"]["type"] == "permanent"


# ---------------------------------------------------------------------------
# create_vehicle
# ---------------------------------------------------------------------------


async def test_create_vehicle_success(httpx_mock):
    created = {**SAMPLE_VEHICLE, "id": "veh-new-456"}
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/vehicles", status_code=201, json=created
    )
    result = json.loads(
        await create_vehicle(
            CreateVehicleInput(name="Test Vehicle", description="A test vehicle")
        )
    )
    assert result["id"] == "veh-new-456"


async def test_create_vehicle_with_tags(httpx_mock):
    created = {**SAMPLE_VEHICLE, "id": "veh-tagged"}
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/vehicles", status_code=201, json=created
    )
    result = json.loads(
        await create_vehicle(
            CreateVehicleInput(
                name="Tagged Vehicle",
                description="With tags",
                tags=["camera", "test"],
            )
        )
    )
    assert result["id"] == "veh-tagged"


async def test_create_vehicle_bad_request(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/vehicles",
        status_code=400,
        json={"message": "Invalid input"},
    )
    result = json.loads(
        await create_vehicle(
            CreateVehicleInput(name="Bad Vehicle", description="Will fail")
        )
    )
    assert result["error"]["type"] == "permanent"


# ---------------------------------------------------------------------------
# update_vehicle
# ---------------------------------------------------------------------------


async def test_update_vehicle_success(httpx_mock):
    updated = {**SAMPLE_VEHICLE, "name": "Updated Vehicle"}
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/vehicles/veh-abc-123", json=updated
    )
    result = json.loads(
        await update_vehicle(
            UpdateVehicleInput(
                vehicle_id="veh-abc-123",
                name="Updated Vehicle",
                description="Updated description",
            )
        )
    )
    assert result["name"] == "Updated Vehicle"


async def test_update_vehicle_not_found(httpx_mock):
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/vehicles/no-such-id", status_code=404
    )
    result = json.loads(
        await update_vehicle(
            UpdateVehicleInput(
                vehicle_id="no-such-id",
                name="Ghost Vehicle",
                description="Does not exist",
            )
        )
    )
    assert result["error"]["type"] == "permanent"


# ---------------------------------------------------------------------------
# delete_vehicle
# ---------------------------------------------------------------------------


async def test_delete_vehicle_success(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE}/vehicles/veh-abc-123", status_code=200
    )
    result = json.loads(
        await delete_vehicle(DeleteVehicleInput(vehicle_id="veh-abc-123"))
    )
    assert "error" not in result


async def test_delete_vehicle_not_found(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE}/vehicles/ghost-id", status_code=404
    )
    result = json.loads(
        await delete_vehicle(DeleteVehicleInput(vehicle_id="ghost-id"))
    )
    assert result["error"]["type"] == "permanent"
