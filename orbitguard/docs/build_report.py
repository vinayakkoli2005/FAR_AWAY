# -*- coding: utf-8 -*-
"""OrbitGuard — project report PDF for FAR AWAY 2026 round-1 submission.

Reads data/scorecard.json so the validation numbers in the PDF are always the
measured ones. Run:  .venv/bin/python docs/build_report.py
"""

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = str(ROOT / "FAR_AWAY_2026_OrbitGuard_Report.pdf")
W, H = A4
FW = W - 3.2 * cm

NAVY = colors.HexColor("#1B2A4A")
NAVY2 = colors.HexColor("#28304A")
CHERRY = colors.HexColor("#E14B5A")
GREEN = colors.HexColor("#1E8E5A")
GREENL = colors.HexColor("#E5F3EC")
RED = colors.HexColor("#C24536")
REDL = colors.HexColor("#FBECEA")
AMBER = colors.HexColor("#C8862B")
AMBERL = colors.HexColor("#FBF1DD")
GOLDL = colors.HexColor("#FBF3E2")
GREY = colors.HexColor("#6B7280")
GRIDE = colors.HexColor("#E3E6EA")
PANEL = colors.HexColor("#F4F6F9")
CYAN = colors.HexColor("#0E7490")

ss = getSampleStyleSheet()
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica",
                      fontSize=9.3, leading=13.0, textColor=NAVY2)
small = ParagraphStyle("small", parent=body, fontSize=7.9, textColor=GREY, leading=10.4)
mono = ParagraphStyle("mono", parent=body, fontName="Courier", fontSize=8.2, leading=11.2)
h1 = ParagraphStyle("h1", parent=body, fontName="Helvetica-Bold", fontSize=15,
                    textColor=NAVY, leading=18)
title_st = ParagraphStyle("t", parent=body, fontName="Helvetica-Bold", fontSize=27,
                          textColor=NAVY, leading=32, alignment=TA_CENTER)
sub_st = ParagraphStyle("s", parent=body, fontSize=11.5, textColor=NAVY2,
                        leading=15.5, alignment=TA_CENTER)


def P(t, st=body):
    return Paragraph(t, st)


def heading(txt):
    t = Table([[Paragraph(f'<font color="white"><b>{txt}</b></font>',
                          ParagraphStyle("hh", parent=body, fontSize=10.5,
                                         textColor=colors.white))]], colWidths=[FW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def qbox(title, txt, accent=CHERRY, bg=GOLDL):
    t = Table([[Paragraph(f'<font color="{accent.hexval()}"><b>{title}</b></font><br/>{txt}',
                          body)]], colWidths=[FW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 4, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def bullets(items, col=NAVY2):
    return Paragraph("<br/>".join(
        f'<font color="{CHERRY.hexval()}">&#8226;</font>&#160;{x}' for x in items), body)


def panel(txt, st=body, bg=PANEL):
    t = Table([[Paragraph(txt, st)]], colWidths=[FW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def grid_table(header, rows, widths, header_bg=NAVY):
    data = [[P(f"<b><font color='white'>{h}</font></b>", small) for h in header]]
    data += [[P(c, small) if isinstance(c, str) else c for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIDE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL])]))
    return t


def metric_tiles(metrics):
    cells, labels = [], []
    for value, label in metrics:
        cells.append(P(f"<b><font size='15' color='{CYAN.hexval()}'>{value}</font></b>",
                       ParagraphStyle("mv", parent=body, alignment=TA_CENTER)))
        labels.append(P(f"<font size='6.6' color='{GREY.hexval()}'>{label}</font>",
                        ParagraphStyle("ml", parent=small, alignment=TA_CENTER)))
    t = Table([cells, labels], colWidths=[FW / len(metrics)] * len(metrics))
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, GRIDE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRIDE),
        ("LINEBELOW", (0, 0), (-1, 0), 0, colors.white),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white)]))
    return t


