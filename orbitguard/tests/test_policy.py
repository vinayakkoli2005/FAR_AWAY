"""Risk-policy table tests (plan Section 5.4) and the evidence/explainer chain."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pytest

from engine.config import RiskConfig, ScreeningConfig
from engine.risk.evidence import build_evidence
from engine.risk.policy import DataGrade, Verdict, assess_event
from engine.explain.templates import render_explanation
from engine.explain.validator import validate_narration
from engine.screening.tca import ConjunctionEvent
from engine.astro.elements import from_omm
from tests.conftest import make_omm

CFG = RiskConfig()


def _event(miss_km: float, vrel_kms: float = 10.0) -> ConjunctionEvent:
    r_a = np.array([6800.0, 0.0, 0.0])
    v_a = np.array([0.0, 7.6, 0.0])
    dr_dir = np.array([0.0, 0.0, 1.0])
    r_b = r_a + dr_dir * miss_km
    v_b = v_a + np.array([0.0, -vrel_kms, 0.0])
    ric = (0.0, 0.0, miss_km)
    return ConjunctionEvent(
        asset_id=90001, object_id=90002,
        tca=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        miss_km=miss_km, vrel_kms=float(np.linalg.norm(v_b - v_a)),
        miss_ric_km=ric, r_asset=r_a, v_asset=v_a, r_object=r_b, v_object=v_b,
    )


def test_cdm_grade_dodge():
    # tight miss, tight covariance => Pc above 1e-4
    cov = np.eye(3) * 0.1**2
    a = assess_event(_event(0.05), cov_combined=cov, hbr_km=0.02, cfg=CFG)
    assert a.grade == DataGrade.CDM
    assert a.pc is not None and a.pc >= 1e-4
    assert a.verdict == Verdict.DODGE
    assert a.pc_chan_crosscheck == pytest.approx(a.pc, rel=2e-2)


def test_cdm_grade_wait():
    cov = np.eye(3) * 0.05**2
    a = assess_event(_event(8.0), cov_combined=cov, hbr_km=0.02, cfg=CFG)
    assert a.verdict == Verdict.WAIT and a.pc < 1e-6


def test_tle_grade_provable_wait():
    # small HBR far miss: PcMax = hbr^2/(e d^2) < 1e-6 => provable clearance
    a = assess_event(_event(9.0), hbr_km=0.005, cfg=CFG)
    assert a.grade == DataGrade.TLE
    assert a.pc is None and a.pc_max is not None and a.pc_max < 1e-6
    assert a.verdict == Verdict.WAIT and not a.escalate


def test_tle_grade_escalation_never_dodge():
    """TLE data can prove safety, never danger: worst case is WATCH+ESCALATE."""
    a = assess_event(_event(0.3), hbr_km=0.02, cfg=CFG)
    assert a.pc_max is not None and a.pc_max >= 1e-4
    assert a.verdict == Verdict.WATCH and a.escalate


def test_tle_grade_inconclusive_watch():
    a = assess_event(_event(8.0), hbr_km=0.02, cfg=CFG)
    assert a.verdict == Verdict.WATCH and not a.escalate


def test_low_vrel_flag_blocks_2d_pc():
    cov = np.eye(3) * 0.1**2
    a = assess_event(_event(0.05, vrel_kms=0.05), cov_combined=cov, hbr_km=0.02, cfg=CFG)
    assert a.low_vrel_flag and a.verdict == Verdict.WATCH


def test_evidence_template_validator_chain():
    asset = from_omm(make_omm(NORAD_CAT_ID=90001, OBJECT_NAME="ASSET-SAT"))
    obj = from_omm(make_omm(NORAD_CAT_ID=90002, OBJECT_NAME="DEBRIS-X"))
    ev = _event(2.5)
    a = assess_event(ev, hbr_km=0.02, cfg=CFG)
    record = build_evidence(ev, a, asset, obj, ScreeningConfig())
    assert record["verdict"] == a.verdict.value
    # probabilities are rounded to 3 significant figures at the evidence layer
    assert record["probability"]["pc_max"] == pytest.approx(a.pc_max, rel=1e-2)

    text = render_explanation(record)
    assert "DEBRIS-X" in text and a.verdict.value in text
    ok, offending = validate_narration(text, record)
    assert ok, f"template narration must always validate, offending: {offending}"


def test_validator_rejects_foreign_numbers():
    asset = from_omm(make_omm(NORAD_CAT_ID=90001))
    obj = from_omm(make_omm(NORAD_CAT_ID=90002))
    ev = _event(2.5)
    a = assess_event(ev, hbr_km=0.02, cfg=CFG)
    record = build_evidence(ev, a, asset, obj, ScreeningConfig())
    # pin the wall-clock-derived fields so the test is deterministic
    record["asset"]["gp_age_hours"] = 10.0
    record["object"]["gp_age_hours"] = 12.0
    ok, offending = validate_narration(
        "The satellites pass within 47.3 km of each other.", record
    )
    assert not ok and "47.3" in offending
