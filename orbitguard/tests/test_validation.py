"""Validation-harness unit tests on synthetic ephemerides with exact answers.

Two Keplerian-free constructions keep the ground truth analytic:
straight-line trajectories are reproduced exactly by Lagrange interpolation,
so TCA and miss distance have closed-form answers to compare against.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.validation.interpolate import LagrangeEphemeris
from engine.validation.matching import KeyEvent, match_events
from engine.validation.screening import screen_pair


def _linear_eph(r0, v, t_grid):
    r0, v = np.asarray(r0, float), np.asarray(v, float)
    pos = r0[None, :] + np.outer(t_grid, v)
    return LagrangeEphemeris(t_grid, pos)


def test_lagrange_reproduces_polynomial_motion():
    t = np.arange(0.0, 600.0, 60.0)
    eph = _linear_eph([7000, 0, 0], [0, 7.5, 0], t)
    assert np.allclose(eph.position(123.4), [7000, 7.5 * 123.4, 0], atol=1e-9)
    assert np.allclose(eph.velocity(123.4), [0, 7.5, 0], atol=1e-9)


def test_screen_pair_finds_planted_crossing():
    # Head-on pass with a constant 2 km lateral offset: dv is exactly
    # perpendicular to dr at t=300 s, so TCA = 300 s and miss = 2 km in
    # closed form (d^2(t) = 4 + (4500 - 15 t)^2).
    t = np.arange(0.0, 600.0, 60.0)
    a = _linear_eph([7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], t)
    b = _linear_eph([7002.0, 4500.0, 0.0], [0.0, -7.5, 0.0], t)

    events = screen_pair(a, b, screen_dist_km=10.0, coarse_step_s=30.0, id_a="A", id_b="B")
    assert len(events) == 1
    e = events[0]
    assert e.tca_s == pytest.approx(300.0, abs=1e-3)
    assert e.miss_km == pytest.approx(2.0, abs=1e-6)
    assert e.vrel_kms == pytest.approx(15.0, rel=1e-9)


def test_screen_pair_no_event_when_clear():
    t = np.arange(0.0, 600.0, 60.0)
    a = _linear_eph([7000, 0, 0], [0, 7.5, 0], t)
    b = _linear_eph([7100, 0, 500], [0, 7.5, 0], t)  # parallel, 500 km away
    assert screen_pair(a, b) == []


def test_match_events_scoring():
    key = [
        KeyEvent("A", "B", 300.0, 2.0),
        KeyEvent("A", "C", 900.0, 1.0),
        KeyEvent("A", "D", 1500.0, 3.0),  # we will miss this one
    ]
    found = [
        KeyEvent("B", "A", 300.4, 2.05),   # match (unordered pair)
        KeyEvent("A", "C", 898.9, 0.97),   # match
        KeyEvent("A", "E", 2000.0, 4.0),   # spurious
    ]
    rep = match_events(found, key, tca_tol_s=5.0)
    assert rep.n_matched == 2
    assert rep.recall == pytest.approx(2 / 3)
    assert rep.precision == pytest.approx(2 / 3)
    assert len(rep.missed) == 1 and rep.missed[0].pair == frozenset({"A", "D"})
    assert len(rep.spurious) == 1
    assert rep.tca_errors_s[0] == pytest.approx(0.4, abs=1e-9)


def test_match_duplicates_hurt_precision():
    key = [KeyEvent("A", "B", 300.0)]
    found = [KeyEvent("A", "B", 300.1), KeyEvent("A", "B", 301.0)]
    rep = match_events(found, key, tca_tol_s=5.0)
    assert rep.n_matched == 1
    assert rep.precision == 0.5 and rep.recall == 1.0
