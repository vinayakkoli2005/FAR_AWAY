"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { Evidence } from "@/lib/api";

function useCountdown(tcaIso: string): string {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const dt = (new Date(tcaIso).getTime() - now) / 1000;
  if (dt < 0) return "TCA passed";
  const d = Math.floor(dt / 86400);
  const h = Math.floor((dt % 86400) / 3600);
  const m = Math.floor((dt % 3600) / 60);
  const s = Math.floor(dt % 60);
  return d > 0 ? `T−${d}d ${h}h ${m}m` : `T−${h}h ${m}m ${s}s`;
}

export default function EventCard({ ev }: { ev: Evidence }) {
  const countdown = useCountdown(ev.tca_utc);
  const pc = ev.probability.pc ?? ev.probability.pc_max;
  return (
    <Link href={`/event/${ev.event_id}`} className={`card ${ev.verdict}`}>
      <div className="head">
        <span>
          <span className={`verdict ${ev.verdict}`}>{ev.verdict}</span>
          {ev.escalate && <span className="esc">REQUEST CDM</span>}
        </span>
        <span className="badge">{ev.data_grade}</span>
      </div>
      <div className="pair">
        {ev.asset.name} ✕ {ev.object.name}
      </div>
      <div className="countdown">{countdown}</div>
      <div className="nums">
        <span>
          miss <b>{ev.miss_distance_km.toFixed(3)} km</b>
        </span>
        <span>
          vrel <b>{ev.relative_velocity_kms.toFixed(1)} km/s</b>
        </span>
        <span>
          {ev.probability.pc != null ? "Pc" : "Pc≤"} <b>{pc?.toExponential(2)}</b>
        </span>
      </div>
    </Link>
  );
}
