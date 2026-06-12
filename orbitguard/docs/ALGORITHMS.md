# OrbitGuard — the algorithms

The math implemented in `engine/`, with the reasoning behind each choice and full references.
This mirrors plan Section 5; everything here is unit-tested (see `tests/`).

## 1. Propagation, time, and frames

GP elements (TLE/OMM) are **mean elements fitted to the SGP4 theory**. Propagating them with any
other propagator (numerical Cowell, Orekit high-fidelity) silently de-calibrates them — a
correctness error many globe demos make. OrbitGuard propagates GP data with `python-sgp4`'s
vectorized `SatrecArray` (C++ core) and nothing else.

SGP4 outputs are in **TEME** (True Equator, Mean Equinox of date). Relative geometry between two
objects at the same instant is frame-invariant under a common rotation, so screening runs in TEME
directly. Display conversions (TEME → GCRS → ITRF) route through a single audited module,
`engine/astro/frames.py`, backed by Skyfield's timescale (UT1/TT, leap seconds). CI cross-checks
our TEME→GCRS chain against Skyfield's independent implementation to < 5 m.

Accuracy model (from the TLE-accuracy literature): ~1 km at epoch, growing 1–3 km/day, in-track
dominant. This bounds what TLE-only screening can claim and motivates the worst-case-bound risk
policy (§4).

## 2. Screening: the three-stage sieve

**Problem.** k assets vs N ≈ 15,000–30,000 catalog objects over a 7-day window with screening
distance D (default 10 km LEO): find every pair approach closer than D.

### Stage A — apogee/perigee gate (Hoots Filter I)

Discard any pair whose altitude bands cannot intersect within pad:

```
reject if  max(q_i, q_j) − min(Q_i, Q_j) > D + margin        (q, Q = perigee/apogee radius)
```

`margin` (default 25 km) absorbs drag/J2 evolution of the bands over the window. O(N) per asset.

### Stage B — padded coarse-grid sieve

Propagate survivors on a coarse grid (Δt = 30 s) and keep any pair whose separation at any grid
time is below the **padded radius**

```
R_pair = D + v_rel,max·Δt/2,   v_rel,max = 15.6 km/s (head-on LEO worst case)
```

**The guarantee.** If a conjunction with miss < D occurs at t\*, the nearest grid point is within
Δt/2 of t\*, and two objects can separate by at most v_rel,max·Δt/2 in that interval. Hence the
grid-time separation is < D + v_rel,max·Δt/2 = R_pair: no true conjunction escapes the net. This
is the "smart sieve" logic of Alarcón-Rodríguez, Martínez-Fadrique & Klinkrad (ESA, 2002).

Implementation: time-chunked vectorized propagation (2 h blocks); for small k, direct broadcast
distance checks beat per-step KD-trees (the tree build is O(N log N) per step and only pays off
for all-vs-all, which is a stretch goal). The classical Hoots Filters II/III (orbit-path/time)
were rejected: they assume near-Keplerian geometry and need fragile edge-case handling for
perturbed or near-co-planar orbits; brute-force-with-a-proof is simpler to verify and fast enough
at k·N scale.

### Stage C — TCA refinement

Within each flagged window, range minima are roots of

```
g(t) = d/dt |Δr(t)|² = 2 Δr(t)·Δv(t)
```

with a − → + sign change. Bracket at 1 s, polish with Brent (`xtol` ≈ 1 ms), deduplicate within
60 s. Output: TCA, miss distance, v_rel, and the miss vector decomposed in the asset's RIC frame.

**Verification.** A property test runs the full pipeline against a brute-force 1-second search
over every pair on synthetic scenes (planted nodal conjunctions, near-misses, GEO/Molniya
decoys) and asserts both recall and precision.

## 3. Collision probability

### Short-encounter 2D collapse

At LEO conjunction speeds (km/s) the encounter is effectively instantaneous: relative motion is
linear, position errors Gaussian and velocity errors negligible. The 3D problem collapses to the
**encounter plane** ⊥ Δv. With combined covariance C = C₁+C₂ projected to 2×2 C_p and projected
miss m (by construction m = (d, 0)):

```
Pc = (2π)⁻¹ |C_p|^(−1/2) ∬_{|x|≤R} exp(−(x−m)ᵀ C_p⁻¹ (x−m)/2) dA
```

R is the combined hard-body radius.

### Foster (1992) — the reference

NASA CARA's operational method. In the principal frame of C_p the inner integral over one axis is
analytic (error functions), leaving a robust 1D adaptive quadrature (`engine/risk/pc_foster.py`).
Valid across the operational range Pc 1e-1…1e-7.

