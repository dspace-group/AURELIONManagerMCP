"""Sensor request schemas."""

from typing import Literal

from aurelion_manager_mcp.tools.schemas.common import ApiSchema, Tag
from aurelion_manager_mcp.versioning import V26_1, V26_2


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
SENSOR_USER_INPUT = {V26_1: SensorUserInputV26_1, V26_2: SensorUserInputV26_2}
