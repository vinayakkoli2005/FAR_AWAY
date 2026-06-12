"""2D probability of collision — Foster (1992) style numerical integration.

This is the accuracy reference (NASA CARA's operational choice). The 2D
Gaussian is integrated over the hard-body disk: working in the principal
frame of the projected covariance, the inner integral over one axis is
analytic (error functions), leaving a robust 1D adaptive quadrature:

    Pc = ∫_{-R}^{R} N(x; mx, sx) * [ Φ((y+(x)-my)/sy) - Φ((y-(x)-my)/sy) ] dx
    with y±(x) = ±sqrt(R² - x²)

Valid over the full operational range Pc 1e-1 .. 1e-7 where all mainstream
methods agree (Foster, Chan, Patera, Alfano).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad

from engine.risk.encounter import principal_frame

_SQRT2 = math.sqrt(2.0)


def pc_foster_principal(mx: float, my: float, sx: float, sy: float, hbr_km: float) -> float:
    """Pc in the principal frame: miss (mx, my), sigmas (sx, sy), hard-body radius R."""
    r = hbr_km
    norm = 1.0 / (sx * math.sqrt(2.0 * math.pi))

    def integrand(x: float) -> float:
        half_chord = math.sqrt(max(r * r - x * x, 0.0))
        gx = norm * math.exp(-0.5 * ((x - mx) / sx) ** 2)
        py = 0.5 * (
            math.erf((half_chord - my) / (_SQRT2 * sy))
            - math.erf((-half_chord - my) / (_SQRT2 * sy))
        )
        return gx * py

    # Split at the miss-projection point when it falls inside the disk —
    # adaptive quad converges much faster with the peak on a boundary.
    points = [p for p in (mx,) if -r < p < r]
    val, _ = quad(integrand, -r, r, points=points or None, limit=200, epsabs=1e-13, epsrel=1e-10)
    return float(min(max(val, 0.0), 1.0))


def pc_foster(m2: np.ndarray, cp: np.ndarray, hbr_km: float) -> float:
    """Pc from encounter-plane miss vector (km) and 2x2 covariance (km^2)."""
    mx, my, sx, sy = principal_frame(np.asarray(m2, float), np.asarray(cp, float))
    return pc_foster_principal(mx, my, sx, sy, hbr_km)
