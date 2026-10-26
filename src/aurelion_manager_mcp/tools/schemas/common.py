"""Request schemas used by several resources."""

from pydantic import BaseModel, ConfigDict


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


class IpConnection(ApiSchema):
    port: float
    host: str
