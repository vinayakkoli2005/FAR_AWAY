# OrbitGuard — 4-Minute Demo Video Script
# FAR AWAY 2026 Hackathon | Space & Aerospace Track
# ─────────────────────────────────────────────────
# FORMAT: [TIME] PAGE/SCREEN — What you see | What you say
# Total runtime: ~4 minutes 00 seconds
# Record at 4K, dark theme. No background music under voiceover.
# Every word spoken maps to something visible on screen.
# ─────────────────────────────────────────────────

---

## ─── SPEAKER SPLIT ───────────────────────────────
#
#  SPEAKER A  →  0:00 – 1:20  (~80 seconds)
#               Scenes 1, 2, 3 + first half of Scene 4
#               Role: The Storyteller — problem, hook, landing page, Mission Control intro
#
#  SPEAKER B  →  1:20 – 2:35  (~75 seconds)
#               Second half of Scene 4 + full Scene 5
#               Role: The Engineer — funnel deep-dive, algorithm, Encounter Inspector
#
#  SPEAKER C  →  2:35 – 4:00  (~85 seconds)
#               Scenes 6, 7, 8
#               Role: The Validator — scorecard, proof, architecture, closing statement
#
# ─────────────────────────────────────────────────

---

## ════════════════════════════════════════════════
## SPEAKER A  [0:00 – 1:20]
## ════════════════════════════════════════════════

## SCENE 1 — COLD OPEN [0:00 – 0:08]
**Screen:** Black screen. Then slow zoom-in on the spinning 3D globe.
Satellites visible as glowing dots — ISS, DRISHTI, EOS-08, FIREFLY-1 orbiting in real-time.
Dark space background. No UI yet. Just the globe.

**Narration:** *(silence — let the visuals speak)*

---

## SCENE 2 — THE PROBLEM [0:08 – 0:40]
**Screen:** Show a real Conjunction Data Message (CDM) email / raw text file on screen.
Dense, technical, unreadable format. Then overlay three stats on screen:

```
27,000+ pieces of debris orbiting Earth right now
99% of collision warnings are false alarms
Commercial tools to decode them: ₹40 lakh per year
```

**Narration:**
"Imagine you're a university team. You launched your first cubesat — years of work,
months of code, everything you built. Then you get this email."

*(show the CDM raw text)*

"A collision warning. Cryptic format. Dense numbers. 99% of the time it's a false
alarm — but you can't tell. And the tools that decode this cost more than your
satellite. Pixxel, GalaxEye, university teams across India — this is their reality,
every single day."

"We built OrbitGuard. Free, open-source, and built on the same algorithms NASA uses."

---

## SCENE 3 — LANDING PAGE [0:40 – 1:00]
**Screen:** OrbitGuard landing page / home screen.
Show the tagline, the 3D globe preview, and the "Start Screening" button.
Highlight these stats on the page:
- 15,697 satellites tracked
- Built on NASA CARA algorithms
- Validated against U.S. TraCSS federal dataset
- 100% free, zero API cost

**Narration:**
"OrbitGuard is a browser-based satellite conjunction assessment system.
You open it, your assets are on the globe, and within 90 seconds you know
exactly which warnings are real and which you can ignore.

No account. No subscription. No ₹40 lakh bill.
Just open-source software on public data."

---

## SCENE 4 — MISSION CONTROL PAGE (Main Globe) [1:00 – 1:45]
**Screen:** The main Mission Control page.
Full-screen 3D CesiumJS globe with:
- Satellites shown as glowing orbital-path dots
- Color coding: GREEN (safe), AMBER (watch), RED (dodge)
- Top-right: the Funnel Strip showing screening progress

### [SPEAKER A — 1:00 to 1:20]
**Narration:**
"This is Mission Control. Every active satellite on one screen —
15,697 objects, screened in real time."

*(point at the funnel strip on top)*

"Watch this funnel. OrbitGuard uses a three-stage screening system.
Stage one — altitude filter. In milliseconds, 90% of the catalog is eliminated
because their orbits mathematically cannot cross."

---

## ════════════════════════════════════════════════
## SPEAKER B  [1:20 – 2:35]
## ════════════════════════════════════════════════

### [SPEAKER B — 1:20 to 1:45]  ← handoff from Speaker A here
**Narration:**
"Stage two — a spatial sieve with vectorized SGP4 propagation.
This stage has a mathematical guarantee: it cannot miss a real conjunction.
The detection pad equals worst-case closing speed multiplied by half the time step.
No event escapes.

