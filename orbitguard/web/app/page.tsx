"use client";

// Mission Control: globe + ranked conjunction dock + funnel strip.

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
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

export default function MissionControl() {
  const [run, setRun] = useState<ConjunctionsResponse | null>(null);
  const [catalog, setCatalog] = useState<CatalogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

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
  if (!run || !catalog)
    return <div className="loading">screening the catalog… first run takes ~1–2 min</div>;

  const events = [...run.events].sort(
    (a, b) =>
      VERDICT_ORDER[a.verdict] - VERDICT_ORDER[b.verdict] ||
      (b.probability.pc ?? b.probability.pc_max ?? 0) -
        (a.probability.pc ?? a.probability.pc_max ?? 0)
  );

  return (
    <main className="mission">
      <div className="globe-wrap">
        <FunnelStrip funnel={run.funnel} />
        <Globe catalog={catalog} events={run.events} assetIds={run.asset_ids} />
      </div>
      <aside className="dock">
        <h2>
          CONJUNCTIONS · NEXT {run.window_days} DAYS · {events.length} EVENTS
        </h2>
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
