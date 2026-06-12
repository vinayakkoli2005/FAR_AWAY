"""Frame conversions — the single audited module (plan risk R3).

All TEME -> GCRS -> ITRF conversions route through here via Skyfield's
timescale (UT1/TT handled internally, leap seconds from Skyfield's bundled
data). Nothing else in the codebase is allowed to rotate frames.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def _timescale():
    from skyfield.api import load
    return load.timescale()


def _sf_time(t: datetime):
    return _timescale().from_datetime(t.astimezone(timezone.utc))


def teme_to_gcrs_matrix(t: datetime) -> np.ndarray:
    """Rotation matrix M such that r_gcrs = M @ r_teme."""
    from skyfield.sgp4lib import TEME
    # Skyfield frames expose rotation_at(t): ICRF/GCRS -> frame; transpose inverts.
    return TEME.rotation_at(_sf_time(t)).T


def gcrs_to_itrf_matrix(t: datetime) -> np.ndarray:
    """Rotation matrix M such that r_itrf = M @ r_gcrs (Earth-fixed, for the globe)."""
    from skyfield.framelib import itrs
    return itrs.rotation_at(_sf_time(t))


def teme_to_itrf(r_teme: np.ndarray, t: datetime) -> np.ndarray:
    return gcrs_to_itrf_matrix(t) @ (teme_to_gcrs_matrix(t) @ r_teme)


def ric_basis(r: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Radial / In-track / Cross-track orthonormal basis as rows of a 3x3 matrix.

    R: along position vector; C: along orbital angular momentum; I: completes
    the right-handed triad (close to the velocity direction for near-circular
    orbits). Rows are [R, I, C], so M @ x expresses x in RIC components.
    """
    r_hat = r / np.linalg.norm(r)
    c = np.cross(r, v)
    c_hat = c / np.linalg.norm(c)
    i_hat = np.cross(c_hat, r_hat)
    return np.vstack([r_hat, i_hat, c_hat])


def to_ric(r_ref: np.ndarray, v_ref: np.ndarray, vec: np.ndarray) -> np.ndarray:
    """Express `vec` in the RIC frame of the reference state."""
    return ric_basis(r_ref, v_ref) @ vec


def ric_to_inertial_cov(r: np.ndarray, v: np.ndarray, cov_ric: np.ndarray) -> np.ndarray:
    """Rotate a 3x3 covariance given in an object's RIC frame into the inertial frame.

    CDMs deliver covariance in RTN/RIC of each object; combining two objects'
    covariances requires a common frame first.
    """
    m = ric_basis(r, v)          # inertial -> RIC
    return m.T @ cov_ric @ m     # RIC -> inertial congruence
