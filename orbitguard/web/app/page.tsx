"use client";

// Mission Control: globe + ranked conjunction dock + funnel strip.

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import EventCard from "@/components/EventCard";
import FunnelStrip from "@/components/FunnelStrip";
import {
  ConjunctionsResponse,
  CatalogEntry,
  fetchCatalog,
  fetchConjunctions,
} from "@/lib/api";

const Globe = dynamic(() => import("@/components/Globe"), { ssr: false });

const VERDICT_ORDER = { DODGE: 0, WATCH: 1, WAIT: 2 } as const;

const LOADING_STAGES = [
  "loading catalog snapshot…",
  "Stage A — perigee/apogee gate",
  "Stage B — coarse-grid sieve (vectorized SGP4)",
  "Stage C — Brent TCA refinement",
  "computing worst-case collision probabilities…",
];

function LoadingScreen() {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setStage((s) => (s + 1) % LOADING_STAGES.length), 2600);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="loading">
      <div className="orbit-spinner">
        <div className="planet" />
        <div className="sat" />
      </div>
      <p style={{ marginTop: 18 }}>screening the catalog — first run takes ~1–2 min</p>
      <p className="stage-line">{LOADING_STAGES[stage]}</p>
    </div>
  );
}

export default function MissionControl() {
  const [run, setRun] = useState<ConjunctionsResponse | null>(null);
  const [catalog, setCatalog] = useState<CatalogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [assetFilter, setAssetFilter] = useState<number | null>(null);
  const [verdictFilter, setVerdictFilter] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetchConjunctions(undefined, 7);
        setRun(r);
        // fetch catalog AFTER the run so event partners are force-included
        setCatalog(await fetchCatalog(1200));
      } catch (e) {
        setError(String(e));
      }
    })();
  }, []);

  const assetNames = useMemo(() => {
    const m = new Map<number, string>();
    run?.events.forEach((e) => m.set(e.asset.norad_id, e.asset.name));
    return m;
  }, [run]);

  if (error)
    return (
      <div className="loading">
        API unreachable — start it with{" "}
        <code>uvicorn engine.api.app:app --port 8000</code>
        <br />
        <br />
        {error}
      </div>
    );
  if (!run || !catalog) return <LoadingScreen />;

  const verdictCounts: Record<string, number> = { DODGE: 0, WATCH: 0, WAIT: 0 };
  run.events.forEach((e) => (verdictCounts[e.verdict] += 1));

  const events = [...run.events]
    .filter((e) => assetFilter === null || e.asset.norad_id === assetFilter)
    .filter((e) => verdictFilter === null || e.verdict === verdictFilter)
    .sort(
      (a, b) =>
        VERDICT_ORDER[a.verdict] - VERDICT_ORDER[b.verdict] ||
        (b.probability.pc ?? b.probability.pc_max ?? 0) -
          (a.probability.pc ?? a.probability.pc_max ?? 0)
    );

  return (
    <main className="mission">
      <div className="globe-wrap">
        <FunnelStrip funnel={run.funnel} />
        <div className="legend">
          <span><i className="sq" style={{ background: "#ff4d4d" }} /> event: dodge</span>
          <span><i className="sq" style={{ background: "#ffb347" }} /> event: watch</span>
          <span><i className="sq" style={{ background: "#3ddc84" }} /> event: wait</span>
          <span><i className="dot" style={{ background: "#4da3ff" }} /> your satellite</span>
          <span><i className="dot" style={{ background: "#9fb0cc" }} /> other objects</span>
        </div>
        <Globe catalog={catalog} events={run.events} assetIds={run.asset_ids} />
      </div>
      <aside className="dock">
        <h2>
          CONJUNCTIONS · NEXT {run.window_days} DAYS · {events.length}
          {assetFilter !== null ? ` / ${run.events.length}` : ""} EVENTS
        </h2>
        <p className="snapshot-line">
          data snapshot {new Date(run.generated_utc).toUTCString().slice(5, 22)} UTC ·
          CelesTrak GP + SATCAT
        </p>
        <div className="chips">
          {(["DODGE", "WATCH", "WAIT"] as const).map((v) => (
            <button
              key={v}
              className={`chip vchip ${v} ${verdictFilter === v ? "on" : ""}`}
              onClick={() => setVerdictFilter(verdictFilter === v ? null : v)}
            >
              {v.toLowerCase()} · {verdictCounts[v]}
            </button>
          ))}
        </div>
        {assetNames.size > 1 && (
          <div className="chips">
            <button
              className={`chip ${assetFilter === null ? "on" : ""}`}
              onClick={() => setAssetFilter(null)}
            >
              all assets
            </button>
            {Array.from(assetNames.entries()).map(([id, name]) => (
              <button
                key={id}
                className={`chip ${assetFilter === id ? "on" : ""}`}
                onClick={() => setAssetFilter(assetFilter === id ? null : id)}
              >
                {name}
              </button>
            ))}
          </div>
        )}
        {events.length === 0 && (
          <p className="note">No conjunctions within the screening distance — clear window.</p>
        )}
        {events.map((ev) => (
          <EventCard key={ev.event_id} ev={ev} />
        ))}
      </aside>
    </main>
  );
}
