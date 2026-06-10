# Railway Domain: Top 5 Unsolved Gaps for FAR AWAY 2026 Hackathon

**Theme:** Safer, smarter, more efficient railways. Focus: Indian Railways + global.

Note: Web search was unavailable; synthesis is drawn from public domain knowledge of Indian Railways (CRIS, RDSO, KAVACH), AAR/UIC standards, and recent academic literature through Jan 2026.

---

## GAP 1: Real-time Track Defect Detection on Legacy Locomotives [MOST RELEVANT]

**Specific unsolved problem:** Most Indian Railways tracks are still inspected by track-recording cars that run every 3–6 months, or by gangmen walking with hammers. Hairline rail fractures, fishplate cracks, and ballast degradation between inspections cause derailments (Balasore 2023 root cause was point machine, but ~70% of derailments trace to track defects). Existing track-recording cars cost INR 30+ crore and cover only ~10% of network monthly.

**Why unsolved:**
- Mounting computer-vision sensors on every locomotive requires ruggedized edge compute + LTE/5G coverage that is patchy on rural routes.
- Indian Railways has 68,000+ km track with massive heterogeneity (BG/MG/NG, concrete/wooden sleepers, varying ballast).
- Labelled defect datasets are not openly available; manual annotation is expensive.

**Existing approaches & shortcomings:**
- USFD (Ultrasonic Flaw Detection) handheld trolleys — slow, manual, miss intermittent defects.
- DFC's track-recording cars — capital-heavy, low coverage frequency.
- Foreign solutions (Plasser & Theurer, Sperry) — cost-prohibitive at IR scale.

**Tech stack to crack it:**
- Edge CV on Jetson Nano / Coral TPU mounted on existing locomotive cab.
- Lightweight YOLO/EfficientDet trained on synthetic + scraped defect images (Roboflow Universe has open rail-defect datasets).
- Vibration + accelerometer fusion (MEMS sensors ~INR 500) for ballast health.
- Store-and-forward to cloud over 4G; geofenced alerts to nearest gang.

**Hackathon winnability:** High — prototype with Raspberry Pi + camera on a toy rail track demonstrates the loop. Pitch ROI: replaces INR 30cr car with INR 30k retrofit.

---

## GAP 2: Unreserved/General Compartment Crowd Density Estimation [MOST RELEVANT]

**Specific unsolved problem:** Indian Railways has no real-time visibility into how crowded a general (unreserved) coach is at the next station. Passengers boarding at intermediate stations face dangerous crush loads (multiple stampede deaths at Surat, Mumbai LTT 2024–25). RailMadad receives complaints but no preventive signal exists.

**Why unsolved:**
- No CCTV in most general coaches; retrofitting 70,000+ coaches is capital-intensive.
- WiFi-probe or BLE-based crowd estimation requires opt-in; rural passengers don't have smartphones with BT-on.
- Weight-sensor approach (track-based axle load) gives total weight, not per-coach.

**Existing approaches & shortcomings:**
- CCTV-based counting at platforms only (entry, not in-coach).
- Manual TTE estimates — unreliable, not communicated upstream.

**Tech stack to crack it:**
- Door-mounted ToF (time-of-flight) sensor / passive IR counter per coach (~INR 2,000/unit) counts entry/exit deltas.
- LoRaWAN backhaul to station master at next halt (no cellular dependency).
- Aggregation API exposed to NTES app: "Coach S5 of 12345 train is 180% capacity at Itarsi."
- ML smoothing for sensor drift + RFID seat-occupancy correlation in reserved coaches.

**Hackathon winnability:** High — easy demo with 2 ultrasonic sensors + ESP32 + a Streamlit dashboard.

---

## GAP 3: KAVACH Gap — Interoperability with Non-KAVACH Trains in Shared Corridors [MOST DIFFICULT]

