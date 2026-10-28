"""Vehicle request schemas."""

from typing import Literal

from pydantic import Field

from aurelion_manager_mcp.tools.schemas.common import ApiSchema, Rotation, Tag, Vector3
from aurelion_manager_mcp.versioning import V26_1, V26_2, V26_3


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


# Keyed by the version that introduced each model.
VEHICLE_USER_INPUT = {
    V26_1: VehicleUserInputV26_1,
    V26_2: VehicleUserInputV26_2,
    V26_3: VehicleUserInputV26_3,
}
