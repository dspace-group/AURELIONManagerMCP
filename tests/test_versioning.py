"""Tests for AURELION Manager version detection and per-version request bodies."""

import json

import httpx
import pytest

from aurelion_manager_mcp import client, versioning
from aurelion_manager_mcp.tools import general, projects, simulation
from aurelion_manager_mcp.tools.sensors import CreateSensorInput, create_sensor
from aurelion_manager_mcp.tools.systems import CreateSystemInput, create_system
from aurelion_manager_mcp.tools.vehicles import (
    CreateVehicleInput,
    UpdateVehicleInput,
    create_vehicle,
    update_vehicle,
)

BASE = f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}"
VERSION_URL = f"{BASE}/general/version"

_SENSOR_INSTANCE = {
    "vehicleComponentId": "comp-1",
    "sensorNumber": 1,
    "rotation": {"roll": 0.0, "yaw": 0.0, "pitch": 0.0},
    "position": {"x": 1.0, "y": 0.0, "z": 1.5},
    "enable": True,
    "sensorId": "sensor-1",
    "name": "Front Camera",
    "id": "inst-1",
}
_COMPONENT = {"name": "Body", "id": "comp-1"}
_SYSTEM = {
    "name": "System",
    "description": "",
    "system_type": "ASM",
    "model_simulator": {
        "type": "VEOS",
        "host": "127.0.0.1",
        "modelConfiguration": {
            "pathScenarioStart": "/start",
            "pathScenarioStop": "/stop",
            "pathScenarioState": "/state",
            "pathScenarioTime": "/time",
            "pathScenarioReset": "/reset",
        },
    },
    "sd_broker": {
        "ip": "127.0.0.1",
        "publisherPort": 5557,
        "registerPort": 5556,
        "api": {"host": "127.0.0.1", "port": 8080},
    },
    "sut_control_sim_frequency": 50.0,
}
_AURELION_INSTANCE = {
    "enabled": True,
    "connection": {"host": "127.0.0.1", "port": 9000},
    "enableSceneView": False,
    "gpuIndex": 0,
    "enableGpuIndex": False,
    "sampleTime": 0.01,
    "mappings": [],
    "name": "AURELION",
    "id": "aur-1",
}


def _mock_version(httpx_mock, version: str) -> None:
    if version == "26.1":
        httpx_mock.add_response(method="GET", url=VERSION_URL, status_code=404)
    else:
        httpx_mock.add_response(method="GET", url=VERSION_URL, json=f"{version}.0")


def _sent_body(httpx_mock, method: str) -> dict:
    (request,) = [r for r in httpx_mock.get_requests() if r.method == method]
    return json.loads(request.content)


def _assert_unsupported(result: str, *fragments: str) -> None:
    error = json.loads(result)["error"]
    assert error["code"] == "UNSUPPORTED_BY_MANAGER_VERSION"
    assert error["type"] == "permanent"
    for fragment in fragments:
        assert fragment in error["message"]


# ---------------------------------------------------------------------------
# Version detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [("26.3.0", (26, 3)), ("v26.2.1-beta", (26, 2)), ("27.10", (27, 10)), ("dev", None)],
)
def test_parse_version(text, expected):
    assert versioning.parse_version(text) == expected


async def test_version_is_cached(httpx_mock):
    _mock_version(httpx_mock, "26.2")
    assert await versioning.get_manager_version() == versioning.V26_2
    assert await versioning.get_manager_version() == versioning.V26_2
    assert len(httpx_mock.get_requests()) == 1


async def test_missing_version_endpoint_means_26_1(httpx_mock):
    _mock_version(httpx_mock, "26.1")
    assert await versioning.get_manager_version() == versioning.V26_1


async def test_connection_error_is_not_cached(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("Refused"), url=VERSION_URL)
    _mock_version(httpx_mock, "26.3")
    first = await versioning.get_manager_version()
    assert first["error"]["code"] == "CONNECTION_ERROR"
    assert await versioning.get_manager_version() == versioning.V26_3


async def test_unknown_version(httpx_mock):
    httpx_mock.add_response(method="GET", url=VERSION_URL, json="dev-build")
    result = await versioning.get_manager_version()
    assert result["error"]["code"] == "UNKNOWN_MANAGER_VERSION"


