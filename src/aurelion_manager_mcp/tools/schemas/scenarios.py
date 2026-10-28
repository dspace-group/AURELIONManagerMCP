"""Scenario request schemas."""

from typing import Annotated, Literal

from pydantic import Field

from aurelion_manager_mcp.tools.schemas.common import ApiSchema


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
