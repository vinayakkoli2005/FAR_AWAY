"""Property test: no true conjunction escapes the sieve.

Ground truth is brute force — a 1-second grid over the whole window for every
pair, no filtering at all. The pipeline (Stage A gate -> 30 s padded sieve ->
Brent refinement) must reproduce every brute-force event and invent none.

The synthetic catalog plants a guaranteed conjunction: two near-circular
orbits sharing a node, phased to cross it together, inclinations 1 deg apart
=> repeated close approaches at every nodal crossing. Background objects and
deliberate near-misses keep both error directions honest.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
from sgp4.api import SatrecArray

from engine.astro.elements import from_omm
from engine.astro.propagate import make_grid
from engine.config import ScreeningConfig
from engine.screening.pipeline import screen_assets
from tests.conftest import make_omm

CFG = ScreeningConfig(window_days=0.25)  # 6-hour window keeps brute force cheap


def _build_scene():
    asset = from_omm(make_omm(NORAD_CAT_ID=90001, OBJECT_NAME="ASSET"))
    catalog = [
        # planted conjunctor: same node, ~5.9 km along-track offset, i +1 deg
        from_omm(make_omm(NORAD_CAT_ID=90002, OBJECT_NAME="PLANTED-HIT",
                          INCLINATION=52.64, MEAN_ANOMALY=0.05)),
        # deliberate near-miss: ~59 km along-track offset at the node
        from_omm(make_omm(NORAD_CAT_ID=90003, OBJECT_NAME="NEAR-MISS",
                          INCLINATION=52.64, MEAN_ANOMALY=0.5)),
        # co-altitude, far RAAN
        from_omm(make_omm(NORAD_CAT_ID=90004, RA_OF_ASC_NODE=10.0)),
        # GEO bird — must die in Stage A
        from_omm(make_omm(NORAD_CAT_ID=90005, OBJECT_NAME="GEO", MEAN_MOTION=1.0027,
                          ECCENTRICITY=0.0002, INCLINATION=0.1, BSTAR=0.0,
                          MEAN_MOTION_DOT=0.0)),
        # eccentric Molniya-like
        from_omm(make_omm(NORAD_CAT_ID=90006, OBJECT_NAME="MOLNIYA", MEAN_MOTION=2.006,
                          ECCENTRICITY=0.74, INCLINATION=63.4, BSTAR=0.0,
                          MEAN_MOTION_DOT=0.0)),
    ]
    # background LEO population
    rng = np.random.default_rng(42)
    for k in range(18):
        catalog.append(
            from_omm(
                make_omm(
                    NORAD_CAT_ID=90100 + k,
                    OBJECT_NAME=f"BG-{k}",
                    MEAN_MOTION=float(15.5 + rng.uniform(-0.4, 0.4)),
                    RA_OF_ASC_NODE=float(rng.uniform(0, 360)),
                    MEAN_ANOMALY=float(rng.uniform(0, 360)),
                    INCLINATION=float(rng.uniform(45, 98)),
                )
            )
        )
    return asset, catalog


def _brute_force_events(asset, catalog, start, cfg):
    """1 s grid, all pairs, no filters: list of (object_id, tca_seconds, miss_km)."""
    duration = cfg.window_days * 86400.0
    grid = make_grid(start, duration, 1.0)
    sats = SatrecArray([asset.satrec] + [o.satrec for o in catalog])
    err, r, _ = sats.sgp4(grid.jd, grid.fr)
    r = np.where((err == 0)[:, :, None], r, np.nan)
    events = []
    for i, obj in enumerate(catalog, start=1):
        d = np.linalg.norm(r[i] - r[0], axis=1)
        interior = (d[1:-1] < d[:-2]) & (d[1:-1] <= d[2:]) & (d[1:-1] < cfg.screen_dist_km)
        for idx in np.nonzero(interior)[0] + 1:
            events.append((obj.norad_id, float(idx), float(d[idx])))
    # cluster per pair within the dedupe gap, keep minimum
    out = []
    by_obj: dict[int, list[tuple[float, float]]] = {}
    for oid, t, miss in sorted(events, key=lambda e: (e[0], e[1])):
        by_obj.setdefault(oid, []).append((t, miss))
    for oid, hits in by_obj.items():
        cluster = [hits[0]]
        for t, miss in hits[1:]:
            if t - cluster[-1][0] <= cfg.dedupe_gap_s:
                cluster.append((t, miss))
            else:
                out.append((oid, *min(cluster, key=lambda h: h[1])))
                cluster = [(t, miss)]
        out.append((oid, *min(cluster, key=lambda h: h[1])))
    return out


def test_pipeline_matches_brute_force():
    asset, catalog = _build_scene()
    start = asset.epoch + timedelta(minutes=10)

    run = screen_assets([asset], catalog, start=start, cfg=CFG)
    truth = _brute_force_events(asset, catalog, start, CFG)

    # The planted pair must produce at least one event in both worlds.
    assert any(oid == 90002 for oid, *_ in truth), "scene construction broken"
    assert any(e.object_id == 90002 for e in run.events)

    # The GEO object must have died in Stage A.
    assert 90005 not in run.funnel.stage_a_per_asset or all(
        e.object_id != 90005 for e in run.events
    )
    assert run.funnel.stage_a_survivors < len(catalog)

    def match(oid, t_s, miss):
        for e in run.events:
            if e.object_id != oid:
                continue
            dt = abs((e.tca - start).total_seconds() - t_s)
            if dt <= 2.0 and abs(e.miss_km - miss) <= 0.05:
                return True
        return False

    # RECALL: every brute-force event clear of the screening boundary is found.
    for oid, t_s, miss in truth:
        if miss < CFG.screen_dist_km - 0.05:
            assert match(oid, t_s, miss), (
                f"sieve missed object {oid}: TCA +{t_s:.0f}s miss {miss:.3f} km"
            )

    # PRECISION: every reported event exists in the brute-force truth.
    for e in run.events:
        ok = any(
            e.object_id == oid
            and abs((e.tca - start).total_seconds() - t_s) <= 2.0
            and miss < CFG.screen_dist_km + 0.05
            for oid, t_s, miss in truth
        )
        assert ok, f"pipeline invented event {e.event_id} (miss {e.miss_km:.3f} km)"


def test_near_miss_excluded():
    asset, catalog = _build_scene()
    start = asset.epoch + timedelta(minutes=10)
    run = screen_assets([asset], catalog, start=start, cfg=CFG)
    near = [e for e in run.events if e.object_id == 90003]
    assert all(e.miss_km <= CFG.screen_dist_km for e in near)
