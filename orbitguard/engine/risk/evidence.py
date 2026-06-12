"""The evidence record — the single source of truth handed to UI and explainer.

Every number a user (or the LLM) ever sees about a conjunction lives in this
JSON-serializable record. The LLM narrates it; it cannot add to it.
"""

from __future__ import annotations

from engine.astro.elements import CatalogObject
from engine.config import ScreeningConfig
from engine.risk.policy import RiskAssessment
from engine.screening.tca import ConjunctionEvent


def _sig3(x: float | None) -> float | None:
    """Probabilities carry 3 significant figures everywhere downstream —
    raw float64 precision is noise the UI and the narrator would only echo."""
    return None if x is None else float(f"{x:.3g}")


def build_evidence(
    event: ConjunctionEvent,
    assessment: RiskAssessment,
    asset: CatalogObject,
    obj: CatalogObject,
    cfg: ScreeningConfig,
    hbr_source: str = "default",
) -> dict:
    r, i, c = event.miss_ric_km
    return {
        "event_id": event.event_id,
        "verdict": assessment.verdict.value,
        "escalate": assessment.escalate,
        "data_grade": assessment.grade.value,
        "asset": {
            "norad_id": asset.norad_id,
            "name": asset.name,
            "gp_epoch_utc": asset.epoch.isoformat(),
            "gp_age_hours": round(asset.epoch_age_hours, 1),
        },
        "object": {
            "norad_id": obj.norad_id,
            "name": obj.name,
            "object_type": obj.object_type,
            "gp_epoch_utc": obj.epoch.isoformat(),
            "gp_age_hours": round(obj.epoch_age_hours, 1),
        },
        "tca_utc": event.tca.isoformat(),
        "miss_distance_km": round(event.miss_km, 4),
        "miss_ric_km": {
            "radial": round(r, 4),
            "in_track": round(i, 4),
            "cross_track": round(c, 4),
        },
        "relative_velocity_kms": round(event.vrel_kms, 4),
        "probability": {
            "pc": _sig3(assessment.pc),
            "pc_max": _sig3(assessment.pc_max),
            "method": assessment.pc_method,
            "chan_crosscheck": _sig3(assessment.pc_chan_crosscheck),
            "hard_body_radius_m": round(assessment.hbr_km * 1000.0, 1),
            "hbr_source": hbr_source,
        },
        "policy": {
            "rationale": assessment.rationale,
            "low_vrel_flag": assessment.low_vrel_flag,
            "thresholds": {"dodge_pc": 1e-4, "watch_pc": 1e-6},
        },
        "screening": {
            "distance_km": cfg.screen_dist_km,
            "window_days": cfg.window_days,
            "coarse_step_s": cfg.coarse_step_s,
        },
        "limits": (
            "TLE/GP accuracy is ~1 km at epoch growing 1-3 km/day (in-track dominant). "
            "TLE-grade results are worst-case bounds: they can prove safety, never danger."
        ),
    }
