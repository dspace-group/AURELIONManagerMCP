"""Structured request schemas shared by the AURELION Manager tools.

Models that changed between AURELION Manager versions carry a ``V<major>_<minor>``
suffix naming the version that introduced them; newer versions subclass older ones.
Tools expose the newest models to the LLM.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from aurelion_manager_mcp.versioning import V26_1, V26_2, V26_3


class ApiSchema(BaseModel):
    """Base schema for API objects with a closed set of properties."""

    model_config = ConfigDict(extra="forbid")


class Vector3(ApiSchema):
    x: float
    y: float
    z: float


class Rotation(ApiSchema):
    roll: float
    yaw: float
    pitch: float


class Tag(ApiSchema):
    name: str


class SensorInstanceV26_3(ApiSchema):
    vehicleComponentId: str
    sensorNumber: float
    mountingObject: str | None = None
    rotation: Rotation
    position: Vector3
    enable: bool
    sensorId: str
    name: str
    id: str


# 26.3 removed 'isValid', so the older model extends the newer one.
class SensorInstanceV26_1(SensorInstanceV26_3):
    isValid: bool = True


class AssetProperty(ApiSchema):
    name: str
    description: str | None = None
    value: str | None = None
    type: str | None = None
    isReadOnly: bool | None = None
    range: str | None = None


class DataStreamMapping(ApiSchema):
    id: str | None = None
    type: str | None = None
    properties: list[AssetProperty] | None = None


class DataStream(ApiSchema):
    name: str | None = None
    type: str | None = None
    id: str | None = None
    mappings: list[DataStreamMapping] | None = None


class GazeLocation(ApiSchema):
    name: str | None = None
    z: float
    y: float
    x: float
    id: float


class ApiInfraredLightSource(ApiSchema):
    rotation: Rotation
    position: Vector3
    attenuationRadius: float
    outerConeAngle: float
    innerConeAngle: float
    intensity: float
    assetPath: str


class DriverOccupantMonitoringV26_2(ApiSchema):
    gazeLocations: list[GazeLocation] | None = None
    accessory: str | None = None
    seatbeltDataStream: str | None = None
    driverAnimationDataStream: str | None = None
    lizardOwlRatioDataStream: str | None = None
    gazeLocationDataStream: str | None = None
    assetPath: str | None = None


class DriverOccupantMonitoringV26_3(DriverOccupantMonitoringV26_2):
    assetId: str | None = Field(
        None,
        description="AURELION asset ID of the driver. Requires AURELION Manager >= 26.3.",
    )


class OccupantMonitoringV26_2(ApiSchema):
    infraredLightSources: list[ApiInfraredLightSource] | None = None
    driver: DriverOccupantMonitoringV26_2 | None = None


class OccupantMonitoringV26_3(OccupantMonitoringV26_2):
    driver: DriverOccupantMonitoringV26_3 | None = None


class ApiVehicleComponentV26_1(ApiSchema):
    assetType: Literal["custom-asset", "aurelion-asset"] | None = None
    sensorMountingObjects: list[str] | None = None
    dataStreams: list[DataStream] | None = None
    baseDataStream: str | None = None
    assetPath: str | None = None
    mappingFile: str | None = None
    model3d: str | None = None
    name: str
    id: str


class ApiVehicleComponentV26_2(ApiVehicleComponentV26_1):
    occupantMonitoring: OccupantMonitoringV26_2 | None = Field(
        None, description="Occupant monitoring setup. Requires AURELION Manager >= 26.2."
    )


class ApiVehicleComponentV26_3(ApiVehicleComponentV26_2):
    occupantMonitoring: OccupantMonitoringV26_3 | None = Field(
        None, description="Occupant monitoring setup. Requires AURELION Manager >= 26.2."
    )


class IpConnection(ApiSchema):
    port: float
    host: str


class CustomDataPort(ApiSchema):
    updateRate: float
    port: float


class ModelSimulatorAdvancedPortConfiguration(ApiSchema):
    customDataPorts: list[CustomDataPort]
    clifPort: float | None = None


class ModelPathsConfiguration(ApiSchema):
    pathScenarioTime: str
    pathScenarioState: str
    pathScenarioStop: str
    pathScenarioStart: str
    pathScenarioReset: str


class ModelSimulator(ApiSchema):
    modelConfiguration: ModelPathsConfiguration
    advancedPortConfiguration: ModelSimulatorAdvancedPortConfiguration | None = None
    motionData: IpConnection | None = None
    host: str
    type: Literal["VEOS", "SCALEXIO"]


class SdBroker(ApiSchema):
    ip: str
    publisherPort: float
    registerPort: float
    api: IpConnection


class Mapping(ApiSchema):
    sensorInstanceId: str


class VEsiConnectionSettings(ApiSchema):
    enableManeuverTsSync: bool | None = None
    customDataChannelPort: float | None = None
    enableCustomDataChannel: bool | None = None
    osiGTPort: float | None = None
    enableOsiGT: bool | None = None
    restbusSimulationPort: float | None = None
    enableRestbusSimulation: bool | None = None
    saveFrameAsBinary: bool | None = None
    saveFrameAsPng: bool | None = None
    simulateHeaderSensorId: float | None = None
    simulateHeader: bool | None = None
    spsPort: float | None = None
    spsIp: str | None = None
    streamingPortRangeUpper: float | None = None
    streamingPortRangeLower: float | None = None
    streamingIp: str | None = None
    streamingVersion: str | None = None


class CompositeViewSettingsV26_1(ApiSchema):
    enableCompositeView: bool | None = None
    windowPosition: str | None = None
    saveFrameAsPng: bool | None = None
    frameSyncMode: str | None = None
    renderExclusively: bool | None = None
    windowMode: Literal["None", "Fullscreen", "WindowedFullscreen", "Windowed"] | None = None
    usePredefinedResolution: bool | None = None
    showHeader: bool | None = None
    screenResolution: str | None = None
    isTopMostWindow: bool | None = None
    displayInUse: float | None = None


class CompositeViewSettingsV26_3(CompositeViewSettingsV26_1):
    frameSyncMode: str | None = Field(
        None,
        description=(
            "Deprecated since AURELION Manager 26.3: use the AURELION instance's "
            "'frameSyncMode' instead."
        ),
    )
    lowLatency: bool | None = Field(
        None,
        description="Enable low-latency mode for the composite view. Requires AURELION Manager >= 26.3.",
    )


class SystemAurelionInstanceV26_1(ApiSchema):
    enabled: bool
    compositeView: CompositeViewSettingsV26_1 | None = None
    vEsiSetting: VEsiConnectionSettings | None = None
    connection: IpConnection
    enableSceneView: bool
    gpuIndex: float
    enableGpuIndex: bool
    sampleTime: float
    mappings: list[Mapping]
    name: str
    id: str


class SystemAurelionInstanceV26_3(SystemAurelionInstanceV26_1):
    compositeView: CompositeViewSettingsV26_3 | None = None
    frameSyncMode: Literal["None", "Default", "LowLatency"] | None = Field(
        None,
        description=(
            "Frame synchronization mode of the AURELION instance. "
            "Requires AURELION Manager >= 26.3."
        ),
    )
    renderOffScreen: bool | None = Field(
        None,
        description="Render the AURELION instance off-screen. Requires AURELION Manager >= 26.3.",
    )


class VehicleReference(ApiSchema):
    name: str
    id: str


class ModelApplicationV26_1(ApiSchema):
    filepath: str | None = None
    # 26.1 has no MA port configuration, but the newer tool schema requires one.
    maPortConfigPath: SkipJsonSchema[str | None] = Field(None, exclude=True)


class ModelApplicationV26_2(ModelApplicationV26_1):
    maPortConfigPath: str = Field(
        ...,
        description="Path to the MA port configuration. Ignored by AURELION Manager 26.1.",
    )


class VegetationGeneration(ApiSchema):
    grassGeneration: bool
    generationCorridorMax: float
    generationCorridorMin: float
    density: float
    enabled: bool


class MaterialDamage(ApiSchema):
    roadMarkingBrightness: float
    roadMarkingDamage: float
    enabled: bool


class RsgScenery(ApiSchema):
    materialDamage: MaterialDamage
    vegetationGeneration: VegetationGeneration
    selection: Literal["rsg"]


class SceneryAurelionEnvironment(ApiSchema):
    path: str
    name: str


class ApiAurScenery(ApiSchema):
    scene: SceneryAurelionEnvironment
    selection: Literal["aur"]


class GlbScenery(ApiSchema):
    path: str
    selection: Literal["glb"]


Scenery = Annotated[
    RsgScenery | ApiAurScenery | GlbScenery,
    Field(discriminator="selection"),
]


# ── Request bodies ──


class VehicleUserInputV26_1(ApiSchema):
    name: str
    description: str
    components: list[ApiVehicleComponentV26_1]
    sensorInstances: list[SensorInstanceV26_1]
    imageFile: str | None = None
    tags: list[Tag] | None = None


class VehicleUserInputV26_2(VehicleUserInputV26_1):
    components: list[ApiVehicleComponentV26_2]


class VehicleUserInputV26_3(VehicleUserInputV26_2):
    components: list[ApiVehicleComponentV26_3]
    sensorInstances: list[SensorInstanceV26_3]


class SystemUserInputV26_1(ApiSchema):
    name: str
    description: str
    type: Literal["ASM", "Replay"]
    modelSimulator: ModelSimulator
    sdBroker: SdBroker
    aurelionInstances: list[SystemAurelionInstanceV26_1]
    sutControlSimFrequency: float
    enableSuts: bool
    numSuts: float
    hideEgoFromSensors: bool
    vehicle: VehicleReference | None = None
    application: ModelApplicationV26_1 | None = None


class SystemUserInputV26_2(SystemUserInputV26_1):
    application: ModelApplicationV26_2 | None = None


class SystemUserInputV26_3(SystemUserInputV26_2):
    aurelionInstances: list[SystemAurelionInstanceV26_3]
    timeStampSource: Literal["SimulationTime", "ManeuverTime"] | None = None


class SensorUserInputV26_1(ApiSchema):
    name: str
    description: str
    type: Literal["CAMERA", "RADAR", "LIDAR", "ULTRASONIC"]
    configFile: str
    imageFile: str | None = None
    additionalFilesDirectory: str | None = None
    tags: list[Tag] | None = None


class SensorUserInputV26_2(SensorUserInputV26_1):
    type: Literal["CAMERA", "RADAR", "LIDAR", "ULTRASONIC", "INFRARED"]


# Keyed by the version that introduced each model.
VEHICLE_USER_INPUT = {
    V26_1: VehicleUserInputV26_1,
    V26_2: VehicleUserInputV26_2,
    V26_3: VehicleUserInputV26_3,
}
SYSTEM_USER_INPUT = {
    V26_1: SystemUserInputV26_1,
    V26_2: SystemUserInputV26_2,
    V26_3: SystemUserInputV26_3,
}
SENSOR_USER_INPUT = {V26_1: SensorUserInputV26_1, V26_2: SensorUserInputV26_2}


# ── AURELION Manager 26.3 only ──


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