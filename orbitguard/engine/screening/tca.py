"""Stage C — TCA refinement via Brent root-finding.

Within each flagged window, the squared range f(t) = |dr(t)|^2 has derivative
g(t) = 2 dr(t)·dv(t). Local minima of range are roots of g with a -/+ sign
change. We bracket on a fine grid, polish with Brent to machine precision,
and keep events whose miss distance is within the screening distance D.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
from scipy.optimize import brentq

from engine.astro.elements import CatalogObject
from engine.astro.propagate import TimeGrid, propagate_pair_rel, utc_to_jd
from engine.astro.frames import to_ric
from engine.config import ScreeningConfig
from engine.screening.sieve import PairWindow


@dataclass
class ConjunctionEvent:
    """One refined close approach, with full state evidence for the risk layer."""

    asset_id: int
    object_id: int
    tca: datetime
    miss_km: float
    vrel_kms: float
    miss_ric_km: tuple[float, float, float]  # miss vector in the ASSET's RIC frame
    r_asset: np.ndarray   # TEME km at TCA
    v_asset: np.ndarray
    r_object: np.ndarray
    v_object: np.ndarray

    @property
    def event_id(self) -> str:
        return f"{self.asset_id}-{self.object_id}-{self.tca.strftime('%Y%m%dT%H%M%S')}"


@dataclass
class RefineResult:
    events: list[ConjunctionEvent]
    n_windows: int
    n_roots_examined: int
    runtime_s: float


def _g_func(sat_a, sat_b, t0: datetime):
    """g(dt_seconds) = dr·dv around reference time t0 (factor 2 irrelevant for roots)."""

    def g(dt_s: float) -> float:
        t = t0 + timedelta(seconds=float(dt_s))
        dr, dv = propagate_pair_rel(sat_a, sat_b, t)
        return float(np.dot(dr, dv))

    return g


def refine_window(
    asset: CatalogObject,
    obj: CatalogObject,
    t_start: datetime,
    t_end: datetime,
    cfg: ScreeningConfig,
) -> list[ConjunctionEvent]:
    """Find all range minima within [t_start, t_end] and keep those with miss <= D."""
    span_s = (t_end - t_start).total_seconds()
    n = max(int(span_s / cfg.fine_step_s) + 1, 3)
    from sgp4.api import SatrecArray

    offsets = np.linspace(0.0, span_s, n)
    jd0, fr0 = utc_to_jd(t_start)
    fr = fr0 + offsets / 86400.0
    jd = np.full(n, jd0) + np.floor(fr)
    fr -= np.floor(fr)

    pair = SatrecArray([asset.satrec, obj.satrec])
    err, r, v = pair.sgp4(jd, fr)
    if (err != 0).any():
        return []
    dr = r[1] - r[0]
    dv = v[1] - v[0]
    g = np.einsum("ij,ij->i", dr, dv)

    g_scalar = _g_func(asset.satrec, obj.satrec, t_start)
    events: list[ConjunctionEvent] = []
    sign_change = (g[:-1] < 0.0) & (g[1:] >= 0.0)
    for i in np.nonzero(sign_change)[0]:
        root_s = brentq(g_scalar, offsets[i], offsets[i + 1], xtol=1e-3)  # ~1 ms in time
        tca = t_start + timedelta(seconds=float(root_s))
        ra, va = _state(asset, tca)
        rb, vb = _state(obj, tca)
        if ra is None or rb is None:
            continue
        dvec = rb - ra
        miss = float(np.linalg.norm(dvec))
        if miss > cfg.screen_dist_km:
            continue
        vrel = float(np.linalg.norm(vb - va))
        ric = to_ric(ra, va, dvec)
        events.append(
            ConjunctionEvent(
                asset_id=asset.norad_id,
                object_id=obj.norad_id,
                tca=tca,
                miss_km=miss,
                vrel_kms=vrel,
                miss_ric_km=(float(ric[0]), float(ric[1]), float(ric[2])),
                r_asset=ra, v_asset=va, r_object=rb, v_object=vb,
            )
        )
    return events


def _state(obj: CatalogObject, t: datetime):
    jd, fr = utc_to_jd(t)
    err, r, v = obj.satrec.sgp4(jd, fr)
    if err != 0:
        return None, None
    return np.array(r), np.array(v)


def stage_c(
    assets: dict[int, CatalogObject],
    objects: dict[int, CatalogObject],
    windows: list[PairWindow],
    grid: TimeGrid,
    cfg: ScreeningConfig,
) -> RefineResult:
    t0 = time.perf_counter()
    events: list[ConjunctionEvent] = []
    n_roots = 0
    for w in windows:
        asset = assets[w.asset_id]
        obj = objects[w.object_id]
        t_start = grid.time_at(w.step_lo)
        t_end = grid.time_at(w.step_hi)
        found = refine_window(asset, obj, t_start, t_end, cfg)
        n_roots += len(found)
        events.extend(found)

    events = _dedupe(events, cfg.dedupe_gap_s)
    events.sort(key=lambda e: e.miss_km)
    return RefineResult(
        events=events,
        n_windows=len(windows),
        n_roots_examined=n_roots,
        runtime_s=time.perf_counter() - t0,
    )


def _dedupe(events: list[ConjunctionEvent], gap_s: float) -> list[ConjunctionEvent]:
    """Collapse events of the same pair with TCAs closer than gap_s (keep min miss)."""
    by_pair: dict[tuple[int, int], list[ConjunctionEvent]] = {}
    for e in events:
        by_pair.setdefault((e.asset_id, e.object_id), []).append(e)
    out: list[ConjunctionEvent] = []
    for evs in by_pair.values():
        evs.sort(key=lambda e: e.tca)
        cluster: list[ConjunctionEvent] = [evs[0]]
        for e in evs[1:]:
            if (e.tca - cluster[-1].tca).total_seconds() <= gap_s:
                cluster.append(e)
            else:
                out.append(min(cluster, key=lambda x: x.miss_km))
                cluster = [e]
        out.append(min(cluster, key=lambda x: x.miss_km))
    return out
