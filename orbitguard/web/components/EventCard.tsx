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

const MEANING: Record<string, string> = {
  DODGE: "above NASA's maneuver-consideration threshold — act now",
  WATCH: "can't be ruled safe yet — monitor every data update",
  WAIT: "provably safe under any consistent error model",
};

export default function EventCard({ ev, locatable = true }: { ev: Evidence; locatable?: boolean }) {
  const countdown = useCountdown(ev.tca_utc);
  const pc = ev.probability.pc ?? ev.probability.pc_max;

  const locate = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    window.dispatchEvent(new CustomEvent("og-focus", { detail: ev.event_id }));
  };

  return (
    <Link href={`/event/${ev.event_id}`} className={`card ${ev.verdict}`}>
      <div className="head">
        <span>
          <span className={`verdict ${ev.verdict}`}>{ev.verdict}</span>
          {ev.escalate && (
            <span className="esc tip" data-tip="TLE data can prove safety, never danger — ask the object's owner or 18 SDS for covariance-grade data before considering a maneuver">
              REQUEST CDM
            </span>
          )}
        </span>
        <span>
          {locatable && (
            <button
              className="locate tip"
              data-tip="Fly the globe to this encounter"
              onClick={locate}
            >
              📍
            </button>
          )}
          <span
            className="badge tip"
            data-tip={
              ev.data_grade === "TLE-GRADE"
                ? "Computed from public TLE orbits — no covariance, so the probability shown is a worst-case bound"
                : "Computed from CDM covariance data — rigorous probability"
            }
          >
            {ev.data_grade}
          </span>
        </span>
      </div>
      <div className="pair">
        {ev.asset.name} <span className="x">✕</span> {ev.object.name}
      </div>
      <div className="meaning">{MEANING[ev.verdict]}</div>
      <div className="countdown">{countdown}</div>
      <div className="nums">
        <span className="tip" data-tip="Predicted closest distance between the two objects">
          miss <b>{ev.miss_distance_km.toFixed(3)} km</b>
        </span>
        <span className="tip" data-tip="Closing speed at the moment of closest approach">
          vrel <b>{ev.relative_velocity_kms.toFixed(1)} km/s</b>
        </span>
        <span
          className="tip"
          data-tip={
            ev.probability.pc != null
              ? "Collision probability (Foster 2D method — what NASA CARA runs)"
              : "Worst-case bound: the collision probability cannot exceed this under ANY error model consistent with the geometry"
          }
        >
          {ev.probability.pc != null ? "Pc" : "Pc≤"} <b>{pc?.toExponential(2)}</b>
        </span>
      </div>
    </Link>
  );
}
