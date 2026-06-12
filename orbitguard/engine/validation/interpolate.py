"""Ephemeris interpolation for the TraCSS verification run.

The answer key tests *screening*, not propagation: we run Stage B/C logic
directly on the provided ephemerides (plan Section 6). Position is
interpolated with a sliding 6-point (5th-order) Lagrange scheme — the
default the TraCSS User's Guide prescribes; velocity comes from the
analytic derivative of the same polynomial, so position and velocity are
always consistent.
"""

from __future__ import annotations

import numpy as np


class LagrangeEphemeris:
    """5th-order sliding-window Lagrange interpolator over an ephemeris table."""

    def __init__(self, times_s: np.ndarray, positions_km: np.ndarray, order: int = 5):
        if len(times_s) < order + 1:
            raise ValueError(f"need at least {order + 1} ephemeris points")
        if np.any(np.diff(times_s) <= 0):
            raise ValueError("ephemeris times must be strictly increasing")
        self.t = np.asarray(times_s, dtype=float)
        self.r = np.asarray(positions_km, dtype=float)
        self.n_nodes = order + 1

    @property
    def t_start(self) -> float:
        return float(self.t[0])

    @property
    def t_end(self) -> float:
        return float(self.t[-1])

    def _window(self, t: float) -> slice:
        i = int(np.searchsorted(self.t, t)) - 1
        half = self.n_nodes // 2
        lo = max(min(i - half + 1, len(self.t) - self.n_nodes), 0)
        return slice(lo, lo + self.n_nodes)

    def position(self, t: float) -> np.ndarray:
        w = self._window(t)
        tn, rn = self.t[w], self.r[w]
        out = np.zeros(3)
        for j in range(len(tn)):
            lj = 1.0
            for k in range(len(tn)):
                if k != j:
                    lj *= (t - tn[k]) / (tn[j] - tn[k])
            out += lj * rn[j]
        return out

    def velocity(self, t: float) -> np.ndarray:
        """Analytic derivative of the Lagrange basis (km/s)."""
        w = self._window(t)
        tn, rn = self.t[w], self.r[w]
        out = np.zeros(3)
        for j in range(len(tn)):
            dlj = 0.0
            for m in range(len(tn)):
                if m == j:
                    continue
                term = 1.0 / (tn[j] - tn[m])
                for k in range(len(tn)):
                    if k != j and k != m:
                        term *= (t - tn[k]) / (tn[j] - tn[k])
                dlj += term
            out += dlj * rn[j]
        return out
