"""System request schemas."""

from typing import Literal

from pydantic import Field
from pydantic.json_schema import SkipJsonSchema

from aurelion_manager_mcp.tools.schemas.common import ApiSchema, IpConnection
from aurelion_manager_mcp.versioning import V26_1, V26_2, V26_3


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


# Keyed by the version that introduced each model.
SYSTEM_USER_INPUT = {
    V26_1: SystemUserInputV26_1,
    V26_2: SystemUserInputV26_2,
    V26_3: SystemUserInputV26_3,
}
