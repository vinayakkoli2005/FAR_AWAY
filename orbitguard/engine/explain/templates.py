"""Deterministic explanation renderer — the fallback that can never go down.

Produces the same structure the LLM is asked for, straight from the evidence
record. "Groq down" can never break the demo (plan risk R8).
"""

from __future__ import annotations

from datetime import datetime


def _fmt_tca(tca_iso: str) -> str:
    dt = datetime.fromisoformat(tca_iso)
    return dt.strftime("%d %b %Y %H:%M:%S UTC")


def render_explanation(ev: dict) -> str:
    asset = ev["asset"]["name"] or f"object {ev['asset']['norad_id']}"
    obj = ev["object"]["name"] or f"object {ev['object']['norad_id']}"
    miss_m = ev["miss_distance_km"] * 1000.0
    prob = ev["probability"]
    verdict = ev["verdict"]

    lines = [
        f"{asset} and {obj} pass within {ev['miss_distance_km']:.2f} km "
        f"({miss_m:.0f} m) of each other at {_fmt_tca(ev['tca_utc'])}, closing at "
        f"{ev['relative_velocity_kms']:.2f} km/s.",
    ]
    ric = ev["miss_ric_km"]
    lines.append(
        f"The miss is {abs(ric['radial']):.2f} km radial, {abs(ric['in_track']):.2f} km "
        f"in-track and {abs(ric['cross_track']):.2f} km cross-track in the asset's frame."
    )
    if prob["pc"] is not None:
        lines.append(
            f"Collision probability is {prob['pc']:.2e} ({prob['method']}, "
            f"hard-body radius {prob['hard_body_radius_m']:.0f} m), computed from "
            f"CDM covariance data."
        )
    else:
        lines.append(
            f"No covariance is available for this pair, so OrbitGuard reports a worst-case "
            f"bound: the collision probability cannot exceed {prob['pc_max']:.2e} under any "
            f"error model consistent with this geometry (hard-body radius "
            f"{prob['hard_body_radius_m']:.0f} m)."
        )
    lines.append(f"Verdict: {verdict}. {ev['policy']['rationale']}")
    if ev.get("escalate"):
        lines.append(
            "Recommended action: request a Conjunction Data Message or owner ephemeris to "
            "obtain covariance before considering any maneuver."
        )
    age = max(ev["asset"]["gp_age_hours"], ev["object"]["gp_age_hours"])
    lines.append(f"Orbit data age: up to {age:.1f} hours; re-screen when fresh GP data arrives.")
    return " ".join(lines)
