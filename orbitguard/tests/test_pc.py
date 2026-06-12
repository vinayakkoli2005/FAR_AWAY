"""Collision-probability correctness certificate.

Three independent referees:
1. EXACT analytic value for the isotropic case — the 2D offset-Gaussian disk
   integral is the noncentral chi-square CDF: Pc = ncx2.cdf((R/s)^2, df=2,
   nc=(d/s)^2). Foster (quadrature) and Chan (series) must both match it.
2. Foster vs Chan agreement on anisotropic cases (independent algorithms).
3. Monte Carlo (2M samples) on an anisotropic case.

Plus the PcMax bound property: the exact isotropic Pc never exceeds
R^2/(e d^2) for any sigma — the theorem the risk policy stands on.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import ncx2

from engine.risk.encounter import encounter_basis, project_encounter
from engine.risk.pc_chan import pc_chan, pc_chan_principal
from engine.risk.pc_foster import pc_foster, pc_foster_principal
from engine.risk.pc_max import pc_max_isotropic


def pc_exact_isotropic(d_km: float, sigma_km: float, hbr_km: float) -> float:
    return float(ncx2.cdf((hbr_km / sigma_km) ** 2, df=2, nc=(d_km / sigma_km) ** 2))


ISOTROPIC_CASES = [
    # (miss d, sigma, HBR) spanning Pc ~ 0.5 down to ~1e-9
    (0.0, 0.1, 0.05),
    (0.1, 0.1, 0.02),
    (0.5, 0.2, 0.02),
    (1.0, 0.3, 0.02),
    (2.0, 0.5, 0.05),
    (5.0, 1.0, 0.02),
    (0.05, 0.5, 0.01),
]


@pytest.mark.parametrize("d,sigma,hbr", ISOTROPIC_CASES)
def test_foster_matches_exact_isotropic(d, sigma, hbr):
    exact = pc_exact_isotropic(d, sigma, hbr)
    got = pc_foster_principal(d, 0.0, sigma, sigma, hbr)
    assert got == pytest.approx(exact, rel=1e-6, abs=1e-14)


@pytest.mark.parametrize("d,sigma,hbr", ISOTROPIC_CASES)
def test_chan_matches_exact_isotropic(d, sigma, hbr):
    # Chan's equivalent-area mapping is exact when sx == sy
    exact = pc_exact_isotropic(d, sigma, hbr)
    got = pc_chan_principal(d, 0.0, sigma, sigma, hbr)
    assert got == pytest.approx(exact, rel=1e-9, abs=1e-15)


def test_foster_chan_agree_anisotropic():
    """Cross-check alarm: a geometry bug (swapped axes, wrong frame) shifts Pc
    by orders of magnitude; Chan's equivalent-area approximation drifts only
    fractionally. Verified against an independent scipy.dblquad referee:
    Foster is exact to machine precision everywhere; Chan is ~2% in the
    operational band and degrades to ~30% at >5-sigma anisotropic misses
    (consistent with the published method comparisons). Tolerances encode
    exactly that."""
    rng = np.random.default_rng(7)
    checked = 0
    for _ in range(60):
        sx = rng.uniform(0.05, 0.6)
        sy = sx * rng.uniform(1.0, 3.0)  # aspect ratio <= 3
        mx, my = rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)
        hbr = rng.uniform(0.005, 0.05)
        f = pc_foster_principal(mx, my, sx, sy, hbr)
        c = pc_chan_principal(mx, my, sx, sy, hbr)
        if f < 1e-10:
            continue
        checked += 1
        rel = 2e-2 if f >= 1e-3 else 0.5  # deep tail: order-of-magnitude alarm only
        assert c == pytest.approx(f, rel=rel), (mx, my, sx, sy, hbr)
    assert checked > 20


def test_foster_matches_dblquad_anisotropic():
    """Foster against a brute independent 2D adaptive integration referee."""
    from scipy import integrate

    rng = np.random.default_rng(13)
    for _ in range(5):
        sx = rng.uniform(0.05, 0.4)
        sy = sx * rng.uniform(1.0, 3.0)
        mx, my = rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6)
        hbr = rng.uniform(0.01, 0.05)

        def pdf(y, x):
            return np.exp(-0.5 * (((x - mx) / sx) ** 2 + ((y - my) / sy) ** 2)) / (
                2 * np.pi * sx * sy
            )

        ref, _ = integrate.dblquad(
            pdf, -hbr, hbr,
            lambda x: -np.sqrt(hbr**2 - x**2), lambda x: np.sqrt(hbr**2 - x**2),
            epsabs=1e-16,
        )
        f = pc_foster_principal(mx, my, sx, sy, hbr)
        if ref > 1e-12:
            assert f == pytest.approx(ref, rel=1e-6)


def test_foster_against_monte_carlo():
    rng = np.random.default_rng(2026)
    mx, my, sx, sy, hbr = 0.12, 0.08, 0.15, 0.05, 0.05
    n = 2_000_000
    x = rng.normal(mx, sx, n)
    y = rng.normal(my, sy, n)
    p_mc = np.mean(x * x + y * y <= hbr * hbr)
    se = np.sqrt(p_mc * (1 - p_mc) / n)
    f = pc_foster_principal(mx, my, sx, sy, hbr)
    assert abs(f - p_mc) < 5 * se


def test_pcmax_bounds_exact_isotropic_pc():
    """The theorem: exact Pc(sigma) <= R^2/(e d^2) for every sigma (R << d)."""
    d, hbr = 1.0, 0.02
    pmax = pc_max_isotropic(d, hbr)
    for sigma in np.logspace(-3, 1, 60):
        assert pc_exact_isotropic(d, sigma, hbr) <= pmax * (1 + 1e-3)
    # the bound is tight: attained near sigma = d/sqrt(2)
    near_opt = pc_exact_isotropic(d, d / np.sqrt(2.0), hbr)
    assert near_opt > 0.95 * pmax


def test_pcmax_geometry_edge_cases():
    assert pc_max_isotropic(0.01, 0.02) == 1.0  # overlap cannot be excluded
    assert pc_max_isotropic(10.0, 0.01) < 1e-6  # clearable far miss (10 m HBR cubesat)
    assert pc_max_isotropic(1.0, 0.02) == pytest.approx(
        0.02**2 / (np.e * 1.0**2), rel=1e-12
    )


def test_encounter_projection_geometry():
    rng = np.random.default_rng(11)
    for _ in range(20):
        dv = rng.normal(size=3) * 7.0
        dr = rng.normal(size=3) * 2.0
        dr -= np.dot(dr, dv) / np.dot(dv, dv) * dv  # true TCA: dr perpendicular to dv
        e = encounter_basis(dr, dv)
        assert np.allclose(e.T @ e, np.eye(2), atol=1e-12)
        assert np.allclose(e.T @ dv, 0.0, atol=1e-9)
        cov = rng.normal(size=(3, 3))
        cov = cov @ cov.T + np.eye(3) * 0.1
        m2, cp = project_encounter(dr, dv, cov)
        assert m2[0] == pytest.approx(np.linalg.norm(dr), rel=1e-12)
        assert abs(m2[1]) < 1e-9
        assert np.all(np.linalg.eigvalsh(cp) > 0)


def test_full_pc_path_from_3d_inputs():
    """3D miss/velocity/covariance through projection into both Pc methods."""
    dr = np.array([0.2, 0.1, 0.0])
    dv = np.array([0.0, 0.0, 7.5])
    cov = np.diag([0.04, 0.01, 0.09])  # km^2
    m2, cp = project_encounter(dr, dv, cov)
    f = pc_foster(m2, cp, 0.02)
    c = pc_chan(m2, cp, 0.02)
    assert 0 < f < 1
    assert c == pytest.approx(f, rel=2e-2)
