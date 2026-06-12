"""OMM record -> SGP4 satellite + derived orbital geometry.

GP mean elements are fitted to the SGP4 theory; they are propagated with SGP4
and nothing else (plan Section 5.1). Catalog IDs are integers end-to-end —
the 5-digit TLE field exhausts ~July 2026 and we refuse to inherit that bug.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from sgp4 import omm as sgp4_omm
from sgp4.api import Satrec

from engine.config import MU_EARTH

_TWO_PI = 2.0 * math.pi


@dataclass
class CatalogObject:
    """One catalog object: identity, SGP4 propagator, and altitude band."""

    norad_id: int
    name: str
    epoch: datetime
    satrec: Satrec
    perigee_km: float   # perigee RADIUS (from geocenter), not altitude
    apogee_km: float    # apogee RADIUS
    mean_motion_rev_day: float
    eccentricity: float
    inclination_deg: float
    object_type: str = ""

    @property
    def epoch_age_hours(self) -> float:
        return (datetime.now(timezone.utc) - self.epoch).total_seconds() / 3600.0


def _parse_epoch(epoch_str: str) -> datetime:
    # CelesTrak OMM epochs look like "2026-06-11T06:21:46.123456"
    dt = datetime.fromisoformat(epoch_str.replace("Z", ""))
    return dt.replace(tzinfo=timezone.utc)


def semi_major_axis_km(mean_motion_rev_day: float) -> float:
    n_rad_s = mean_motion_rev_day * _TWO_PI / 86400.0
    return (MU_EARTH / (n_rad_s * n_rad_s)) ** (1.0 / 3.0)


def from_omm(fields: dict) -> CatalogObject:
    """Build a CatalogObject from one CelesTrak OMM JSON record."""
    sat = Satrec()
    sgp4_omm.initialize(sat, fields)

    mm = float(fields["MEAN_MOTION"])
    ecc = float(fields["ECCENTRICITY"])
    a = semi_major_axis_km(mm)
    return CatalogObject(
        norad_id=int(fields["NORAD_CAT_ID"]),
        name=str(fields.get("OBJECT_NAME", "")).strip(),
        epoch=_parse_epoch(fields["EPOCH"]),
        satrec=sat,
        perigee_km=a * (1.0 - ecc),
        apogee_km=a * (1.0 + ecc),
        mean_motion_rev_day=mm,
        eccentricity=ecc,
        inclination_deg=float(fields["INCLINATION"]),
        object_type=str(fields.get("OBJECT_TYPE", "")),
    )


def load_catalog(records: list[dict]) -> tuple[list[CatalogObject], list[dict]]:
    """Parse all OMM records; returns (objects, rejects). Bad records never crash ingest."""
    objects: list[CatalogObject] = []
    rejects: list[dict] = []
    seen: set[int] = set()
    for rec in records:
        try:
            obj = from_omm(rec)
        except (KeyError, ValueError, TypeError) as exc:
            rejects.append({"record": rec.get("NORAD_CAT_ID", "?"), "error": str(exc)})
            continue
        if obj.norad_id in seen:
            continue
        seen.add(obj.norad_id)
        objects.append(obj)
    return objects, rejects
