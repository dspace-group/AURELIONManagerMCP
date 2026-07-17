"""Unit tests for simulation control tools."""

import json

import httpx

from aurelion_manager_mcp import client
from aurelion_manager_mcp.tools.simulation import (
    CheckPreconditionsInput,
    ControlScenarioStateInput,
    SynchronizeSimulationInput,
    cancel_synchronization,
    check_simulation_preconditions,
    control_scenario_state,
    get_scenario_state,
    get_simulation_diagnostics,
    get_simulation_state,
    reset_simulation,
    synchronize_simulation,
)

BASE = f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}"


# ---------------------------------------------------------------------------
# get_simulation_state
# ---------------------------------------------------------------------------


async def test_get_simulation_state_success(httpx_mock):
    state = {"system": {"id": "sys-1", "name": "ASM System"}, "scenario": {"id": "scn-1"}}
    httpx_mock.add_response(method="GET", url=f"{BASE}/simulation/state", json=state)
    result = json.loads(await get_simulation_state())
    assert result["system"]["id"] == "sys-1"


async def test_get_simulation_state_no_project(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/simulation/state", status_code=412
    )
    result = json.loads(await get_simulation_state())
    assert result["error"]["code"] == "NO_OPEN_PROJECT"
    assert result["error"]["type"] == "permanent"


# ---------------------------------------------------------------------------
# get_simulation_diagnostics
# ---------------------------------------------------------------------------


async def test_get_simulation_diagnostics_success(httpx_mock):
    diag = {
        "aurelion": {"status": "Connected"},
        "modelDesk": {"status": "Connected"},
    }
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/simulation/diagnostics", json=diag
    )
    result = json.loads(await get_simulation_diagnostics())
    assert result["aurelion"]["status"] == "Connected"


async def test_get_simulation_diagnostics_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("Refused"))
    result = json.loads(await get_simulation_diagnostics())
    assert result["error"]["type"] == "transient"


# ---------------------------------------------------------------------------
# check_simulation_preconditions
# ---------------------------------------------------------------------------


async def test_check_preconditions_met(httpx_mock):
    preconditions = {"conditionsMet": True, "errors": [], "warnings": []}
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/simulation/preconditions/sys-1/scn-1",
        json=preconditions,
    )
    result = json.loads(
        await check_simulation_preconditions(
            CheckPreconditionsInput(system_id="sys-1", scenario_id="scn-1")
        )
    )
    assert result["conditionsMet"] is True
    assert result["errors"] == []


async def test_check_preconditions_not_met(httpx_mock):
    preconditions = {
        "conditionsMet": False,
        "errors": ["ModelDesk not connected", "AURELION instance offline"],
        "warnings": [],
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/simulation/preconditions/sys-1/scn-1",
        json=preconditions,
    )
    result = json.loads(
        await check_simulation_preconditions(
            CheckPreconditionsInput(system_id="sys-1", scenario_id="scn-1")
        )
    )
    assert result["conditionsMet"] is False
    assert len(result["errors"]) == 2


# ---------------------------------------------------------------------------
# synchronize_simulation
# ---------------------------------------------------------------------------


async def test_synchronize_with_ids(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/simulation/synchronize/sys-1/scn-1",
        status_code=204,
    )
    result = json.loads(
        await synchronize_simulation(
            SynchronizeSimulationInput(system_id="sys-1", scenario_id="scn-1")
        )
    )
    assert result.get("success") is True


async def test_synchronize_without_ids(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/simulation/synchronize",
        status_code=204,
    )
    result = json.loads(await synchronize_simulation(SynchronizeSimulationInput()))
    assert result.get("success") is True


async def test_synchronize_with_scenario_params(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/simulation/synchronize/sys-1/scn-1",
        status_code=204,
    )
    result = json.loads(
        await synchronize_simulation(
            SynchronizeSimulationInput(
                system_id="sys-1",
                scenario_id="scn-1",
                autostart=True,
                scenario_parameter_values={"Ego_Speed": "80"},
            )
        )
    )
    assert result.get("success") is True


async def test_synchronize_server_error(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/simulation/synchronize",
        status_code=500,
    )
    result = json.loads(await synchronize_simulation(SynchronizeSimulationInput()))
    assert result["error"]["type"] == "transient"


# ---------------------------------------------------------------------------
# reset_simulation
# ---------------------------------------------------------------------------


async def test_reset_simulation_success(httpx_mock):
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/simulation/reset", status_code=204
    )
    result = json.loads(await reset_simulation())
    assert result.get("success") is True


# ---------------------------------------------------------------------------
# cancel_synchronization
# ---------------------------------------------------------------------------


async def test_cancel_synchronization_success(httpx_mock):
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/simulation/cancel", status_code=204
    )
    result = json.loads(await cancel_synchronization())
    assert result.get("success") is True


# ---------------------------------------------------------------------------
# get_scenario_state
# ---------------------------------------------------------------------------


async def test_get_scenario_state_running(httpx_mock):
    state = {"scenario": "Running", "time": 12.5}
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/scenario-state", json=state
    )
    result = json.loads(await get_scenario_state())
    assert result["scenario"] == "Running"
    assert result["time"] == 12.5


async def test_get_scenario_state_disconnected(httpx_mock):
    state = {"scenario": "Disconnected", "time": 0}
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/scenario-state", json=state
    )
    result = json.loads(await get_scenario_state())
    assert result["scenario"] == "Disconnected"


# ---------------------------------------------------------------------------
# control_scenario_state
# ---------------------------------------------------------------------------


async def test_control_scenario_state_running(httpx_mock):
    httpx_mock.add_response(method="PUT", url=f"{BASE}/scenario-state", status_code=200)
    result = json.loads(
        await control_scenario_state(ControlScenarioStateInput(state="Running"))
    )
    assert "error" not in result


async def test_control_scenario_state_stopped(httpx_mock):
    httpx_mock.add_response(method="PUT", url=f"{BASE}/scenario-state", status_code=200)
    result = json.loads(
        await control_scenario_state(ControlScenarioStateInput(state="Stopped"))
    )
    assert "error" not in result


async def test_control_scenario_state_reset(httpx_mock):
    httpx_mock.add_response(method="PUT", url=f"{BASE}/scenario-state", status_code=200)
    result = json.loads(
        await control_scenario_state(ControlScenarioStateInput(state="Reset"))
    )
    assert "error" not in result


async def test_control_scenario_state_server_error(httpx_mock):
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/scenario-state", status_code=500
    )
    result = json.loads(
        await control_scenario_state(ControlScenarioStateInput(state="Running"))
    )
    assert result["error"]["type"] == "transient"
