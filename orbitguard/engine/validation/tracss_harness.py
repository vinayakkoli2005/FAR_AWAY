"""TraCSS verification run orchestration — two phases sized for an 8 GB laptop.

Phase 1 (one-time):
    python -m engine.validation.tracss_harness convert \
        --eph-dir "/Volumes/SSD/.../AerospaceIVVDataset_20251009" \
        --cache-dir "/Volumes/SSD/.../npy_cache" [--workers 6]

Parses every OCM into {n}.t.npy (float64 seconds) + {n}.p.npy (float32 km)
plus one index.json. The 14-day OD-staleness rule is applied here.

Phase 2:
    python -m engine.validation.tracss_harness run \
        --cache-dir "/Volumes/SSD/.../npy_cache" \
        --key data/tracss/IVV_Releasable_Dataset_Spherical_DefaultHBR.csv.gz \
        --out data/scorecard.json [--hours 24] [--slice-hours 24]

Screens all-vs-all in time slices (memory-bounded), matches against the
answer key, writes the scorecard + missed/spurious autopsies.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
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

OD_STALENESS_DAYS = 14.0   # User's Guide configuration rule 4
N_LAGRANGE_PAD = 8         # ephemeris rows kept beyond each slice edge
WINDOW_S = (SCREEN_WINDOW_STOP - SCREEN_WINDOW_START).total_seconds()


# ---------------------------------------------------------------------------
# Phase 1 — convert
# ---------------------------------------------------------------------------

def _convert_one(args: tuple[str, str]) -> tuple[str, dict] | tuple[str, None]:
    path, cache_dir = args
    try:
        ocm = parse_ocm(path, SCREEN_WINDOW_START)
        if ocm.od_epoch is not None:
            age_d = (SCREEN_WINDOW_START - ocm.od_epoch).total_seconds() / 86400.0
            if age_d > OD_STALENESS_DAYS:
                return path, {"skipped": "stale_od"}
        if len(ocm.times_s) < 6:
            return path, {"skipped": "too_short"}
        stem = Path(path).stem
        cd = Path(cache_dir)
        np.save(cd / f"{stem}.t.npy", ocm.times_s.astype(np.float64))
        np.save(cd / f"{stem}.p.npy", ocm.pos_km.astype(np.float32))
        return path, {
            "stem": stem,
            "obj_id": ocm.obj_id,
            "us": float(ocm.usable_start_s),
            "ue": float(ocm.usable_stop_s),
            "n": int(len(ocm.times_s)),
        }
    except Exception as exc:  # malformed file must not kill a 20 GB run
        return path, {"skipped": f"error: {exc}"}


def convert(eph_dir: Path, cache_dir: Path, workers: int = 6) -> None:
    # "._*" are macOS AppleDouble sidecars on exFAT volumes, not data
    files = sorted(str(p) for p in eph_dir.rglob("*.ocm") if not p.name.startswith("._"))
    if not files:
        raise SystemExit(f"no .ocm files under {eph_dir}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    log.info("converting %d OCM files with %d workers", len(files), workers)

    index: dict[str, dict] = {}
    skipped: dict[str, str] = {}
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, (path, meta) in enumerate(
            ex.map(_convert_one, ((f, str(cache_dir)) for f in files), chunksize=16)
        ):
            if i % 2000 == 0:
                log.info("converted %d/%d (%.0f s)", i, len(files), time.perf_counter() - t0)
            if meta is None or "skipped" in (meta or {}):
                skipped[path] = (meta or {}).get("skipped", "unknown")
            else:
                index[meta["stem"]] = meta
    (cache_dir / "index.json").write_text(json.dumps(index))
    (cache_dir / "skipped.json").write_text(json.dumps(skipped, indent=1))
    log.info("convert done: %d usable, %d skipped, %.0f s",
             len(index), len(skipped), time.perf_counter() - t0)


# ---------------------------------------------------------------------------
# Phase 2 — sliced run
# ---------------------------------------------------------------------------

def _load_slice(cache_dir: Path, index: dict[str, dict],
                t0: float, t1: float) -> list[EphRecord]:
    """Memory-mapped row slices: only the ephemeris rows covering [t0, t1]
    (plus interpolation pad) are copied into RAM."""
    records: list[EphRecord] = []
    for stem, meta in index.items():
        if meta["ue"] < t0 or meta["us"] > t1:
            continue
        times = np.load(cache_dir / f"{stem}.t.npy", mmap_mode="r")
        lo = max(int(np.searchsorted(times, t0)) - N_LAGRANGE_PAD, 0)
        hi = min(int(np.searchsorted(times, t1)) + N_LAGRANGE_PAD, len(times))
        if hi - lo < 6:
            continue
        t_slice = np.array(times[lo:hi], dtype=np.float64)
        pos = np.load(cache_dir / f"{stem}.p.npy", mmap_mode="r")
        p_slice = np.array(pos[lo:hi], dtype=np.float64)
        records.append(
            EphRecord(
                obj_id=meta["obj_id"],
                eph=LagrangeEphemeris(t_slice, p_slice),
                usable_start_s=max(meta["us"], float(t_slice[0])),
                usable_stop_s=min(meta["ue"], float(t_slice[-1])),
            )
        )
    return records


def run(cache_dir: Path, key_path: Path, out_path: Path,
        hours: float | None, slice_hours: float) -> dict:
    index = json.loads((cache_dir / "index.json").read_text())
    t_max = min(hours * 3600.0, WINDOW_S) if hours else WINDOW_S

    found = []
    t0 = time.perf_counter()
    s = 0.0
    while s < t_max:
        e = min(s + slice_hours * 3600.0, t_max)
        margin = 120.0
        records = _load_slice(cache_dir, index, max(s - margin, 0.0), e + margin)
        log.info("slice %.0f-%.0f h: %d ephemerides", s / 3600, e / 3600, len(records))
        events = screen_all_vs_all(
            records, window_s=t_max, slice_start_s=s, slice_stop_s=e,
        )
        found.extend(events)
        log.info("slice done: +%d events (total %d)", len(events), len(found))
        s = e
    runtime_s = time.perf_counter() - t0

    key = load_answer_key(key_path, t_min=0.0, t_max=t_max)
    report = match_events([e.as_key_event() for e in found], key, tca_tol_s=5.0)

    tca_err = np.array(report.tca_errors_s) if report.tca_errors_s else np.array([0.0])
    miss_err = np.array(report.miss_errors_km) if report.miss_errors_km else np.array([0.0])
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()

    scorecard = {
        "status": "complete" if t_max >= WINDOW_S else f"subset (first {t_max/3600:.0f} h)",
        "dataset": (
            "TraCSS Dataset for Conjunction Assessment Verification (CC0), "
            "spherical 10 km / DefaultHBR answer key"
        ),
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
        "n_ephemerides": len(index),
        "hardware": "Apple Silicon laptop, 8 GB RAM (time-sliced all-vs-all)",
        "git_sha": sha,
        "methodology": [
            "Stage B+C screening run directly on the provided OCM ephemerides (no SGP4 in the loop)",
            "6-point Lagrange interpolation on position, analytic velocity derivative",
            "All-vs-all, usable windows honored, OD epoch < 14 d, same-designator pairs excluded",
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

    autopsy = out_path.with_name(out_path.stem + "_autopsy.json")
    autopsy.write_text(json.dumps({
        "missed": [vars(k) for k in report.missed[:1000]],
        "spurious": [vars(k) for k in report.spurious[:1000]],
    }, indent=1, default=str))

    log.info("scorecard -> %s  recall=%.4f precision=%.4f", out_path,
             report.recall, report.precision)
    return scorecard


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("convert")
    pc.add_argument("--eph-dir", required=True, type=Path)
    pc.add_argument("--cache-dir", required=True, type=Path)
    pc.add_argument("--workers", type=int, default=6)

    pr = sub.add_parser("run")
    pr.add_argument("--cache-dir", required=True, type=Path)
    pr.add_argument("--key", required=True, type=Path)
    pr.add_argument("--out", default=Path("data/scorecard.json"), type=Path)
    pr.add_argument("--hours", type=float, default=None)
    pr.add_argument("--slice-hours", type=float, default=24.0)

    args = ap.parse_args()
    if args.cmd == "convert":
        convert(args.eph_dir, args.cache_dir, args.workers)
        return 0
    sc = run(args.cache_dir, args.key, args.out, args.hours, args.slice_hours)
    print(json.dumps({k: sc[k] for k in
                      ("status", "recall", "precision", "f1", "events_key",
                       "events_found", "tca_rms_ms", "miss_rms_m", "runtime_s")},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
