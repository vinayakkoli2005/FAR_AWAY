"""TraCSS verification run orchestration.

    python -m engine.validation.tracss_harness \
        --eph-dir /Volumes/SSD/tracss/ephemerides \
        --key data/tracss/IVV_Releasable_Dataset_Spherical_DefaultHBR.csv.gz \
        --out data/scorecard.json [--hours 24] [--cache-dir /Volumes/SSD/tracss/npz]

Subset-first discipline: --hours 24 runs the first day only (key sliced the
same way) to debug matching before committing to the full 7-day run.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import numpy as np

from engine.validation.allvsall import EphRecord, screen_all_vs_all
from engine.validation.answer_key import (
    SCREEN_WINDOW_START,
    SCREEN_WINDOW_STOP,
    load_answer_key,
)
from engine.validation.interpolate import LagrangeEphemeris
from engine.validation.matching import match_events
from engine.validation.ocm import parse_ocm

log = logging.getLogger("tracss")

OD_STALENESS_DAYS = 14.0  # User's Guide configuration rule 4


def _load_ephemerides(eph_dir: Path, cache_dir: Path | None) -> list[EphRecord]:
    """Parse every OCM under eph_dir (recursive), with an .npz cache layer."""
    files = sorted(
        p for p in eph_dir.rglob("*") if p.is_file() and p.suffix.lower() in (".ocm", ".txt")
    )
    if not files:
        raise SystemExit(f"no .ocm files under {eph_dir}")
    log.info("found %d ephemeris files", len(files))

    records: list[EphRecord] = []
    n_stale = n_bad = 0
    for i, path in enumerate(files):
        if i % 2000 == 0:
            log.info("parsing %d/%d ...", i, len(files))
        npz = (cache_dir / (path.stem + ".npz")) if cache_dir else None
        try:
            if npz is not None and npz.exists():
                z = np.load(npz, allow_pickle=False)
                times, pos, vel = z["t"], z["p"], z["v"]
                meta = json.loads(str(z["meta"]))
                obj_id = meta["obj_id"]
                us, ue = meta["us"], meta["ue"]
            else:
                ocm = parse_ocm(path, SCREEN_WINDOW_START)
                if ocm.od_epoch is not None:
                    age = (SCREEN_WINDOW_START - ocm.od_epoch).total_seconds() / 86400.0
                    if age > OD_STALENESS_DAYS:
                        n_stale += 1
                        continue
                if ocm.vel_kms is None:
                    n_bad += 1
                    continue
                times, pos, vel = ocm.times_s, ocm.pos_km, ocm.vel_kms
                obj_id, us, ue = ocm.obj_id, ocm.usable_start_s, ocm.usable_stop_s
                if npz is not None:
                    npz.parent.mkdir(parents=True, exist_ok=True)
                    np.savez_compressed(
                        npz, t=times, p=pos.astype(np.float64), v=vel.astype(np.float64),
                        meta=json.dumps({"obj_id": obj_id, "us": us, "ue": ue}),
                    )
            if len(times) < 6:
                n_bad += 1
                continue
            records.append(
                EphRecord(
                    obj_id=obj_id,
                    eph=LagrangeEphemeris(times, pos),
                    usable_start_s=float(us),
                    usable_stop_s=float(ue),
                )
            )
        except Exception as exc:
            n_bad += 1
            log.warning("skip %s: %s", path.name, exc)
    log.info("loaded %d ephemerides (%d stale-OD filtered, %d unusable)",
             len(records), n_stale, n_bad)
    return records


def run(eph_dir: Path, key_path: Path, out_path: Path,
        hours: float | None, cache_dir: Path | None) -> dict:
    window_s = (SCREEN_WINDOW_STOP - SCREEN_WINDOW_START).total_seconds()
    t_max = hours * 3600.0 if hours else window_s

    records = _load_ephemerides(eph_dir, cache_dir)

    # attach velocities to the interpolators for refinement
    t0 = time.perf_counter()
    found = screen_all_vs_all(records, window_s=t_max)
    runtime_s = time.perf_counter() - t0

    key = load_answer_key(key_path, t_min=0.0, t_max=t_max)
    report = match_events([e.as_key_event() for e in found], key, tca_tol_s=5.0)

    tca_err = np.array(report.tca_errors_s) if report.tca_errors_s else np.array([0.0])
    miss_err = np.array(report.miss_errors_km) if report.miss_errors_km else np.array([0.0])
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()

    scorecard = {
        "status": "complete" if not hours else f"subset ({hours} h)",
        "dataset": "TraCSS Dataset for Conjunction Assessment Verification (CC0), spherical/DefaultHBR key",
        "screening_window": f"{SCREEN_WINDOW_START.isoformat()} +{t_max/3600:.0f}h",
        "recall": round(report.recall, 5),
        "precision": round(report.precision, 5),
        "f1": round(report.f1, 5),
        "events_key": report.n_key,
        "events_found": report.n_found,
        "events_matched": report.n_matched,
        "tca_rms_ms": round(float(np.sqrt(np.mean(tca_err**2))) * 1000.0, 2),
        "tca_p95_ms": round(float(np.percentile(np.abs(tca_err), 95)) * 1000.0, 2),
        "miss_rms_m": round(float(np.sqrt(np.mean(miss_err**2))) * 1000.0, 2),
        "miss_p95_m": round(float(np.percentile(np.abs(miss_err), 95)) * 1000.0, 2),
        "runtime_s": round(runtime_s, 1),
        "n_ephemerides": len(records),
        "git_sha": sha,
        "methodology": [
            "Stage B+C screening run directly on the provided OCM ephemerides (no SGP4 in the loop)",
            "6-point Lagrange interpolation, analytic velocity derivative",
            "Matched to the spherical DefaultHBR key on (unordered pair, |dTCA| <= 5 s)",
            "Duplicates count against precision; each key row claimable once",
        ],
        "disclaimer": (
            "Dataset is for algorithm testing, not operational certification "
            "(per the Office of Space Commerce)."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(scorecard, indent=1))

    # missed-event autopsy file for the error-analysis appendix
    autopsy = out_path.with_name(out_path.stem + "_autopsy.json")
    autopsy.write_text(json.dumps({
        "missed": [vars(k) for k in report.missed[:500]],
        "spurious": [vars(k) for k in report.spurious[:500]],
    }, indent=1, default=str))

    log.info("scorecard -> %s  recall=%.4f precision=%.4f", out_path,
             report.recall, report.precision)
    return scorecard


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--eph-dir", required=True, type=Path)
    ap.add_argument("--key", required=True, type=Path)
    ap.add_argument("--out", default=Path("data/scorecard.json"), type=Path)
    ap.add_argument("--hours", type=float, default=None,
                    help="subset run: first N hours only")
    ap.add_argument("--cache-dir", type=Path, default=None,
                    help="npz cache for parsed OCMs (re-runs become instant)")
    args = ap.parse_args()
    sc = run(args.eph_dir, args.key, args.out, args.hours, args.cache_dir)
    print(json.dumps({k: sc[k] for k in
                      ("status", "recall", "precision", "f1", "events_key",
                       "events_found", "tca_rms_ms", "miss_rms_m")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