Stage three — exact collision probability using the Foster 1992 algorithm —
the same method NASA's Conjunction Assessment Risk Analysis team uses."

*(watch funnel animate: 15,697 → 834 → 1,967 → 7 events)*

"15,697 satellites. 90 seconds. 7 real events worth your attention.
Every other warning — safely dismissed, with proof."

*(scroll the ranked verdict dock on the right side)*

"Each card shows: the conjunction name, the time to closest approach,
the probability score, and a clear verdict — DODGE, WATCH, or WAIT."

---

### [SPEAKER B continues — 1:45 to 2:35]
## SCENE 5 — ENCOUNTER INSPECTOR PAGE [1:45 – 2:35]
**Screen:** Click on the top card — DRISHTI conjunction event.
Encounter Inspector page opens showing:
- Encounter-plane ellipse plot (hard-body circle + miss vector + error distribution)
- Probability number with confidence level
- Time to Closest Approach (TCA) countdown
- The AI-generated plain-English explanation panel
- "Show Raw Evidence" toggle button

**Narration:**
"Let's open the top event — a conjunction involving GalaxEye's DRISHTI satellite."

*(encounter-plane plot on screen)*

"This is the encounter plane — the operational picture every space agency uses.
The circle in the center is the combined hard-body radius of both objects.
The ellipse is the worst-case error distribution given TLE data accuracy.
The dot is the predicted miss vector."

"The collision probability here is computed using Foster's 1992 closed-form method —
and our implementation matches the exact NASA CARA reference result
to one part in a million."

*(scroll down to the AI explanation panel)*

"This plain-English explanation is generated by an LLM — but here's what makes it
different from every other AI demo you've seen."

*(click 'Show Raw Evidence')*

"Every single number the AI says — the Pc value, the miss distance, the TCA —
is pulled from this evidence record. A post-generation validator runs and
rejects any claim not supported by the underlying data.
The AI cannot hallucinate here. If the data doesn't say it, the AI can't say it."

---

## ════════════════════════════════════════════════
## SPEAKER C  [2:35 – 4:00]
## ════════════════════════════════════════════════

## SCENE 6 — SCORECARD / VALIDATION PAGE [2:35 – 3:15]
**Screen:** Navigate to the Scorecard page.
Show the validation metrics panel:
- Recall % against TraCSS dataset
- Precision %
- TCA error (seconds)
- Miss-distance error (meters)
- Number of events validated
- "Honest Limits" card at the bottom

**Narration:**
"Now here's what separates OrbitGuard from every other hackathon project
in this competition."

*(point at the scorecard metrics)*

"We don't mark our own homework."

"The U.S. Office of Space Commerce publishes TraCSS — 20 gigabytes of federal
test ephemerides with a known answer key. Real conjunction events, exact TCAs,
exact miss distances — a government-grade exam."

"We ran OrbitGuard's engine against it and published every number publicly:
recall, precision, TCA error in seconds, miss-distance error in meters.
If we miss an event — it shows. If we flag a false positive — it shows.
This scorecard ships empty until the validation run completes.
Because we only publish what we can prove."

*(scroll to the Honest Limits card)*

"And we tell you what the system cannot do.
TLE orbital data has 1-kilometre accuracy at best, growing by 1 to 3 km per day.
That means OrbitGuard can prove you are safe — the objects are far enough apart
that even worst-case error cannot create a collision.
But it can never prove you must move. That requires high-fidelity ephemerides
that commercial operators keep private.
We draw that line clearly. Because in space, overconfidence kills."

---

## SCENE 7 — ARCHITECTURE OVERVIEW [3:15 – 3:35]
**Screen:** Architecture diagram on screen (the README diagram or a styled version).
Show the data flow:
CelesTrak (free) → Engine (Python/SGP4) → FastAPI → Next.js → CesiumJS Globe

Briefly show the GitHub repo — green CI badge, test suite, folder structure.
Flash the pytest output: all tests green.

**Narration:**
"Under the hood: Python engine with vectorized SGP4 propagation,
FastAPI backend, Next.js with CesiumJS for the globe.

Every algorithm is tested against published reference vectors.
The SGP4 implementation is cross-checked against Vallado's golden test cases.
The Pc math is cross-checked against NASA CARA's own test suite.