**Verification.** (a) The isotropic case has a closed form — the offset-Gaussian disk integral is
the noncentral-χ² CDF, `Pc = ncx2.cdf((R/σ)², df=2, nc=(d/σ)²)` — matched to 1e-6 relative.
(b) An independent `scipy.dblquad` 2D adaptive referee — matched to machine precision on random
anisotropic cases. (c) 2M-sample Monte Carlo within sampling error.

### Chan (1997) — the cross-check

Equivalent-area Rician series with u = R²/(σₓσᵧ), v = mₓ²/σₓ² + mᵧ²/σᵧ²:

```
Pc = e^{−v/2} Σ_m (v^m / 2^m m!) [1 − e^{−u/2} Σ_{k≤m} u^k / 2^k k!]
```

Exact when σₓ = σᵧ (verified to 1e-9); for anisotropic covariance it is an approximation —
~2% in the operational band, degrading to tens of percent beyond 5σ misses (we measured 27% at
Pc ≈ 1.4e-7 against the dblquad referee; consistent with published comparisons). Its job is the
**disagreement alarm**: a frame/geometry bug moves Pc by orders of magnitude, not percent.

### PcMax — when there is no covariance

GP data carries no covariance and we refuse to invent one. Over all isotropic covariances
consistent with miss distance d (R ≪ d):

```
Pc(σ) ≈ (R²/2σ²)·exp(−d²/2σ²);   maximized at σ² = d²/2   ⇒   PcMax = R²/(e·d²)
```

CI sweeps σ over four decades and confirms the exact (ncx2) Pc never exceeds the bound and
attains it at σ = d/√2. **The asymmetry that defines the product:** an upper bound can *clear*
an event (PcMax < threshold ⇒ safe under any consistent covariance) but can never *convict* one.
TLE data can prove safety, never danger.

### Known limits

v_rel < 100 m/s (GEO neighbors, formation flying) violates the short-encounter assumptions and
needs 3D/nonlinear Pc (Coppola). OrbitGuard detects this and labels the event "2D-Pc not
applicable" rather than printing a wrong number.

## 4. Risk policy

Thresholds per the NASA CA Handbook (maneuver consideration at Pc ≥ 1e-4; monitoring floor 1e-6):

| Grade | Condition | Verdict |
|---|---|---|
| CDM | Pc ≥ 1e-4 | DODGE |
| CDM | 1e-6 ≤ Pc < 1e-4 | WATCH |
| CDM | Pc < 1e-6 | WAIT |
| TLE | PcMax < 1e-6 | WAIT (provable clearance) |
| TLE | PcMax ≥ 1e-4 ∧ d < 5 km | WATCH + **ESCALATE: request CDM** |
| TLE | otherwise | WATCH |
| any | v_rel < 100 m/s | WATCH + 2D-Pc-invalid flag |

## 5. Grounded explanation layer

Input: the final JSON evidence record. Contract: 4–6 sentences, **no number that is not in the
record** (rounding and km↔m conversion allowed). Enforcement: a digit-level post-validator
(`engine/explain/validator.py`) rejects violations and falls back to a deterministic template
renderer that produces the same structure. Cache keyed by (pair, TCA-minute, verdict, grade).

## References

1. Foster, J. & Estes, H. — *A parametric analysis of orbital debris collision probability and maneuver rate for space vehicles.* NASA JSC-25898 (1992).
2. Chan, K. — *Spacecraft Collision Probability.* Aerospace Press (2008); original series method 1997.
3. Hejduk, M. et al. — *Satellite Conjunction Assessment Risk Analysis for "Dilution Region" Events.* / *2D-Pc Implementation Recommendations and Usage.* NASA NTRS 20190028900.
4. Alfano, S. — *A numerical implementation of spherical object collision probability.* J. Astronaut. Sci. 53(1), 2005.
5. Alarcón-Rodríguez, J.R., Martínez-Fadrique, F., Klinkrad, H. — *Collision risk assessment with a "smart sieve" method.* ESA SP-486 (2002).
6. Hoots, F., Crawford, L., Roehrich, R. — *An analytic method to determine future close approaches between satellites.* Celestial Mechanics 33 (1984).
7. Vallado, D., Crawford, P., Hujsak, R., Kelso, T.S. — *Revisiting Spacetrack Report #3.* AIAA 2006-6753 (SGP4 reference, TEME).
8. NASA — *Spacecraft Conjunction Assessment and Collision Avoidance Best Practices Handbook v2* (2023). NTRS 20230002470.
9. Office of Space Commerce — *Dataset for Conjunction Assessment Verification* (TraCSS, CC0).
10. Kelso, T.S. — CelesTrak GP data formats (OMM; catalog-number exhaustion at 69999, ~2026-07-12).
11. Frisbee, J. — *An upper bound on high speed satellite collision probability when only one object has position uncertainty information.* (max-Pc lineage); Alfano 2014.
12. NASA CARA Analysis Tools — github.com/nasa/CARA_Analysis_Tools (the open reference SDKs this project's methods follow).
