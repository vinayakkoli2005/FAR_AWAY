"""All-vs-all conjunction screening on ephemerides (the TraCSS configuration).

Same padded coarse-grid guarantee as the live sieve, engineered for ~24,000
objects x 7 days on an 8 GB laptop:

  Stage B: interpolate every usable object onto the coarse grid (vectorized
           Lagrange, float32 chunk buffers), per-step cKDTree.query_pairs at
           the padded radius R = D + vrel_max*dt/2 — no true sub-D conjunction
           can evade it. Hit bookkeeping is pure numpy: pairs become int64
           keys; windows come from one lexsort + run-length pass.
  Stage C: fully batched refinement — sample times for ~10^5 windows are
           concatenated, interpolation is evaluated once per OBJECT (not per
           window), minima brackets of g(t) = dr·dv come from one vectorized
           sign-change pass, and the root is solved by in-bracket secant
           (g is locally linear over the 1 s bracket; TCA error ~1 ms versus
           the 5 s matching tolerance, miss-distance error centimetres
           because d'(TCA) = 0).

Per the User's Guide: candidate OCMs sharing an object designator are never
screened against each other; usable start/stop honored; TCA strictly inside
the screening window; OD_EPOCH staleness filtered upstream.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from engine.validation.interpolate import LagrangeEphemeris
from engine.validation.matching import KeyEvent

log = logging.getLogger(__name__)


@dataclass
class EphRecord:
    """One ephemeris ready for screening; times in seconds from window start."""

    obj_id: str            # object designator (conjunctions never within same id)
    eph: LagrangeEphemeris
    usable_start_s: float
    usable_stop_s: float


@dataclass
class AvAEvent:
    id_a: str
    id_b: str
    tca_s: float
    miss_km: float
    vrel_kms: float

    def as_key_event(self) -> KeyEvent:
        return KeyEvent(self.id_a, self.id_b, self.tca_s, self.miss_km)


# ---------------------------------------------------------------------------
# Stage B
# ---------------------------------------------------------------------------

def _stage_b(
    records: list[EphRecord],
    grid: np.ndarray,
    r_pair: float,
    chunk_steps: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns window arrays (pair_key, step_lo, step_hi), key = a*n + b, a < b."""
    n = len(records)
    code_of = {d: c for c, d in enumerate(sorted({r.obj_id for r in records}))}
    id_codes = np.array([code_of[r.obj_id] for r in records], dtype=np.int64)
    starts = np.array([r.usable_start_s for r in records])
    stops = np.array([r.usable_stop_s for r in records])

    key_chunks: list[np.ndarray] = []
    step_chunks: list[np.ndarray] = []
    n_steps = len(grid)

    for c0 in range(0, n_steps, chunk_steps):
        c1 = min(c0 + chunk_steps, n_steps)
        ts = grid[c0:c1]
        m = len(ts)
        pos = np.full((n, m, 3), np.nan, dtype=np.float32)
        # objects fully outside this chunk are skipped wholesale
        maybe = np.nonzero((starts <= ts[-1]) & (stops >= ts[0]))[0]
        for i in maybe:
            rec = records[i]
            mask = (ts >= rec.usable_start_s) & (ts <= rec.usable_stop_s)
            if mask.any():
                pos[i, mask] = rec.eph.positions(ts[mask]).astype(np.float32)

        for s in range(m):
            finite = np.isfinite(pos[:, s, 0])
            idx = np.nonzero(finite)[0]
            if idx.size < 2:
                continue
            tree = cKDTree(pos[idx, s])
            prs = tree.query_pairs(r_pair, output_type="ndarray")
            if prs.shape[0] == 0:
                continue
            a = idx[prs[:, 0]]
            b = idx[prs[:, 1]]
            keep = id_codes[a] != id_codes[b]
            if not keep.any():
                continue
            a, b = a[keep], b[keep]
            lo = np.minimum(a, b).astype(np.int64)
            hi = np.maximum(a, b).astype(np.int64)
            key_chunks.append(lo * n + hi)
            step_chunks.append(np.full(lo.shape, c0 + s, dtype=np.int64))

    if not key_chunks:
        z = np.empty(0, np.int64)
        return z, z.copy(), z.copy()

    keys = np.concatenate(key_chunks)
    steps = np.concatenate(step_chunks)
    order = np.lexsort((steps, keys))
    keys, steps = keys[order], steps[order]

    new_run = np.ones(len(keys), dtype=bool)
    new_run[1:] = (keys[1:] != keys[:-1]) | (steps[1:] - steps[:-1] > 1)
    firsts = np.nonzero(new_run)[0]
    lasts = np.append(firsts[1:] - 1, len(keys) - 1)
    return keys[firsts], steps[firsts], steps[lasts]