The entire stack — zero paid APIs. Groq's free tier for explanations.
CelesTrak's public data for the catalog.
Runs on your laptop."

*(flash GitHub — green CI badge, test files visible)*

"Open source. MIT licensed. Every line of code is on GitHub."

---

## SCENE 8 — CLOSE [3:35 – 4:00]
**Screen:** Back to the spinning globe. Satellites orbiting peacefully.
Overlay the OrbitGuard logo + tagline.
Then: GitHub URL + team name.

**Narration:**
"There are 2,000 active satellites operated by university teams and small startups
around the world. Every one of them faces the same problem — cryptic warnings,
false alarms, and tools they cannot afford.

OrbitGuard is for them.

Free, open-source, validated against federal data, built on the same math NASA uses.
The operators that commercial space-traffic services price out —
they deserve the same protection as everyone else."

*(globe keeps spinning — satellites keep orbiting)*

"OrbitGuard. Clear skies for everyone."

*(fade to black — show repo URL)*
`github.com/vinayakkoli2005/FAR_AWAY`

---

## ─── FULL TIMELINE + SPEAKER ASSIGNMENT ─────────

| Time        | Speaker    | Scene                        | Key Message                                         |
|-------------|------------|------------------------------|-----------------------------------------------------|
| 0:00–0:08   | SPEAKER A  | Cold open — spinning globe   | Visual hook, no words                               |
| 0:08–0:40   | SPEAKER A  | The Problem                  | CDM email, 99% false alarms, ₹40L tool cost         |
| 0:40–1:00   | SPEAKER A  | Landing Page                 | OrbitGuard intro, free + NASA-grade                 |
| 1:00–1:20   | SPEAKER A  | Mission Control — Stage 1    | Globe intro, altitude filter explanation            |
| 1:20–1:45   | SPEAKER B  | Mission Control — Stages 2&3 | SGP4 sieve, Foster Pc, funnel animation, verdict dock|
| 1:45–2:35   | SPEAKER B  | Encounter Inspector          | Encounter-plane plot, Pc math, validated AI          |
| 2:35–3:15   | SPEAKER C  | Scorecard / Validation       | TraCSS 20GB dataset, honest limits, no self-grading |
| 3:15–3:35   | SPEAKER C  | Architecture + GitHub        | Full free stack, green CI, open source              |
| 3:35–4:00   | SPEAKER C  | Close                        | Who this is for, repo URL, "clear skies for everyone"|

## ─── SPEAKER SUMMARY ────────────────────────────

| Speaker    | Time Slot     | Duration | Role           | Scenes Covered                          |
|------------|---------------|----------|----------------|-----------------------------------------|
| SPEAKER A  | 0:00 – 1:20   | ~80 sec  | The Storyteller| Cold open, Problem, Landing, MC intro   |
| SPEAKER B  | 1:20 – 2:35   | ~75 sec  | The Engineer   | MC deep-dive (algo), Encounter Inspector|
| SPEAKER C  | 2:35 – 4:00   | ~85 sec  | The Validator  | Scorecard, Architecture, Close          |

---

## ─── KEY FACTS TO MEMORISE (NEVER GET THESE WRONG) ──

- **15,697** — number of active satellites screened
- **90 seconds** — time to screen full catalog on a laptop
- **99%** — false-alarm base rate of conjunction warnings
- **3 stages** — altitude filter → KDTree sieve → Foster Pc
- **1 in a million** — our Pc match accuracy vs NASA CARA reference
- **20 GB** — size of TraCSS federal validation dataset
- **1 km** — TLE accuracy at epoch (honest limit)
- **₹40 lakh/year** — what commercial tools cost (LeoLabs, Kayhan)
- **₹0** — what OrbitGuard costs

---

## ─── RECORDING NOTES ──────────────────────────────

- **Setup before recording:** Run offline mode with frozen snapshot. Pre-warm Groq
  explanation cache for top 3 events. Globe already spinning when camera rolls.
- **Pace:** Slow and confident. Don't rush the funnel animation — let viewers see
  the numbers change.
- **Tone:** Not a sales pitch. Sound like an engineer who built something real
  and is showing you exactly how it works.
- **Camera:** Screen recording at 4K. Dark theme. No watermarks.
- **No music under narration.** Ambient space ambience under cold open only.
- **Every stat on screen** must match what you say. Pause on the scorecard.
  Let numbers sit for 2 seconds before moving on.
