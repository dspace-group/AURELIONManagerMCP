"""Regression tests for MCP tool input JSON Schemas."""

from aurelion_manager_mcp.tools.scenarios import CreateScenarioInput
from aurelion_manager_mcp.tools.systems import CreateSystemInput
from aurelion_manager_mcp.tools.vehicles import CreateVehicleInput


def test_vehicle_input_schema_uses_structured_component_and_sensor_definitions():
    schema = CreateVehicleInput.model_json_schema()

    assert schema["properties"]["components"]["items"] == {
        "$ref": "#/$defs/ApiVehicleComponent"
    }
    assert schema["properties"]["sensor_instances"]["items"] == {
        "$ref": "#/$defs/SensorInstance"
    }
    assert schema["$defs"]["ApiVehicleComponent"]["required"] == ["name", "id"]
    assert schema["$defs"]["SensorInstance"]["required"] == [
        "vehicleComponentId",
        "sensorNumber",
        "isValid",
        "rotation",
        "position",
        "enable",
        "sensorId",
        "name",
        "id",
    ]


def test_system_input_schema_uses_structured_definitions():
    schema = CreateSystemInput.model_json_schema()

    assert schema["properties"]["model_simulator"]["$ref"] == (
        "#/$defs/ModelSimulator"
    )
    assert schema["properties"]["sd_broker"]["$ref"] == "#/$defs/SdBroker"
    assert schema["properties"]["aurelion_instances"]["items"] == {
        "$ref": "#/$defs/SystemAurelionInstance"
    }
    assert schema["properties"]["vehicle"]["anyOf"][0] == {
        "$ref": "#/$defs/VehicleReference"
    }
    assert schema["properties"]["application"]["anyOf"][0] == {
        "$ref": "#/$defs/ModelApplication"
    }


def test_scenery_schema_is_discriminated_by_selection():
    schema = CreateScenarioInput.model_json_schema()
    scenery = schema["properties"]["scenery"]["anyOf"][0]

    assert scenery["discriminator"] == {
        "mapping": {
            "aur": "#/$defs/ApiAurScenery",
            "glb": "#/$defs/GlbScenery",
            "rsg": "#/$defs/RsgScenery",
        },
        "propertyName": "selection",
    }
    assert scenery["oneOf"] == [
        {"$ref": "#/$defs/RsgScenery"},
        {"$ref": "#/$defs/ApiAurScenery"},
        {"$ref": "#/$defs/GlbScenery"},
    ]