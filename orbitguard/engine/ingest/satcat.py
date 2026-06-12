"""SATCAT ingest — per-object size class and type for physical HBR estimates.

The GP catalog carries no size data, but CelesTrak's SATCAT publishes a
radar-cross-section class (SMALL < 0.1 m^2, MEDIUM 0.1-1 m^2, LARGE > 1 m^2)
and an object type (PAY/DEB/R/B) for every catalog entry. A constant
hard-body radius makes worst-case bounds uniformly inconclusive (everything
becomes WATCH); RCS-derived radii restore the physics: small debris passing
8 km away is provably safe, a rocket body at 800 m is not.

Same cache discipline as GP: one download per day, served from cache after.
"""

from __future__ import annotations

import csv
import logging
import time
from pathlib import Path

import httpx

from engine.config import CACHE_DIR

log = logging.getLogger(__name__)

SATCAT_URL = "https://celestrak.org/pub/satcat.csv"
MIN_REFETCH_HOURS = 24.0

# RCS class -> effective bounding radius (metres). Deliberately conservative:
# these feed a worst-case bound, so we round sizes up, never down.
RCS_RADIUS_M = {"SMALL": 0.5, "MEDIUM": 2.0, "LARGE": 5.0}
DEFAULT_RADIUS_M = 2.0

# objects much larger than their RCS class suggests
NAME_OVERRIDES_M = {
    "ISS (ZARYA)": 55.0,   # ~110 m span, bounding-sphere radius
    "ISS (NAUKA)": 55.0,
    "CSS (TIANHE)": 35.0,
}


def _cache_path() -> Path:
    d = CACHE_DIR / "satcat"
    d.mkdir(parents=True, exist_ok=True)
    return d / "satcat.csv"


def fetch_satcat(force: bool = False) -> Path | None:
    """Disciplined download; returns None when offline and no cache exists."""
    path = _cache_path()
    if path.exists():
        age_h = (time.time() - path.stat().st_mtime) / 3600.0
        if not force or age_h < 1.0:
            if age_h < MIN_REFETCH_HOURS or not force:
                return path
    try:
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            resp = client.get(SATCAT_URL)
            resp.raise_for_status()
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(resp.content)
        tmp.rename(path)
        log.info("satcat: cached %s (%.1f MB)", path, len(resp.content) / 1e6)
    except Exception as exc:
        log.warning("satcat: download failed (%s); using cache if present", exc)
    return path if path.exists() else None


def load_size_map(path: Path | None = None) -> dict[int, tuple[str, str]]:
    """norad_id -> (object_type, rcs_class). Empty dict when unavailable."""
    path = path or fetch_satcat()
    if path is None or not path.exists():
        return {}
    out: dict[int, tuple[str, str]] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                nid = int(row["NORAD_CAT_ID"])
            except (KeyError, ValueError):
                continue
            rcs = (row.get("RCS") or row.get("RCS_SIZE") or "").strip().upper()
            if rcs not in RCS_RADIUS_M:
                try:  # numeric RCS in m^2 -> class
                    val = float(rcs)
                    rcs = "SMALL" if val < 0.1 else "MEDIUM" if val <= 1.0 else "LARGE"
                except ValueError:
                    rcs = ""
            out[nid] = ((row.get("OBJECT_TYPE") or "").strip(), rcs)
    return out


def radius_m(name: str, object_type: str, rcs_class: str) -> float:
    """Effective bounding radius for one object."""
    for key, r in NAME_OVERRIDES_M.items():
        if key in name.upper():
            return r
    if rcs_class in RCS_RADIUS_M:
        return RCS_RADIUS_M[rcs_class]
    # name/type heuristics when SATCAT is unavailable (offline fixture mode)
    up = f"{name} {object_type}".upper()
    if "DEB" in up:
        return RCS_RADIUS_M["SMALL"]
    if "R/B" in up or "ROCKET" in up:
        return RCS_RADIUS_M["LARGE"]
    return DEFAULT_RADIUS_M


def combined_hbr_km(
    asset_name: str, asset_meta: tuple[str, str],
    obj_name: str, obj_meta: tuple[str, str],
    floor_m: float = 1.0,
) -> tuple[float, str]:
    """Combined hard-body radius (km) and a provenance string for the evidence."""
    ra = radius_m(asset_name, *asset_meta)
    rb = radius_m(obj_name, *obj_meta)
    hbr_m = max(ra + rb, floor_m)
    prov = (
        f"RCS-derived: {asset_meta[1] or 'heuristic'} ({ra:.1f} m) + "
        f"{obj_meta[1] or 'heuristic'} ({rb:.1f} m)"
    )
    return hbr_m / 1000.0, prov
