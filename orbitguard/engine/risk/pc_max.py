"""Worst-case collision probability bound when no covariance exists (TLE-grade).

We never invent a covariance for GP/TLE data. Instead we compute the maximum
possible Pc over all covariances consistent with the observed miss geometry.
For the isotropic family, with R << d:

    Pc(σ) ≈ (R²/2σ²) · exp(-d²/2σ²);  dPc/dσ = 0  =>  σ² = d²/2
    =>  PcMax = R² / (e · d²)

The asymmetry this creates is the heart of the risk policy: an upper bound
can CLEAR an event (PcMax < threshold => safe under any consistent
covariance) but can never CONVICT one. TLE data can prove safety, never danger.

The general anisotropic bound (Alfano 2014 / Frisbee 2015) is tighter ways of
saying the same thing; the isotropic bound is conservative for the clearing
decision, which is the only decision we let it make.
"""

from __future__ import annotations

import math


def pc_max_isotropic(miss_km: float, hbr_km: float) -> float:
    """Upper bound on Pc given only miss distance and hard-body radius."""
    if miss_km <= hbr_km:
        return 1.0  # geometric overlap cannot be excluded
    return min((hbr_km * hbr_km) / (math.e * miss_km * miss_km), 1.0)
