"""Structured request schemas shared by the AURELION Manager tools."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


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


class SensorInstance(ApiSchema):
    vehicleComponentId: str
    sensorNumber: float
    mountingObject: str | None = None
    isValid: bool
    rotation: Rotation
    position: Vector3
    enable: bool
    sensorId: str
    name: str
    id: str


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


class DriverOccupantMonitoring(ApiSchema):
    gazeLocations: list[GazeLocation] | None = None
    accessory: str | None = None
    seatbeltDataStream: str | None = None
    driverAnimationDataStream: str | None = None
    lizardOwlRatioDataStream: str | None = None
    gazeLocationDataStream: str | None = None
    assetPath: str | None = None


class OccupantMonitoring(ApiSchema):
    infraredLightSources: list[ApiInfraredLightSource] | None = None
    driver: DriverOccupantMonitoring | None = None


class ApiVehicleComponent(ApiSchema):
    occupantMonitoring: OccupantMonitoring | None = None
    assetType: Literal["custom-asset", "aurelion-asset"] | None = None
    sensorMountingObjects: list[str] | None = None
    dataStreams: list[DataStream] | None = None
    baseDataStream: str | None = None
    assetPath: str | None = None
    mappingFile: str | None = None
    model3d: str | None = None
    name: str
    id: str


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


class CompositeViewSettings(ApiSchema):
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


class SystemAurelionInstance(ApiSchema):
    enabled: bool
    compositeView: CompositeViewSettings | None = None
    vEsiSetting: VEsiConnectionSettings | None = None
    connection: IpConnection
    enableSceneView: bool
    gpuIndex: float
    enableGpuIndex: bool
    sampleTime: float
    mappings: list[Mapping]
    name: str
    id: str


class VehicleReference(ApiSchema):
    name: str
    id: str


class ModelApplication(ApiSchema):
    maPortConfigPath: str
    filepath: str | None = None


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