async def test_too_old_version(httpx_mock):
    httpx_mock.add_response(method="GET", url=VERSION_URL, json="25.4.0")
    result = await versioning.get_manager_version()
    assert result["error"]["code"] == "UNSUPPORTED_MANAGER_VERSION"


async def test_newer_version_uses_newest_models(httpx_mock):
    _mock_version(httpx_mock, "27.1")
    httpx_mock.add_response(method="POST", url=f"{BASE}/sensors", json={"id": "s"})
    await create_sensor(
        CreateSensorInput(
            name="IR", description="", sensor_type="INFRARED", config_file="ir.json"
        )
    )
    assert _sent_body(httpx_mock, "POST")["type"] == "INFRARED"


async def test_get_version_on_26_1(httpx_mock):
    _mock_version(httpx_mock, "26.1")
    result = json.loads(await general.get_version())
    assert result["version"] == "26.1"


# ---------------------------------------------------------------------------
# Tool gating
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        general.get_log_file_path,
        projects.get_current_project,
        simulation.get_simulation_state,
        simulation.reset_simulation,
        simulation.cancel_synchronization,
        simulation.get_scenario_state,
    ],
)
async def test_26_2_tools_rejected_on_26_1(httpx_mock, call):
    _mock_version(httpx_mock, "26.1")
    _assert_unsupported(await call(), call.__name__, "26.2", "26.1")


@pytest.mark.parametrize(
    "call",
    [simulation.get_synchronization_settings, simulation.get_simulation_hooks],
)
async def test_26_3_tools_rejected_on_26_2(httpx_mock, call):
    _mock_version(httpx_mock, "26.2")
    _assert_unsupported(await call(), call.__name__, "26.3", "26.2")


async def test_diagnostics_available_on_26_1(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/simulation/diagnostics", json=[])
    assert json.loads(await simulation.get_simulation_diagnostics()) == []


async def test_update_synchronization_settings_sends_only_given_groups(httpx_mock):
    _mock_version(httpx_mock, "26.3")
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/simulation/synchronization-settings", json={}
    )
    await simulation.update_synchronization_settings(
        simulation.UpdateSynchronizationSettingsInput(scenario_control={"autostart": True})
    )
    assert _sent_body(httpx_mock, "PUT") == {"scenarioControl": {"autostart": True}}


async def test_set_simulation_hooks_sends_array(httpx_mock):
    _mock_version(httpx_mock, "26.3")
    httpx_mock.add_response(method="PUT", url=f"{BASE}/simulation/hooks", json=[])
    await simulation.set_simulation_hooks(
        simulation.SetSimulationHooksInput(hooks=[{"path": "/pre", "isEnabled": False}])
    )
    assert _sent_body(httpx_mock, "PUT") == [{"path": "/pre", "isEnabled": False}]


# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------


def _infrared_sensor() -> CreateSensorInput:
    return CreateSensorInput(
        name="IR", description="", sensor_type="INFRARED", config_file="ir.json"
    )


async def test_infrared_sensor_rejected_on_26_1(httpx_mock):
    _mock_version(httpx_mock, "26.1")
    _assert_unsupported(await create_sensor(_infrared_sensor()), "type", "26.1")


async def test_infrared_sensor_sent_on_26_2(httpx_mock):
    _mock_version(httpx_mock, "26.2")
    httpx_mock.add_response(method="POST", url=f"{BASE}/sensors", json={"id": "s"})
    await create_sensor(_infrared_sensor())
    assert _sent_body(httpx_mock, "POST")["type"] == "INFRARED"


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------


def _vehicle_with(component: dict) -> CreateVehicleInput:
    return CreateVehicleInput(name="V", description="", components=[component])


@pytest.mark.parametrize(("version", "is_valid"), [("26.1", True), ("26.2", True), ("26.3", None)])
async def test_sensor_instance_is_valid_per_version(httpx_mock, version, is_valid):
    _mock_version(httpx_mock, version)
    httpx_mock.add_response(method="POST", url=f"{BASE}/vehicles", json={"id": "v"})
    await create_vehicle(
        CreateVehicleInput(
            name="V", description="", components=[_COMPONENT], sensor_instances=[_SENSOR_INSTANCE]
        )
    )
    (instance,) = _sent_body(httpx_mock, "POST")["sensorInstances"]
    assert instance.get("isValid") is is_valid


