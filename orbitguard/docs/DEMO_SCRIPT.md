# Demo script (3 minutes) & video shot list

**Setup before going on stage:** API + web running locally against the cached snapshot
(offline mode — the network is not in the demo's critical path). Browser at Mission Control,
globe already spinning. `--explain` cache pre-warmed for the top events.

## Live demo

1. **Hook (20 s).** "A university cubesat team gets a collision warning email. Cryptic format,
   99% false-alarm base rate, and the tools that decode it cost more than their satellite.
   Here's what they should have instead." — gesture at the globe: ISS, Pixxel FIREFLY-1,
   GalaxEye DRISHTI, ISRO EOS-08 moving on live public data.
2. **Screen (40 s).** Point at the funnel strip: "15,697 objects screened down to N real
   conjunctions in about 90 seconds, on this laptop — and the middle stage is mathematically
   guaranteed not to miss anything: the pad equals the worst closing speed times half the grid
   step." Scroll the ranked dock: verdict colors, countdowns, escalation chips.
3. **Inspect (60 s).** Open the top DRISHTI event. Encounter-plane plot: "This is the actual
   operational picture — hard-body circle, miss vector, and the worst-case error distribution.
   The probability method is the same one NASA CARA runs, and our implementation matches the
   exact closed-form result to one part in a million." Read the explanation aloud; click
   "show raw evidence" — "every number the AI says is in this record; a validator rejects
   anything else."
4. **Trust (40 s).** Scorecard page: "We don't mark our own homework. The screening engine is
   built to be graded against the official U.S. TraCSS answer key — 20 GB of federal test
   ephemerides — and the scorecard ships empty until the run completes, because we publish what
   we measure. And when the data can't justify a number, we say so: TLE data can prove you're
   safe; it can never prove you must move."
5. **Close (20 s).** "Free, open source, built on public data — for the university cubesats and
   Indian smallsat startups that commercial space-traffic services price out."

## Video (2–3 min) shot list

| t | Shot |
|---|---|
| 0:00–0:05 | Cold open: globe zoom-in, dark theme, no narration |
| 0:05–0:15 | Problem stat over a real CDM screenshot ("99% of warnings are false alarms") |
| 0:15–0:30 | Funnel strip animating during a live screen run (screen capture) |
| 0:30–1:00 | Mission Control: dock cards, countdowns, DRISHTI events |
| 1:00–1:30 | Encounter Inspector: plane plot, evidence card, raw-JSON toggle, explanation |
| 1:30–1:50 | Scorecard + honest-limits card ("prove safety, never danger") |
| 1:50–2:05 | Architecture diagram pan (README ASCII or styled redraw) |
| 2:05–2:20 | Test suite green run (`pytest` output) + property-test docstring close-up |
| 2:20–2:30 | Team + repo URL + "free for the operators SSA leaves behind" |

Record at 4K, dark theme, no music under voiceover segments. Every claim in the voiceover maps
to something on screen.
