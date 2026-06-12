"""Stage A — apogee/perigee gate (Hoots Filter I with a safety pad).

Discard any catalog object whose altitude band cannot intersect the asset's
within the padded screening distance. O(N) per asset; eliminates most of the
catalog for typical LEO assets before any propagation happens.
"""

from __future__ import annotations

from engine.astro.elements import CatalogObject
from engine.config import ScreeningConfig


def altitude_bands_overlap(
    a: CatalogObject, b: CatalogObject, pad_km: float
) -> bool:
    """True if the [perigee, apogee] radius bands come within pad_km of touching.

    reject if max(q_i, q_j) - min(Q_i, Q_j) > pad  (q = perigee radius, Q = apogee radius)
    """
    return max(a.perigee_km, b.perigee_km) - min(a.apogee_km, b.apogee_km) <= pad_km


def stage_a(
    asset: CatalogObject,
    catalog: list[CatalogObject],
    cfg: ScreeningConfig,
) -> list[CatalogObject]:
    """Survivors of the perigee/apogee gate for one asset (asset itself excluded)."""
    pad = cfg.screen_dist_km + cfg.stage_a_pad_km
    return [
        obj
        for obj in catalog
        if obj.norad_id != asset.norad_id and altitude_bands_overlap(asset, obj, pad)
    ]
