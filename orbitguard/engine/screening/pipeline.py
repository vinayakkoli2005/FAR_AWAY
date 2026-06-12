"""End-to-end screening pipeline: Stage A -> B -> C, with the funnel telemetry.

The funnel (catalog -> gate survivors -> flagged windows -> refined events)
is itself a product artifact: the UI renders it with timings.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from engine.astro.elements import CatalogObject
from engine.astro.propagate import make_grid
from engine.config import SETTINGS, ScreeningConfig
from engine.screening.filters import stage_a
from engine.screening.sieve import stage_b
from engine.screening.tca import ConjunctionEvent, stage_c


@dataclass
class Funnel:
    catalog_size: int
    stage_a_survivors: int          # union across assets
    stage_a_per_asset: dict[int, int]
    stage_b_windows: int
    stage_c_events: int
    stage_a_runtime_s: float
    stage_b_runtime_s: float
    stage_c_runtime_s: float
    total_runtime_s: float

    def as_dict(self) -> dict:
        return {
            "catalog_size": self.catalog_size,
            "stage_a_survivors": self.stage_a_survivors,
            "stage_a_per_asset": {str(k): v for k, v in self.stage_a_per_asset.items()},
            "stage_b_windows": self.stage_b_windows,
            "stage_c_events": self.stage_c_events,
            "runtime_s": {
                "stage_a": round(self.stage_a_runtime_s, 3),
                "stage_b": round(self.stage_b_runtime_s, 3),
                "stage_c": round(self.stage_c_runtime_s, 3),
                "total": round(self.total_runtime_s, 3),
            },
        }


@dataclass
class ScreeningRun:
    start: datetime
    window_days: float
    config: ScreeningConfig
    events: list[ConjunctionEvent]
    funnel: Funnel
    asset_ids: list[int] = field(default_factory=list)


def screen_assets(
    assets: list[CatalogObject],
    catalog: list[CatalogObject],
    start: datetime | None = None,
    cfg: ScreeningConfig | None = None,
) -> ScreeningRun:
    """Screen k assets against the catalog over the configured window."""
    cfg = cfg or SETTINGS.screening
    start = start or datetime.now(timezone.utc)
    t_total = time.perf_counter()

    t_a = time.perf_counter()
    survivors = {a.norad_id: stage_a(a, catalog, cfg) for a in assets}
    stage_a_runtime = time.perf_counter() - t_a
    union_ids = {o.norad_id for objs in survivors.values() for o in objs}

    grid = make_grid(start, cfg.window_days * 86400.0, cfg.coarse_step_s)
    sieve = stage_b(assets, survivors, grid, cfg)

    asset_map = {a.norad_id: a for a in assets}
    object_map = {o.norad_id: o for objs in survivors.values() for o in objs}
    refine = stage_c(asset_map, object_map, sieve.windows, grid, cfg)

    funnel = Funnel(
        catalog_size=len(catalog),
        stage_a_survivors=len(union_ids),
        stage_a_per_asset={aid: len(objs) for aid, objs in survivors.items()},
        stage_b_windows=len(sieve.windows),
        stage_c_events=len(refine.events),
        stage_a_runtime_s=stage_a_runtime,
        stage_b_runtime_s=sieve.runtime_s,
        stage_c_runtime_s=refine.runtime_s,
        total_runtime_s=time.perf_counter() - t_total,
    )
    return ScreeningRun(
        start=start,
        window_days=cfg.window_days,
        config=cfg,
        events=refine.events,
        funnel=funnel,
        asset_ids=[a.norad_id for a in assets],
    )
