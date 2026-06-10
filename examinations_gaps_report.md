# Top 5 Unsolved Gaps in Examinations — FAR AWAY 2026

Theme: Secure, fair, and intelligent examination solutions. Focus: Indian high-stakes exams (NEET, JEE, UPSC, university) with global relevance.

---

## GAP 1 — Pre-Exam Question Paper Leak Provenance Tracing [MOST RELEVANT]

**Specific unsolved problem:** When a paper leaks (NEET-UG 2024, multiple SSC/UPSC pre-leaks), authorities cannot trace WHICH printing press, custodian, or distribution node leaked it. Post-mortem forensics takes months; by then the exam is compromised.

**Why unsolved:**
- Papers are printed identically across centers — no per-custodian fingerprint.
- Chain-of-custody is paper-based, not cryptographically auditable.
- Existing "watermarking" is visual and easily photographed around.

**Existing approaches & shortfalls:**
- CCTV in printing presses (reactive, not preventive).
- Encrypted PDFs at exam centers (TCS iON model) — works for CBT but 70% of high-stakes Indian exams are still pen-paper.
- Microdot watermarks — defeat-able by retyping.

**Tech stack to crack it:**
- **Steganographic per-copy fingerprinting**: each printed paper gets imperceptible variations (kerning, glyph micro-shifts, invisible Unicode) encoding custodian-ID + timestamp.
- **Blockchain chain-of-custody** (Hyperledger Fabric) for each batch hand-off.
- **OCR + diffing pipeline** that, given a leaked photo, reconstructs the fingerprint within minutes.
- Stack: Python (OpenCV, Tesseract, PyMuPDF), Hyperledger, React dashboard.

---

## GAP 2 — Live, Bias-Audited AI Proctoring for Low-Bandwidth & Diverse Students [MOST RELEVANT]

**Specific unsolved problem:** Current AI proctors (ProctorU, Mercer-Mettl, AIProctor) misflag students with darker skin tones, hijabs, disabilities, tics, or in noisy rural environments at 2–4x the rate of the baseline group. They also need 5+ Mbps stable upload — failing rural India.

**Why unsolved:**
- Training datasets skew Western, well-lit, broadband.
- Vendors optimize for false-negatives (catching cheaters), not false-positive equity.
- No public fairness audit standard exists for proctoring.

**Existing approaches & shortfalls:**
- Honorlock/Proctorio — black-box, sued in US for ADA violations.
- Manual review — doesn't scale to NEET's 24 lakh candidates.

**Tech stack to crack it:**
- **Edge-first proctoring**: on-device TFLite gaze/pose models, only flagged 10s clips uploaded — works on 2G.
- **Fairness layer**: demographic-stratified threshold calibration; per-cohort FPR reporting dashboard.
- **Multimodal fusion**: gaze + audio anomaly + keystroke cadence, with explainable AI (SHAP) so flags are appealable.
- Stack: MediaPipe, TensorFlow Lite, FastAPI, React, Fairlearn library.

---

## GAP 3 — Authentic Assessment in the GenAI Era [MOST DIFFICULT]

**Specific unsolved problem:** Take-home assignments, online MCQs, and essays are now trivially solvable by GPT-5/Claude. Universities globally cannot reliably distinguish AI-written from student-written work — GPTZero and Turnitin AI-detector have ~30% false-positive and ~40% false-negative rates. The very definition of "individual assessment" is collapsing.

**Why unsolved:**
- LLM outputs converge with human writing at sufficient prompting.
- Watermarking from model side (Google SynthID) requires vendor cooperation that students bypass via open models.
- Stylometry breaks when students lightly paraphrase.

**Existing approaches & shortfalls:**
- AI-detectors — unreliable and bias against non-native English speakers.
- Lockdown browsers — break for essays/coding.
- Oral viva — doesn't scale.

**Tech stack to crack it:**
- **Process-based assessment**: capture keystroke dynamics, revision history, pause patterns, draft evolution — assess the *process*, not just the artifact.
- **Personalized baseline modeling**: each student has a writing-fingerprint trained on supervised in-class work; deviation triggers oral follow-up.
- **AI-collaborative rubrics**: redesign assessment so AI use is allowed but the student must defend, critique, and extend AI output via in-person micro-vivas auto-generated from their submission.
- Stack: VS Code/Google Docs extensions for telemetry, Transformer-based stylometry (BERT embeddings), LangChain for auto-viva-question generation.

