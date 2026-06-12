"""Conjunction screening on interpolated ephemerides (no SGP4 in the loop).

Same padded-coarse-grid guarantee as the live sieve, applied to ephemeris
interpolators: grid separation < D + vrel_max * dt/2 cannot be evaded by a
true sub-D approach. Refinement is Brent on g(t) = dr·dv, identical math to
Stage C.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from engine.validation.interpolate import LagrangeEphemeris


@dataclass
class EphemerisEvent:
    id_a: str
    id_b: str
    tca_s: float       # seconds in the ephemeris time base
    miss_km: float
    vrel_kms: float


def screen_pair(
    eph_a: LagrangeEphemeris,
    eph_b: LagrangeEphemeris,
    screen_dist_km: float = 10.0,
    coarse_step_s: float = 30.0,
    vrel_max_kms: float = 15.6,
    fine_step_s: float = 1.0,
    id_a: str = "A",
    id_b: str = "B",
) -> list[EphemerisEvent]:
    t0 = max(eph_a.t_start, eph_b.t_start)
    t1 = min(eph_a.t_end, eph_b.t_end)
    if t1 <= t0:
        return []

    pad = screen_dist_km + vrel_max_kms * coarse_step_s / 2.0
    grid = np.arange(t0, t1 + coarse_step_s, coarse_step_s)
    grid = grid[grid <= t1]
    ra = np.array([eph_a.position(t) for t in grid])
    rb = np.array([eph_b.position(t) for t in grid])
    d = np.linalg.norm(rb - ra, axis=1)
    hits = np.nonzero(d < pad)[0]
    if hits.size == 0:
        return []

    def g(t: float) -> float:
        dr = eph_b.position(t) - eph_a.position(t)
        dv = eph_b.velocity(t) - eph_a.velocity(t)
        return float(np.dot(dr, dv))

    events: list[EphemerisEvent] = []
    # merge hit indices into windows, then bracket g sign changes at fine step
    runs: list[tuple[int, int]] = []
    lo = hi = int(hits[0])
    for h in hits[1:]:
        if h - hi <= 1:
            hi = int(h)
        else:
            runs.append((lo, hi))
            lo = hi = int(h)
    runs.append((lo, hi))

    for lo, hi in runs:
        w0 = max(grid[lo] - coarse_step_s, t0)
        w1 = min(grid[hi] + coarse_step_s, t1)
        ts = np.arange(w0, w1 + fine_step_s, fine_step_s)
        ts = ts[ts <= t1]
        gs = np.array([g(t) for t in ts])
        for i in np.nonzero((gs[:-1] < 0) & (gs[1:] >= 0))[0]:
            tca = brentq(g, ts[i], ts[i + 1], xtol=1e-6)
            dr = eph_b.position(tca) - eph_a.position(tca)
            miss = float(np.linalg.norm(dr))
            if miss > screen_dist_km:
                continue
            dv = eph_b.velocity(tca) - eph_a.velocity(tca)
            events.append(
                EphemerisEvent(
                    id_a=id_a, id_b=id_b, tca_s=float(tca),
                    miss_km=miss, vrel_kms=float(np.linalg.norm(dv)),
                )
            )
    # dedupe within 60 s, keep min miss
    events.sort(key=lambda e: e.tca_s)
    out: list[EphemerisEvent] = []
    for e in events:
        if out and e.tca_s - out[-1].tca_s <= 60.0:
            if e.miss_km < out[-1].miss_km:
                out[-1] = e
        else:
            out.append(e)
    return out
