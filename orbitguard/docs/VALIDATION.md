# Validation methodology

OrbitGuard's credibility engine: accuracy is measured against external references, in two rings.

## Ring 1 — continuous (runs in CI on every commit)

| Property | Referee | Status |
|---|---|---|
| Sieve completeness (recall) & soundness (precision) | Brute-force 1 s search over all pairs on synthetic scenes with planted conjunctions, near-misses, GEO/Molniya decoys | ✅ green |
| Foster 2D-Pc correctness | Closed-form noncentral-χ² (isotropic); independent `scipy.dblquad` adaptive 2D integration (anisotropic); 2M-sample Monte Carlo | ✅ green |
| Chan series | Exact-isotropic identity (1e-9); bounded anisotropic drift vs Foster | ✅ green |
| PcMax bound theorem | σ-sweep over 4 decades: exact Pc ≤ R²/(e·d²), attained at σ = d/√2 | ✅ green |
| Propagation & frames | Skyfield independent TEME→GCRS chain, < 5 m | ✅ green |
| TCA refinement | Closed-form linear-motion scenes (exact TCA/miss) through the ephemeris harness | ✅ green |
| Harness scoring | Synthetic answer-key matching incl. duplicate and false-positive handling | ✅ green |

Run it: `.venv/bin/pytest` (43 tests).

## Ring 2 — the federal exam (TraCSS), status: PENDING

**Dataset.** Office of Space Commerce, *Dataset for Conjunction Assessment Verification*:
`AerospaceIVVDataset_20251009a.tar.gz` (20.73 GB ephemerides), spherical answer key
(`IVV_Releasable_Dataset_Spherical_DefaultHBR.csv.gz`), SFSH rectangular key, screening-volume
mapping, User's Guide. CC0. Access via Google Form (immediate path).

**Protocol.**

1. Convert ephemerides → Parquet (one-time, chunked).
2. Run **Stage B + C directly on the provided ephemerides** — no SGP4 in the loop. The answer key
   tests *screening*, not propagation; this decouples the two error sources and makes the claim
   stronger. Interpolation: sliding 6-point Lagrange on position, analytic derivative for
   velocity (`engine/validation/interpolate.py`), confirmed against the User's Guide before the
   full run.
3. **Primary run:** spherical volumes / DefaultHBR key. Match on (unordered pair, |ΔTCA| ≤ τ)
   with τ from the User's Guide (default ±5 s); each key row claimable once, duplicates count
   against precision (`engine/validation/matching.py`).
4. **Metrics published:** recall, precision, F1; TCA error distribution (RMS, p95);
   miss-distance error distribution; breakdowns by altitude regime and eccentricity; runtime and
   funnel-reduction statistics on disclosed hardware.
5. **Subset-first discipline:** day-1 uses a 1-day time slice to debug matching; the full run
   follows. Missed-event autopsies go in an appendix.
6. Output lands in `data/scorecard.json`, which `/scorecard` serves and the web scorecard
   renders, with run configuration, dataset citation, and git SHA.

**Targets** (commitments to publish, not to a number): recall ≥ 0.98, precision ≥ 0.95 on the
spherical run. Whatever we measure is what we ship.

**Stretch:** SFSH rectangular volumes / DiscreteHBR key (per-object RIC-frame box tests).

**Cross-check oracle (live mode):** weekly diff of our CelesTrak-driven screening list against
SOCRATES Plus for overlapping pairs; differences investigated, not hidden.

**Disclaimer carried verbatim in-app:** the dataset is for algorithm testing, not operational
certification (per the Office of Space Commerce).