def shot(path, width):
    img = Image(str(path))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width
    img.drawHeight = width * ratio
    return img


# ---------------------------------------------------------------- scorecard
sc_path = ROOT / "data" / "scorecard.json"
sc = json.loads(sc_path.read_text()) if sc_path.exists() else {}
recall = sc.get("recall")
precision = sc.get("precision")
rec_str = f"{recall*100:.2f}%" if recall is not None else "pending"
prec_str = f"{precision*100:.2f}%" if precision is not None else "pending"
tca_rms = f'{sc.get("tca_rms_ms", "—")} ms' if sc else "pending"
miss_rms = f'{sc.get("miss_rms_m", "—")} m' if sc else "pending"
n_key = f'{sc.get("events_key", 913330):,}'
n_eph = f'{sc.get("n_ephemerides", "~24,000"):,}' if isinstance(
    sc.get("n_ephemerides"), int) else "~24,000"

story = []

# ---------------------------------------------------------------- cover
story += [
    Spacer(1, 2.2 * cm),
    P("🛰", ParagraphStyle("e", parent=title_st, fontSize=34)),
    Spacer(1, 0.3 * cm),
    P("ORBITGUARD", title_st),
    Spacer(1, 0.35 * cm),
    P("Free, explainable, <b>validated</b> satellite conjunction screening<br/>"
      "for the operators commercial space-traffic services price out", sub_st),
    Spacer(1, 1.0 * cm),
    metric_tiles([
        (rec_str, f"RECALL vs {n_key}-EVENT FEDERAL ANSWER KEY"),
        (prec_str, "PRECISION"),
        ("48", "AUTOMATED TESTS (CI)"),
        ("11.6 s", "ISS vs 15,697 OBJECTS, 7 DAYS"),
    ]),
    Spacer(1, 1.0 * cm),
    P("FAR AWAY 2026 · Space &amp; Aerospace track · Round-1 project report",
      ParagraphStyle("c2", parent=sub_st, fontSize=10, textColor=GREY)),
    Spacer(1, 0.2 * cm),
    P("Python · FastAPI · CesiumJS · Next.js · Groq — $0 infrastructure, 100% public data",
      ParagraphStyle("c3", parent=sub_st, fontSize=9, textColor=GREY)),
    PageBreak(),
]

