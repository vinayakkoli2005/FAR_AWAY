"""Encounter-plane (B-plane) geometry for the short-encounter 2D-Pc collapse.

At TCA the relative velocity is approximately constant through the encounter
and position errors dominate, so the 3D problem collapses onto the 2D plane
perpendicular to the relative velocity. This module builds that plane and
projects miss vector and combined covariance into it.
"""

from __future__ import annotations

import numpy as np


def encounter_basis(dr: np.ndarray, dv: np.ndarray) -> np.ndarray:
    """3x2 matrix E whose columns span the plane perpendicular to dv.

    Column 1 points along the (projected) miss vector, so the projected miss
    is (d, 0) by construction. At a true TCA dr is already ~perpendicular to
    dv; we project anyway to make the basis exact.
    """
    v_hat = dv / np.linalg.norm(dv)
    m = dr - np.dot(dr, v_hat) * v_hat
    m_norm = np.linalg.norm(m)
    if m_norm < 1e-12:
        # head-on: any orthonormal pair perpendicular to v_hat works
        helper = np.array([1.0, 0.0, 0.0])
        if abs(v_hat[0]) > 0.9:
            helper = np.array([0.0, 1.0, 0.0])
        e1 = np.cross(v_hat, helper)
        e1 /= np.linalg.norm(e1)
    else:
        e1 = m / m_norm
    e2 = np.cross(v_hat, e1)
    return np.column_stack([e1, e2])


def project_encounter(
    dr: np.ndarray, dv: np.ndarray, cov_combined: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Project (miss vector, combined 3x3 covariance) into the encounter plane.

    Returns (m2, Cp): 2-vector km and 2x2 covariance km^2. By construction
    m2 = (d, 0).
    """
    e = encounter_basis(dr, dv)
    m2 = e.T @ dr
    cp = e.T @ cov_combined @ e
    return m2, cp


def principal_frame(m2: np.ndarray, cp: np.ndarray) -> tuple[float, float, float, float]:
    """Diagonalize Cp; return (mx, my, sx, sy) — miss components and sigmas
    along the principal axes of the projected covariance."""
    w, vecs = np.linalg.eigh(cp)
    w = np.maximum(w, 1e-20)  # numerical floor; Cp must be PSD
    mr = vecs.T @ m2
    return float(mr[0]), float(mr[1]), float(np.sqrt(w[0])), float(np.sqrt(w[1]))
