import type { Funnel } from "@/lib/api";

// The funnel strip communicates more engineering than any paragraph:
// 15,697 objects -> Stage A -> Stage B -> Stage C, with timings.
export default function FunnelStrip({ funnel }: { funnel: Funnel }) {
  return (
    <div className="funnel-strip">
      <span>
        <b>{funnel.catalog_size.toLocaleString()}</b> objects
      </span>
      <span className="arrow">→ gate</span>
      <span>
        <b>{funnel.stage_a_survivors.toLocaleString()}</b>
      </span>
      <span className="arrow">→ sieve</span>
      <span>
        <b>{funnel.stage_b_windows.toLocaleString()}</b> windows
      </span>
      <span className="arrow">→ refine</span>
      <span>
        <b>{funnel.stage_c_events}</b> conjunctions
      </span>
      <span className="t">{funnel.runtime_s.total.toFixed(1)}s</span>
    </div>
  );
}