# ---------------------------------------------------------------- problem
story += [
    heading("1 · THE PROBLEM"),
    Spacer(1, 8),
    P("Low-Earth orbit is filling up: more than <b>11,000 active satellites</b> share the "
      "shells below 2,000 km with tens of thousands of tracked debris objects, and a single "
      "collision (Iridium-33/Cosmos-2251, 2009) can add thousands of fragments that stay up "
      "for decades. Every operator — including university cubesat teams and Indian smallsat "
      "startups like Pixxel and GalaxEye — receives <b>conjunction warnings</b>: cryptic "
      "Conjunction Data Messages with a roughly 99% false-alarm base rate."),
    Spacer(1, 6),
    P("The tools that turn those warnings into decisions are <b>commercial SSA services "
      "costing lakhs of rupees per year</b> (LeoLabs, COMSPOC) — priced for constellations, "
      "not for a team flying one satellite. The free alternatives are tables without "
      "explanations (SOCRATES), visualizations without validated math (most globe demos), "
      "or raw catalogs. None of them answer the operator's actual question:"),
    Spacer(1, 6),
    qbox("THE OPERATOR'S QUESTION",
         "&#8220;Do I need to move my satellite, and can I trust the number that says so?&#8221;"),
    Spacer(1, 10),
    heading("2 · THE SOLUTION"),
    Spacer(1, 8),
    P("OrbitGuard is a browser-based conjunction-assessment system built entirely on free, "
      "public data. It screens an operator's satellites against the full public catalog, "
      "computes collision probability with the <b>same class of method NASA CARA runs "
      "operationally</b>, triages every event into an explained <b>DODGE / WAIT / WATCH</b> "
      "verdict, and narrates the evidence in plain language. Its defining property:"),
    Spacer(1, 6),
    qbox("THE HONESTY PRINCIPLE",
         "Public TLE data carries no error model, so OrbitGuard never invents one. It computes "
         "the <b>worst-case</b> collision probability over every error model consistent with the "
         "geometry: PcMax = R&#178;/(e&#183;d&#178;). An upper bound can <b>prove an event safe</b> "
         "(PcMax below threshold under any covariance) but can <b>never order a maneuver</b> — "
         "for that, the verdict escalates to requesting CDM-grade data. TLE data can prove "
         "safety, never danger.", GREEN, GREENL),
    Spacer(1, 8),
    P("<b>Key features</b>"),
    Spacer(1, 3),
    bullets([
        "<b>Mission Control:</b> live 3D globe (CesiumJS) with animated assets, the ambient catalog, "
        "ranked verdict cards with countdown-to-TCA, and the screening funnel with timings.",
        "<b>Encounter Inspector:</b> per-event flyby view, encounter-plane figure (hard-body circle, "
        "miss vector, worst-case error circles), full numeric evidence record with raw-JSON toggle.",
        "<b>Validation Scorecard:</b> recall/precision against the official U.S. TraCSS answer key, "
        "rendered in-app with dataset citation and git SHA — we do not mark our own homework.",
        "<b>Grounded AI explanations:</b> a narrate-only LLM (Groq, llama-3.3-70b) converts the final "
        "evidence JSON to prose; a validator rejects any output containing numbers not present in "
        "the evidence; a deterministic template renderer is the always-on fallback.",
        "<b>India story:</b> demo assets are ISS, Pixxel FIREFLY-1, GalaxEye DRISHTI (NORAD 69010 — "
        "adjacent to the July-2026 5-digit catalog rollover our OMM-first design survives), ISRO EOS-08.",
    ]),
    PageBreak(),
]

# ---------------------------------------------------------------- architecture
story += [
    heading("3 · ARCHITECTURE"),
    Spacer(1, 8),
    panel(
        "CelesTrak GP (OMM JSON) ──&gt;  ingest  ──&gt;  astro (vectorized SGP4 · TEME frames)<br/>"
        "TraCSS OCM ephemerides ──&gt;  validation harness (no SGP4 in the loop)<br/>"
        "&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;"
        "&#9660;<br/>"
        "screening: Stage A perigee/apogee gate ──&gt; Stage B padded coarse-grid sieve ──&gt; "
        "Stage C Brent TCA refinement<br/>"
        "&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;"
        "&#9660;<br/>"
        "risk: Foster 2D-Pc · Chan cross-check · PcMax bound · DODGE/WAIT/WATCH policy ──&gt; "
        "evidence record (JSON)<br/>"
        "&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;"
        "&#9660;<br/>"
        "FastAPI (OpenAPI contract) ──&gt; Next.js + CesiumJS UI &#160;&#183;&#160; "
        "explain layer (Groq, narrate-only + validator + template fallback)", mono),
    Spacer(1, 6),
    P("<b>Data-flow rule that keeps the system honest:</b> every number shown anywhere is "
      "computed in the Python data plane. The LLM converts one finished JSON record into "
      "sentences; it cannot change a verdict, a probability, or a distance. OrbitGuard is not "
      "an AI wrapper — it is a numerical pipeline with an explanation layer bolted on the end."),
    Spacer(1, 8),
    grid_table(
        ["Layer", "Choice", "Why"],
        [
            ["Propagation", "python-sgp4 (vectorized SatrecArray) + Skyfield frames",
             "GP elements are fitted to SGP4 — anything else de-calibrates them; "
             "TEME&#8594;GCRS cross-checked &lt; 5 m vs Skyfield"],
            ["Screening", "3-stage sieve, numpy + cKDTree",
             "provable no-miss pad; 15,697 objects &#8594; 7 events in 11.6 s"],
            ["Probability", "Foster-1992 quadrature + Chan-1997 series + PcMax bound",
             "NASA CARA's operational method; two independent implementations cross-check in CI"],
            ["API", "FastAPI + pydantic", "frozen OpenAPI contract decouples frontend"],
            ["UI", "Next.js 14 + CesiumJS + satellite.js",
             "offline NaturalEarthII imagery — no ion token, demo survives dead Wi-Fi"],
            ["LLM", "Groq free tier, llama-3.3-70b-versatile",
             "narrate-only contract, digit validator, deterministic fallback"],
            ["Hosting", "$0 — laptop / free tiers", "committed fixtures make offline demo first-class"],
        ],
        [70, 165, FW - 235]),
    PageBreak(),
]

