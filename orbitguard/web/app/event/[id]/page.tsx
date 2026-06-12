"use client";

// Encounter Inspector: flyby view + encounter-plane plot + evidence card +
// grounded explanation with raw-evidence toggle (transparency as UI).

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import EncounterPlane from "@/components/EncounterPlane";
import {
  CatalogEntry,
  Evidence,
  Explanation,
  fetchCatalog,
  fetchConjunctions,
  fetchEvent,
  fetchExplanation,
} from "@/lib/api";

const Globe = dynamic(() => import("@/components/Globe"), { ssr: false });

export default function Inspector({ params }: { params: { id: string } }) {
  const [ev, setEv] = useState<Evidence | null>(null);
  const [exp, setExp] = useState<Explanation | null>(null);
  const [catalog, setCatalog] = useState<CatalogEntry[] | null>(null);
  const [showRaw, setShowRaw] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        let record: Evidence;
        try {
          record = await fetchEvent(params.id);
        } catch {
          // server restarted and lost the run cache: recompute, then retry
          await fetchConjunctions(undefined, 7);
          record = await fetchEvent(params.id);
        }
        setEv(record);
        setCatalog(
          await fetchCatalog(300, `${record.asset.norad_id},${record.object.norad_id}`)
        );
        setExp(await fetchExplanation(params.id));
      } catch (e) {
        setError(String(e));
      }
    })();
  }, [params.id]);

  if (error) return <div className="loading">{error}</div>;
  if (!ev) return <div className="loading">loading evidence…</div>;

  const pc = ev.probability.pc ?? ev.probability.pc_max;
  const rows: [string, string][] = [
    ["TCA (UTC)", new Date(ev.tca_utc).toISOString().replace("T", " ").slice(0, 19)],
    ["Miss distance", `${ev.miss_distance_km.toFixed(3)} km`],
    ["· radial", `${ev.miss_ric_km.radial.toFixed(3)} km`],
    ["· in-track", `${ev.miss_ric_km.in_track.toFixed(3)} km`],
    ["· cross-track", `${ev.miss_ric_km.cross_track.toFixed(3)} km`],
    ["Relative velocity", `${ev.relative_velocity_kms.toFixed(2)} km/s`],
    [ev.probability.pc != null ? "Pc" : "Pc (worst-case bound)", pc?.toExponential(3) ?? "—"],
    ["Method", ev.probability.method],
    ["Hard-body radius", `${ev.probability.hard_body_radius_m.toFixed(0)} m`],
    ["Data grade", ev.data_grade],
    ["Asset GP age", `${ev.asset.gp_age_hours.toFixed(1)} h`],
    ["Object GP age", `${ev.object.gp_age_hours.toFixed(1)} h`],
    ["Screening volume", `${ev.screening.distance_km} km / ${ev.screening.window_days} d`],
  ];

  return (
    <main>
      <div className="inspector">
        <section className="panel" style={{ position: "relative", minHeight: 460 }}>
          <h3>
            <span className={`verdict ${ev.verdict}`}>{ev.verdict}</span>
            {ev.escalate && <span className="esc">REQUEST CDM</span>}
            &nbsp;· {ev.asset.name} ✕ {ev.object.name}
          </h3>
          <div style={{ position: "absolute", inset: "52px 16px 16px" }}>
            {catalog && (
              <Globe
                catalog={catalog}
                events={[ev]}
                assetIds={[ev.asset.norad_id]}
                focusEventId={ev.event_id}
              />
            )}
          </div>
        </section>

        <section className="panel">
          <h3>ENCOUNTER PLANE</h3>
          <EncounterPlane ev={ev} />
          <h3 style={{ marginTop: 18 }}>EVIDENCE</h3>
          <div className="evidence-grid">
            {rows.map(([k, v]) => (
              <div key={k} style={{ display: "contents" }}>
                <span className="k">{k}</span>
                <span className="v">{v}</span>
              </div>
            ))}
          </div>

          <h3 style={{ marginTop: 18 }}>
            EXPLANATION{" "}
            {exp && <span className="source-tag">[{exp.source}{exp.model ? ` · ${exp.model}` : ""}]</span>}
          </h3>
          <div className="explain-box">{exp ? exp.text : "generating…"}</div>
          <button className="raw-toggle" onClick={() => setShowRaw(!showRaw)}>
            {showRaw ? "hide" : "show"} raw evidence record
          </button>
          {showRaw && <pre className="raw">{JSON.stringify(ev, null, 2)}</pre>}
        </section>
      </div>
    </main>
  );
}
