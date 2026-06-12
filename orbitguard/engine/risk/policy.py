"""DODGE / WAIT / WATCH triage policy (plan Section 5.4).

Thresholds anchor to NASA CA Handbook practice: Pc >= 1e-4 triggers maneuver
consideration; 1e-6 is the monitoring floor. The TLE-grade branch enforces
the asymmetry from pc_max.py: worst-case bounds can clear, never convict.
Every verdict ships with its full numeric evidence record — that record, not
free text, is what the explainer receives.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from engine.config import SETTINGS, RiskConfig
from engine.risk.encounter import project_encounter
from engine.risk.pc_chan import pc_chan
from engine.risk.pc_foster import pc_foster
from engine.risk.pc_max import pc_max_isotropic
from engine.screening.tca import ConjunctionEvent


class Verdict(str, Enum):
    DODGE = "DODGE"
    WATCH = "WATCH"
    WAIT = "WAIT"


class DataGrade(str, Enum):
    CDM = "CDM-GRADE"
    TLE = "TLE-GRADE"


@dataclass
class RiskAssessment:
    verdict: Verdict
    grade: DataGrade
    escalate: bool
    low_vrel_flag: bool
    pc: float | None              # rigorous Pc (CDM-grade only)
    pc_method: str
    pc_chan_crosscheck: float | None
    pc_max: float | None          # worst-case bound (TLE-grade)
    hbr_km: float
    rationale: str

    def headline_pc(self) -> float:
        return self.pc if self.pc is not None else (self.pc_max or 0.0)


def assess_event(
    event: ConjunctionEvent,
    cov_combined: np.ndarray | None = None,
    hbr_km: float | None = None,
    cfg: RiskConfig | None = None,
) -> RiskAssessment:
    """Assess one conjunction. cov_combined (3x3 inertial, km^2) marks CDM-grade."""
    cfg = cfg or SETTINGS.risk
    hbr = hbr_km if hbr_km is not None else cfg.default_hbr_m / 1000.0
    low_vrel = event.vrel_kms < cfg.low_vrel_kms
    dr = event.r_object - event.r_asset
    dv = event.v_object - event.v_asset

    if cov_combined is not None:
        m2, cp = project_encounter(dr, dv, cov_combined)
        pc = pc_foster(m2, cp, hbr)
        pc_x = pc_chan(m2, cp, hbr)
        grade = DataGrade.CDM
        if low_vrel:
            verdict, esc = Verdict.WATCH, False
            why = (
                f"Relative velocity {event.vrel_kms*1000:.0f} m/s is below the short-encounter "
                "validity floor; 2D-Pc is not applicable. High-fidelity analysis required."
            )
        elif pc >= cfg.pc_dodge:
            verdict, esc = Verdict.DODGE, False
            why = f"Pc {pc:.2e} is at or above the NASA maneuver-consideration threshold (1e-4)."
        elif pc >= cfg.pc_watch:
            verdict, esc = Verdict.WATCH, False
            why = f"Pc {pc:.2e} sits in the monitoring band (1e-6 to 1e-4); re-screen on every data update."
        else:
            verdict, esc = Verdict.WAIT, False
            why = f"Pc {pc:.2e} is below the concern band (1e-6)."
        return RiskAssessment(
            verdict=verdict, grade=grade, escalate=esc, low_vrel_flag=low_vrel,
            pc=pc, pc_method="Foster-1992 2D quadrature", pc_chan_crosscheck=pc_x,
            pc_max=None, hbr_km=hbr, rationale=why,
        )

    # TLE-grade: no covariance — worst-case bound only.
    pmax = pc_max_isotropic(event.miss_km, hbr)
    if low_vrel:
        verdict, esc = Verdict.WATCH, False
        why = (
            f"Relative velocity {event.vrel_kms*1000:.0f} m/s is below the short-encounter "
            "validity floor; 2D-Pc is not applicable. High-fidelity analysis required."
        )
    elif pmax < cfg.pc_watch:
        verdict, esc = Verdict.WAIT, False
        why = (
            f"Worst-case Pc bound {pmax:.2e} is below 1e-6: safe under ANY covariance "
            "consistent with this geometry (provable clearance)."
        )
    elif pmax >= cfg.pc_dodge and event.miss_km < cfg.escalation_miss_km:
        verdict, esc = Verdict.WATCH, True
        why = (
            f"Worst-case Pc bound {pmax:.2e} cannot rule out risk at {event.miss_km:.2f} km miss, "
            "but TLE-grade data cannot justify a maneuver. Action: request a CDM or owner "
            "ephemeris. TLE data can prove safety, never danger."
        )
    else:
        verdict, esc = Verdict.WATCH, False
        why = (
            f"Worst-case Pc bound {pmax:.2e} is inconclusive; monitor the next GP update "
            f"(miss {event.miss_km:.2f} km)."
        )
    return RiskAssessment(
        verdict=verdict, grade=DataGrade.TLE, escalate=esc, low_vrel_flag=low_vrel,
        pc=None, pc_method="PcMax isotropic worst-case bound", pc_chan_crosscheck=None,
        pc_max=pmax, hbr_km=hbr, rationale=why,
    )
