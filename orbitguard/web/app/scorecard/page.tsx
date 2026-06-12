"use client";

// Validation scorecard: we don't mark our own homework. Renders the TraCSS
// metrics JSON when the run is complete; until then, the methodology and an
// honest "pending" state. Screenshot-ready by design.

import { useEffect, useState } from "react";
import { fetchScorecard } from "@/lib/api";

type Scorecard = {
  status?: string;
  recall?: number;
  precision?: number;
  f1?: number;
  events_matched?: number;
  events_key?: number;
  tca_rms_ms?: number;
  miss_rms_m?: number;
  dataset?: string;
  methodology?: string[];
  disclaimer?: string;
  run?: Record<string, unknown>;
};

export default function ScorecardPage() {
  const [sc, setSc] = useState<Scorecard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchScorecard().then(setSc as never).catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="loading">{error}</div>;
  if (!sc) return <div className="loading">loading…</div>;

  const pending = sc.status === "pending";

  return (
    <main className="scorecard">
      <h1 style={{ margin: "18px 0 4px" }}>Validation Scorecard</h1>
      <p className="note">
        OrbitGuard&apos;s screening engine is graded against the official U.S. TraCSS{" "}
        <em>Dataset for Conjunction Assessment Verification</em> — 20.7 GB of federal test
        ephemerides with a published conjunction answer key (CC0).
      </p>

      <div className="tiles">
        <div className="tile">
          <div className="big">{pending ? "—" : `${((sc.recall ?? 0) * 100).toFixed(1)}%`}</div>
          <div className="lbl">RECALL vs ANSWER KEY</div>
        </div>
        <div className="tile">
          <div className="big">{pending ? "—" : `${((sc.precision ?? 0) * 100).toFixed(1)}%`}</div>
          <div className="lbl">PRECISION</div>
        </div>
        <div className="tile">
          <div className="big">{pending ? "—" : sc.tca_rms_ms?.toFixed(0) ?? "—"}</div>
          <div className="lbl">TCA RMS ERROR (ms)</div>
        </div>
        <div className="tile">
          <div className="big">{pending ? "—" : sc.miss_rms_m?.toFixed(1) ?? "—"}</div>
          <div className="lbl">MISS RMS ERROR (m)</div>
        </div>
      </div>

      {pending && (
        <div className="honest">
          <b>Status: pending.</b> The dataset run has not completed yet, so these tiles are
          empty on purpose. We publish what we measure — not what we hope. What is already
          verified in CI today: the screening pipeline reproduces a brute-force 1-second
          ground-truth search (recall and precision) on property-test scenes, the Foster Pc
          implementation matches the exact noncentral-χ² result and an independent adaptive
          double-quadrature referee to better than 1e-6 relative, and propagation matches
          Skyfield to under 5 meters.
        </div>
      )}

      <h3 style={{ margin: "22px 0 8px" }}>Methodology</h3>
      <ol className="note" style={{ paddingLeft: 18 }}>
        {(sc.methodology ?? []).map((m) => (
          <li key={m}>{m}</li>
        ))}
      </ol>

      <div className="honest">
        <b>Honest limits.</b> TLE/GP accuracy is ~1 km at epoch and degrades 1–3 km/day
        (in-track dominant). Without covariance, OrbitGuard reports a worst-case Pc bound:
        it can prove an event is safe under any consistent error model, but it can never
        prove danger — that requires CDM-grade data. Low relative-velocity encounters
        (&lt; 100 m/s) violate the 2D-Pc assumptions and are flagged, not faked.
      </div>

      {sc.disclaimer && (
        <p className="note" style={{ marginTop: 14 }}>
          Dataset disclaimer: “{sc.disclaimer}”
        </p>
      )}
    </main>
  );
}
