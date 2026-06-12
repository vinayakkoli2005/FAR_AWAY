"""OrbitGuard API — serves precomputed/on-demand screening runs.

Demo discipline (plan risk R7): the server boots from the newest cached
snapshot, falling back to the committed fixture — so the demo works with the
network cable pulled. Screening runs are cached in-process per asset set.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from engine import __version__
from engine.api.schemas import (
    CatalogEntry,
    ConjunctionsResponse,
    Evidence,
    ExplainResponse,
    FunnelOut,
    HealthResponse,
)
from engine.astro.elements import CatalogObject, load_catalog
from engine.config import SETTINGS, FIXTURES_DIR, ScreeningConfig
from engine.explain.groq_client import explain
from engine.ingest.celestrak import latest_snapshot, load_snapshot, snapshot_age_hours
from engine.risk.evidence import build_evidence
from engine.risk.policy import assess_event
from engine.screening.pipeline import screen_assets

log = logging.getLogger(__name__)

DEFAULT_ASSETS = [
    int(x) for x in os.environ.get("ORBITGUARD_ASSETS", "25544,62701,69010,60454").split(",")
]


class AppState:
    def __init__(self) -> None:
        self.snapshot_path = None
        self.records: list[dict] = []
        self.catalog: list[CatalogObject] = []
        self.by_id: dict[int, CatalogObject] = {}
        self.raw_by_id: dict[int, dict] = {}
        self.size_map: dict[int, tuple[str, str]] = {}  # norad -> (type, rcs class)
        self.runs: dict[str, dict] = {}        # cache key -> response dict
        self.evidence: dict[str, dict] = {}    # event_id -> evidence record
        self.lock = threading.Lock()

    def load(self) -> None:
        snap = latest_snapshot("active")
        if snap is None:
            snap = FIXTURES_DIR / "gp_active_subset.json"
            if not snap.exists():
                raise RuntimeError("no snapshot and no fixture — run `orbitguard fetch`")
        self.snapshot_path = snap
        self.records = load_snapshot(snap)
        self.catalog, rejects = load_catalog(self.records)
        self.by_id = {o.norad_id: o for o in self.catalog}
        self.raw_by_id = {int(r["NORAD_CAT_ID"]): r for r in self.records}
        from engine.ingest.satcat import load_size_map

        self.size_map = load_size_map()  # offline-safe: empty dict -> heuristics
        log.info("loaded %d objects from %s (%d rejects, %d satcat sizes)",
                 len(self.catalog), snap, len(rejects), len(self.size_map))


STATE = AppState()

app = FastAPI(
    title="OrbitGuard API",
    version=__version__,
    description=(
        "**Free, explainable, validated conjunction screening for small operators.**\n\n"
        "This is the machine interface behind the OrbitGuard web app — the same data the "
        "UI renders, available to any script or ground-segment tool. Typical flow:\n\n"
        "1. `GET /conjunctions` — screen your satellites against the full public catalog "
        "(7-day window). Returns the screening funnel and one *evidence record* per close "
        "approach: TCA, miss distance (with radial/in-track/cross-track split), relative "
        "velocity, collision probability (or worst-case bound), data grade, and the "
        "DODGE/WAIT/WATCH verdict with its rationale.\n"
        "2. `GET /conjunction/{event_id}` — one evidence record.\n"
        "3. `GET /explain/{event_id}` — plain-language narration of that record "
        "(LLM with a strict no-new-numbers contract, deterministic fallback).\n"
        "4. `GET /catalog` — orbit data for 3D visualization (OMM + TLE transport).\n"
        "5. `GET /scorecard` — how this engine scores against the official U.S. TraCSS "
        "conjunction answer key.\n\n"
        "Every number is computed by the physics engine; the LLM can only narrate. "
        "Probabilities on TLE-grade data are worst-case bounds: they can prove safety, "
        "never justify a maneuver."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    STATE.load()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        catalog_objects=len(STATE.catalog),
        snapshot=str(STATE.snapshot_path),
        snapshot_age_hours=round(snapshot_age_hours(STATE.snapshot_path), 2),
        version=__version__,
    )


@app.get("/assets")
def assets() -> list[dict]:
    out = []
    for nid in DEFAULT_ASSETS:
        obj = STATE.by_id.get(nid)
        if obj is None:
            continue
        out.append(
            {
                "norad_id": obj.norad_id,
                "name": obj.name,
                "perigee_km": round(obj.perigee_km, 1),
                "apogee_km": round(obj.apogee_km, 1),
                "inclination_deg": obj.inclination_deg,
                "gp_age_hours": round(obj.epoch_age_hours, 1),
            }
        )
    return out


def _run_screening(asset_ids: list[int], days: float) -> dict:
    missing = [i for i in asset_ids if i not in STATE.by_id]
    if missing:
        raise HTTPException(404, f"assets not in catalog: {missing}")
    from engine.ingest.satcat import combined_hbr_km

    cfg = ScreeningConfig(window_days=days)
    run = screen_assets([STATE.by_id[i] for i in asset_ids], STATE.catalog, cfg=cfg)
    events = []
    for e in run.events:
        asset, obj = STATE.by_id[e.asset_id], STATE.by_id[e.object_id]
        hbr_km, hbr_src = combined_hbr_km(
            asset.name, STATE.size_map.get(e.asset_id, ("", "")),
            obj.name, STATE.size_map.get(e.object_id, ("", "")),
        )
        a = assess_event(e, hbr_km=hbr_km)
        record = build_evidence(e, a, asset, obj, cfg, hbr_source=hbr_src)
        STATE.evidence[record["event_id"]] = record
        events.append(record)

    if os.environ.get("ORBITGUARD_DEMO", "1") == "1" and asset_ids:
        from engine.risk.simulate import simulated_dodge_event

        sim = simulated_dodge_event(STATE.by_id[asset_ids[0]], cfg)
        if sim is not None:
            STATE.evidence[sim["event_id"]] = sim
            events.insert(0, sim)
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(STATE.snapshot_path),
        "window_days": days,
        "asset_ids": asset_ids,
        "funnel": run.funnel.as_dict(),
        "events": events,
    }


@app.get("/conjunctions", response_model=ConjunctionsResponse)
def conjunctions(
    assets: str | None = Query(None, description="comma-separated NORAD IDs"),
    days: float = Query(7.0, ge=0.1, le=14.0),
    refresh: bool = False,
) -> ConjunctionsResponse:
    asset_ids = (
        [int(x) for x in assets.split(",")] if assets else list(DEFAULT_ASSETS)
    )
    key = f"{sorted(asset_ids)}|{days}"
    with STATE.lock:
        if refresh or key not in STATE.runs:
            STATE.runs[key] = _run_screening(asset_ids, days)
        payload = STATE.runs[key]
    return ConjunctionsResponse(
        generated_utc=payload["generated_utc"],
        source=payload["source"],
        window_days=payload["window_days"],
        asset_ids=payload["asset_ids"],
        funnel=FunnelOut(**payload["funnel"]),
        events=[Evidence(**e) for e in payload["events"]],
    )


@app.get("/conjunction/{event_id}", response_model=Evidence)
def conjunction(event_id: str) -> Evidence:
    record = STATE.evidence.get(event_id)
    if record is None:
        raise HTTPException(404, "unknown event_id (run /conjunctions first)")
    return Evidence(**record)


@app.get("/explain/{event_id}", response_model=ExplainResponse)
def explain_event(event_id: str) -> ExplainResponse:
    record = STATE.evidence.get(event_id)
    if record is None:
        raise HTTPException(404, "unknown event_id (run /conjunctions first)")
    exp = explain(record)
    return ExplainResponse(
        event_id=event_id, text=exp.text, source=exp.source, model=exp.model
    )


@app.get("/catalog", response_model=list[CatalogEntry])
def catalog(
    limit: int = Query(2000, ge=1, le=40000),
    ids: str | None = Query(None, description="comma-separated NORAD IDs to force-include"),
) -> list[CatalogEntry]:
    """Catalog slice for the globe: assets + requested ids + sampled background.

    Raw OMM fields ride along so the client can run satellite.js propagation
    for 60 fps animation without server round-trips.
    """
    forced = set(DEFAULT_ASSETS)
    if ids:
        forced |= {int(x) for x in ids.split(",")}
    forced |= {ev["object"]["norad_id"] for ev in STATE.evidence.values()}

    picked: list[CatalogObject] = [STATE.by_id[i] for i in forced if i in STATE.by_id]
    if len(picked) < limit:
        stride = max(len(STATE.catalog) // (limit - len(picked)), 1)
        for obj in STATE.catalog[::stride]:
            if len(picked) >= limit:
                break
            if obj.norad_id not in forced:
                picked.append(obj)

    from sgp4 import exporter

    out: list[CatalogEntry] = []
    for o in picked:
        try:
            line1, line2 = exporter.export_tle(o.satrec)
            tle = [line1, line2]
        except Exception:  # >5-digit IDs etc. — OMM remains the canonical record
            tle = None
        out.append(
            CatalogEntry(
                norad_id=o.norad_id,
                name=o.name,
                object_type=o.object_type,
                perigee_km=round(o.perigee_km, 1),
                apogee_km=round(o.apogee_km, 1),
                inclination_deg=o.inclination_deg,
                epoch_utc=o.epoch.isoformat(),
                omm=STATE.raw_by_id.get(o.norad_id, {}),
                tle=tle,
            )
        )
    return out


@app.get("/scorecard")
def scorecard() -> dict:
    """TraCSS validation scorecard. Until the 20.7 GB dataset run completes,
    this returns the committed methodology with status=pending — we publish
    what we measure, not what we hope."""
    import json
    from engine.config import DATA_DIR

    path = DATA_DIR / "scorecard.json"
    if path.exists():
        return json.loads(path.read_text())
    return {
        "status": "pending",
        "dataset": "TraCSS Dataset for Conjunction Assessment Verification (CC0)",
        "methodology": [
            "Run Stage B+C screening directly on the provided ephemerides (no SGP4 in the loop)",
            "Match events to the spherical DefaultHBR answer key on (pair, TCA within tolerance)",
            "Publish recall, precision, F1, TCA and miss-distance error distributions",
        ],
        "disclaimer": (
            "Dataset is for algorithm testing, not operational certification "
            "(per the Office of Space Commerce)."
        ),
    }
