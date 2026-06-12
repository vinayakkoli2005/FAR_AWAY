"use client";

// Encounter Inspector: a full-screen cinematic stage (the simulation deserves
// the whole viewport), with the analysis — encounter plane, evidence record,
// grounded explanation — laid out full-width below. A pulsing prompt on the
// stage makes sure nobody misses the scroll.

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
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
  const detailsRef = useRef<HTMLElement>(null);

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
    ["HBR source", ev.probability.hbr_source ?? "default"],
    ["Data grade", ev.data_grade],
    ["Asset GP age", `${ev.asset.gp_age_hours.toFixed(1)} h`],
    ["Object GP age", `${ev.object.gp_age_hours.toFixed(1)} h`],
    ["Screening volume", `${ev.screening.distance_km} km / ${ev.screening.window_days} d`],
  ];

  const scrollToDetails = () =>
    detailsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });

  return (
    <main>
      {/* ---- full-viewport cinematic stage ---- */}
      <section className="stage">
        {catalog && (
          <Globe
            catalog={catalog}
            events={[ev]}
            assetIds={[ev.asset.norad_id]}
            focusEventId={ev.event_id}
            encounter={{
              tcaIso: ev.tca_utc,
              assetId: ev.asset.norad_id,
              objectId: ev.object.norad_id,
              missKm: ev.miss_distance_km,
            }}
          />
        )}
        <div className="stage-head">
          <span className={`verdict ${ev.verdict}`}>{ev.verdict}</span>
          {ev.escalate && <span className="esc">REQUEST CDM</span>}
          {ev.simulated && (
            <span className="sim-chip tip" data-tip="Training scenario: simulated geometry and CDM covariance — but the probability, ellipse and verdict come from the real Foster/Chan pipeline">
              SIMULATED
            </span>
          )}
          <span className="pair-title">
            {ev.asset.name} ✕ {ev.object.name}
          </span>
          <span className="miss-pill">
            miss {ev.miss_distance_km.toFixed(3)} km · {ev.probability.pc != null ? "Pc" : "Pc≤"}{" "}
            {pc?.toExponential(2)}
          </span>
        </div>
        <button className="detail-fab" onClick={scrollToDetails}>
          📊 View detailed analysis ↓
        </button>
      </section>

      {/* ---- full-width analysis below the stage ---- */}
      <section className="details" ref={detailsRef}>
        <div className={`verdict-banner ${ev.verdict}`}>
          <b>{ev.verdict}</b> —{" "}
          {ev.verdict === "DODGE"
            ? "collision probability is above NASA's maneuver-consideration threshold."
            : ev.verdict === "WAIT"
            ? "provably safe: no error model consistent with this geometry exceeds the concern threshold."
            : ev.escalate
            ? "risk cannot be ruled out at this distance, but TLE data can never justify a maneuver — request covariance-grade data (CDM)."
            : "inconclusive at current data quality — re-screen when fresh orbit data arrives."}
        </div>

        <div className="details-grid">
          <div className="panel">
            <h3>ENCOUNTER PLANE</h3>
            <EncounterPlane ev={ev} />
            <details className="howto">
              <summary>How to read this figure</summary>
              <p>
                You are looking along the relative velocity vector — the plane in which the two
                objects actually pass each other. The <b style={{ color: "#9fb0cc" }}>grey dot</b>{" "}
                is the other object; the <b style={{ color: "#4da3ff" }}>blue arrow</b> is the miss
                vector to your satellite at closest approach. The small{" "}
                <b style={{ color: "#ff4d4d" }}>red circle</b> is the combined hard-body size —
                physical contact means being inside it. The dashed or elliptical contours show the
                position-error distribution used by the probability integral.
              </p>
            </details>
          </div>

          <div className="panel">
            <h3>EVIDENCE</h3>
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
              {exp && (
                <span className="source-tag">
                  [{exp.source}
                  {exp.model ? ` · ${exp.model}` : ""}]
                </span>
              )}
            </h3>
            <div className="explain-box">{exp ? exp.text : "generating…"}</div>
            <button className="raw-toggle" onClick={() => setShowRaw(!showRaw)}>
              {showRaw ? "hide" : "show"} raw evidence record
            </button>
            {showRaw && <pre className="raw">{JSON.stringify(ev, null, 2)}</pre>}
          </div>
        </div>
      </section>
    </main>
  );
}