---

## GAP 4 — Truly Accessible Examination Platform for Disabled Candidates [MOST RELEVANT]

**Specific unsolved problem:** Indian competitive exams provide a "scribe" for visually-impaired/dyslexic/motor-disabled candidates. Scribes are often unqualified, introduce error, leak content, or refuse to come. JEE/NEET still don't have a compliant screen-reader CBT interface for STEM diagrams, chemistry equations, or graphs.

**Why unsolved:**
- MathML/LaTeX → screen reader is solved for blind users in theory, but Indian exam software uses image-based equations.
- No Indian-language TTS exists at exam-grade quality for STEM vocabulary.
- Dyslexic students need font/spacing controls disallowed by lockdown browsers.

**Existing approaches & shortfalls:**
- Human scribe — error-prone, slow, unfair allocation.
- JAWS/NVDA — doesn't read image equations; no Hindi STEM voice.

**Tech stack to crack it:**
- **AI scribe**: speech-to-text (Whisper fine-tuned on Indian English + Hindi) + on-screen handwriting equation recognizer (MathPix-style) + TTS readback for confirmation.
- **Adaptive UI layer**: OpenDyslexic font, color overlays, extra time auto-granted, all within a lockdown environment.
- **MathML rendering** with semantic screen-reader hooks (MathJax + ARIA).
- Stack: Whisper, MathJax, Coqui TTS for Indic, Electron lockdown shell.

---

## GAP 5 — Verifiable Adaptive Testing at National Scale [MOST DIFFICULT]

**Specific unsolved problem:** Computerized Adaptive Testing (CAT — like GRE/GMAT) gives each candidate a different question sequence, improving measurement precision. But for NEET/JEE scale (24L+ candidates), it's never been deployed because: (a) item-pool exposure risk, (b) no way to *prove* to a candidate post-hoc that their adaptive sequence was fair and not algorithmically biased against them, (c) legal challenges in India demand identical-paper "fairness."

**Why unsolved:**
- IRT (Item Response Theory) calibration needs massive pre-test data — politically risky to "pilot" on real students.
- Adaptive algorithms are opaque; courts have ruled non-identical papers as discriminatory in Indian context.
- Item pool of 50,000+ calibrated questions doesn't exist publicly for Indian syllabi.

**Existing approaches & shortfalls:**
- ETS/Pearson — proprietary, closed item pools, not auditable.
- Fixed-form CBT (current NTA model) — wastes measurement on already-known ability levels.

**Tech stack to crack it:**
- **Zero-knowledge proofs of fair adaptation**: candidate gets a cryptographic receipt proving their sequence was drawn from an equally-difficult equivalent set (ZK-SNARK over IRT parameters).
- **Federated item calibration**: coaching institutes contribute anonymized response data to build the item pool without exposing questions.
- **Explainable CAT**: post-exam, each candidate sees the difficulty curve they navigated vs. the cohort.
- Stack: pyirt / mirt (R), Circom/snarkjs for ZKP, PostgreSQL, Next.js candidate portal.

---

## Summary Matrix

| # | Gap | Rating | Hackathon Winnability |
|---|-----|--------|-----------------------|
| 1 | Paper-leak provenance | MOST RELEVANT | High — demoable with steganography + blockchain MVP |
| 2 | Fair low-bandwidth proctoring | MOST RELEVANT | High — edge AI on phone, visible fairness dashboard |
| 3 | Post-GenAI authentic assessment | MOST DIFFICULT | Medium — process telemetry MVP feasible, full solution research-grade |
| 4 | Accessible CBT for disabled | MOST RELEVANT | High — strong social-impact narrative, modular components exist |
| 5 | Verifiable adaptive testing | MOST DIFFICULT | Low-Medium — ZKP+IRT is cutting-edge but transformative |

**Recommendation for hackathon:** Gap 1 (paper-leak provenance) or Gap 4 (accessible CBT) offer the strongest combination of demoability, social impact, and judging-panel resonance for an Indian audience. Gap 3 wins if the team has ML depth and wants the "transformative" narrative.
