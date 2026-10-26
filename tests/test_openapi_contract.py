"""Check the versioned request models against the OpenAPI specs of each AURELION Manager version."""

import json
import types
import typing
from pathlib import Path

import pytest
from pydantic import BaseModel

from aurelion_manager_mcp import versioning
from aurelion_manager_mcp.tools.schemas import sensors, simulation, systems, vehicles

SPEC_DIR = Path(__file__).parent / "openapi"
VERSIONS = {
    versioning.V26_1: "openapi_v1_26.1.0.json",
    versioning.V26_2: "openapi_v1_26.2.0.json",
    versioning.V26_3: "openapi_v1_26.3.0.json",
}

# (model, field) pairs that deliberately differ from the spec.
KNOWN_DIFFERENCES = {
    # Filled in with a default because the newest tool schema no longer has it.
    ("SensorInstanceV26_1", "isValid"),
    # Deprecated in 26.3; superseded by the AURELION instance's 'renderOffScreen'.
    ("CompositeViewSettingsV26_3", "renderOffScreen"),
}


def _load_spec(version: versioning.Version) -> dict:
    return json.loads((SPEC_DIR / VERSIONS[version]).read_text(encoding="utf-8"))


def _resolve(spec: dict, schema: dict) -> dict:
    """Follow ``$ref`` and merge ``allOf`` into a single schema."""
    while "$ref" in schema:
        schema = spec["components"]["schemas"][schema["$ref"].rsplit("/", 1)[1]]
    if "allOf" not in schema:
        return schema
    merged: dict = {"properties": {}, "required": []}
    for part in schema["allOf"]:
        part = _resolve(spec, part)
        merged["properties"].update(part.get("properties", {}))
        merged["required"] += part.get("required", [])
        for key in ("enum", "items", "type"):
            if key in part:
                merged[key] = part[key]
    return merged


def _unwrap(annotation) -> object:
    """Strip Optional, list and Annotated wrappers from a field annotation."""
    while True:
        origin = typing.get_origin(annotation)
        if origin in (typing.Union, types.UnionType):
            (annotation,) = [a for a in typing.get_args(annotation) if a is not type(None)]
        elif origin in (list, typing.Annotated):
            annotation = typing.get_args(annotation)[0]
        else:
            return annotation


def _compare(spec: dict, model: type[BaseModel], schema: dict, path: str) -> list[str]:
    schema = _resolve(spec, schema)
    if schema.get("type") == "array":
        schema = _resolve(spec, schema["items"])
    fields = {name: f for name, f in model.model_fields.items() if not f.exclude}
    spec_properties = schema.get("properties", {})
    spec_required = set(schema.get("required", []))
    problems = []

    for name in fields.keys() ^ spec_properties.keys():
        if (model.__name__, name) not in KNOWN_DIFFERENCES:
            where = "model" if name in fields else "spec"
            problems.append(f"{path}.{name}: only in {where} ({model.__name__})")

    for name, field in fields.items():
        if name not in spec_properties:
            continue
        if field.is_required() != (name in spec_required) and (
            (model.__name__, name) not in KNOWN_DIFFERENCES
        ):
            problems.append(f"{path}.{name}: required mismatch ({model.__name__})")

        sub_schema = _resolve(spec, spec_properties[name])
        if sub_schema.get("type") == "array":
            sub_schema = _resolve(spec, sub_schema["items"])
        inner = _unwrap(field.annotation)
        if isinstance(inner, type) and issubclass(inner, BaseModel):
            problems += _compare(spec, inner, sub_schema, f"{path}.{name}")
        elif typing.get_origin(inner) is typing.Literal or "enum" in sub_schema:
            model_values = set(typing.get_args(inner))
            if model_values != set(sub_schema.get("enum", [])):
                problems.append(
                    f"{path}.{name}: enum {sorted(model_values)} != "
                    f"{sorted(sub_schema.get('enum', []))}"
                )
    return problems


def _model_for(registry: dict, version: versioning.Version) -> type[BaseModel]:
    return registry[max(v for v in registry if v <= version)]