# ---------------------------------------------------------------- algorithms
story += [
    heading("4 · THE ALGORITHMS (AND WHY THEY ARE RIGHT)"),
    Spacer(1, 8),
    P("<b>4.1 The screening sieve.</b> Stage A discards objects whose perigee/apogee bands "
      "cannot meet the asset's (Hoots Filter I). Stage B propagates survivors on a coarse grid "
      "(&#916;t = 30 s live, 8 s all-vs-all) and flags any pair within the padded radius:"),
    Spacer(1, 4),
    panel("R<sub>pair</sub> = D + v<sub>rel,max</sub> &#183; &#916;t / 2 "
          "&#160;&#160;&#160;(v<sub>rel,max</sub> = 15.6 km/s, head-on LEO worst case)", mono),
    Spacer(1, 4),
    P("If a conjunction with miss &lt; D occurs at t*, the nearest grid point lies within "
      "&#916;t/2 and the pair can separate by at most v<sub>rel,max</sub>&#183;&#916;t/2 — so its "
      "grid separation is below R<sub>pair</sub>. <b>No true conjunction can escape the coarse "
      "net</b> (Alarc&#243;n-Rodr&#237;guez et al., ESA 2002). Stage C finds the exact TCA as a "
      "root of g(t) = &#916;r&#183;&#916;v with Brent's method."),
    Spacer(1, 8),
    P("<b>4.2 Collision probability.</b> At LEO closing speeds the encounter is instantaneous "
      "and the 3D problem collapses onto the 2D plane perpendicular to the relative velocity. "
      "The probability is a 2D Gaussian integrated over the combined hard-body disk:"),
    Spacer(1, 4),
    panel("Pc = (2&#960;)<sup>-1</sup>|C<sub>p</sub>|<sup>-1/2</sup> &#8747;&#8747;"
          "<sub>|x|&#8804;R</sub> exp(-(x-m)<sup>T</sup>C<sub>p</sub><sup>-1</sup>(x-m)/2) dA"
          "&#160;&#160;&#160;&#160;[Foster 1992 — NASA CARA's operational method]", mono),
    Spacer(1, 4),
    P("Foster (adaptive quadrature) is the displayed value; Chan's Rician series is computed "
      "alongside as a cross-check — an axis swap or frame bug moves Pc by orders of magnitude "
      "and trips the CI alarm. When no covariance exists (all public TLE data), the worst-case "
      "bound PcMax = R&#178;/(e&#183;d&#178;) is reported instead, with the policy asymmetry of "
      "Section 2."),
    Spacer(1, 8),
    grid_table(
        ["Data grade", "Condition", "Verdict"],
        [
            ["CDM-grade", "Pc &#8805; 10&#8315;&#8308;", "<b>DODGE</b> — NASA maneuver-consideration threshold"],
            ["CDM-grade", "10&#8315;&#8310; &#8804; Pc &lt; 10&#8315;&#8308;", "WATCH — monitoring band"],
            ["CDM-grade", "Pc &lt; 10&#8315;&#8310;", "WAIT"],
            ["TLE-grade", "PcMax &lt; 10&#8315;&#8310;", "WAIT — <b>provable</b> clearance under any covariance"],
            ["TLE-grade", "PcMax &#8805; 10&#8315;&#8308; and miss &lt; 5 km",
             "WATCH + <b>ESCALATE</b>: request CDM / owner ephemeris"],
            ["any", "v&#8347;&#8342;&#8343; &lt; 100 m/s", "WATCH + flag: 2D-Pc not applicable (disclosed, not faked)"],
        ],
        [70, 150, FW - 220]),
    PageBreak(),
]

