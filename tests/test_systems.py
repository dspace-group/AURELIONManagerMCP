"""Unit tests for system tools."""

import json

import httpx
import pytest

from aurelion_manager_mcp import client
from aurelion_manager_mcp.tools.systems import (
    CreateSystemInput,
    DeleteSystemInput,
    GetSystemInput,
    UpdateSystemInput,
    create_system,
    delete_system,
    get_system,
    list_systems,
    update_system,
)

BASE = f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}"

pytestmark = pytest.mark.usefixtures("manager_version")

_MODEL_SIM = {
    "type": "VEOS",
    "host": "127.0.0.1",
    "modelConfiguration": {
        "pathScenarioStart": "/Model/start",
        "pathScenarioStop": "/Model/stop",
        "pathScenarioState": "/Model/state",
        "pathScenarioTime": "/Model/time",
        "pathScenarioReset": "/Model/reset",
    },
}
_SD_BROKER = {
    "ip": "127.0.0.1",
    "publisherPort": 5557,
    "registerPort": 5556,
    "api": {"host": "127.0.0.1", "port": 8080},
}
SAMPLE_SYSTEM = {
    "id": "sys-abc-123",
    "name": "ASM Test System",
    "description": "Test system",
    "type": "ASM",
    "modelSimulator": _MODEL_SIM,
    "sdBroker": _SD_BROKER,
    "aurelionInstances": [],
    "sutControlSimFrequency": 50.0,
    "enableSuts": False,
    "numSuts": 0,
    "hideEgoFromSensors": False,
}


# ---------------------------------------------------------------------------
# list_systems
# ---------------------------------------------------------------------------


async def test_list_systems_success(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/systems", json=[SAMPLE_SYSTEM])
    result = json.loads(await list_systems())
    assert result == [SAMPLE_SYSTEM]


async def test_list_systems_no_project(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/systems", status_code=412)
    result = json.loads(await list_systems())
    assert result["error"]["code"] == "NO_OPEN_PROJECT"


async def test_list_systems_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("Refused"))
    result = json.loads(await list_systems())
    assert result["error"]["type"] == "transient"


# ---------------------------------------------------------------------------
# get_system
# ---------------------------------------------------------------------------


async def test_get_system_success(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/systems/sys-abc-123", json=SAMPLE_SYSTEM
    )
    result = json.loads(await get_system(GetSystemInput(system_id="sys-abc-123")))
    assert result["id"] == "sys-abc-123"
    assert result["type"] == "ASM"


async def test_get_system_not_found(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/systems/no-such", status_code=404
    )
    result = json.loads(await get_system(GetSystemInput(system_id="no-such")))
    assert result["error"]["type"] == "permanent"


# ---------------------------------------------------------------------------
# create_system
# ---------------------------------------------------------------------------


async def test_create_system_success(httpx_mock):
    created = {**SAMPLE_SYSTEM, "id": "sys-new-456"}
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/systems", status_code=201, json=created
    )
    result = json.loads(
        await create_system(
            CreateSystemInput(
                name="ASM Test System",
                description="Test system",
                system_type="ASM",
                model_simulator=_MODEL_SIM,
                sd_broker=_SD_BROKER,
            )
        )
    )
    assert result["id"] == "sys-new-456"


async def test_create_system_with_vehicle(httpx_mock):
    created = {**SAMPLE_SYSTEM, "id": "sys-veh-789", "vehicle": {"id": "veh-abc", "name": "Sedan"}}
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/systems", status_code=201, json=created
    )
    result = json.loads(
        await create_system(
            CreateSystemInput(
                name="System With Vehicle",
                description="System with vehicle assigned",
                system_type="ASM",
                model_simulator=_MODEL_SIM,
                sd_broker=_SD_BROKER,
                vehicle={"id": "veh-abc", "name": "Sedan"},
            )
        )
    )
    assert result["vehicle"]["id"] == "veh-abc"


# ---------------------------------------------------------------------------
# update_system
# ---------------------------------------------------------------------------


async def test_update_system_success(httpx_mock):
    updated = {**SAMPLE_SYSTEM, "name": "Updated System"}
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/systems/sys-abc-123", json=updated
    )
    result = json.loads(
        await update_system(
            UpdateSystemInput(
                system_id="sys-abc-123",
                name="Updated System",
                description="Updated description",
                system_type="ASM",
                model_simulator=_MODEL_SIM,
                sd_broker=_SD_BROKER,
            )
        )
    )
    assert result["name"] == "Updated System"


# ---------------------------------------------------------------------------
# delete_system
# ---------------------------------------------------------------------------


async def test_delete_system_success(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE}/systems/sys-abc-123", status_code=200
    )
    result = json.loads(await delete_system(DeleteSystemInput(system_id="sys-abc-123")))
    assert "error" not in result


async def test_delete_system_not_found(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE}/systems/ghost-id", status_code=404
    )
    result = json.loads(await delete_system(DeleteSystemInput(system_id="ghost-id")))
    assert result["error"]["type"] == "permanent"
