"use client";

// First-visit guide + always-available "What am I looking at?" launcher.
// The product's job is triage; the guide's job is to make the screen
// self-explanatory in under a minute.

import { useEffect, useState } from "react";

const STEPS = [
  {
    icon: "🌍",
    title: "1 · The sky right now",
    text: "The globe shows your satellites (cyan, with orbit trails) flying through the full public catalog — every grey dot is a real tracked object, moving on real orbital data. Drag to rotate, scroll to zoom, and use the timeline at the bottom to fast-forward.",
  },
  {
    icon: "🔻",
    title: "2 · The funnel",
    text: "The strip at the top-left is the screening engine at work: from ~16,000 catalog objects, a geometry gate and a mathematically-guaranteed sieve narrow down to the handful of real close approaches — with the compute time shown. Nothing inside 10 km escapes the net.",
  },
  {
    icon: "🚦",
    title: "3 · The verdicts",
    text: "Each card on the right is one close approach, ranked by risk. WAIT (green) = provably safe. WATCH (amber) = monitor; data can't rule risk out yet. DODGE (red) = above NASA's maneuver-consideration threshold. A REQUEST CDM chip means: this needs better data, not a maneuver.",
  },
  {
    icon: "🔍",
    title: "4 · Trust, but verify",
    text: "Click any card to open the Encounter Inspector: the exact geometry, the worst-case probability math, a plain-English explanation — and a button showing the raw evidence JSON, because every number is auditable. The Scorecard page shows how the engine scores against the official U.S. TraCSS answer key.",
  },
];

export default function GuideModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("og-guide-seen")) setOpen(true);
  }, []);

  const close = () => {
    localStorage.setItem("og-guide-seen", "1");
    setOpen(false);
  };

  return (
    <>
      <button className="guide-btn" onClick={() => setOpen(true)}>
        ？ Guide
      </button>
      {open && (
        <div className="modal-backdrop" onClick={close}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>
              🛰 Welcome to OrbitGuard
              <span className="modal-sub">
                free conjunction screening for small satellite operators
              </span>
            </h2>
            <p className="modal-lede">
              Somewhere above you, two objects are heading for a close pass. OrbitGuard finds
              every such event for your satellites over the next 7 days, computes how dangerous
              it really is — with the same math NASA uses — and tells you what to do about it.
            </p>
            <div className="guide-grid">
              {STEPS.map((s) => (
                <div className="guide-step" key={s.title}>
                  <div className="guide-icon">{s.icon}</div>
                  <b>{s.title}</b>
                  <p>{s.text}</p>
                </div>
              ))}
            </div>
            <div className="modal-foot">
              <span className="note">
                Tip: the 📍 button on a card flies the globe to that encounter.
              </span>
              <button className="cta" onClick={close}>
                Explore the sky →
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