# ---------------------------------------------------------------- validation
story += [
    heading("5 · VERIFICATION — MEASURED, NOT ASSERTED"),
    Spacer(1, 8),
    P("<b>Ring 1 — continuous (48 tests, every commit).</b>"),
    Spacer(1, 4),
    grid_table(
        ["Claim", "Independent referee"],
        [
            ["The sieve misses nothing", "brute-force 1 s search over every pair — recall AND "
             "precision asserted on scenes with planted conjunctions, near-misses, GEO/Molniya decoys"],
            ["Foster Pc is exact", "closed-form noncentral-&#967;&#178; (isotropic), scipy dblquad "
             "referee (anisotropic, machine precision), 2M-sample Monte Carlo"],
            ["PcMax is a theorem", "&#963;-sweep over 4 decades: exact Pc never exceeds "
             "R&#178;/(e&#183;d&#178;), bound attained at &#963; = d/&#8730;2"],
            ["Frames are right", "Skyfield's independent TEME&#8594;GCRS pipeline, &lt; 5 m"],
            ["Harness scores correctly", "synthetic ephemerides with closed-form TCA/miss; "
             "duplicate events penalize precision"],
        ],
        [120, FW - 120]),
    Spacer(1, 10),
    P("<b>Ring 2 — the federal exam.</b> The U.S. Office of Space Commerce (TraCSS program) "
      "publishes a <i>Dataset for Conjunction Assessment Verification</i> (The Aerospace "
      "Corporation, 2026, CC0): 20.7 GB of CCSDS-OCM ephemerides — the real TLE-derived "
      "catalog plus synthetic maneuvering objects, historical-CDM reconstructions and the "
      "OSIRIS-REx reentry — with a <b>" + n_key + "-conjunction answer key</b> generated by "
      "Aerospace's validated CSieve tool. OrbitGuard's screening engine runs directly on those "
      "ephemerides (no SGP4 in the loop — the key tests screening, not propagation), all-vs-all "
      "over " + n_eph + " ephemerides, 7-day window, on an 8 GB laptop."),
    Spacer(1, 6),
    metric_tiles([
        (rec_str, "RECALL"),
        (prec_str, "PRECISION"),
        (tca_rms, "TCA RMS ERROR"),
        (miss_rms, "MISS RMS ERROR"),
    ]),
    Spacer(1, 6),
    P(f'<font size="7.9" color="{GREY.hexval()}">Matching: unordered pair + |&#916;TCA| &#8804; 5 s, '
      'each key row claimable once. Run configuration per the official User&#8217;s Guide: spherical '
      '10 km volume, usable-window bounds honored, OD epoch &lt; 14 days, TCA strictly inside '
      '2025-01-01T12:00&#8594;2025-01-08T12:00 UTC. Disclaimer carried verbatim in-app: the dataset '
      'is for algorithm testing, not operational certification.</font>'),
    PageBreak(),
]

# ---------------------------------------------------------------- screenshots
shots_dir = ROOT / "docs" / "screenshots"
story += [heading("6 · THE PRODUCT"), Spacer(1, 8)]
for fname, caption in [
    ("mission-control.png",
     "Mission Control — live globe, animated assets and top-risk markers, ranked verdict cards "
     "with countdowns, and the screening funnel strip (15,697 objects &#8594; events, with timings)."),
    ("encounter-inspector.png",
     "Encounter Inspector — encounter-plane figure (hard-body circle, miss vector, worst-case "
     "&#963; circles), full evidence grid, grounded LLM explanation with raw-JSON toggle."),
    ("scorecard.png",
     "Validation Scorecard — the federal-answer-key metrics rendered in-app, with methodology "
     "and honest-limits statement."),
]:
    p = shots_dir / fname
    if p.exists():
        story += [shot(p, FW), Spacer(1, 3),
                  P(f'<font size="7.9" color="{GREY.hexval()}">{caption}</font>'), Spacer(1, 10)]

