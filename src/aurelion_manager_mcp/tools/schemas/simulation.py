"""Simulation request schemas (AURELION Manager 26.3 and newer)."""

from pydantic import Field

from aurelion_manager_mcp.tools.schemas.common import ApiSchema


class AsmGtVisualizationSettings(ApiSchema):
    sensorCones: bool = Field(..., description="Visualize sensor cones provided by ASM sensor data.")
    laneArrows: bool = Field(..., description="Visualize lane arrows provided by ASM sensor data.")
    sensorPoints: bool = Field(..., description="Visualize sensor points provided by ASM sensor data.")
    boundingBoxes: bool = Field(
        ..., description="Visualize bounding boxes provided by ASM sensor data."
    )


class ScenarioControlSettings(ApiSchema):
    autostart: bool = Field(
        ..., description="Start the scenario automatically after synchronization."
    )


class RoadAndSceneryGeneratorSettings(ApiSchema):
    configPath: str | None = Field(None, description="Path to the RSG configuration file.")


class ApplicationSynchronizationSettings(ApiSchema):
    downloadWhenDifferent: bool = Field(
        ..., description="Replace a downloaded application if present."
    )


class SimulationHook(ApiSchema):
    path: str = Field(..., description="Path identifying the hook, as returned by get_simulation_hooks.")
    isEnabled: bool = Field(..., description="Whether the hook runs during synchronization.")
