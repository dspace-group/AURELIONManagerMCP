"""Unit tests for scenario tools."""

import json

import httpx

from aurelion_manager_mcp import client
from aurelion_manager_mcp.tools.scenarios import (
    CreateScenarioInput,
    DeleteScenarioInput,
    GetScenarioInput,
    GetScenarioParametersInput,
    GetScenarioValidationInput,
    UpdateScenarioInput,
    create_scenario,
    delete_scenario,
    get_scenario,
    get_scenario_parameters,
    get_scenario_validation_result,
    list_scenarios,
    update_scenario,
)

BASE = f"{client.AURELION_MANAGER_API_URL}{client.API_BASE_PATH}"

SAMPLE_SCENARIO = {
    "id": "scn-abc-123",
    "name": "Highway Merge Test",
    "description": "Highway merge scenario",
    "type": "OpenScenario",
    "xoscPath": "C:/Scenarios/highway_merge.xosc",
}


# ---------------------------------------------------------------------------
# list_scenarios
# ---------------------------------------------------------------------------


async def test_list_scenarios_success(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/scenarios", json=[SAMPLE_SCENARIO]
    )
    result = json.loads(await list_scenarios())
    assert result == [SAMPLE_SCENARIO]


async def test_list_scenarios_no_project(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/scenarios", status_code=412)
    result = json.loads(await list_scenarios())
    assert result["error"]["code"] == "NO_OPEN_PROJECT"
    assert result["error"]["type"] == "permanent"


async def test_list_scenarios_connection_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("Refused"))
    result = json.loads(await list_scenarios())
    assert result["error"]["code"] == "CONNECTION_ERROR"


# ---------------------------------------------------------------------------
# get_scenario
# ---------------------------------------------------------------------------


async def test_get_scenario_success(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/scenarios/scn-abc-123", json=SAMPLE_SCENARIO
    )
    result = json.loads(await get_scenario(GetScenarioInput(scenario_id="scn-abc-123")))
    assert result["id"] == "scn-abc-123"
    assert result["type"] == "OpenScenario"


async def test_get_scenario_not_found(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{BASE}/scenarios/no-such", status_code=404
    )
    result = json.loads(await get_scenario(GetScenarioInput(scenario_id="no-such")))
    assert result["error"]["type"] == "permanent"


# ---------------------------------------------------------------------------
# create_scenario
# ---------------------------------------------------------------------------


async def test_create_openscenario_success(httpx_mock):
    created = {**SAMPLE_SCENARIO, "id": "scn-new-456"}
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/scenarios", status_code=201, json=created
    )
    result = json.loads(
        await create_scenario(
            CreateScenarioInput(
                name="Highway Merge Test",
                description="Highway scenario",
                scenario_type="OpenScenario",
                xosc_path="C:/Scenarios/highway_merge.xosc",
            )
        )
    )
    assert result["id"] == "scn-new-456"


async def test_create_modeldesk_scenario_success(httpx_mock):
    md_scenario = {
        "id": "scn-md-789",
        "name": "ASM City Drive",
        "type": "ModelDesk",
    }
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/scenarios", status_code=201, json=md_scenario
    )
    result = json.loads(
        await create_scenario(
            CreateScenarioInput(
                name="ASM City Drive",
                description="ModelDesk scenario",
                scenario_type="ModelDesk",
            )
        )
    )
    assert result["type"] == "ModelDesk"


# ---------------------------------------------------------------------------
# update_scenario
# ---------------------------------------------------------------------------


async def test_update_scenario_success(httpx_mock):
    updated = {**SAMPLE_SCENARIO, "name": "Updated Scenario"}
    httpx_mock.add_response(
        method="PUT", url=f"{BASE}/scenarios/scn-abc-123", json=updated
    )
    result = json.loads(
        await update_scenario(
            UpdateScenarioInput(
                scenario_id="scn-abc-123",
                name="Updated Scenario",
                description="Updated",
                scenario_type="OpenScenario",
                xosc_path="C:/Scenarios/updated.xosc",
            )
        )
    )
    assert result["name"] == "Updated Scenario"


# ---------------------------------------------------------------------------
# delete_scenario
# ---------------------------------------------------------------------------


async def test_delete_scenario_success(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE}/scenarios/scn-abc-123", status_code=200
    )
    result = json.loads(
        await delete_scenario(DeleteScenarioInput(scenario_id="scn-abc-123"))
    )
    assert "error" not in result


# ---------------------------------------------------------------------------
# get_scenario_parameters
# ---------------------------------------------------------------------------


async def test_get_scenario_parameters_success(httpx_mock):
    params = [
        {"name": "Ego_Speed", "parameterType": "double", "value": {"value": "80"}},
        {"name": "TrafficDensity", "parameterType": "string"},
    ]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/scenarios/scn-abc-123/parameters",
        json=params,
    )
    result = json.loads(
        await get_scenario_parameters(
            GetScenarioParametersInput(scenario_id="scn-abc-123")
        )
    )
    assert len(result) == 2
    assert result[0]["name"] == "Ego_Speed"


async def test_get_scenario_parameters_not_found(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/scenarios/no-such/parameters",
        status_code=404,
    )
    result = json.loads(
        await get_scenario_parameters(
            GetScenarioParametersInput(scenario_id="no-such")
        )
    )
    assert result["error"]["type"] == "permanent"


# ---------------------------------------------------------------------------
# get_scenario_validation_result
# ---------------------------------------------------------------------------


async def test_get_scenario_validation_success(httpx_mock):
    validation = {
        "isValid": True,
        "results": [{"file": "highway_merge.xosc", "isValid": True, "errors": []}],
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/scenarios/scn-abc-123/validation-result",
        json=validation,
    )
    result = json.loads(
        await get_scenario_validation_result(
            GetScenarioValidationInput(scenario_id="scn-abc-123")
        )
    )
    assert result["isValid"] is True


async def test_get_scenario_validation_failure(httpx_mock):
    validation = {
        "isValid": False,
        "results": [
            {
                "file": "broken.xosc",
                "isValid": False,
                "errors": ["Line 42: unknown entity"],
            }
        ],
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/scenarios/scn-abc-123/validation-result",
        json=validation,
    )
    result = json.loads(
        await get_scenario_validation_result(
            GetScenarioValidationInput(scenario_id="scn-abc-123")
        )
    )
    assert result["isValid"] is False
    assert len(result["results"][0]["errors"]) == 1