story += [PageBreak()]

# ---------------------------------------------------------------- datasets + honest limits + close
story += [
    heading("7 · DATA SOURCES (ALL FREE, ALL PUBLIC)"),
    Spacer(1, 8),
    grid_table(
        ["Source", "What", "Discipline"],
        [
            ["CelesTrak GP", "full active catalog as OMM JSON (15,697 objects)",
             "2 h refresh cadence enforced in code; every snapshot cached; OMM-first — integer "
             "catalog IDs survive the July-2026 5-digit rollover"],
            ["TraCSS verification dataset", "20.7 GB OCM ephemerides + CSieve answer keys (CC0)",
             "downloaded once to external SSD; .npy cache; subset-first runs"],
            ["Space-Track CDMs", "covariance for rigorous Pc (stretch)", "nightly batch, throttled"],
            ["Groq free tier", "llama-3.3-70b narration", "30 RPM / 100K tokens-day budget; "
             "SQLite cache; template fallback"],
        ],
        [95, 150, FW - 245]),
    Spacer(1, 10),
    heading("8 · HONEST LIMITS"),
    Spacer(1, 8),
    bullets([
        "GP/TLE accuracy is ~1 km at epoch, degrading 1–3 km/day (in-track dominant) — which is "
        "exactly why TLE-grade verdicts are worst-case bounds with an escalation path, never "
        "maneuver orders.",
        "Low relative-velocity encounters (&lt; 100 m/s) violate the short-encounter 2D-Pc "
        "assumptions; OrbitGuard flags them instead of printing a wrong number.",
        "Chan's series is an approximation: ~2% near the operational band, tens of percent in the "
        "deep tail — measured against an independent integration referee and documented; Foster "
        "is the displayed reference everywhere.",
        "A hackathon project is not an operational CA service; the TraCSS dataset is a diagnostic, "
        "not a certification.",
    ]),
    Spacer(1, 10),
    heading("9 · WHAT THIS PROJECT DEMONSTRATES"),
    Spacer(1, 8),
    P("A production-shaped system on real physics: vectorized SGP4 screening with a provable "
      "completeness guarantee; NASA-method collision probability verified against exact "
      "closed forms, independent integrators and Monte Carlo; a risk policy derived from an "
      "operational handbook with a defensible information-theoretic asymmetry; a "
      "<b>" + n_key + "-event federal answer-key validation</b> executed end-to-end on consumer "
      "hardware via deliberate vectorization (40&#215; refinement speedup); a strictly grounded "
      "LLM layer; CI, typed contracts, offline-first demo engineering — built in days, "
      "documented, tested, and reproducible."),
    Spacer(1, 8),
    P(f'<font size="8" color="{GREY.hexval()}">References: Foster &amp; Estes 1992 (NASA JSC-25898) · '
      'Chan 1997/2008 · NASA CARA 2D-Pc recommendations (NTRS 20190028900) · NASA CA Handbook v2 '
      '(NTRS 20230002470) · Alarc&#243;n-Rodr&#237;guez et al., ESA SP-486 (2002) · Hoots et al. 1984 · '
      'Vallado et al. 2006 · Auman et al., AMOS 2025 (TraCSS validation methodology) · Office of Space '
      'Commerce, Dataset for Conjunction Assessment Verification (CC0) · CelesTrak GP documentation. '
      'Full list in docs/ALGORITHMS.md.</font>'),
]

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
                        title="OrbitGuard — FAR AWAY 2026 Project Report")
doc.build(story)
print("built", OUT)
