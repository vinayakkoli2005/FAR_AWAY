"""Per-object hard-body radius logic (SATCAT RCS classes + heuristics)."""

from __future__ import annotations

from engine.ingest.satcat import combined_hbr_km, radius_m


def test_rcs_class_radii_ordering():
    assert radius_m("X", "PAY", "SMALL") < radius_m("X", "PAY", "MEDIUM") < radius_m(
        "X", "PAY", "LARGE"
    )


def test_name_overrides_beat_rcs():
    assert radius_m("ISS (ZARYA)", "PAY", "LARGE") == 55.0


def test_heuristics_without_satcat():
    assert radius_m("FENGYUN 1C DEB", "", "") == radius_m("X", "", "SMALL")
    assert radius_m("CZ-4B R/B", "", "") == radius_m("X", "", "LARGE")
    assert radius_m("SOMESAT-1", "", "") == 2.0  # default medium-ish


def test_combined_hbr_and_provenance():
    hbr_km, src = combined_hbr_km("A-SAT", ("PAY", "MEDIUM"), "B DEB", ("DEB", "SMALL"))
    assert hbr_km == (2.0 + 0.5) / 1000.0
    assert "MEDIUM" in src and "SMALL" in src

    # floor: two unknowns never produce a sub-metre combined HBR
    hbr_km, _ = combined_hbr_km("a", ("", "SMALL"), "b", ("", "SMALL"), floor_m=1.5)
    assert hbr_km >= 1.5 / 1000.0


def test_verdict_diversity_restored():
    """The reason this module exists: with RCS-derived HBRs, far misses become
    provably safe (WAIT) instead of everything collapsing to WATCH."""
    from engine.risk.pc_max import pc_max_isotropic

    small_pair_hbr, _ = combined_hbr_km("CUBESAT", ("PAY", "SMALL"), "DEB", ("DEB", "SMALL"))
    assert pc_max_isotropic(8.0, small_pair_hbr) < 1e-6  # WAIT reachable inside 10 km

    iss_hbr, _ = combined_hbr_km("ISS (ZARYA)", ("PAY", "LARGE"), "DEB", ("DEB", "SMALL"))
    assert pc_max_isotropic(0.7, iss_hbr) >= 1e-4  # close ISS pass still escalates