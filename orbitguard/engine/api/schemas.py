"""Pydantic schemas = the frozen OpenAPI contract the frontend builds against."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssetInfo(BaseModel):
    norad_id: int
    name: str
    gp_epoch_utc: str
    gp_age_hours: float


class ObjectInfo(AssetInfo):
    object_type: str = ""


class MissRIC(BaseModel):
    radial: float
    in_track: float
    cross_track: float


class Probability(BaseModel):
    pc: float | None = None
    pc_max: float | None = None
    method: str
    chan_crosscheck: float | None = None
    hard_body_radius_m: float
    hbr_source: str = "default"


class PolicyInfo(BaseModel):
    rationale: str
    low_vrel_flag: bool
    thresholds: dict[str, float]


class ScreeningInfo(BaseModel):
    distance_km: float
    window_days: float
    coarse_step_s: float


class Evidence(BaseModel):
    event_id: str
    verdict: str
    escalate: bool
    data_grade: str
    asset: AssetInfo
    object: ObjectInfo
    tca_utc: str
    miss_distance_km: float
    miss_ric_km: MissRIC
    relative_velocity_kms: float
    probability: Probability
    policy: PolicyInfo
    screening: ScreeningInfo
    limits: str


class FunnelOut(BaseModel):
    catalog_size: int
    stage_a_survivors: int
    stage_a_per_asset: dict[str, int]
    stage_b_windows: int
    stage_c_events: int
    runtime_s: dict[str, float]


class ConjunctionsResponse(BaseModel):
    generated_utc: str
    source: str
    window_days: float
    asset_ids: list[int]
    funnel: FunnelOut
    events: list[Evidence]


class ExplainResponse(BaseModel):
    event_id: str
    text: str
    source: str = Field(description="groq | template | cache")
    model: str | None = None


class CatalogEntry(BaseModel):
    norad_id: int
    name: str
    object_type: str = ""
    perigee_km: float
    apogee_km: float
    inclination_deg: float
    epoch_utc: str
    # OMM mean elements (canonical) + derived TLE lines as the satellite.js
    # animation transport; TLE is edge-format only, never internal (Section 4.2)
    omm: dict
    tle: list[str] | None = None


class HealthResponse(BaseModel):
    status: str
    catalog_objects: int
    snapshot: str
    snapshot_age_hours: float
    version: str
