"""Vectorized SGP4 propagation over time grids.

SGP4 outputs are in TEME (True Equator, Mean Equinox of date). For relative
geometry between two objects at the same instant — which is everything the
screening engine needs — TEME-vs-TEME is exact; frame conversions for display
live in frames.py and are applied once, centrally.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
from sgp4.api import Satrec, SatrecArray, jday


@dataclass(frozen=True)
class TimeGrid:
    """A UTC time grid expressed as (jd, fr) pairs for SGP4."""

    start: datetime
    step_s: float
    n_steps: int
    jd: np.ndarray  # whole part, shape (n_steps,)
    fr: np.ndarray  # fractional day part, shape (n_steps,)

    def times(self) -> list[datetime]:
        return [self.start + timedelta(seconds=i * self.step_s) for i in range(self.n_steps)]

    def time_at(self, idx: float) -> datetime:
        return self.start + timedelta(seconds=idx * self.step_s)

    def slice(self, i0: int, i1: int) -> "TimeGrid":
        return TimeGrid(
            start=self.start + timedelta(seconds=i0 * self.step_s),
            step_s=self.step_s,
            n_steps=i1 - i0,
            jd=self.jd[i0:i1],
            fr=self.fr[i0:i1],
        )


def utc_to_jd(t: datetime) -> tuple[float, float]:
    t = t.astimezone(timezone.utc)
    jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond * 1e-6)
    return jd, fr


def make_grid(start: datetime, duration_s: float, step_s: float) -> TimeGrid:
    n = int(round(duration_s / step_s)) + 1
    jd0, fr0 = utc_to_jd(start)
    offsets = np.arange(n) * (step_s / 86400.0)
    fr = fr0 + offsets
    jd = np.full(n, jd0)
    # keep fr in [0, 1) so SGP4's time handling stays in its accurate regime
    carry = np.floor(fr)
    jd += carry
    fr -= carry
    return TimeGrid(start=start, step_s=step_s, n_steps=n, jd=jd, fr=fr)


def propagate_many(satrecs: list[Satrec], grid: TimeGrid) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Propagate all satellites over the grid.

    Returns (r, v, ok): r/v shape (n_sats, n_steps, 3) in km / km/s (TEME),
    ok boolean mask, False where SGP4 reported an error (decayed, bad elements);
    those positions are NaN.
    """
    arr = SatrecArray(satrecs)
    err, r, v = arr.sgp4(grid.jd, grid.fr)
    ok = err == 0
    bad = ~ok
    if bad.any():
        r = r.copy()
        v = v.copy()
        r[bad] = np.nan
        v[bad] = np.nan
    return r, v, ok


def propagate_one(satrec: Satrec, t: datetime) -> tuple[np.ndarray, np.ndarray]:
    """Single satellite, single time. Raises on SGP4 error."""
    jd, fr = utc_to_jd(t)
    err, r, v = satrec.sgp4(jd, fr)
    if err != 0:
        raise RuntimeError(f"SGP4 error {err} for sat {satrec.satnum} at {t.isoformat()}")
    return np.array(r), np.array(v)


def propagate_pair_rel(
    sat_a: Satrec, sat_b: Satrec, t: datetime
) -> tuple[np.ndarray, np.ndarray]:
    """Relative state (dr, dv) of B w.r.t. A at time t, TEME km / km/s."""
    ra, va = propagate_one(sat_a, t)
    rb, vb = propagate_one(sat_b, t)
    return rb - ra, vb - va
