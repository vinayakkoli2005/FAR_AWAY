"""Stage B — padded coarse-grid sieve (the "smart sieve" guarantee).

If a conjunction with miss distance < D occurs at t*, the nearest grid point
is within dt/2 of t*, and the pair can have separated by at most
vrel_max * dt/2 — so its grid-time separation is < D + vrel_max*dt/2 = R_pair.
No true conjunction can escape the coarse net (Alarcón-Rodríguez et al. 2002).

For k assets vs N survivors this is a direct vectorized distance check,
O(k·N) per step — faster than a KD-tree below a few dozen assets because the
tree build itself is O(N log N) per step. The KD-tree path belongs to the
all-vs-all stretch goal, not here.

Propagation is chunked in time blocks to bound memory (N x chunk x 3 floats).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from sgp4.api import SatrecArray

from engine.astro.elements import CatalogObject
from engine.astro.propagate import TimeGrid
from engine.config import ScreeningConfig


@dataclass
class PairWindow:
    """A coarse-grid hit region for one (asset, object) pair, in grid indices."""

    asset_id: int
    object_id: int
    step_lo: int  # inclusive, already padded by one step each side
    step_hi: int


@dataclass
class SieveResult:
    windows: list[PairWindow]
    n_pairs_checked: int
    n_grid_hits: int
    runtime_s: float
    per_asset_hits: dict[int, int] = field(default_factory=dict)


def _merge_runs(steps: np.ndarray, max_gap: int = 1) -> list[tuple[int, int]]:
    """Merge sorted step indices into [lo, hi] runs, joining gaps <= max_gap."""
    runs: list[tuple[int, int]] = []
    lo = hi = int(steps[0])
    for s in steps[1:]:
        s = int(s)
        if s - hi <= max_gap:
            hi = s
        else:
            runs.append((lo, hi))
            lo = hi = s
    runs.append((lo, hi))
    return runs


def stage_b(
    assets: list[CatalogObject],
    survivors: dict[int, list[CatalogObject]],
    grid: TimeGrid,
    cfg: ScreeningConfig,
) -> SieveResult:
    """Flag (asset, object) pairs that come within the padded radius on the coarse grid.

    `survivors` maps asset norad_id -> Stage A survivor list for that asset.
    """
    t0 = time.perf_counter()
    r_pair = cfg.pair_radius_km
    r_pair_sq = r_pair * r_pair

    # Union of survivors across assets, propagated once.
    union: dict[int, CatalogObject] = {}
    for objs in survivors.values():
        for o in objs:
            union[o.norad_id] = o
    union_ids = sorted(union)
    union_objs = [union[i] for i in union_ids]
    row_of = {nid: i for i, nid in enumerate(union_ids)}
    # Per-asset row indices into the union array.
    asset_rows = {
        a.norad_id: np.array([row_of[o.norad_id] for o in survivors[a.norad_id]], dtype=np.intp)
        for a in assets
    }

    asset_arr = SatrecArray([a.satrec for a in assets])
    cat_arr = SatrecArray([o.satrec for o in union_objs]) if union_objs else None

    hits: dict[tuple[int, int], list[int]] = {}
    n_grid_hits = 0
    per_asset_hits: dict[int, int] = {a.norad_id: 0 for a in assets}

    for c0 in range(0, grid.n_steps, cfg.chunk_steps):
        c1 = min(c0 + cfg.chunk_steps, grid.n_steps)
        jd, fr = grid.jd[c0:c1], grid.fr[c0:c1]

        _, r_assets, _ = asset_arr.sgp4(jd, fr)          # (k, m, 3)
        if cat_arr is None:
            continue
        _, r_cat, _ = cat_arr.sgp4(jd, fr)               # (N, m, 3)

        for ai, asset in enumerate(assets):
            rows = asset_rows[asset.norad_id]
            if rows.size == 0:
                continue
            diff = r_cat[rows] - r_assets[ai][None, :, :]     # (n_a, m, 3)
            d2 = np.einsum("ijk,ijk->ij", diff, diff)         # squared distances
            mask = d2 < r_pair_sq                              # NaN compares False
            if not mask.any():
                continue
            obj_idx, step_idx = np.nonzero(mask)
            n_grid_hits += obj_idx.size
            per_asset_hits[asset.norad_id] += obj_idx.size
            for oi, si in zip(obj_idx, step_idx):
                key = (asset.norad_id, union_ids[rows[oi]])
                hits.setdefault(key, []).append(c0 + int(si))

    windows: list[PairWindow] = []
    last_step = grid.n_steps - 1
    for (aid, oid), steps in hits.items():
        for lo, hi in _merge_runs(np.array(sorted(set(steps)))):
            windows.append(
                PairWindow(
                    asset_id=aid,
                    object_id=oid,
                    step_lo=max(lo - 1, 0),
                    step_hi=min(hi + 1, last_step),
                )
            )

    n_pairs = sum(len(v) for v in survivors.values())
    return SieveResult(
        windows=windows,
        n_pairs_checked=n_pairs,
        n_grid_hits=n_grid_hits,
        runtime_s=time.perf_counter() - t0,
        per_asset_hits=per_asset_hits,
    )
