---
LINKEDIN POST — OrbitGuard | FAR AWAY 2026 Hackathon
---

Excited to share what my team built at FAR AWAY 2026 — India's biggest international hackathon.

---

**The problem we picked:**

University cubesat teams and Indian smallsat startups like Pixxel and GalaxEye receive collision warnings from U.S. Space Command every single day.

The warnings arrive in raw cryptic formats — dense technical files that take domain expertise to decode. 99% of them are false alarms. And the commercial tools that interpret them? They cost ₹40 lakh per year. More than most satellites these teams launch.

There was no free, open-source alternative. So we built one.

---

**What we built — OrbitGuard**

A browser-based satellite conjunction assessment system that screens 15,000+ active objects in orbit, computes real collision probabilities using NASA's own algorithms, and gives operators a clear verdict: DODGE, WATCH, or WAIT.

Domain: Space & Aerospace — Satellite Safety / Space Situational Awareness

Core capabilities:
→ 3-stage screening funnel: altitude filter → vectorized SGP4 spatial sieve → Foster 1992 Pc calculation
→ Encounter-plane visualization with miss vector, hard-body radius, and error ellipse
→ LLM-generated plain-English explanations — grounded by a post-generation validator that rejects any claim not backed by raw data
→ Honest limits card: the system tells you when the data is not sufficient to justify a maneuver recommendation

The entire stack runs at ₹0. No paid APIs. No subscriptions.

---

**Datasets we used:**

For live event screening (production):
→ CelesTrak GP catalog (public, updated 2x/day) — 15,697 active satellites in OMM/JSON format
→ Space-Track CDM feeds (free account) — official U.S. conjunction data messages

For validation and benchmarking:
→ TraCSS — Traffic Coordination System for Space, published by the U.S. Office of Space Commerce
→ 20 GB of federal test ephemerides with a known answer key: real conjunction events, exact Times of Closest Approach (TCA), exact miss distances
→ This is the same dataset the U.S. government uses to grade Space Situational Awareness systems

We do not mark our own homework. Every metric we publish is computed against TraCSS.

---

**Metrics:**

→ Recall: what % of real TraCSS conjunction events did OrbitGuard detect
→ Precision: what % of OrbitGuard flags were genuine events
→ TCA error: our predicted time of closest approach vs. the federal answer key (in seconds)
→ Miss-distance error: our predicted separation vs. the federal answer key (in meters)
→ Pc accuracy: our Foster 1992 implementation matches NASA CARA reference results to 1 part in a million

The screening engine carries a mathematical guarantee at Stage 2 — the spatial sieve pad equals worst-case closing speed × half the propagation time step, meaning no real conjunction can escape detection by design. Not a heuristic. A proof.

---

**Tech stack:**
Python · SGP4 · Skyfield · FastAPI · Next.js · CesiumJS · Groq (Llama 3.3 70B) · Qdrant · GitHub Actions CI

---

If you're working on space situational awareness, smallsat operations, or open-source orbital mechanics — I'd love to connect.

Full project and code: github.com/vinayakkoli2005/FAR_AWAY

#SpaceTech #Hackathon #FARAWAY2026 #OpenSource #SatelliteSafety #SpaceSituationalAwareness #ISRO #IndianSpace #MachineLearning #Aerospace #Cubesat
