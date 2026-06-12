import type { Funnel } from "@/lib/api";

// The funnel strip communicates more engineering than any paragraph —
// and every stage explains itself on hover.
export default function FunnelStrip({ funnel }: { funnel: Funnel }) {
  return (
    <div className="funnel-strip">
      <span
        className="tip"
        data-tip="Every tracked object in the public CelesTrak catalog, refreshed every 2 hours"
      >
        <b>{funnel.catalog_size.toLocaleString()}</b> objects
      </span>
      <span className="arrow">→</span>
      <span
        className="tip"
        data-tip="Stage A: objects whose orbital altitude band can never touch yours are discarded by pure geometry — no propagation needed"
      >
        gate <b>{funnel.stage_a_survivors.toLocaleString()}</b>
      </span>
      <span className="arrow">→</span>
      <span
        className="tip"
        data-tip="Stage B: survivors are propagated on a 30 s grid; the padded search radius mathematically guarantees no real close approach can slip through"
      >
        sieve <b>{funnel.stage_b_windows.toLocaleString()}</b> windows
      </span>
      <span className="arrow">→</span>
      <span
        className="tip"
        data-tip="Stage C: each flagged window is refined to the exact time of closest approach (millisecond precision) and kept only if the miss is inside 10 km"
      >
        refine <b>{funnel.stage_c_events}</b> conjunctions
      </span>
      <span className="t tip" data-tip="Total engine time on this machine — full catalog, 7-day window">
        {funnel.runtime_s.total.toFixed(1)}s
      </span>
    </div>
  );
}
