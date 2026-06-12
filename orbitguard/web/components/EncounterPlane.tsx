"use client";

// Encounter-plane figure. By construction the projected miss vector is
// (d, 0). TLE-grade events have no covariance: we draw the hard-body circle,
// the miss vector, and the worst-case sigma circle (sigma* = d/sqrt(2), the
// covariance that attains PcMax) — the picture of "prove safety, not danger".

import type { Evidence } from "@/lib/api";

export default function EncounterPlane({ ev }: { ev: Evidence }) {
  const d = ev.miss_distance_km;
  const hbr = ev.probability.hard_body_radius_m / 1000;
  const ellipse = ev.probability.ellipse ?? null;
  const sigmaStar = d / Math.SQRT2;
  const sigmaExtent = ellipse ? ellipse.sigma_major_m / 1000 : sigmaStar;

  // scale: fit miss + error distribution into the view
  const extent = Math.max(d * 1.35, sigmaExtent * 2.2);
  const W = 460;
  const H = 320;
  const s = (W * 0.42) / extent; // km -> px
  const cx = W * 0.38;
  const cy = H * 0.5;
  const missX = cx + d * s;
  const hbrPx = Math.max(hbr * s, 3); // keep visible even at scale

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", background: "#050a14", borderRadius: 8 }}>
        {/* axes */}
        <line x1={8} y1={cy} x2={W - 8} y2={cy} stroke="#1c2c4d" strokeWidth={1} />
        <line x1={cx} y1={10} x2={cx} y2={H - 10} stroke="#1c2c4d" strokeWidth={1} />

        {ellipse ? (
          /* CDM-grade: the actual combined covariance ellipse (1/2/3 sigma) */
          <g transform={`rotate(${-ellipse.theta_deg} ${cx} ${cy})`}>
            {[1, 2, 3].map((k) => (
              <ellipse key={k} cx={cx} cy={cy}
                rx={(ellipse.sigma_major_m / 1000) * k * s}
                ry={(ellipse.sigma_minor_m / 1000) * k * s}
                fill={k === 1 ? "rgba(67,210,255,0.10)" : "none"}
                stroke="#5fb6d9" strokeWidth={k === 1 ? 1.4 : 0.8}
                strokeDasharray={k === 1 ? undefined : "4 5"}
                opacity={1.1 - k * 0.25} />
            ))}
            <text x={cx + (ellipse.sigma_major_m / 1000) * s * 0.7}
              y={cy - (ellipse.sigma_minor_m / 1000) * s * 0.8}
              fill="#5fb6d9" fontSize={10.5} fontFamily="monospace">1σ covariance</text>
          </g>
        ) : (
          /* TLE-grade: worst-case sigma circles (1 and 2 sigma*) */
          <g>
            <circle cx={cx} cy={cy} r={sigmaStar * s} fill="none" stroke="#ffb347"
              strokeWidth={1.2} strokeDasharray="6 5" opacity={0.8} />
            <circle cx={cx} cy={cy} r={2 * sigmaStar * s} fill="none" stroke="#ffb347"
              strokeWidth={0.8} strokeDasharray="3 6" opacity={0.45} />
            <text x={cx + sigmaStar * s * 0.72} y={cy - sigmaStar * s * 0.74} fill="#ffb347"
              fontSize={10.5} fontFamily="monospace">σ* = d/√2</text>
          </g>
        )}

        {/* secondary object at origin */}
        <circle cx={cx} cy={cy} r={4} fill="#ffb347" />
        <text x={cx - 8} y={cy + 18} fill="#ffb347" fontSize={11} fontFamily="monospace"
          textAnchor="end">{ev.object.name}</text>

        {/* miss vector */}
        <line x1={cx} y1={cy} x2={missX} y2={cy} stroke="#43d2ff" strokeWidth={1.6}
          markerEnd="url(#arrow)" />
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"
            markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#43d2ff" />
          </marker>
        </defs>
        <text x={(cx + missX) / 2} y={cy - 8} fill="#43d2ff" fontSize={11}
          fontFamily="monospace" textAnchor="middle">d = {d.toFixed(3)} km</text>

        {/* hard-body circle at the asset position */}
        <circle cx={missX} cy={cy} r={hbrPx} fill="rgba(255,77,77,0.25)"
          stroke="#ff4d4d" strokeWidth={1.5} />
        <circle cx={missX} cy={cy} r={3.4} fill="#43d2ff" />
        <text x={missX + 10} y={cy + 18} fill="#43d2ff" fontSize={11}
          fontFamily="monospace">{ev.asset.name}</text>
        <text x={missX + 10} y={cy + 32} fill="#ff4d4d" fontSize={10.5}
          fontFamily="monospace">HBR {ev.probability.hard_body_radius_m.toFixed(0)} m</text>
      </svg>
      <p className="note" style={{ marginTop: 8 }}>
        Encounter plane (perpendicular to the relative velocity).{" "}
        {ellipse ? (
          <>
            The blue ellipses are the actual combined position-error covariance (1σ/2σ/3σ)
            from CDM-grade data; integrating it over the hard-body disk gives Pc ={" "}
            <b style={{ fontFamily: "var(--mono)" }}>
              {ev.probability.pc?.toExponential(2)}
            </b>{" "}
            (Foster method — cross-checked by Chan series at{" "}
            {ev.probability.chan_crosscheck?.toExponential(2)}).
          </>
        ) : (
          <>
            The dashed circles show the worst-case position-error distribution — the one that
            maximizes collision probability for this geometry. Even then, Pc cannot exceed{" "}
            <b style={{ fontFamily: "var(--mono)" }}>
              {(ev.probability.pc ?? ev.probability.pc_max)?.toExponential(2)}
            </b>
            . TLE-grade data can prove safety, never danger.
          </>
        )}
      </p>
    </div>
  );
}
