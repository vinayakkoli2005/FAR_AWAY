# -*- coding: utf-8 -*-
"""FAR AWAY 2026 - Final 3 deep-dive build + feasibility report PDF."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

W,H=A4; OUT="FAR_AWAY_2026_OrbitGuard_DeepDive.pdf"; FW=W-3.2*cm
NAVY=colors.HexColor("#1B2A4A"); NAVY2=colors.HexColor("#28304A"); CHERRY=colors.HexColor("#E14B5A")
CREAM=colors.HexColor("#F6F2E9"); GREEN=colors.HexColor("#1E8E5A"); GREENL=colors.HexColor("#E5F3EC")
RED=colors.HexColor("#C24536"); REDL=colors.HexColor("#FBECEA"); AMBER=colors.HexColor("#C8862B")
AMBERL=colors.HexColor("#FBF1DD"); GOLDL=colors.HexColor("#FBF3E2"); GREY=colors.HexColor("#6B7280")
GRIDE=colors.HexColor("#E3E6EA"); PANEL=colors.HexColor("#F4F6F9")

def bd(s,sc=5.0):
    v=s/sc
    return GREEN if v>=0.9 else colors.HexColor("#3FA776") if v>=0.78 else AMBER if v>=0.68 else colors.HexColor("#CF6B2E") if v>=0.58 else RED

ss=getSampleStyleSheet()
body=ParagraphStyle("body",parent=ss["Normal"],fontName="Helvetica",fontSize=9.3,leading=12.9,textColor=NAVY2)
small=ParagraphStyle("small",parent=body,fontSize=7.9,textColor=GREY,leading=10.3)
h1=ParagraphStyle("h1",parent=body,fontName="Helvetica-Bold",fontSize=15,textColor=NAVY,leading=18)

def P(t,st=body): return Paragraph(t,st)
def L(label,lcol,txt): return Paragraph(f'<font color="{lcol.hexval()}"><b>{label}</b></font>&#160;&#160;{txt}',body)
def bullets(items,col=NAVY2): return Paragraph("<br/>".join(f'<font color="{col.hexval()}">&#8226;</font>&#160;{x}' for x in items),body)
def heading(txt):
    t=Table([[Paragraph(f'<font color="white"><b>{txt}</b></font>',ParagraphStyle("hh",parent=body,fontSize=10.5,textColor=colors.white))]],colWidths=[FW])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),NAVY),("LEFTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)])); return t

def bar(score):
    full=int(score); half=1 if (score-full)>=0.5 else 0; fill=bd(score)
    t=Table([[" "]*5],colWidths=[13]*5,rowHeights=[8])
    cmds=[("INNERGRID",(0,0),(-1,-1),1.5,colors.white),("BOX",(0,0),(-1,-1),0.5,GRIDE),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0)]
    for i in range(5):
        c=fill if i<full else (colors.HexColor("#A9C9B8") if (i==full and half) else GRIDE); cmds.append(("BACKGROUND",(i,0),(i,0),c))
    t.setStyle(TableStyle(cmds)); return t
AX=["Resume / recruiter pull","Real-world impact","Technical depth","Originality","Demo legibility","Buildability"]
def ratings_grid(scores):
    pairs=list(zip(AX,scores)); rows=[[P(pairs[i][0],small),bar(pairs[i][1]),P(pairs[i+1][0],small),bar(pairs[i+1][1])] for i in range(0,6,2)]
    t=Table(rows,colWidths=[92,72,92,72],hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),6)])); return t

def proscons(pros,cons):
    ph=Paragraph('<font color="white"><b>PROS</b></font>',ParagraphStyle("p",parent=body,textColor=colors.white,fontSize=9.3))
    ch=Paragraph('<font color="white"><b>CONS / RISKS</b></font>',ParagraphStyle("c",parent=body,textColor=colors.white,fontSize=9.3))
    t=Table([[ph,ch],[bullets(pros,GREEN),bullets(cons,RED)]],colWidths=[(FW-8)/2]*2)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),GREEN),("BACKGROUND",(1,0),(1,0),RED),("BACKGROUND",(0,1),(0,1),GREENL),("BACKGROUND",(1,1),(1,1),REDL),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),7),("LINEAFTER",(0,0),(0,-1),6,colors.white)])); return t

def qbox(title,txt):
    t=Table([[Paragraph(f'<font color="{CHERRY.hexval()}"><b>{title}</b></font><br/>{txt}',body)]],colWidths=[FW])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GOLDL),("LINEBEFORE",(0,0),(0,-1),4,CHERRY),("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)])); return t

def pipeline(stages):
    inner="<br/>".join(f'<font color="{CHERRY.hexval()}"><b>{i+1}.</b></font>&#160;{s}' for i,s in enumerate(stages))
    t=Table([[Paragraph(inner,body)]],colWidths=[FW])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)])); return t

def steps_table(steps):
    rows=[[Paragraph(f'<b>{a}</b>',small),P(b,small)] for a,b in steps]
    t=Table(rows,colWidths=[120,FW-120])
    t.setStyle(TableStyle([("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white,PANEL]),("GRID",(0,0),(-1,-1),0.5,GRIDE),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)])); return t

def risk_panel(items):
    hdr=Paragraph('<font color="white"><b>WHAT CAN BREAK / WHAT WE ARE MISSING</b></font>',ParagraphStyle("rh",parent=body,textColor=colors.white,fontSize=9.3))
    t=Table([[hdr],[bullets(items,AMBER)]],colWidths=[FW])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),AMBER),("BACKGROUND",(0,1),(0,1),AMBERL),("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),7)])); return t

# ----------------------------------------------------------------------------- content
PROJ=[
 dict(name="OrbitGuard", overall=8.2, scores=[4,3.5,4.5,4,5,3.5],
   tag="Free, explainable satellite collision-risk screening + 3D globe, validated on the official TraCSS answer key",
   oneliner="Ingest public orbital data, screen for close approaches, score the risk WITH an explanation, and show a 3D globe with a DODGE / WAIT / WATCH call for small operators.",
   qtitle="YOUR QUESTION - live free API or static data? ANSWER: both, and that is the strength",
   q="LIVE free data exists: CelesTrak GP serves TLE / OMM element sets, refreshed every 2 hours (cache it - "
     "over 100 MB per day or more than one download per update can get your IP firewalled). Space-Track.org "
     "(free account) adds TLEs AND real Conjunction Data Messages (CDMs) that carry covariance. STATIC "
     "validation exists too: the Office of Space Commerce TraCSS &#8216;Dataset for Conjunction Assessment "
     "Verification&#8217; ships TWO answer keys (a spherical screening volume and the SFSH rectangular volumes) "
     "plus a User&#8217;s Guide - request access with a Google account. APPROACH: drive the live 3D globe and "
     "screening from CelesTrak TLEs, then VALIDATE your screener against the TraCSS answer key for credible "
     "accuracy; use CDM covariance for a real collision probability, or a transparent simplified estimate where it is missing.",
   build="A free, browser-based dashboard that ingests public orbital data, screens for close approaches, scores "
     "the risk with an explanation, and shows a 3D globe with a clear DODGE / WAIT / WATCH call for small operators.",
   pipe=["Fetch and cache public element sets (CelesTrak GP TLE / OMM; Space-Track for CDMs)",
     "Propagate orbits with Skyfield / SGP4 (pure Python)",
     "Coarse pre-filter candidate pairs (altitude bands, orbital-geometry sieve) - avoids the O(N squared) blow-up",
     "Fine search: step through time to find time of closest approach and miss distance",
     "Risk: collision probability from CDM covariance, or a transparent simplified estimate from TLEs",
     "Explain: an LLM turns the geometry into &#8216;why&#8217; plus a DODGE / WAIT / WATCH recommendation",
     "Visualise: a CesiumJS / Three.js 3D globe with the conjunction, a timeline and a recommendation panel",
     "Validate: run the screener on the TraCSS answer key and report accuracy"],
   steps=[("Phase 1 - Data + globe","Fetch and cache TLEs; parse with Skyfield; render a handful of satellites on a 3D globe."),
     ("Phase 2 - Closest approach","Vector subtraction over a time grid to find time of closest approach and miss distance for a pair."),
     ("Phase 3 - Screening at scale","Coarse pre-filters to shortlist candidate pairs, then fine search; validate on the TraCSS spherical-volume answer key."),
     ("Phase 4 - Risk + explanation","Simplified collision probability first, then CDM-covariance probability where available; LLM explanation + DODGE / WAIT / WATCH."),
     ("Phase 5 - 3D UX","Highlight conjunctions, add a timeline and a recommendation panel on the globe."),
     ("Phase 6 - Accuracy (+ stretch)","Report recall vs the TraCSS key; stretch: live CDM ingestion from Space-Track.")],
   metric="Headline you can defend: &#8216;our screener reproduces the official TraCSS answer-key conjunctions "
     "(spherical volume) at X percent recall, with a live 3D globe from public TLEs and an explainable DODGE / "
     "WAIT call.&#8217; The numbers are credible because they are checked against an OFFICIAL key, not a toy.",
   risks=["TLEs carry NO covariance, so a proper collision probability needs CDM covariance - do not overclaim probability from TLEs alone; use CDMs or a clearly-labelled simplified estimate.",
     "SGP4 / TLE accuracy is kilometre-level and degrades with propagation time, so screening is approximate (the TraCSS key lets you quantify this honestly).",
     "All-pairs screening is O(N squared) per time step - without coarse pre-filters it will not scale; the sieve IS the real engineering.",
     "Reference frames and time systems (TEME to ECI / ECEF, UTC vs TT) are easy to get wrong and silently corrupt results.",
     "NORAD 5-digit catalog numbers run out around 12 July 2026; new objects get 6-digit IDs with NO TLE-format data - use OMM / JSON.",
     "TraCSS files are by-request on Google Drive - request access EARLY; CelesTrak rate limits mean you must cache.",
     "SpaceX Stargaze and commercial SSA already screen conjunctions - your wedge is explainability + small / Indian operators, not raw screening."],
   pros=["Live free data AND an official answer key - real, defensible numbers, not a toy globe.",
     "Huge judge wow (a live 3D globe of real orbits with collision alerts).",
     "Standout, hard-to-fake resume line (aerospace + ML + visualisation).",
     "100 percent software and public data; strong India angle (Pixxel / GalaxEye / ISRO)."],
   cons=["Niche user base and unclear monetisation versus the exam ideas.",
     "Orbital-mechanics correctness is unforgiving - the math must be right under demo pressure.",
     "A defensible collision probability needs covariance (CDMs), adding plumbing."],
   mvp="One primary satellite vs a curated catalog subset: screen + closest approach + simplified risk + 3D globe + TraCSS spherical-volume validation.",
   stretch="Full all-vs-all screening with pre-filters, CDM-covariance probability, and a live Space-Track CDM feed.",
   team=["Data + propagation (Skyfield / SGP4)","Screening algorithm + TraCSS validation","Risk / probability + LLM explainer","3D globe (CesiumJS / Three.js)","Backend / API + integration"],
   stack="Python (Skyfield / SGP4, NumPy); CelesTrak GP + Space-Track APIs; TraCSS verification dataset; claude-opus-4-8 for explanations; CesiumJS / Three.js + Next.js."),
]

# ----------------------------------------------------------------------------- furniture
def cover(c,doc):
    c.saveState(); c.setFillColor(NAVY); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(CHERRY); c.rect(0,H-150,W,6,fill=1,stroke=0)
    c.setFillColor(CHERRY); c.setFont("Helvetica-Bold",12); c.drawCentredString(W/2,H-110,"F A R   A W A Y   ·   2 0 2 6")
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold",30); c.drawCentredString(W/2,H-200,"OrbitGuard — Deep-Dive")
    c.drawCentredString(W/2,H-238,"Build + Feasibility Report")
    c.setFillColor(CREAM); c.setFont("Helvetica",12.5); c.drawCentredString(W/2,H-272,"Space & Aerospace  ·  FAR AWAY 2026")
    c.setFont("Helvetica-Oblique",10.5); c.drawCentredString(W/2,H-293,"End-to-end pipeline, step-by-step plan, real data sources, honest metrics, and what can break")
    bx,bw,bh=58,W-116,150; by=H-490
    c.setFillColor(CREAM); c.roundRect(bx,by,bw,bh,10,fill=1,stroke=0)
    c.setFillColor(CHERRY); c.setFont("Helvetica-Bold",10.5); c.drawString(bx+20,by+bh-26,"KEY FEASIBILITY ANSWER")
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold",11); c.drawString(bx+20,by+bh-48,"Data sources:")
    c.setFillColor(NAVY2); c.setFont("Helvetica",10)
    c.drawString(bx+120,by+bh-48,"LIVE free APIs (CelesTrak + Space-Track CDMs) AND a static")
    c.drawString(bx+20,by+bh-64,"official answer key (TraCSS) to prove accuracy — use both.")
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold",11); c.drawString(bx+20,by+bh-88,"The engineering:")
    c.setFillColor(NAVY2); c.setFont("Helvetica",10)
    c.drawString(bx+118,by+bh-88,"coarse pre-filter sieve (avoids O(N²) blow-up) +")
    c.drawString(bx+20,by+bh-104,"Skyfield/SGP4 propagation + LLM explainer + CesiumJS 3D globe.")
    c.setFillColor(GREY); c.setFont("Helvetica",9.5)
    c.drawString(bx+20,by+22,"Validate screener against the TraCSS answer key — that gives you a real, defensible recall metric.")
    c.setFillColor(CREAM); c.setFont("Helvetica",9)
    c.drawCentredString(W/2,66,"Prepared by Claude (Opus 4.8)  ·  11 June 2026  ·  Deeply researched against the live web")
    c.restoreState()

def later(c,doc):
    c.saveState(); c.setFillColor(CHERRY); c.rect(0,H-6,W,6,fill=1,stroke=0)
    c.setFillColor(GREY); c.setFont("Helvetica",8); c.drawString(1.6*cm,H-22,"FAR AWAY 2026  -  Final 3 Deep-Dive")
    c.drawRightString(W-1.6*cm,H-22,f"Page {doc.page}")
    c.setStrokeColor(GRIDE); c.setLineWidth(0.5); c.line(1.6*cm,24,W-1.6*cm,24)
    c.setFillColor(GREY); c.setFont("Helvetica",8); c.drawString(1.6*cm,14,"Confidential draft for team review"); c.drawRightString(W-1.6*cm,14,"claude-opus-4-8")
    c.restoreState()

# ----------------------------------------------------------------------------- story
story=[PageBreak(),P("OrbitGuard — project snapshot",h1),Spacer(1,4)]
snap=[[P('<font color="white"><b>What it is</b></font>',small),
       P('<font color="white"><b>Data sources</b></font>',small),P('<font color="white"><b>Honest metric</b></font>',small),
       P('<font color="white"><b>Top risk</b></font>',small),P('<font color="white"><b>Rating</b></font>',small)]]
snap+= [
 [P("Explainable collision screening + 3D globe for small operators",small),P("Live CelesTrak/Space-Track + TraCSS key",small),P("Recall vs official TraCSS key",small),P("Orbital math; Pc needs covariance",small),P("<b>8.2</b>",small)]]
snt=Table(snap,colWidths=[130,108,96,100,FW-434])
snt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,PANEL]),
   ("GRID",(0,0),(-1,-1),0.5,GRIDE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
   ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("ALIGN",(4,0),(4,-1),"CENTER")]))
story+=[snt,Spacer(1,8),P("The deep-dive below covers: the key feasibility question answered, the end-to-end pipeline, a "
   "step-by-step build plan, the realistic result you can claim (with citations), and an honest &#8216;what can break&#8217; list.",small)]

for pr in PROJ:
    story.append(PageBreak())
    badge=Table([[P(f'<font color="white"><b>{pr["name"]}</b></font><br/><font color="{CREAM.hexval()}" size=8.5>{pr["tag"]}</font>',
                ParagraphStyle("bn",parent=body,fontSize=16,textColor=colors.white,leading=18)),
                P(f'<font color="white" size=8>CLAUDE&#8217;S RATING</font><br/><font color="white"><b>{pr["overall"]:.1f}</b></font><font color="white" size=10> / 10</font>',
                ParagraphStyle("br",parent=body,fontSize=25,textColor=colors.white,alignment=TA_CENTER,leading=26))]],colWidths=[FW-118,118])
    badge.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),NAVY),("BACKGROUND",(1,0),(1,0),CHERRY),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(1,0),(1,0),"CENTER"),("LEFTPADDING",(0,0),(0,0),12),("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9)]))
    story+=[badge,Spacer(1,3),P(pr["oneliner"],small),Spacer(1,7),qbox(pr["qtitle"],pr["q"]),Spacer(1,8),
        heading("WHAT YOU ARE BUILDING"),Spacer(1,3),P(pr["build"]),Spacer(1,7),
        heading("END-TO-END PIPELINE (start to finish)"),Spacer(1,3),pipeline(pr["pipe"]),Spacer(1,7),
        heading("STEP-BY-STEP BUILD"),Spacer(1,3),steps_table(pr["steps"]),Spacer(1,7),
        L("REALISTIC RESULT YOU CAN CLAIM",GREEN,pr["metric"]),Spacer(1,7),
        risk_panel(pr["risks"]),Spacer(1,8),
        P(f'<font color="{NAVY.hexval()}"><b>RATINGS</b></font>'),Spacer(1,3),ratings_grid(pr["scores"]),Spacer(1,7),
        proscons(pr["pros"],pr["cons"]),Spacer(1,7),
        L("MVP - lock this demo path",NAVY,pr["mvp"]),Spacer(1,4),
        L("STRETCH",GREY,pr["stretch"]),Spacer(1,4),
        L("TEAM (5 lanes)",CHERRY," &#160; · &#160; ".join(pr["team"])),Spacer(1,4),
        L("STACK",GREY,pr["stack"])]

# final page
story.append(PageBreak()); story.append(P("OrbitGuard — scores at a glance",h1)); story.append(Spacer(1,5))
axes=["Data ready now","Demo wow","Honest metric","Low build risk","Novelty","Sellable / product","Recruiter pull"]
vals={"OrbitGuard":[4,5,4,3,4,2,4]}
hd=[P('<font color="white"><b>Axis</b></font>',small),P('<font color="white"><b>OrbitGuard</b></font>',small)]
mrows=[hd]; mstyle=[("BACKGROUND",(0,0),(-1,0),NAVY),("GRID",(0,0),(-1,-1),0.5,colors.white),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
   ("ALIGN",(1,0),(-1,-1),"CENTER"),("LEFTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]
for ai,ax in enumerate(axes,start=1):
    s=vals["OrbitGuard"][ai-1]; mrows.append([P(ax,small),P(f'<font color="white"><b>{s:g}</b></font>',small)]); mstyle.append(("BACKGROUND",(1,ai),(1,ai),bd(s)))
mrows.append([P("<b>Overall</b>",small),P('<font color="white"><b>8.2</b></font>',small)])
mstyle.extend([("BACKGROUND",(1,len(axes)+1),(1,len(axes)+1),bd(8.2,10)),("BACKGROUND",(0,len(axes)+1),(0,len(axes)+1),PANEL)])
mt=Table(mrows,colWidths=[FW-120,120]); mt.setStyle(TableStyle(mstyle))
story+=[mt,Spacer(1,10)]
rec=Table([[P(f'<font color="white"><b>CHOSEN PROJECT: OrbitGuard</b>  —  Space &amp; Aerospace</font><br/>'
   f'<font color="{CREAM.hexval()}" size=9>Maximum judge wow (live 3D globe of real orbits + collision alerts). '
   f'Standout resume line that is hard to fake (aerospace + ML + visualisation). '
   f'100 percent software + 100 percent public data. Strong India angle (Pixxel / GalaxEye / ISRO). '
   f'The TraCSS answer key (Jan 2026) gives a real, defensible recall metric — not a toy globe.</font>',
   ParagraphStyle("rec",parent=body,textColor=colors.white,fontSize=11.5,leading=15.5))]],colWidths=[FW])
rec.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GREEN),("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),11)]))
story+=[rec,Spacer(1,10),heading("LOCK THESE ON DAY ZERO — DO THESE FIRST"),Spacer(1,5),bullets([
   "<b>1.</b> REQUEST TraCSS dataset access NOW (Google account at the Office of Space Commerce portal) — files are on Google Drive and access is not instant.",
   "<b>2.</b> Create a free Space-Track.org account to get CDM covariance data.",
   "<b>3.</b> Cache a CelesTrak GP TLE/OMM snapshot locally — do NOT hammer the API (100 MB+/day; IP firewall risk).",
   "<b>4.</b> Choose ONE primary satellite to anchor the MVP (e.g. a Pixxel or GalaxEye satellite, or ISRO TechSat).",
   "<b>5.</b> Confirm your team&#8217;s five lanes: propagation / screening+validation / risk+LLM / 3D globe / backend.",
   "<b>6.</b> Use OMM / JSON format for new objects (NORAD 5-digit IDs run out ~12 July 2026)."]),
   Spacer(1,12),
   P(f'<font color="{NAVY.hexval()}"><b>Key sources (June 2026):</b></font> '
     'CelesTrak GP (TLE / OMM, free, 2-hour refresh); Space-Track.org (CDMs, free account); '
     'Skyfield (Python SGP4 propagator); TraCSS &#8216;Dataset for Conjunction Assessment Verification&#8217; '
     '(Office of Space Commerce, Jan 2026, spherical + SFSH volume answer keys); '
     'Cesium ion / CesiumJS (3D globe, free tier); Three.js; Next.js; claude-opus-4-8 (LLM explainer).',small)]

doc=SimpleDocTemplate(OUT,pagesize=A4,leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=2.0*cm,bottomMargin=1.8*cm,
   title="FAR AWAY 2026 - Final 3 Deep-Dive",author="Claude (Opus 4.8)")
doc.build(story,onFirstPage=cover,onLaterPages=later); print("OK ->",OUT)
