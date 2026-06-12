"""Golden tests for ingest, propagation and frames (plan risk R3).

The Skyfield cross-check exercises the full chain: OMM -> Satrec -> SGP4 ->
TEME -> GCRS, against an independent implementation of the TEME rotation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from engine.astro.elements import from_omm, load_catalog, semi_major_axis_km
from engine.astro.frames import ric_basis, teme_to_gcrs_matrix, to_ric
from engine.astro.propagate import make_grid, propagate_many, propagate_one
from tests.conftest import make_omm


def test_from_omm_geometry(iss_like_omm):
    obj = from_omm(iss_like_omm)
    assert obj.norad_id == 90001
    # ISS-like: a ~ 6795 km radius, near-circular
    assert 6700 < obj.perigee_km < obj.apogee_km < 6900
    assert obj.epoch.tzinfo is not None


def test_semi_major_axis_sanity():
    # geostationary: 1 rev/day -> a ~ 42164 km
    assert abs(semi_major_axis_km(1.0027) - 42164) < 50


def test_load_catalog_skips_bad_records(iss_like_omm):
    bad = {"OBJECT_NAME": "BROKEN"}  # missing everything
    objects, rejects = load_catalog([iss_like_omm, bad])
    assert len(objects) == 1 and len(rejects) == 1


def test_propagation_altitude_band(iss_like_omm):
    obj = from_omm(iss_like_omm)
    t0 = obj.epoch
    grid = make_grid(t0, 3 * 3600.0, 60.0)
    r, v, ok = propagate_many([obj.satrec], grid)
    assert ok.all()
    radii = np.linalg.norm(r[0], axis=1)
    assert radii.min() > obj.perigee_km - 5
    assert radii.max() < obj.apogee_km + 5
    speeds = np.linalg.norm(v[0], axis=1)
    assert 7.0 < speeds.mean() < 8.0  # LEO orbital speed


def test_grid_fraction_stays_normalized(iss_like_omm):
    obj = from_omm(iss_like_omm)
    start = obj.epoch.replace(hour=23, minute=30)  # force a day rollover
    grid = make_grid(start, 7200.0, 30.0)
    assert (grid.fr >= 0).all() and (grid.fr < 1).all()
    # continuity across the rollover: consecutive positions ~ v * dt apart
    r, v, ok = propagate_many([obj.satrec], grid)
    steps = np.linalg.norm(np.diff(r[0], axis=0), axis=1)
    assert (steps < 8.0 * 30.0 * 1.1).all()


def test_skyfield_cross_check(iss_like_omm):
    """Our TEME->GCRS position must match Skyfield's independent pipeline to <5 m."""
    skyfield = pytest.importorskip("skyfield.api")
    from skyfield.api import load
    from skyfield.sgp4lib import EarthSatellite

    obj = from_omm(iss_like_omm)
    ts = load.timescale()
    sat = EarthSatellite.from_satrec(obj.satrec, ts)

    for hours in (0.0, 1.0, 25.0, 90.0):
        t = obj.epoch + timedelta(hours=hours)
        r_teme, _ = propagate_one(obj.satrec, t)
        r_gcrs_ours = teme_to_gcrs_matrix(t) @ r_teme
        r_gcrs_sky = sat.at(ts.from_datetime(t)).position.km
        assert np.linalg.norm(r_gcrs_ours - r_gcrs_sky) < 0.005, f"divergence at +{hours}h"


def test_ric_basis_orthonormal_and_oriented(iss_like_omm):
    obj = from_omm(iss_like_omm)
    r, v = propagate_one(obj.satrec, obj.epoch + timedelta(minutes=17))
    m = ric_basis(r, v)
    assert np.allclose(m @ m.T, np.eye(3), atol=1e-12)
    # radial unit vector along r; in-track roughly along v for near-circular orbit
    assert np.dot(m[0], r / np.linalg.norm(r)) > 0.999999
    assert np.dot(m[1], v / np.linalg.norm(v)) > 0.99
    # a purely radial offset decomposes purely radially
    ric = to_ric(r, v, r / np.linalg.norm(r) * 1.5)
    assert abs(ric[0] - 1.5) < 1e-9 and abs(ric[1]) < 1e-9 and abs(ric[2]) < 1e-9