async def test_update_vehicle_prepends_id(httpx_mock):
    _mock_version(httpx_mock, "26.1")
    httpx_mock.add_response(method="PUT", url=f"{BASE}/vehicles/v-1", json={"id": "v-1"})
    await update_vehicle(
        UpdateVehicleInput(
            vehicle_id="v-1", name="V", description="", sensor_instances=[_SENSOR_INSTANCE]
        )
    )
    body = _sent_body(httpx_mock, "PUT")
    assert next(iter(body)) == "id"
    assert body["sensorInstances"][0]["isValid"] is True


async def test_occupant_monitoring_rejected_on_26_1(httpx_mock):
    _mock_version(httpx_mock, "26.1")
    component = {**_COMPONENT, "occupantMonitoring": {"driver": {"assetPath": "driver"}}}
    result = await create_vehicle(_vehicle_with(component))
    _assert_unsupported(result, "occupantMonitoring")


async def test_driver_asset_id_rejected_on_26_2(httpx_mock):
    _mock_version(httpx_mock, "26.2")
    component = {**_COMPONENT, "occupantMonitoring": {"driver": {"assetId": "a-1"}}}
    result = await create_vehicle(_vehicle_with(component))
    _assert_unsupported(result, "assetId")


async def test_driver_asset_id_sent_on_26_3(httpx_mock):
    _mock_version(httpx_mock, "26.3")
    httpx_mock.add_response(method="POST", url=f"{BASE}/vehicles", json={"id": "v"})
    component = {**_COMPONENT, "occupantMonitoring": {"driver": {"assetId": "a-1"}}}
    await create_vehicle(_vehicle_with(component))
    (sent,) = _sent_body(httpx_mock, "POST")["components"]
    assert sent["occupantMonitoring"]["driver"]["assetId"] == "a-1"


# ---------------------------------------------------------------------------
# Systems
# ---------------------------------------------------------------------------


async def test_ma_port_config_path_dropped_on_26_1(httpx_mock):
    _mock_version(httpx_mock, "26.1")
    httpx_mock.add_response(method="POST", url=f"{BASE}/systems", json={"id": "s"})
    await create_system(
        CreateSystemInput(
            **_SYSTEM, application={"filepath": "app.sdf", "maPortConfigPath": "ma.xml"}
        )
    )
    assert _sent_body(httpx_mock, "POST")["application"] == {"filepath": "app.sdf"}


async def test_ma_port_config_path_sent_on_26_2(httpx_mock):
    _mock_version(httpx_mock, "26.2")
    httpx_mock.add_response(method="POST", url=f"{BASE}/systems", json={"id": "s"})
    await create_system(
        CreateSystemInput(
            **_SYSTEM, application={"filepath": "app.sdf", "maPortConfigPath": "ma.xml"}
        )
    )
    assert _sent_body(httpx_mock, "POST")["application"]["maPortConfigPath"] == "ma.xml"


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"time_stamp_source": "ManeuverTime"}, "timeStampSource"),
        ({"aurelion_instances": [{**_AURELION_INSTANCE, "frameSyncMode": "Default"}]}, "frameSyncMode"),
        ({"aurelion_instances": [{**_AURELION_INSTANCE, "renderOffScreen": True}]}, "renderOffScreen"),
        (
            {"aurelion_instances": [{**_AURELION_INSTANCE, "compositeView": {"lowLatency": True}}]},
            "lowLatency",
        ),
    ],
)
async def test_26_3_system_fields_rejected_on_26_2(httpx_mock, overrides, fragment):
    _mock_version(httpx_mock, "26.2")
    _assert_unsupported(await create_system(CreateSystemInput(**_SYSTEM, **overrides)), fragment)


async def test_26_3_system_fields_sent_on_26_3(httpx_mock):
    _mock_version(httpx_mock, "26.3")
    httpx_mock.add_response(method="POST", url=f"{BASE}/systems", json={"id": "s"})
    await create_system(
        CreateSystemInput(
            **_SYSTEM,
            time_stamp_source="ManeuverTime",
            aurelion_instances=[{**_AURELION_INSTANCE, "frameSyncMode": "LowLatency"}],
        )
    )
    body = _sent_body(httpx_mock, "POST")
    assert body["timeStampSource"] == "ManeuverTime"
    assert body["aurelionInstances"][0]["frameSyncMode"] == "LowLatency"