# ---------------------------------------------------------------------------
# Stage C — batched, vectorized
# ---------------------------------------------------------------------------

def _eval_grouped(
    records: list[EphRecord],
    obj_of_sample: np.ndarray,
    ts: np.ndarray,
    want_velocity: bool,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Evaluate positions (and optionally velocities) for samples that belong
    to many different objects: one interpolator call per unique object."""
    pos = np.empty((len(ts), 3))
    vel = np.empty((len(ts), 3)) if want_velocity else None
    order = np.argsort(obj_of_sample, kind="stable")
    sorted_obj = obj_of_sample[order]
    uniq, first_idx = np.unique(sorted_obj, return_index=True)
    bounds = np.append(first_idx, len(sorted_obj))
    for u, lo, hi in zip(uniq, bounds[:-1], bounds[1:]):
        idxs = order[lo:hi]
        eph = records[int(u)].eph
        pos[idxs] = eph.positions(ts[idxs])
        if want_velocity:
            vel[idxs] = eph.velocities(ts[idxs])
    return pos, vel


def _stage_c_batch(
    records: list[EphRecord],
    grid: np.ndarray,
    keys: np.ndarray,
    s_lo: np.ndarray,
    s_hi: np.ndarray,
    *,
    window_s: float,
    screen_dist_km: float,
    coarse_step_s: float,
    fine_step_s: float,
) -> list[AvAEvent]:
    n = len(records)
    a_idx, b_idx = np.divmod(keys, n)
    usable_start = np.array([r.usable_start_s for r in records])
    usable_stop = np.array([r.usable_stop_s for r in records])

    w0 = np.maximum.reduce(
        [grid[s_lo] - coarse_step_s, usable_start[a_idx], usable_start[b_idx],
         np.zeros(len(keys))]
    )
    w1 = np.minimum.reduce(
        [grid[s_hi] + coarse_step_s, usable_stop[a_idx], usable_stop[b_idx],
         np.full(len(keys), window_s)]
    )
    valid = w1 - w0 >= fine_step_s
    if not valid.any():
        return []
    a_idx, b_idx, w0, w1 = a_idx[valid], b_idx[valid], w0[valid], w1[valid]
    nw = len(w0)

    n_samp = np.floor((w1 - w0) / fine_step_s).astype(np.int64) + 1
    offsets = np.concatenate([[0], np.cumsum(n_samp)])
    total = int(offsets[-1])
    win_of = np.repeat(np.arange(nw), n_samp)
    ts = w0[win_of] + (np.arange(total) - offsets[win_of]) * fine_step_s

    pa, va = _eval_grouped(records, a_idx[win_of], ts, want_velocity=True)
    pb, vb = _eval_grouped(records, b_idx[win_of], ts, want_velocity=True)
    dr = pb - pa
    dv = vb - va
    g = np.einsum("ij,ij->i", dr, dv)

    same_win = win_of[1:] == win_of[:-1]
    bracket = (g[:-1] < 0.0) & (g[1:] >= 0.0) & same_win
    i = np.nonzero(bracket)[0]
    if i.size == 0:
        return []

    denom = g[i + 1] - g[i]
    denom[denom == 0.0] = 1e-30
    t_star = ts[i] - g[i] * fine_step_s / denom

    # miss distance at the root: one more grouped evaluation, positions only
    win_r = win_of[i]
    pa_r, _ = _eval_grouped(records, a_idx[win_r], t_star, want_velocity=False)
    pb_r, _ = _eval_grouped(records, b_idx[win_r], t_star, want_velocity=False)
    miss = np.linalg.norm(pb_r - pa_r, axis=1)
    # relative speed varies negligibly across the 1 s bracket: use the sample value
    vrel = np.linalg.norm(dv[i], axis=1)

    keep = (miss <= screen_dist_km) & (t_star > 0.0) & (t_star < window_s)
    events: list[AvAEvent] = []
    for j in np.nonzero(keep)[0]:
        ia = records[int(a_idx[win_r[j]])].obj_id
        ib = records[int(b_idx[win_r[j]])].obj_id
        events.append(
            AvAEvent(min(ia, ib), max(ia, ib), float(t_star[j]), float(miss[j]),
                     float(vrel[j]))
        )
    return events


def screen_all_vs_all(
    records: list[EphRecord],
    window_s: float,
    screen_dist_km: float = 10.0,
    coarse_step_s: float = 8.0,
    vrel_max_kms: float = 15.6,
    fine_step_s: float = 1.0,
    chunk_steps: int = 450,
    dedupe_gap_s: float = 60.0,
    batch_windows: int = 100_000,
    slice_start_s: float | None = None,
    slice_stop_s: float | None = None,
) -> list[AvAEvent]:
    """Screen everything against everything.

    slice_start/stop_s allow memory-bounded runs over a sub-interval of the
    full window: the coarse grid covers the slice (with a one-step margin),
    and an event is reported by the slice that half-open-contains its TCA —
    so a sliced run over the whole window reports each event exactly once.
    `window_s` always bounds TCA validity globally (guide configuration #1).
    """
    t_start = time.perf_counter()
    s0 = 0.0 if slice_start_s is None else max(slice_start_s, 0.0)
    s1 = window_s if slice_stop_s is None else min(slice_stop_s, window_s)
    r_pair = screen_dist_km + vrel_max_kms * coarse_step_s / 2.0
    g0 = max(s0 - 2 * coarse_step_s, 0.0)
    g1 = min(s1 + 2 * coarse_step_s, window_s)
    n_steps = int(round((g1 - g0) / coarse_step_s)) + 1
    grid = g0 + np.arange(n_steps) * coarse_step_s

    keys, s_lo, s_hi = _stage_b(records, grid, r_pair, chunk_steps)
    log.info(
        "stage B [%.0f-%.0f s]: %d windows over %d pairs, r_pair=%.1f km, %.1f s",
        s0, s1, len(keys), len(np.unique(keys)) if len(keys) else 0, r_pair,
        time.perf_counter() - t_start,
    )

    t_c = time.perf_counter()
    events: list[AvAEvent] = []
    for b0 in range(0, len(keys), batch_windows):
        b1 = min(b0 + batch_windows, len(keys))
        events.extend(
            _stage_c_batch(
                records, grid, keys[b0:b1], s_lo[b0:b1], s_hi[b0:b1],
                window_s=window_s, screen_dist_km=screen_dist_km,
                coarse_step_s=coarse_step_s, fine_step_s=fine_step_s,
            )
        )

    # half-open slice ownership (except the final slice, which owns its end)
    if slice_start_s is not None or slice_stop_s is not None:
        end_inclusive = s1 >= window_s
        events = [
            e for e in events
            if (e.tca_s >= s0) and (e.tca_s < s1 or (end_inclusive and e.tca_s <= s1))
        ]

    events = _dedupe(events, dedupe_gap_s)
    log.info(
        "stage C: %d events after dedupe, %.1f s (total %.1f s)",
        len(events), time.perf_counter() - t_c, time.perf_counter() - t_start,
    )
    return events


def _dedupe(events: list[AvAEvent], gap_s: float) -> list[AvAEvent]:
    by_pair: dict[tuple[str, str], list[AvAEvent]] = {}
    for e in events:
        by_pair.setdefault((e.id_a, e.id_b), []).append(e)
    out: list[AvAEvent] = []
    for evs in by_pair.values():
        evs.sort(key=lambda e: e.tca_s)
        cluster = [evs[0]]
        for e in evs[1:]:
            if e.tca_s - cluster[-1].tca_s <= gap_s:
                cluster.append(e)
            else:
                out.append(min(cluster, key=lambda x: x.miss_km))
                cluster = [e]
        out.append(min(cluster, key=lambda x: x.miss_km))
    return out