**Specific unsolved problem:** KAVACH (India's ATP system) deployment is at ~1,500 km of 68,000 km. The hard problem: trains equipped with KAVACH (Loco Pilot Assistance) share track with non-KAVACH trains. Current SPAD (Signal Passed at Danger) prevention only works if BOTH trains have onboard units AND track-side RFID. Mixed traffic creates blind spots — a KAVACH train can be hit by a non-KAVACH train running through a red.

**Why unsolved:**
- Retrofitting all 14,000 locomotives is a 10+ year program.
- Cross-vendor interoperability (Medha, HBL, Kernex) has version mismatches; ETCS-L2 harmonization unresolved.
- Track-side infrastructure (RFID tags every 1km, towers every 10km) is a capex bottleneck.

**Existing approaches & shortcomings:**
- KAVACH itself — designed for fully-equipped corridors.
- European ETCS Level 2 — assumes GSM-R coverage; India lacks dedicated spectrum.
- ATP/ATC retrofits cost INR 50L+ per loco.

**Tech stack to crack it:**
- V2V (vehicle-to-vehicle) train comms over LoRa-mesh or 5G sidelink (3GPP Rel-17 NR-V2X) — broadcast position/speed independent of trackside infra.
- Onboard GNSS + IMU + open-source EKF fusion for ±2m accuracy without RFID.
- Federated learning across locomotives to learn braking curves per gradient.
- Open spec: define a lightweight "KAVACH-Lite" beacon protocol any retrofit can speak.

**Hackathon winnability:** Difficult but transformative. Demo with 2 RC trains + LoRa modules showing collision avoidance is impressive. Likely "Most Difficult" award track.

---

## GAP 4: Predictive Maintenance for Point Machines & Track Circuits [MOST DIFFICULT]

**Specific unsolved problem:** Point machine failures (the device that switches tracks) caused Balasore 2023 (288 dead). Track circuit malfunctions cause ~40% of signaling failures. There is no predictive maintenance — only reactive (after failure) or scheduled (every X months regardless of usage). Sensor data is collected by RRI/EI systems but locked in vendor silos (Siemens, Alstom, Kyosan).

**Why unsolved:**
- Failure data is rare (good — but means small ML training sets).
- Vendor lock-in: Siemens Westrace logs are proprietary; data egress blocked.
- Safety-Critical SIL-4 certification required for any system that influences signaling — hackathon prototypes can't ship to prod.

**Existing approaches & shortcomings:**
- Vendor-supplied "asset health" dashboards — surface only basic alarms.
- IRISET research on motor-current signature analysis — academic, not deployed.
- Anomaly detection literature (PHM Society) — generic, not point-machine specific.

**Tech stack to crack it:**
- Non-invasive current clamp (CT sensor) on point-machine motor — reads current waveform without touching the SIL-4 path.
- LSTM autoencoder for unsupervised anomaly detection on current signature (well-studied — see IEEE Trans. on Intelligent Transportation Systems 2023–24 papers).
- Digital twin in ROS2/Gazebo simulating wear patterns.
- Edge inference + MQTT to S&T section dashboard.
- Acoustic emission sensors as a second modality.

**Hackathon winnability:** Difficult — requires domain access to a point machine for realistic demo. But synthetic data + a servo motor mock-up is feasible. High research depth = "Most Difficult" award.

---

## GAP 5: Last-Mile Wayfinding for Visually-Impaired & First-Time Passengers [MOST RELEVANT]

**Specific unsolved problem:** Indian Railways stations (especially A1/A category like New Delhi, Howrah) have 16+ platforms, complex foot-over-bridges, signage in 2–3 languages. Visually-impaired passengers and first-time travelers (esp. rural-to-urban migrants) cannot reliably find their coach position before the train departs (coach position changes per rake; only announced 20 min before arrival).

**Why unsolved:**
- Indoor GPS doesn't work; BLE beacon deployment is patchy.
- Coach Position Indicator (CPI) displays exist but are visual-only.
- IRCTC app shows train running status but NOT coach-board-position relative to user's current platform location.

**Existing approaches & shortcomings:**
- Static CPI signage — outdated, language-limited, useless to VI users.
- "Rail Madad" — reactive, post-incident.
- Google Maps indoor — only ~5 IR stations mapped.

**Tech stack to crack it:**
- Crowdsourced BLE beacons (Eddystone/iBeacon) — INR 200/unit, stuck to pillars.
- AR + audio nav via smartphone (ARCore + TalkBack) — "walk 30m forward, your S5 coach will stop here."
- Coach-position API from NTES/COA (Coach Composition) feed.
- Multilingual TTS (Hindi/Tamil/Bengali) via Bhashini.
- Computer vision OCR on coach numbers as a fallback (camera reads "S5" sticker).

**Hackathon winnability:** High — clean UX demo + accessibility angle (UN SDG 10) + Bhashini integration scores well on Indian-context judging.

---

## Synthesis & Recommendation

| Gap | Difficulty | Impact | Hackathon Fit |
|-----|-----------|--------|---------------|
| 1. Track defect detection | Medium | Very High | RELEVANT — strong demo |
| 2. Crowd density | Low | High | RELEVANT — easy MVP |
| 3. KAVACH interop | Very High | Transformative | DIFFICULT — research-heavy |
| 4. Predictive maintenance | High | Very High | DIFFICULT — domain access needed |
| 5. Wayfinding | Medium | High | RELEVANT — accessibility hook |

**Recommendation for a balanced team:** Pick Gap 2 or Gap 5 if optimizing to win. Pick Gap 3 or Gap 4 if optimizing for "Most Innovative" / research-grade impact. Gap 1 sits in the sweet spot — moderately difficult, very demoable, massive ROI narrative.

**Cross-cutting tech themes:**
- Edge AI on cheap hardware (Jetson, ESP32, Coral)
- LoRaWAN/5G-sidelink for connectivity-sparse routes
- Open data layers on top of vendor-locked subsystems
- Bhashini for multilingual accessibility (India-specific differentiator)
