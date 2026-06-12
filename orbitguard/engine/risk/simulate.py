"""Simulated training event — exercises the CDM-grade path honestly.

Public TLE data can never produce a DODGE (worst-case bounds only clear or
escalate), so live demos would never show the maneuver-alert path. This event
is simulated GEOMETRY with realistic CDM covariance — but the probability,
ellipse and verdict come from the REAL Foster/Chan pipeline, nothing is
hard-coded. The record carries simulated=true and the UI badges it.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import numpy as np

from engine.astro.elements import CatalogObject
from engine.astro.frames import ric_basis, ric_to_inertial_cov
from engine.astro.propagate import propagate_one
from engine.config import ScreeningConfig
from engine.risk.evidence import build_evidence
from engine.risk.policy import assess_event
from engine.screening.tca import ConjunctionEvent

SIM_OBJECT_ID = 99999
SIM_OBJECT_NAME = "SIM-DEBRIS (TRAINING)"


def simulated_dodge_event(asset: CatalogObject, cfg: ScreeningConfig) -> dict | None:
    """Evidence record for a training conjunction ~30 h out against `asset`."""
    try:
        tca = datetime.now(timezone.utc) + timedelta(hours=30)
        r_a, v_a = propagate_one(asset.satrec, tca)
    except Exception:
        return None
    ric = ric_basis(r_a, v_a)
    dr = ric.T @ np.array([0.080, 0.050, 0.060])  # ~112 m miss
    r_b = r_a + dr
    rhat = ric[0]
    ang = math.radians(60.0)
    v_b = (v_a * math.cos(ang) + np.cross(rhat, v_a) * math.sin(ang)
           + rhat * float(np.dot(rhat, v_a)) * (1 - math.cos(ang)))

    event = ConjunctionEvent(
        asset_id=asset.norad_id, object_id=SIM_OBJECT_ID, tca=tca,
        miss_km=float(np.linalg.norm(dr)),
        vrel_kms=float(np.linalg.norm(v_b - v_a)),
        miss_ric_km=tuple(float(x) for x in (ric @ dr)),
        r_asset=r_a, v_asset=v_a, r_object=r_b, v_object=v_b,
    )
    # realistic LEO CDM 1-sigma covariances in each object's RIC frame (km)
    c1 = ric_to_inertial_cov(r_a, v_a, np.diag([0.060, 0.250, 0.090]) ** 2)
    c2 = ric_to_inertial_cov(r_b, v_b, np.diag([0.080, 0.350, 0.120]) ** 2)
    assessment = assess_event(event, cov_combined=c1 + c2, hbr_km=0.025)

    fake_obj = SimpleNamespace(
        norad_id=SIM_OBJECT_ID, name=SIM_OBJECT_NAME, epoch=tca,
        epoch_age_hours=0.5, object_type="DEB",
    )
    return build_evidence(
        event, assessment, asset, fake_obj, cfg,
        hbr_source="simulated CDM exercise (25 m combined)",
        simulated=True,
    )