@pytest.mark.parametrize("version", list(VERSIONS), ids=versioning.format_version)
@pytest.mark.parametrize(
    ("registry", "spec_schema"),
    [
        (vehicles.VEHICLE_USER_INPUT, "VehicleUserInput"),
        (systems.SYSTEM_USER_INPUT, "SystemUserInput"),
        (sensors.SENSOR_USER_INPUT, "SensorUserInput"),
    ],
    ids=["vehicle", "system", "sensor"],
)
def test_request_body_matches_spec(version, registry, spec_schema):
    spec = _load_spec(version)
    model = _model_for(registry, version)
    schema = {"$ref": f"#/components/schemas/{spec_schema}"}
    assert _compare(spec, model, schema, spec_schema) == []


def test_compare_detects_version_differences():
    spec = _load_spec(versioning.V26_3)
    vehicle = {"$ref": "#/components/schemas/VehicleUserInput"}
    system = {"$ref": "#/components/schemas/SystemUserInput"}
    sensor = {"$ref": "#/components/schemas/SensorUserInput"}
    assert _compare(spec, vehicles.VehicleUserInputV26_2, vehicle, "V") == [
        "V.components.occupantMonitoring.driver.assetId: only in spec "
        "(DriverOccupantMonitoringV26_2)"
    ]
    assert "S.timeStampSource: only in spec (SystemUserInputV26_2)" in _compare(
        spec, systems.SystemUserInputV26_2, system, "S"
    )
    assert _compare(spec, sensors.SensorUserInputV26_1, sensor, "T") == [
        "T.type: enum ['CAMERA', 'LIDAR', 'RADAR', 'ULTRASONIC'] != "
        "['CAMERA', 'INFRARED', 'LIDAR', 'RADAR', 'ULTRASONIC']"
    ]


@pytest.mark.parametrize(
    ("model", "spec_property"),
    [
        (simulation.AsmGtVisualizationSettings, "asmGtVisualization"),
        (simulation.ScenarioControlSettings, "scenarioControl"),
        (simulation.RoadAndSceneryGeneratorSettings, "roadAndSceneryGenerator"),
        (simulation.ApplicationSynchronizationSettings, "application"),
    ],
)
def test_synchronization_settings_match_spec(model, spec_property):
    spec = _load_spec(versioning.V26_3)
    settings = spec["components"]["schemas"]["SynchronizationSettings"]
    assert _compare(spec, model, settings["properties"][spec_property], spec_property) == []


def test_simulation_hook_matches_spec():
    spec = _load_spec(versioning.V26_3)
    schema = {"$ref": "#/components/schemas/HookV1"}
    assert _compare(spec, simulation.SimulationHook, schema, "HookV1") == []


# (method, path, version that introduced the endpoint) for every gated tool.
GATED_ENDPOINTS = [
    ("get", "/general/settings/log", versioning.V26_2),
    ("get", "/projects/current-project", versioning.V26_2),
    ("put", "/projects/open-project", versioning.V26_2),
    ("get", "/simulation/state", versioning.V26_2),
    ("get", "/simulation/preconditions/{systemId}/{scenarioId}", versioning.V26_2),
    ("post", "/simulation/synchronize/{systemId}/{scenarioId}", versioning.V26_2),
    ("put", "/simulation/reset", versioning.V26_2),
    ("put", "/simulation/cancel", versioning.V26_2),
    ("get", "/scenario-state", versioning.V26_2),
    ("put", "/scenario-state", versioning.V26_2),
    ("get", "/simulation/synchronization-settings", versioning.V26_3),
    ("put", "/simulation/synchronization-settings", versioning.V26_3),
    ("get", "/simulation/hooks", versioning.V26_3),
    ("put", "/simulation/hooks", versioning.V26_3),
]


@pytest.mark.parametrize("version", list(VERSIONS), ids=versioning.format_version)
def test_gated_endpoints_match_spec(version):
    paths = _load_spec(version)["paths"]
    for method, path, introduced in GATED_ENDPOINTS:
        exists = method in paths.get(path, {})
        assert exists == (version >= introduced), (method, path)


@pytest.mark.parametrize("version", list(VERSIONS), ids=versioning.format_version)
def test_ungated_endpoints_exist_in_all_versions(version):
    paths = _load_spec(version)["paths"]
    for path in ("/vehicles", "/systems", "/sensors", "/scenarios", "/simulation/diagnostics"):
        assert path in paths
