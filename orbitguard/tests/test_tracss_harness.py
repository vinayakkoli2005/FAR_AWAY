"""OCM parser + all-vs-all engine tests on synthetic data with exact answers."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from engine.validation.allvsall import EphRecord, screen_all_vs_all
from engine.validation.interpolate import LagrangeEphemeris
from engine.validation.ocm import parse_ocm

REF = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

OCM_RELATIVE = """CCSDS_OCM_VERS = 3.0
CREATION_DATE = 2025-10-09T00:00:00
ORIGINATOR = AEROSPACE
META_START
OBJECT_DESIGNATOR = 12345
TIME_SYSTEM = UTC
EPOCH_TZERO = 2025-01-01T12:00:00.000
META_STOP
OD_EPOCH = 2024-12-30T00:00:00
TRAJ_START
TRAJ_REF_FRAME = J2000
USEABLE_START_TIME = 2025-01-01T12:01:00.000
USEABLE_STOP_TIME = 2025-01-01T12:09:00.000
TRAJ_TYPE = CARTPV
0.0   7000.0 0.0 0.0   0.0 7.5 0.0
60.0  7000.0 450.0 0.0  0.0 7.5 0.0
120.0 7000.0 900.0 0.0  0.0 7.5 0.0
180.0 7000.0 1350.0 0.0 0.0 7.5 0.0
240.0 7000.0 1800.0 0.0 0.0 7.5 0.0
300.0 7000.0 2250.0 0.0 0.0 7.5 0.0
360.0 7000.0 2700.0 0.0 0.0 7.5 0.0
420.0 7000.0 3150.0 0.0 0.0 7.5 0.0
480.0 7000.0 3600.0 0.0 0.0 7.5 0.0
540.0 7000.0 4050.0 0.0 0.0 7.5 0.0
600.0 7000.0 4500.0 0.0 0.0 7.5 0.0
TRAJ_STOP
"""


def test_parse_ocm_relative_times(tmp_path):
    p = tmp_path / "12345.ocm"
    p.write_text(OCM_RELATIVE)
    ocm = parse_ocm(p, REF)
    assert ocm.obj_id == "12345"
    assert ocm.times_s[0] == 0.0 and ocm.times_s[-1] == 600.0
    assert ocm.pos_km.shape == (11, 3)
    assert ocm.vel_kms is not None and ocm.vel_kms[0, 1] == 7.5
    assert ocm.usable_start_s == 60.0 and ocm.usable_stop_s == 540.0
    assert ocm.od_epoch is not None and ocm.od_epoch.year == 2024


def test_parse_ocm_iso_times(tmp_path):
    iso = OCM_RELATIVE
    # replace relative data lines with absolute ISO epochs
    lines = []
    for line in iso.splitlines():
        parts = line.split()
        if parts and parts[0].replace(".", "").isdigit() and len(parts) == 7:
            sec = float(parts[0])
            mm, ss = divmod(int(sec), 60)
            lines.append(
                f"2025-01-01T12:{mm:02d}:{ss:02d}.000 " + " ".join(parts[1:])
            )
        else:
            lines.append(line)
    p = tmp_path / "12345.ocm"
    p.write_text("\n".join(lines))
    ocm = parse_ocm(p, REF)
    assert ocm.times_s[0] == 0.0 and ocm.times_s[-1] == 600.0
    assert np.allclose(ocm.pos_km[-1], [7000.0, 4500.0, 0.0])


def _linear_record(obj_id, r0, v, t_grid, us=None, ue=None) -> EphRecord:
    r0, v = np.asarray(r0, float), np.asarray(v, float)
    pos = r0[None, :] + np.outer(t_grid, v)
    eph = LagrangeEphemeris(t_grid, pos)
    return EphRecord(
        obj_id=str(obj_id), eph=eph,
        usable_start_s=us if us is not None else float(t_grid[0]),
        usable_stop_s=ue if ue is not None else float(t_grid[-1]),
    )


def test_all_vs_all_finds_planted_crossings():
    t = np.arange(0.0, 1200.0, 60.0)
    # head-on pass with 2 km offset at t=300 (closed form, see test_validation)
    a = _linear_record("100", [7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], t)
    b = _linear_record("200", [7002.0, 4500.0, 0.0], [0.0, -7.5, 0.0], t)
    # crossing pair planted at t=900 with 1 km offset in z
    c = _linear_record("300", [9000.0, 0.0, 0.0], [0.0, 7.0, 0.0], t)
    d = _linear_record("400", [9000.0, 6300.0 + 6300.0, 1.0], [0.0, -7.0, 0.0], t)
    # far bystander
    e = _linear_record("500", [42000.0, 0.0, 0.0], [3.0, 0.0, 0.0], t)

    events = screen_all_vs_all([a, b, c, d, e], window_s=1200.0)
    pairs = {(ev.id_a, ev.id_b): ev for ev in events}
    assert ("100", "200") in pairs
    ev = pairs[("100", "200")]
    assert ev.tca_s == pytest.approx(300.0, abs=1e-2)
    assert ev.miss_km == pytest.approx(2.0, abs=1e-5)
    assert ("300", "400") in pairs
    assert pairs[("300", "400")].tca_s == pytest.approx(900.0, abs=1e-2)
    assert pairs[("300", "400")].miss_km == pytest.approx(1.0, abs=1e-5)
    assert all("500" not in p for p in pairs)


def test_all_vs_all_respects_usable_window_and_same_id():
    t = np.arange(0.0, 1200.0, 60.0)
    a = _linear_record("100", [7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], t)
    # same conjunction geometry, but B's usable window ends before the event
    b = _linear_record("200", [7002.0, 4500.0, 0.0], [0.0, -7.5, 0.0], t, ue=200.0)
    events = screen_all_vs_all([a, b], window_s=1200.0)
    assert events == []

    # candidate OCMs of the SAME object designator are never screened together
    b2 = _linear_record("100", [7002.0, 4500.0, 0.0], [0.0, -7.5, 0.0], t)
    events = screen_all_vs_all([a, b2], window_s=1200.0)
    assert events == []


def test_all_vs_all_excludes_tca_outside_window():
    # conjunction at t=300 but window cut to 250 s: TCA outside => no report
    t = np.arange(0.0, 1200.0, 60.0)
    a = _linear_record("100", [7000.0, 0.0, 0.0], [0.0, 7.5, 0.0], t)
    b = _linear_record("200", [7002.0, 4500.0, 0.0], [0.0, -7.5, 0.0], t)
    events = screen_all_vs_all([a, b], window_s=250.0)
    assert events == []
