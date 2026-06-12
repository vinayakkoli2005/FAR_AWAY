"""Shared fixtures: synthetic OMM records so unit tests never need the network.

A real CelesTrak fixture subset lives in data/fixtures/ for integration tests;
tests that need it skip cleanly when it is absent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.config import FIXTURES_DIR

ISS_LIKE = {
    "OBJECT_NAME": "TESTSAT-A (ISS-LIKE)",
    "OBJECT_ID": "1998-067A",
    "EPOCH": "2026-06-10T12:00:00.000000",
    "MEAN_MOTION": 15.50098000,
    "ECCENTRICITY": 0.0004000,
    "INCLINATION": 51.6400,
    "RA_OF_ASC_NODE": 120.0000,
    "ARG_OF_PERICENTER": 0.0000,
    "MEAN_ANOMALY": 0.0000,
    "EPHEMERIS_TYPE": 0,
    "CLASSIFICATION_TYPE": "U",
    "NORAD_CAT_ID": 90001,
    "ELEMENT_SET_NO": 999,
    "REV_AT_EPOCH": 10000,
    "BSTAR": 0.000030,
    "MEAN_MOTION_DOT": 0.00001,
    "MEAN_MOTION_DDOT": 0.0,
}


def make_omm(**overrides) -> dict:
    rec = dict(ISS_LIKE)
    rec.update(overrides)
    return rec


@pytest.fixture
def iss_like_omm() -> dict:
    return dict(ISS_LIKE)


@pytest.fixture
def fixture_catalog_path() -> Path:
    path = FIXTURES_DIR / "gp_active_subset.json"
    if not path.exists():
        pytest.skip("real CelesTrak fixture not present (run `orbitguard fixture`)")
    return path


@pytest.fixture
def fixture_catalog(fixture_catalog_path) -> list[dict]:
    with open(fixture_catalog_path) as f:
        return json.load(f)
