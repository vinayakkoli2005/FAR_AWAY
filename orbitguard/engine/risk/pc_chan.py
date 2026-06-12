"""2D probability of collision — Chan (1997) equivalent-area Rician series.

Chan maps the anisotropic 2D Gaussian/disk integral onto an equivalent
isotropic problem and expands it as a convergent series:

    u = R² / (sx·sy)                  (object size term)
    v = mx²/sx² + my²/sy²             (Mahalanobis miss term)

    Pc = e^{-v/2} Σ_{m≥0} (v^m / (2^m m!)) [ 1 - e^{-u/2} Σ_{k≤m} (u^k / (2^k k!)) ]

Orders of magnitude faster than the Foster quadrature; used as the CI
cross-check — |Foster - Chan| disagreement flags a geometry bug.
"""

from __future__ import annotations

import math

import numpy as np

from engine.risk.encounter import principal_frame


def pc_chan_principal(
    mx: float, my: float, sx: float, sy: float, hbr_km: float,
    max_terms: int = 200, tol: float = 1e-14,
) -> float:
    u = hbr_km * hbr_km / (sx * sy)
    v = (mx / sx) ** 2 + (my / sy) ** 2

    # inner = e^{-u/2} Σ_{k=0..m} u^k/(2^k k!), built incrementally
    inner_term = math.exp(-u / 2.0)
    inner_sum = inner_term
    outer_term = math.exp(-v / 2.0)  # m = 0 term of e^{-v/2} v^m/(2^m m!)
    if outer_term == 0.0:
        # far-miss underflow regime: Pc is below double precision anyway
        return 0.0

    total = outer_term * (1.0 - inner_sum)
    for m in range(1, max_terms):
        outer_term *= v / (2.0 * m)
        inner_term *= u / (2.0 * m)
        inner_sum += inner_term
        contrib = outer_term * (1.0 - inner_sum)
        total += contrib
        if outer_term < tol and contrib < tol:
            break
    return float(min(max(total, 0.0), 1.0))


def pc_chan(m2: np.ndarray, cp: np.ndarray, hbr_km: float) -> float:
    mx, my, sx, sy = principal_frame(np.asarray(m2, float), np.asarray(cp, float))
    return pc_chan_principal(mx, my, sx, sy, hbr_km)
