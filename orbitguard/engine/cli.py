"""OrbitGuard command line.

    orbitguard fetch   [--group active] [--force]
    orbitguard fixture [--max 800] [--include 25544,...] [--out PATH]
    orbitguard screen  --assets 25544[,ID...] [--days 7] [--snapshot PATH]
                       [--hbr-m 20] [--json out.json] [--explain]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from engine.config import SETTINGS, FIXTURES_DIR, PACKAGE_ROOT, ScreeningConfig


def cmd_fetch(args) -> int:
    from engine.ingest.celestrak import fetch_group

    records, path = fetch_group(args.group, force=args.force)
    print(f"{len(records)} records -> {path}")
    return 0


def cmd_fixture(args) -> int:
    from engine.ingest.celestrak import latest_snapshot, load_snapshot

    snap = latest_snapshot(args.group)
    if snap is None:
        print("no cached snapshot; run `orbitguard fetch` first", file=sys.stderr)
        return 1
    records = load_snapshot(snap)
    include = {int(x) for x in args.include.split(",")} if args.include else set()
    picked = [r for r in records if int(r["NORAD_CAT_ID"]) in include]
    seen = {int(r["NORAD_CAT_ID"]) for r in picked}
    stride = max(len(records) // max(args.max - len(picked), 1), 1)
    for r in records[::stride]:
        if len(picked) >= args.max:
            break
        nid = int(r["NORAD_CAT_ID"])
        if nid not in seen:
            picked.append(r)
            seen.add(nid)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(picked, f)
    print(f"{len(picked)} of {len(records)} records -> {out}")
    return 0


def cmd_screen(args) -> int:
    from engine.astro.elements import load_catalog
    from engine.ingest.celestrak import latest_snapshot, load_snapshot
    from engine.risk.evidence import build_evidence
    from engine.risk.policy import assess_event
    from engine.screening.pipeline import screen_assets

    if args.snapshot:
        records = load_snapshot(Path(args.snapshot))
        source = args.snapshot
    else:
        snap = latest_snapshot("active")
        if snap is None:
            fixture = FIXTURES_DIR / "gp_active_subset.json"
            if not fixture.exists():
                print("no snapshot/fixture; run `orbitguard fetch`", file=sys.stderr)
                return 1
            snap = fixture
        records = load_snapshot(snap)
        source = str(snap)

    catalog, rejects = load_catalog(records)
    by_id = {o.norad_id: o for o in catalog}
    asset_ids = [int(x) for x in args.assets.split(",")]
    missing = [i for i in asset_ids if i not in by_id]
    if missing:
        print(f"assets not in catalog: {missing}", file=sys.stderr)
        return 1
    assets = [by_id[i] for i in asset_ids]

    cfg = ScreeningConfig(window_days=args.days)
    run = screen_assets(assets, catalog, cfg=cfg)
    f = run.funnel

    print(f"\nOrbitGuard screening — {source}")
    print(f"  window: {args.days} d from {run.start.isoformat(timespec='seconds')}")
    print(
        f"  FUNNEL  {f.catalog_size} objects -> Stage A: {f.stage_a_survivors} "
        f"-> Stage B: {f.stage_b_windows} windows -> Stage C: {f.stage_c_events} events"
    )
    print(
        f"  timing  A {f.stage_a_runtime_s:.2f}s | B {f.stage_b_runtime_s:.2f}s | "
        f"C {f.stage_c_runtime_s:.2f}s | total {f.total_runtime_s:.2f}s"
        + (f" | {len(rejects)} records rejected at ingest" if rejects else "")
    )

    from engine.ingest.satcat import combined_hbr_km, load_size_map

    size_map = load_size_map()
    evidence_records = []
    for e in run.events:
        asset, obj = by_id[e.asset_id], by_id[e.object_id]
        if args.hbr_m is not None:
            hbr_km, hbr_src = args.hbr_m / 1000.0, f"manual ({args.hbr_m:.0f} m)"
        else:
            hbr_km, hbr_src = combined_hbr_km(
                asset.name, size_map.get(e.asset_id, ("", "")),
                obj.name, size_map.get(e.object_id, ("", "")),
            )
        a = assess_event(e, hbr_km=hbr_km)
        record = build_evidence(e, a, asset, obj, cfg, hbr_source=hbr_src)
        evidence_records.append(record)

    if not evidence_records:
        print("\n  no conjunctions within screening distance — clear window.")
    else:
        print(f"\n  {'VERDICT':<8} {'ASSET':<22} {'OBJECT':<26} {'TCA (UTC)':<20} "
              f"{'MISS km':>8} {'Pc/PcMax':>10}")
        for r in evidence_records:
            pc = r["probability"]["pc"] or r["probability"]["pc_max"]
            flag = " ESC" if r["escalate"] else ""
            print(
                f"  {r['verdict']:<8} {r['asset']['name'][:21]:<22} "
                f"{r['object']['name'][:25]:<26} {r['tca_utc'][:19]:<20} "
                f"{r['miss_distance_km']:>8.3f} {pc:>10.2e}{flag}"
            )

    if args.explain and evidence_records:
        from engine.explain.groq_client import explain

        print("\nExplanations:")
        for r in evidence_records[: args.explain_top]:
            exp = explain(r)
            print(f"\n[{r['event_id']}] ({exp.source})\n  {exp.text}")

    if args.json:
        out = {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "funnel": f.as_dict(),
            "config": {
                "screen_dist_km": cfg.screen_dist_km,
                "window_days": cfg.window_days,
                "coarse_step_s": cfg.coarse_step_s,
                "hbr_m": args.hbr_m,
            },
            "events": evidence_records,
        }
        with open(args.json, "w") as fp:
            json.dump(out, fp, indent=1)
        print(f"\nresults -> {args.json}")
    return 0


def cmd_bake(args) -> int:
    """Freeze a full demo dataset into static JSON for serverless deployment.

    The deployed site (Vercel) is pure static files + client-side Cesium: all
    physics runs here, once, and the results ship as /data/*.json. Re-run and
    redeploy to refresh the snapshot.
    """
    from datetime import datetime, timezone

    from sgp4 import exporter

    from engine.astro.elements import load_catalog
    from engine.explain.groq_client import explain
    from engine.ingest.celestrak import latest_snapshot, load_snapshot
    from engine.ingest.satcat import combined_hbr_km, load_size_map
    from engine.risk.evidence import build_evidence
    from engine.risk.policy import assess_event
    from engine.risk.simulate import simulated_dodge_event
    from engine.screening.pipeline import screen_assets

    snap = latest_snapshot("active")
    if snap is None:
        snap = FIXTURES_DIR / "gp_active_subset.json"
    records = load_snapshot(snap)
    catalog, _ = load_catalog(records)
    by_id = {o.norad_id: o for o in catalog}
    asset_ids = [int(x) for x in args.assets.split(",") if int(x) in by_id]
    assets = [by_id[i] for i in asset_ids]
    size_map = load_size_map()

    cfg = ScreeningConfig(window_days=args.days)
    run = screen_assets(assets, catalog, cfg=cfg)

    events = []
    sim = simulated_dodge_event(assets[0], cfg) if assets else None
    if sim is not None:
        events.append(sim)
    for e in run.events:
        asset, obj = by_id[e.asset_id], by_id[e.object_id]
        hbr_km, hbr_src = combined_hbr_km(
            asset.name, size_map.get(e.asset_id, ("", "")),
            obj.name, size_map.get(e.object_id, ("", "")),
        )
        a = assess_event(e, hbr_km=hbr_km)
        events.append(build_evidence(e, a, asset, obj, cfg, hbr_source=hbr_src))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    conjunctions = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": f"CelesTrak GP snapshot {snap.name}",
        "window_days": cfg.window_days,
        "asset_ids": asset_ids,
        "funnel": run.funnel.as_dict(),
        "events": events,
    }
    with open(out / "conjunctions.json", "w") as f:
        json.dump(conjunctions, f)

    # explanations: Groq for the top events (budget discipline), template rest
    def rank(ev):
        return -(ev["probability"]["pc"] or ev["probability"]["pc_max"] or 0.0)

    explanations = {}
    for i, ev in enumerate(sorted(events, key=rank)):
        if i >= args.explain_top:
            from engine.explain.templates import render_explanation

            explanations[ev["event_id"]] = {
                "text": render_explanation(ev), "source": "template", "model": None,
            }
        else:
            exp = explain(ev)
            explanations[ev["event_id"]] = {
                "text": exp.text, "source": exp.source, "model": exp.model,
            }
    with open(out / "explanations.json", "w") as f:
        json.dump(explanations, f)

    # catalog slice for the globe: assets + partners forced, sampled background
    forced = set(asset_ids) | {ev["object"]["norad_id"] for ev in events}
    picked = [by_id[i] for i in forced if i in by_id]
    stride = max(len(catalog) // max(args.catalog_size - len(picked), 1), 1)
    for o in catalog[::stride]:
        if len(picked) >= args.catalog_size:
            break
        if o.norad_id not in forced:
            picked.append(o)
    cat_out = []
    for o in picked:
        try:
            l1, l2 = exporter.export_tle(o.satrec)
            tle = [l1, l2]
        except Exception:
            tle = None
        cat_out.append({
            "norad_id": o.norad_id, "name": o.name, "object_type": o.object_type,
            "perigee_km": round(o.perigee_km, 1), "apogee_km": round(o.apogee_km, 1),
            "inclination_deg": o.inclination_deg, "epoch_utc": o.epoch.isoformat(),
            "omm": {}, "tle": tle,
        })
    with open(out / "catalog.json", "w") as f:
        json.dump(cat_out, f)

    sc_path = PACKAGE_ROOT / "data" / "scorecard.json"
    if sc_path.exists():
        (out / "scorecard.json").write_text(sc_path.read_text())

    n_groq = sum(1 for v in explanations.values() if v["source"] == "groq")
    print(f"baked {len(events)} events ({n_groq} groq-narrated), "
          f"{len(cat_out)} catalog objects -> {out}")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="orbitguard")
    sub = p.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("fetch", help="download/cache a CelesTrak GP group (OMM JSON)")
    pf.add_argument("--group", default="active")
    pf.add_argument("--force", action="store_true")
    pf.set_defaults(fn=cmd_fetch)

    px = sub.add_parser("fixture", help="freeze a committed fixture subset from the cache")
    px.add_argument("--group", default="active")
    px.add_argument("--max", type=int, default=800)
    px.add_argument("--include", default="25544")
    px.add_argument("--out", default=str(FIXTURES_DIR / "gp_active_subset.json"))
    px.set_defaults(fn=cmd_fixture)

    ps = sub.add_parser("screen", help="screen assets against the catalog")
    ps.add_argument("--assets", required=True, help="comma-separated NORAD IDs")
    ps.add_argument("--days", type=float, default=SETTINGS.screening.window_days)
    ps.add_argument("--snapshot", default=None)
    ps.add_argument("--hbr-m", type=float, default=None,
                    help="override combined hard-body radius (default: per-object RCS sizes)")
    ps.add_argument("--json", default=None)
    ps.add_argument("--explain", action="store_true")
    ps.add_argument("--explain-top", type=int, default=5)
    ps.set_defaults(fn=cmd_screen)

    pb = sub.add_parser("bake", help="freeze a static demo dataset for serverless deploy")
    pb.add_argument("--assets", default="25544,62701,69010,60454")
    pb.add_argument("--days", type=float, default=SETTINGS.screening.window_days)
    pb.add_argument("--out", default=str(PACKAGE_ROOT / "web" / "public" / "data"))
    pb.add_argument("--catalog-size", type=int, default=1200)
    pb.add_argument("--explain-top", type=int, default=40)
    pb.set_defaults(fn=cmd_bake)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
