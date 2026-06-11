# -*- coding: utf-8 -*-
"""Builds the FAR AWAY 2026 Problem-Statement Decision Brief PDF (final, 8 candidates)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)

W, H = A4
OUT = "FAR_AWAY_2026_Problem_Statement_Decision_Brief.pdf"
FW = W - 3.2*cm   # frame width

NAVY=colors.HexColor("#1B2A4A"); NAVY2=colors.HexColor("#28304A")
CHERRY=colors.HexColor("#E14B5A"); CREAM=colors.HexColor("#F6F2E9")
GREEN=colors.HexColor("#1E8E5A"); GREENL=colors.HexColor("#E5F3EC")
RED=colors.HexColor("#C24536"); REDL=colors.HexColor("#FBECEA")
AMBER=colors.HexColor("#C8862B"); ORANGE=colors.HexColor("#CF6B2E")
GOLD=colors.HexColor("#E0A43B"); GOLDL=colors.HexColor("#FBF3E2")
GREY=colors.HexColor("#6B7280"); GRIDE=colors.HexColor("#E3E6EA"); PANEL=colors.HexColor("#F4F6F9")

def band(s, scale=5.0):
    v=s/scale
    if v>=0.90: return GREEN
    if v>=0.78: return colors.HexColor("#3FA776")
    if v>=0.68: return AMBER
    if v>=0.58: return ORANGE
    return RED

ss=getSampleStyleSheet()
body=ParagraphStyle("body",parent=ss["Normal"],fontName="Helvetica",fontSize=9.3,leading=12.9,textColor=NAVY2)
small=ParagraphStyle("small",parent=body,fontSize=7.9,textColor=GREY,leading=10.3)
h1=ParagraphStyle("h1",parent=body,fontName="Helvetica-Bold",fontSize=15,textColor=NAVY,leading=18,spaceAfter=2)

def P(t,st=body): return Paragraph(t,st)
def L(label,lcol,txt): return Paragraph('<font color="%s"><b>%s</b></font>&#160;&#160;%s'%(lcol.hexval(),label,txt),body)
def bullets(items,col=NAVY2):
    return Paragraph("<br/>".join('<font color="%s">&#8226;</font>&#160;%s'%(col.hexval(),x) for x in items),body)

def heading(txt):
    t=Table([[Paragraph('<font color="white"><b>%s</b></font>'%txt,
              ParagraphStyle("hh",parent=body,fontSize=11.5,textColor=colors.white))]],colWidths=[FW])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),NAVY),("LEFTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)])); return t

def bar(score):
    full=int(score); half=1 if (score-full)>=0.5 else 0; fill=band(score)
    t=Table([[" "]*5],colWidths=[13]*5,rowHeights=[8])
    cmds=[("INNERGRID",(0,0),(-1,-1),1.5,colors.white),("BOX",(0,0),(-1,-1),0.5,GRIDE),
          ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0)]
    for i in range(5):
        c=fill if i<full else (colors.HexColor("#A9C9B8") if (i==full and half) else GRIDE)
        cmds.append(("BACKGROUND",(i,0),(i,0),c))
    t.setStyle(TableStyle(cmds)); return t

AX=["Resume / recruiter pull","Real-world impact","Technical depth","Originality","Demo legibility","Buildability"]
def ratings_grid(scores):
    pairs=list(zip(AX,scores)); rows=[]
    for i in range(0,6,2):
        rows.append([P(pairs[i][0],small),bar(pairs[i][1]),P(pairs[i+1][0],small),bar(pairs[i+1][1])])
    t=Table(rows,colWidths=[92,72,92,72],hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),6)]))
    return t

def proscons(pros,cons):
    ph=Paragraph('<font color="white"><b>PROS</b></font>',ParagraphStyle("p",parent=body,textColor=colors.white,fontSize=9.3))
    ch=Paragraph('<font color="white"><b>CONS / RISKS</b></font>',ParagraphStyle("c",parent=body,textColor=colors.white,fontSize=9.3))
    t=Table([[ph,ch],[bullets(pros,GREEN),bullets(cons,RED)]],colWidths=[(FW-8)/2]*2)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),GREEN),("BACKGROUND",(1,0),(1,0),RED),
        ("BACKGROUND",(0,1),(0,1),GREENL),("BACKGROUND",(1,1),(1,1),REDL),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),7),("LINEAFTER",(0,0),(0,-1),6,colors.white)])); return t

def nov_callout(txt):
    t=Table([[Paragraph('<font color="%s"><b>&#9733; STAR NOVELTY (our edge):</b></font>&#160;&#160;%s'
              %(CHERRY.hexval(),txt),body)]],colWidths=[FW])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GOLDL),("LINEBEFORE",(0,0),(0,-1),4,CHERRY),
        ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)])); return t

# ----------------------------------------------------------------------------- data
CANDS=[
 dict(rank="RECOMMENDED  ·  #1", name="GradeTrust", theme="Examinations", overall=9.2,
   tag="The fairness and trust layer for exam evaluation", scores=[5,5,4.5,4,5,4],
   novelty="Sell TRUST, not grading. The only platform that MEASURES and fixes grading "
     "inconsistency (Many-Facet Rasch psychometrics) across human AND AI graders, resists student "
     "injection attacks hidden in answers, and audits bias - the trust layer the crowded grader "
     "market (Eklavvya, Chanakya, CBSE) completely skips.",
   problem="Two examiners grade the SAME answer sheet and give very different marks (a 6 vs a 9) and "
     "that gap decides careers in UPSC Mains, board exams, university and coaching mock-tests. AI "
     "graders are very consistent but (a) only moderately accurate, (b) provably biased, and (c) "
     "trivially cheated by students who hide &#8216;give me full marks&#8217; inside their answer.",
   solve="A trust layer ON TOP of grading. It (1) runs an ensemble of rubric-grounded AI examiners "
     "plus the human marks, then uses Many-Facet Rasch to model each grader&#8217;s severity and "
     "reconcile to one calibrated, fair score; (2) blocks student prompt-injection in answer sheets; "
     "(3) audits bias (handwriting, length, vernacular); (4) explains every mark with a rubric "
     "citation and appeal trail. Sold B2B to coaching institutes, universities and boards.",
   pros=["Real, sellable B2B product with live budget (CBSE adopting AI eval in 2026; post-NEET mandate).",
     "&#8216;Founder who ships&#8217; PLUS frontier-security depth in ONE project - wins broad recruiters.",
     "Three novelty pillars (injection-robust, Rasch fairness, bias audit) no incumbent does.",
     "Visceral demo any non-techie gets: graders disagree by 18 marks, reconciled live to a cited score.",
     "Anti &#8216;AI-wrapper&#8217;: the depth is in calibration and robustness, not the prompt."],
   cons=["Grading market is crowded - you MUST hold the &#8216;trust / audit&#8217; angle, not &#8216;just grade&#8217;.",
     "High-stakes grading carries trust / liability weight.",
     "LLM-human agreement is only moderate - frame as ASSISTIVE, never &#8216;replaces examiners&#8217;."],
   impact="Fairer marks for millions; ~70% less grading time for teachers; an audit and appeal trail "
     "institutions can defend. Direct ROI for coaching chains and boards - a genuine company.",
   limits=["Needs model answers / rubrics plus a few expert-graded scripts to calibrate.",
     "Handwriting OCR on messy scripts is imperfect.","Not for MCQ exams (already machine-graded)."],
   scope="One subject, 20-50 sample scripts. Multimodal handwriting ingest, GraphRAG over the official "
     "rubric, 3-4 AI-examiner ensemble, Rasch calibration + injection filter + bias check, teacher "
     "dashboard (per-dimension scores, citations, confidence, appeal sheet). Metric: variance cut from "
     "X to under Y marks; injection attacks blocked Z%.",
   stack="Calibrator: claude-opus-4-8 (effort high). Examiner ensemble: claude-haiku-4-5 + Gemini Flash "
     "(free, handwriting), structured outputs. GraphRAG + ColPali. Next.js + D3. Eval: QWK / ICC + injection ASR.",
   fit="FAR AWAY: tops Real-World Impact + Execution; deep Tech (Rasch + robustness + multimodal RAG). "
     "Resume: &#8216;AI exam-evaluation trust layer - Rasch calibration cut examiner variance to under 4 "
     "marks, hardened vs answer-embedded injection, with bias audit&#8217; = product + ML + security in one line."),

 dict(rank="NEW STAR  ·  #2", name="VivaProof", theme="Examinations", overall=8.6,
   tag="GenAI-era authorship verification by auto-viva + process telemetry", scores=[4.5,4.5,4,4,4.5,3.5],
   novelty="Stop DETECTING AI (it is broken - high false-positive AND negative). VERIFY authorship "
     "instead: auto-generate a personalized viva from the student&#8217;s OWN submission plus draft / "
     "version telemetry, so they must defend their work - defensible exactly where GPTZero and Turnitin fail.",
   problem="Universities can no longer tell which work is the student&#8217;s: GPT writes original text "
     "that AI-detectors flag unreliably - too many false positives AND negatives for high-stakes calls. "
     "&#8216;Authentic&#8217; take-home tasks are no longer authentic. This is openly unsolved in 2026.",
   solve="From the student&#8217;s submission, auto-generate a personalized viva (timed-written or oral) "
     "that probes whether they can defend, critique and extend their own work, fused with process "
     "telemetry (draft / version history, editing patterns). Output: an authorship-confidence score "
     "plus a defensible evidence trail - not an automated accusation.",
   pros=["Rides a massive, panicked 2026 pain (every university, globally) - easy B2B sell.",
     "Sidesteps the unwinnable AI-detection arms race - defensible, low false-positive.",
     "Spectacular legible demo: AI grills a student on their own essay; a GPT-only author cannot answer.",
     "Software-only, multimodal (voice viva via STT); strong India + global fit."],
   cons=["Coursera and others are entering - validates the market but watch competition.",
     "Viva fairness / accessibility must be handled (anxiety, disability, language).",
     "Authorship &#8216;confidence&#8217; must be assistive evidence, never an automated verdict."],
   impact="Restores trust in assessment for thousands of institutions; saves faculty from manual vivas; "
     "a clear SaaS to universities, MOOCs and coaching - on one of 2026&#8217;s hottest pains.",
   limits=["Needs the student present for the viva (async-viva mitigates).",
     "Telemetry needs an editor / LMS integration.","Voice / vernacular STT quality varies."],
   scope="One course / assignment type. Ingest submission + draft history, RAG over the rubric / source, "
     "auto-generate 5 probing questions targeting the submission&#8217;s specific claims, run a timed "
     "written or voice viva (Whisper STT), score defensibility + telemetry consistency, output an "
     "authorship-confidence report. Metric: separates GPT-only vs genuine authors at X% on a seeded set.",
   stack="Question-gen + scoring: claude-opus-4-8 (structured outputs). Voice viva: Whisper STT + TTS. "
     "RAG: Chroma / GraphRAG. Telemetry: editor / Docs extension. Next.js viva UI.",
   fit="FAR AWAY: top Real-World Impact + Innovation + Demo; strong Tech (telemetry + RAG + voice). "
     "Resume: &#8216;authorship-verification platform that replaces broken AI-detection with auto-generated "
     "vivas + process telemetry&#8217; = product + applied ML on a hot, legible problem."),

 dict(rank="SECURITY STAR  ·  #3", name="FireBreak", theme="Agentic and Autonomous Systems", overall=8.3,
   tag="Containment layer that stops prompt-injection &#8216;worms&#8217; across multi-agent systems", scores=[4.5,3,5,5,4,3],
   novelty="Containment, not prevention. The first capability / provenance layer that stops &#8216;Prompt "
     "Infection&#8217; from spreading ACROSS multi-agent handoffs - the one agent-security gap the 2026 "
     "survey still calls unsolved at scale (while authz, memory and MCP firewalls already shipped).",
   problem="When AI agents work as a team and pass tasks to each other, one poisoned input can infect "
     "agent after agent like a virus (&#8216;Prompt Infection&#8217;) - stealing data or escalating actions "
     "across the whole pipeline. The 2026 survey says no published defense blocks this at scale.",
   solve="A containment layer: every inter-agent message carries provenance / capability labels so "
     "untrusted-derived text cannot cross a handoff as a command, and each agent is held to Meta&#8217;s "
     "&#8216;Rule of Two&#8217;. Demo: a worm spreads across four agents and exfiltrates, then FireBreak "
     "quarantines it at each handoff.",
   pros=["Genuinely unsolved frontier - maximum originality (unlike the now-saturated security primitives).",
     "Elite signal for AI-safety / security / research roles.","Spectacular &#8216;AI virus vs containment&#8217; live demo.",
     "Extends a real multi-agent framework (anti-wrapper)."],
   cons=["Research-y / infrastructure - NOT a product you can sell.",
     "Abstract to product-minded recruiters.","Hardest core to get working in the window.",
     "Honest framing must be &#8216;containment&#8217;, not &#8216;solved&#8217;."],
   impact="Protects the multi-agent systems everyone is racing to deploy in 2026; shrinks injection blast "
     "radius. High value to AI labs, low legibility to a normal user.",
   limits=["Cannot claim to &#8216;prevent&#8217; injection - only contain propagation.",
     "Needs a believable multi-agent victim scenario.","Credible eval needs adaptive attackers."],
   scope="A 4-agent CrewAI / AutoGen pipeline + containment middleware (provenance-tagged message bus + "
     "capability policy) + a Prompt-Infection corpus + a live agent-graph dashboard + a propagation-rate "
     "eval (naive vs contained).",
   stack="Agents: claude-opus-4-8; quarantined readers: claude-haiku-4-5 (structured outputs); MCP tools; "
     "LangGraph / CrewAI extension; Next.js graph dashboard.",
   fit="FAR AWAY: tops Tech Depth + Innovation; weaker Impact legibility. Resume: &#8216;first capability-based "
     "containment for LLM-to-LLM Prompt Infection across a multi-agent pipeline&#8217; = elite AI-safety signal "
     "(for a narrower set of roles)."),

 dict(rank="NEW  ·  #4", name="SentryBrowse", theme="Agentic and Autonomous Systems", overall=8.2,
   tag="Firewall + live red-team for browser / computer-use agents", scores=[4.5,3.5,4.5,3.5,5,3],
   novelty="Defuse the attack OpenAI says &#8216;may never be solved&#8217;: a deployable browser-agent firewall "
     "(visible-content sandboxing + action-risk gating) PLUS an RL red-team that proves it against "
     "invisible-text web injections - the exact vector Anthropic measured at a 31.5% hijack rate.",
   problem="Browser agents (ChatGPT Atlas, Comet, Claude for Chrome) get hijacked by invisible instructions "
     "on web pages - white-on-white text, HTML comments - into leaking OTPs or hitting banking portals. "
     "OpenAI says it may never be solved; Anthropic measured a 31.5% hijack rate before safeguards.",
   solve="A defense layer + live red-team: separate what the agent SEES from what it can be TOLD (strip "
     "injected instructions from page content), gate risky actions by data-provenance + risk score, and "
     "ship an RL-style attacker that auto-discovers bypasses. Demo: a booby-trapped page hijacks a naive "
     "browser agent to exfiltrate an OTP; SentryBrowse blocks it.",
   pros=["One of the hottest, most-cited problems in 2026 (OpenAI + Anthropic publicly flagging it).",
     "Maximally legible, dramatic demo (watch an AI get phished by a web page).",
     "Deep + frontier: provenance + sandboxing + RL red-teaming = serious engineering."],
   cons=["Research-crowded (ceLLMate, MUZZLE, VPI-Bench; frontier labs actively shipping).",
     "&#8216;Solving&#8217; it is impossible - frame as risk-reduction + red-team.",
     "Computer-use plumbing is fiddly to demo reliably."],
   impact="Protects browser agents about to reach millions of users; the red-team harness is independently "
     "useful. High lab / security value.",
   limits=["You compete with OpenAI / Anthropic&#8217;s own teams on the headline.",
     "Needs a controlled browser-agent setup to demo.","Containment, not a cure."],
   scope="Wrap one open browser-agent (Browser-use / Agent-E) with a provenance-aware content filter + "
     "action-risk gate + a small RL / templated attacker over booby-trapped pages; dashboard shows "
     "hijack-attempt vs blocked + attack-success-rate before / after.",
   stack="Agent: claude-opus-4-8 (computer-use); defense middleware in Python; attacker via templated + RL "
     "prompts; Playwright; Next.js dashboard.",
   fit="FAR AWAY: tops Innovation + Demo + Tech Depth; mid Impact legibility. Resume: &#8216;browser-agent "
     "firewall + RL red-team for indirect prompt injection&#8217; = elite AI-security signal on the year&#8217;s "
     "hottest agent problem (but a contested space)."),

 dict(rank="NEW WILDCARD  ·  #5", name="OrbitGuard", theme="Space and Aerospace", overall=8.0,
   tag="Explainable satellite collision-risk screening + 3D globe for small operators", scores=[4,3.5,4,4,5,3.5],
   novelty="Bench-marked space safety for the rest of us: a free browser 3D conjunction screen + an "
     "EXPLAINABLE ML risk score for small / Indian operators, validated against the Jan-2026 TraCSS OPEN "
     "answer-key dataset - real, defensible accuracy numbers, not a toy globe.",
   problem="Small / university / Indian satellite operators get cryptic collision warnings and cannot "
     "afford the commercial tools (lakhs per year) to interpret them - so they fly blind or dodge "
     "needlessly. Until Jan 2026 there was not even open test data to build against.",
   solve="A free, browser-based conjunction-screening dashboard: public orbital data (TLEs), propagate "
     "orbits, screen for close approaches, an explainable ML risk score (probability + why), a 3D globe "
     "with a clear DODGE / WAIT / WATCH recommendation - validated against the new TraCSS answer key.",
   pros=["Huge judge wow (live 3D globe of real orbits + collision alerts).",
     "Unusual, memorable resume line (aerospace + ML + viz) that stands out in a CS pile.",
     "Genuinely fresh enabler: the TraCSS answer-key dataset only opened Jan 2026.",
     "100% software, 100% public data; strong India angle (Pixxel / GalaxEye / ISRO)."],
   cons=["Less of a sellable product / narrower user base than the exam ideas.",
     "SpaceX Stargaze + commercial SSA exist - your wedge is explainability + small operators.",
     "Orbital-mechanics correctness is unforgiving; the math must be right."],
   impact="Democratizes collision safety for operators priced out of commercial SSA; civic + space-policy "
     "resonance, especially in India.",
   limits=["Niche user base; monetization unclear.","Needs careful propagation (Skyfield) to be credible.",
     "Public TLEs are lower-accuracy than operator ephemerides."],
   scope="A region of LEO + a few public satellites. TLEs (Celestrak / Space-Track), Skyfield propagation, "
     "close-approach screening, an ML / analytic risk score + natural-language explanation, a Cesium / "
     "Three.js 3D globe + DODGE / WAIT panel; report accuracy vs the TraCSS answer key.",
   stack="Python (Skyfield) propagation + screening; a light ML risk model; claude-opus-4-8 for the "
     "&#8216;why + recommendation&#8217;; Cesium / Three.js + Next.js; TraCSS + Celestrak public data.",
   fit="FAR AWAY: tops Demo / Innovation + a rare Space entry; mid Impact-sellability. Resume: &#8216;explainable "
     "satellite-collision dashboard validated on the official TraCSS dataset&#8217; = standout, hard-to-fake "
     "aerospace + ML line."),

 dict(rank="#6", name="ExamShield", theme="Examinations", overall=7.5,
   tag="Agentic exam-integrity SOC for the NEET-2026 crisis", scores=[3.5,4.5,3.5,3,5,3],
   novelty="Catch the LEAK, not the cheater. SOC-style PRE-exam leak detection (RAG content-fingerprinting "
     "of untrusted social / Telegram feeds) - the upstream angle that proctoring tools entirely ignore.",
   problem="NEET-2026 was cancelled after a paper leaked on WhatsApp ~weeks early (22.8 lakh students, 4 "
     "suicides). No single system catches leaks early, proctors fairly, AND audits the paper chain.",
   solve="A multi-agent platform: LeakDetector (RAG fingerprinting over social feeds), Proctor (bias-audited "
     "gaze / object detection), Auditor (tamper-evident paper chain) - optionally hardened with the dual-LLM "
     "pattern since it reads untrusted feeds.",
   pros=["Maximum judge emotional pull (timely national crisis).","Broad, instantly legible, strong India context.",
     "Several demoable modules."],
   cons=["Three loosely-coupled modules - wide but shallow.","Proctoring carries real bias / liability baggage.",
     "Less of a single sellable product; weaker pure-resume novelty."],
   impact="High civic resonance and a &#8216;would-have-caught-the-leak&#8217; narrative; reads as a public-good "
     "prototype more than a company or a deep system.",
   limits=["Hard to build all three modules deeply.","Proctoring fairness is a minefield.",
     "Leak-detection demo relies on simulated feeds."],
   scope="Focus the demo on LeakDetector (RAG fingerprint match on a simulated leak feed) + a thin proctor "
     "+ an audit timeline; do not try to ship all three deeply.",
   stack="CrewAI; LlamaIndex / Chroma; MediaPipe; claude-opus-4-8 + claude-haiku-4-5; Next.js.",
   fit="FAR AWAY: tops Real-World Impact + Demo; mid Tech / Originality. Resume: good impact story, weaker "
     "&#8216;deep system&#8217; or &#8216;product&#8217; signal than GradeTrust / VivaProof."),

 dict(rank="#7", name="JusticeRAG", theme="Examinations", overall=7.3,
   tag="Free &#8216;second-opinion&#8217; score auditor for UPSC aspirants", scores=[3.5,3.5,4,3,4,4],
   novelty="A free, explainable second-opinion score (rubric-grounded multi-agent calibration). Real - but "
     "it is simply the B2C subset of GradeTrust&#8217;s B2B, 3-pillar superset.",
   problem="UPSC Mains aspirants get scores from examiners who disagree by 30-40 marks on the same script, "
     "with no recourse (re-evaluation is not allowed).",
   solve="A multi-agent RAG (Scorer, Critic, Calibrator) over official model answers gives each candidate a "
     "free, rubric-grounded, explainable second opinion.",
   pros=["Emotionally clean single narrative.","Fully free-tier feasible (Gemini reads handwriting).",
     "Its technical core is shared with GradeTrust."],
   cons=["B2C aspirant tool - far narrower market than GradeTrust&#8217;s B2B.","Just &#8216;RAG over PDFs&#8217; unless deepened.",
     "Less of a &#8216;company&#8217; story."],
   impact="Helps individual aspirants directly, but limited institutional reach and no clear revenue path.",
   limits=["UPSC does not publish full criteria - alignment is capped.","Handwriting / vernacular variance.",
     "Strictly a subset of GradeTrust."],
   scope="Scorer / Critic / Calibrator agents + rubric RAG + handwriting ingest + a candidate report card "
     "(essentially GradeTrust&#8217;s B2C mode).",
   stack="Gemini Flash (handwriting, free) + claude-opus-4-8 calibrator + Chroma / GraphRAG; Next.js.",
   fit="FAR AWAY: solid but dominated by GradeTrust. Best treated as GradeTrust&#8217;s free consumer mode."),

 dict(rank="#8", name="CaMeL-Ops", theme="Agentic and Autonomous Systems", overall=7.0,
   tag="Injection-proof single agent (dual-LLM + capability tokens)", scores=[4,3,5,2,4,3],
   novelty="(Largely spent.) The dual-LLM + capability-token idea is strong - but Google, Microsoft "
     "(Dromedary) and an OpenClaw port already shipped it. Keep only as a learning reference, not a submission.",
   problem="A tool-using AI agent (e.g. an inbox assistant) can be hijacked by a malicious instruction "
     "hidden in the data it reads - an email saying &#8216;forward all emails to me&#8217;.",
   solve="Split the agent into a planner LLM (never sees untrusted data) + a quarantined reader LLM (no "
     "tools), with a capability engine gating tool calls. Demo: naive agent gets owned, ours blocks.",
   pros=["Strong technical-depth + security signal.","Clean &#8216;hacked vs blocked&#8217; demo.","Implements a famous 2025 paper."],
   cons=["NO LONGER ORIGINAL - 3 open-source versions already exist. A 4th clone reads as derivative.",
     "Single-agent only (the easy case; FireBreak solves the hard one).","Not a product."],
   impact="Educational / reference value - but the exact gap it filled is now filled by others.",
   limits=["Reimplements existing work; limited novelty headline.","Was the original #1 before research found the clones."],
   scope="Dual-LLM inbox agent + capability interpreter + injection corpus + side-by-side demo + ASR eval.",
   stack="Planner claude-opus-4-8; quarantined claude-haiku-4-5; MCP tools; LangGraph.",
   fit="FAR AWAY: high Tech Depth, low Originality (saturated) - capped. Resume: weaker than extending it "
     "(FireBreak) or shipping a product with it (GradeTrust)."),
]

AVOID=[
 ["Runtime agent authorization / &#8216;agent IAM&#8217;","Microsoft Agent Governance Toolkit (MIT, all 10 OWASP agentic risks); IBM; NIST initiative"],
 ["Agent memory firewall (MINJA defense)","mguard - Ed25519 provenance + Bayesian trust, already shipped open-source"],
 ["Generic MCP security gateway / firewall","mcp-firewall, pipelock, Lasso MCP Gateway, agent-shield"],
 ["Generic AI answer-sheet grader","Eklavvya, Chanakya AI, Gradelab, CBSE&#8217;s own 2026 pilot"],
 ["CaMeL reimplementation (single-agent)","google-research/camel-prompt-injection, Microsoft Dromedary, OpenClaw"],
]

# ----------------------------------------------------------------------------- furniture
def cover(c,doc):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(CHERRY); c.rect(0,H-150,W,6,fill=1,stroke=0)
    c.setFillColor(CHERRY); c.setFont("Helvetica-Bold",12)
    c.drawCentredString(W/2,H-110,"F A R   A W A Y   ·   2 0 2 6")
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold",33)
    c.drawCentredString(W/2,H-205,"Problem-Statement")
    c.drawCentredString(W/2,H-245,"Decision Brief")
    c.setFillColor(CREAM); c.setFont("Helvetica",13)
    c.drawCentredString(W/2,H-280,"8 candidates  ·  rated and compared  ·  pick one")
    c.setFont("Helvetica-Oblique",10.5)
    c.drawCentredString(W/2,H-302,"Optimised for: builder-first hackathon scoring + maximum resume / recruiter pull")
    bx,bw,bh=60,W-120,158; by=H-493
    c.setFillColor(CREAM); c.roundRect(bx,by,bw,bh,10,fill=1,stroke=0)
    c.setFillColor(CHERRY); c.setFont("Helvetica-Bold",11)
    c.drawString(bx+22,by+bh-30,"OUR RECOMMENDATION")
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold",18); c.drawString(bx+22,by+bh-58,"GradeTrust")
    c.setFont("Helvetica",11.5); c.setFillColor(NAVY2); c.drawString(bx+150,by+bh-57,"the fairness + trust layer for exam evaluation")
    c.setFillColor(NAVY2); c.setFont("Helvetica",9.5)
    c.drawString(bx+22,by+bh-84,"A sellable product that also showcases frontier AI-security depth (injection-robust grading).")
    c.drawString(bx+22,by+bh-99,"Freshest new contender: VivaProof (GenAI-era authorship verification).  Deepest security pick: FireBreak.")
    c.setFillColor(CHERRY); c.setFont("Helvetica-Bold",30); c.drawRightString(bx+bw-22,by+22,"9.2 / 10")
    c.setFillColor(GREY); c.setFont("Helvetica",8.5); c.drawString(bx+22,by+18,"Claude's overall rating")
    px=60
    for p in ["Software-only","Resume-first","Team of 4-5"]:
        pw=8+c.stringWidth(p,"Helvetica-Bold",10)+8
        c.setFillColor(colors.HexColor("#2C3B5C")); c.roundRect(px,118,pw,24,6,fill=1,stroke=0)
        c.setFillColor(CREAM); c.setFont("Helvetica-Bold",10); c.drawString(px+8,125,p); px+=pw+10
    c.setFillColor(CREAM); c.setFont("Helvetica",9)
    c.drawCentredString(W/2,70,"Prepared by Claude (Opus 4.8)  ·  11 June 2026  ·  Share with your team to finalise on one")
    c.restoreState()

def later(c,doc):
    c.saveState()
    c.setFillColor(CHERRY); c.rect(0,H-6,W,6,fill=1,stroke=0)
    c.setFillColor(GREY); c.setFont("Helvetica",8)
    c.drawString(1.6*cm,H-22,"FAR AWAY 2026  -  Problem-Statement Decision Brief")
    c.drawRightString(W-1.6*cm,H-22,"Page %d"%doc.page)
    c.setStrokeColor(GRIDE); c.setLineWidth(0.5); c.line(1.6*cm,24,W-1.6*cm,24)
    c.setFillColor(GREY); c.setFont("Helvetica",8)
    c.drawString(1.6*cm,14,"Confidential draft for team review"); c.drawRightString(W-1.6*cm,14,"claude-opus-4-8")
    c.restoreState()

# ----------------------------------------------------------------------------- story
story=[PageBreak()]
story+=[P("How to read this brief",h1),
  P("This brief compares EIGHT problem statements for FAR AWAY 2026, each researched against the live web "
    "in June 2026 and framed to be strong on BOTH the hackathon&#8217;s builder-first scoring and resume / "
    "recruiter pull. Each is rated by Claude on six axes (1-5), given an overall out of 10, and carries an "
    "explicit STAR NOVELTY - the specific edge that makes it stand out. Read the matrix, skim the profiles, "
    "then use the 5-minute team vote on the last page.",body),
  Spacer(1,6),
  P('<font color="%s"><b>What deeper research changed:</b></font>  agent-security <i>primitives</i> '
    '(runtime authz, memory firewall, MCP gateway, single-agent CaMeL) are ALREADY shipped in 2026 by '
    'Microsoft, Google and mguard - so they are no longer novel. Novelty has moved to <b>vertical products</b>: '
    'hence GradeTrust and the new <b>VivaProof</b>, plus a Space wildcard (<b>OrbitGuard</b>). <b>FireBreak</b> '
    'is the one security primitive still genuinely open (multi-agent infection).'%CHERRY.hexval(),body),
  Spacer(1,10), P("Scoring legend",h1)]
legend=Table([[P("<b>Axis</b>",small),P("<b>What it measures</b>",small)],
   [P("Resume / recruiter pull",small),P("How strongly it makes a recruiter want to interview you",small)],
   [P("Real-world impact",small),P("Does it solve a real, felt problem? Could it be sold / shipped?",small)],
   [P("Technical depth",small),P("Real engineering vs a thin &#8216;AI wrapper&#8217; (which the rubric penalises)",small)],
   [P("Originality",small),P("How crowded the space already is - how novel your angle is",small)],
   [P("Demo legibility",small),P("Can a non-technical judge instantly &#8216;get&#8217; the 2-minute demo?",small)],
   [P("Buildability",small),P("Realistic to ship a strong version with a 4-5 person team in the window",small)]],
   colWidths=[150,FW-150])
legend.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,PANEL]),
   ("GRID",(0,0),(-1,-1),0.5,GRIDE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),6),
   ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
story+=[legend,Spacer(1,12),P("The eight candidates at a glance",h1)]

hdr=["Problem statement","Res.","Impact","Tech","Orig.","Demo","Build","Overall"]
mrows=[[P('<font color="white"><b>%s</b></font>'%h,small) for h in hdr]]
mstyle=[("BACKGROUND",(0,0),(-1,0),NAVY),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("GRID",(0,0),(-1,-1),0.5,colors.white),
   ("ALIGN",(1,0),(-1,-1),"CENTER"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
   ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]
for r,cd in enumerate(CANDS,start=1):
    row=[P("<b>%s</b>  <font size=7 color='%s'>%s</font>"%(cd["name"],GREY.hexval(),cd["theme"]),small)]
    for s in cd["scores"]: row.append(P('<font color="white"><b>%g</b></font>'%s,small))
    row.append(P('<font color="white"><b>%.1f</b></font>'%cd["overall"],small))
    mrows.append(row)
    for ci,s in enumerate(cd["scores"],start=1): mstyle.append(("BACKGROUND",(ci,r),(ci,r),band(s)))
    mstyle.append(("BACKGROUND",(7,r),(7,r),band(cd["overall"],scale=10)))
    mstyle.append(("BACKGROUND",(0,r),(0,r),colors.white if r%2 else PANEL))
mat=Table(mrows,colWidths=[FW-7*40]+[40]*7); mat.setStyle(TableStyle(mstyle))
story+=[mat,Spacer(1,5),P("Cell colour = score band (green high to red low). Deep-dive profiles follow, one per page.",small)]

story+=[Spacer(1,12),heading("THE DECISION IN ONE LINE"),Spacer(1,6),bullets([
  "<b>Balanced #1 (product + security depth + legible):</b>  build <b>GradeTrust</b>  -  our pick.",
  "<b>Freshest new vertical (hot university pain):</b>  <b>VivaProof</b>  (authorship verification).",
  "<b>Deepest security signal (still-open frontier):</b>  <b>FireBreak</b>.",
  "<b>Most dramatic demo / hottest agent topic:</b>  <b>SentryBrowse</b>  (but a contested research space).",
  "<b>Judge-wow wildcard / standout resume line:</b>  <b>OrbitGuard</b>  (Space).",
  "<b>Avoid as primary:</b>  CaMeL-Ops, JusticeRAG, and anything in the &#8216;already shipped&#8217; box below."])]

story+=[Spacer(1,12),heading("ALREADY SHIPPED IN 2026 - DO NOT PICK AS YOUR CORE"),Spacer(1,6)]
arows=[[P("<b>Tempting idea</b>",small),P("<b>Who already shipped it (so it is no longer novel)</b>",small)]]
arows+=[[P(a,small),P(b,small)] for a,b in AVOID]
at=Table(arows,colWidths=[185,FW-185])
at.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),RED),("ROWBACKGROUNDS",(0,1),(-1,-1),[REDL,colors.white]),
   ("GRID",(0,0),(-1,-1),0.5,GRIDE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),6),
   ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
story+=[at]

for cd in CANDS:
    story.append(PageBreak())
    badge=Table([[P('<font color="white"><b>%s</b></font><br/><font color="%s" size=9>%s</font>'
        %(cd["name"],CREAM.hexval(),cd["tag"]),ParagraphStyle("bn",parent=body,fontSize=16,textColor=colors.white,leading=19)),
        P('<font color="white" size=8>CLAUDE&#8217;S RATING</font><br/><font color="white"><b>%.1f</b></font><font color="white" size=10> / 10</font>'
        %cd["overall"],ParagraphStyle("br",parent=body,fontSize=26,textColor=colors.white,alignment=TA_CENTER,leading=27))]],
        colWidths=[FW-120,120])
    badge.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),NAVY),("BACKGROUND",(1,0),(1,0),CHERRY),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(1,0),(1,0),"CENTER"),("LEFTPADDING",(0,0),(0,0),12),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))
    story.append(badge)
    story.append(P('<font color="%s"><b>%s</b></font>&#160;&#160;&#160;Theme: %s'%(CHERRY.hexval(),cd["rank"],cd["theme"]),small))
    story.append(Spacer(1,6))
    story.append(nov_callout(cd["novelty"]))
    story.append(Spacer(1,8))
    pc=Table([[Paragraph('<font color="%s"><b>THE PROBLEM (plain English)</b></font><br/>%s'%(NAVY.hexval(),cd["problem"]),body),
        Paragraph('<font color="%s"><b>HOW WE&#8217;D SOLVE IT</b></font><br/>%s'%(CHERRY.hexval(),cd["solve"]),body)]],
        colWidths=[(FW-8)/2]*2)
    pc.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),PANEL),("BACKGROUND",(1,0),(1,0),CREAM),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),8),
        ("BOTTOMPADDING",(0,0),(-1,-1),9),("LINEAFTER",(0,0),(0,-1),8,colors.white)]))
    story.append(pc)
    story.append(Spacer(1,8))
    story.append(P('<font color="%s"><b>RATINGS</b></font>'%NAVY.hexval(),body)); story.append(Spacer(1,3))
    story.append(ratings_grid(cd["scores"])); story.append(Spacer(1,8))
    story.append(proscons(cd["pros"],cd["cons"])); story.append(Spacer(1,8))
    story.append(L("REAL-WORLD IMPACT &amp; SELLABILITY",GREEN,cd["impact"])); story.append(Spacer(1,5))
    story.append(P('<font color="%s"><b>LIMITATIONS &amp; RISKS</b></font>'%RED.hexval(),body)); story.append(bullets(cd["limits"],RED))
    story.append(Spacer(1,5)); story.append(L("HACKATHON SCOPE (MVP)",NAVY,cd["scope"]))
    story.append(Spacer(1,5)); story.append(L("TECH STACK",GREY,cd["stack"]))
    story.append(Spacer(1,5)); story.append(L("FAR AWAY FIT + RESUME SIGNAL",CHERRY,cd["fit"]))

story.append(PageBreak())
story.append(P("Final recommendation + how to decide together",h1)); story.append(Spacer(1,4))
rec=Table([[Paragraph('<font color="white"><b>BUILD THIS:&#160; GradeTrust</b> - the exam-evaluation trust layer.</font>'
   '<br/><font color="%s" size=9>It is the only candidate that is BOTH a sellable product AND a frontier-depth '
   'build: rubric-grounded multimodal RAG + Many-Facet Rasch fairness calibration + student-injection defence + '
   'bias audit + appeal-grade explanations. It escapes the crowded &#8216;AI grader&#8217; market by selling TRUST, not '
   'speed, and keeps the AI-security depth as a real anti-cheating feature. <b>Freshest alternative:</b> VivaProof '
   '(authorship verification) - same Examinations theme; the two could even combine into one Exam-Integrity suite.</font>'
   %CREAM.hexval(),ParagraphStyle("rec",parent=body,textColor=colors.white,fontSize=12,leading=16))]],colWidths=[FW])
rec.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GREEN),("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
   ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),11)]))
story+=[rec,Spacer(1,12),heading("HOW TO DECIDE AS A TEAM (5-minute vote)"),Spacer(1,6),bullets([
  "<b>Step 1 - role check:</b> if MOST of you target AI-safety / security labs, shortlist FireBreak or SentryBrowse; otherwise GradeTrust / VivaProof lead.",
  "<b>Step 2 - gut-check the demo:</b> which 2-minute demo makes a stranger lean in? (GradeTrust: graders disagree, we fix it. VivaProof: AI grills you on your own essay. SentryBrowse: AI gets phished by a web page.)",
  "<b>Step 3 - capacity:</b> the vertical products (GradeTrust / VivaProof) split cleanly into 5 lanes; the security ones (FireBreak / SentryBrowse) have a harder, riskier core.",
  "<b>Step 4 - vote</b> below; highest total wins. Tie-break toward the more sellable + more legible option."])]
vrows=[[P("<b>Candidate</b>",small)]+[P("<b>%s</b>"%n,small) for n in ["M1","M2","M3","M4","M5","Total"]]]
for cd in CANDS: vrows.append([P(cd["name"],small),"","","","","",""])
vt=Table(vrows,colWidths=[FW-6*52]+[52]*6,rowHeights=[20]+[22]*len(CANDS))
vt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,PANEL]),
   ("GRID",(0,0),(-1,-1),0.5,GRIDE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),6)]))
story+=[vt,Spacer(1,4),
  P("(Each member scores every candidate 1-10 on &#8216;how proud would I be to put this on my resume AND demo it on stage&#8217;.)",small),
  Spacer(1,12),
  P('<font color="'+NAVY.hexval()+'"><b>Key sources (June 2026):</b></font> CaMeL (arXiv:2503.18813) + Google / Microsoft Dromedary / '
    'OpenClaw impls; Prompt Infection (arXiv:2410.07283); Meta &#8216;Agents Rule of Two&#8217;; Microsoft Agent Governance '
    'Toolkit; mguard memory firewall; MINJA (arXiv:2503.03704); browser-agent injection (OpenAI / Anthropic 31.5%, '
    'ceLLMate, MUZZLE, VPI-Bench); TraCSS open dataset (Jan 2026); Eklavvya / Chanakya / CBSE pilot; SteLLA + GraphRAG '
    'ASAG; Wharton GAIL injection-on-grading; Many-Facet Rasch AES studies; authentic-assessment / auto-viva (BERA, '
    'Coursera, IATED).',small)]

doc=SimpleDocTemplate(OUT,pagesize=A4,leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=2.0*cm,bottomMargin=1.8*cm,
   title="FAR AWAY 2026 - Problem-Statement Decision Brief",author="Claude (Opus 4.8)")
doc.build(story,onFirstPage=cover,onLaterPages=later)
print("OK ->",OUT)
