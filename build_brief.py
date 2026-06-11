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
OUT = "FAR_AWAY_2026_OrbitGuard_Brief.pdf"
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
 dict(rank="CHOSEN PROJECT  ·  #1", name="OrbitGuard", theme="Space and Aerospace", overall=8.0,
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
    c.drawCentredString(W/2,H-280,"Space & Aerospace  ·  FAR AWAY 2026")
    c.setFont("Helvetica-Oblique",10.5)
    c.drawCentredString(W/2,H-302,"Optimised for: builder-first hackathon scoring + maximum resume / recruiter pull")
    bx,bw,bh=60,W-120,158; by=H-493
    c.setFillColor(CREAM); c.roundRect(bx,by,bw,bh,10,fill=1,stroke=0)
    c.setFillColor(CHERRY); c.setFont("Helvetica-Bold",11)
    c.drawString(bx+22,by+bh-30,"CHOSEN PROJECT")
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold",18); c.drawString(bx+22,by+bh-58,"OrbitGuard")
    c.setFont("Helvetica",11.5); c.setFillColor(NAVY2); c.drawString(bx+152,by+bh-57,"explainable satellite collision screening + 3D globe")
    c.setFillColor(NAVY2); c.setFont("Helvetica",9.5)
    c.drawString(bx+22,by+bh-84,"Maximum judge wow (live 3D globe). Standout resume line. 100% software + public data.")
    c.drawString(bx+22,by+bh-99,"Validated against the official TraCSS answer key (Jan 2026) — real, defensible recall numbers.")
    c.setFillColor(CHERRY); c.setFont("Helvetica-Bold",30); c.drawRightString(bx+bw-22,by+22,"8.0 / 10")
    c.setFillColor(GREY); c.setFont("Helvetica",8.5); c.drawString(bx+22,by+18,"Claude's overall rating")
    px=60
    for p in ["Software-only","Resume-first","Team of 4-5"]:
        pw=8+c.stringWidth(p,"Helvetica-Bold",10)+8
        c.setFillColor(colors.HexColor("#2C3B5C")); c.roundRect(px,118,pw,24,6,fill=1,stroke=0)
        c.setFillColor(CREAM); c.setFont("Helvetica-Bold",10); c.drawString(px+8,125,p); px+=pw+10
    c.setFillColor(CREAM); c.setFont("Helvetica",9)
    c.drawCentredString(W/2,70,"Prepared by Claude (Opus 4.8)  ·  11 June 2026  ·  OrbitGuard — Space & Aerospace")
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
story+=[P("OrbitGuard — project brief",h1),
  P("This brief covers OrbitGuard, the chosen project for FAR AWAY 2026, researched against the live web "
    "in June 2026. The project is rated by Claude on six axes (1-5), given an overall out of 10, and carries an "
    "explicit STAR NOVELTY — the specific edge that makes it stand out. Theme: Space &amp; Aerospace.",body),
  Spacer(1,6),
  P('<font color="%s"><b>Why OrbitGuard:</b></font>  maximum judge wow (live 3D globe of real orbits + collision alerts), '
    'standout resume line (aerospace + ML + visualisation), 100 percent software + 100 percent public data, '
    'strong India angle (Pixxel / GalaxEye / ISRO), and the TraCSS answer key (Jan 2026) gives real, '
    'defensible accuracy numbers — not a toy globe.'%CHERRY.hexval(),body),
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
story+=[legend,Spacer(1,12),P("OrbitGuard at a glance",h1)]

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

story+=[Spacer(1,12),heading("THE DECISION"),Spacer(1,6),bullets([
  "<b>Chosen project:</b>  <b>OrbitGuard</b>  —  Space &amp; Aerospace.",
  "<b>Why:</b>  maximum judge wow (live 3D globe + collision alerts), unusual resume line, 100% software + public data.",
  "<b>Your edge:</b>  explainability + small/Indian operators + TraCSS validation — not raw screening (SpaceX Stargaze does that).",
  "<b>Day-zero:</b>  request TraCSS access, create Space-Track account, cache CelesTrak TLEs, pick one primary satellite."])]

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
story.append(P("OrbitGuard — build commitment",h1)); story.append(Spacer(1,4))
rec=Table([[Paragraph('<font color="white"><b>BUILD THIS:&#160; OrbitGuard</b> — Space &amp; Aerospace.</font>'
   '<br/><font color="%s" size=9>Free, explainable satellite collision-risk screening + 3D globe for small operators, '
   'validated against the official TraCSS answer key (Jan 2026). '
   'Maximum judge wow: a live 3D globe of real orbits with collision alerts. '
   'Standout, hard-to-fake resume line (aerospace + ML + visualisation). '
   '100 percent software + 100 percent public data. Strong India angle (Pixxel / GalaxEye / ISRO).'
   '</font>'%CREAM.hexval(),ParagraphStyle("rec",parent=body,textColor=colors.white,fontSize=12,leading=16))]],colWidths=[FW])
rec.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GREEN),("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
   ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),11)]))
story+=[rec,Spacer(1,12),heading("DAY-ZERO CHECKLIST — DO BEFORE WRITING ANY CODE"),Spacer(1,6),bullets([
  "<b>1.</b> Request TraCSS dataset access (Google account, Office of Space Commerce) — NOT instant, do this first.",
  "<b>2.</b> Create a free Space-Track.org account to get CDM covariance data.",
  "<b>3.</b> Cache a CelesTrak GP TLE/OMM snapshot locally (do NOT hammer the API — rate-limit risk).",
  "<b>4.</b> Choose one primary satellite to anchor the MVP (e.g. Pixxel Firefly, GalaxEye SAR-1, or ISRO TechSat).",
  "<b>5.</b> Assign the five team lanes: propagation / screening+validation / risk+LLM / 3D globe / backend.",
  "<b>6.</b> Use OMM / JSON format for new objects (NORAD 5-digit IDs run out ~12 July 2026)."])]
story+=[Spacer(1,12),
  P('<font color="'+NAVY.hexval()+'"><b>Key sources (June 2026):</b></font> '
    'CelesTrak GP (TLE / OMM, free, 2-hour refresh); Space-Track.org (CDMs, free account); '
    'Skyfield (Python SGP4); TraCSS &#8216;Dataset for Conjunction Assessment Verification&#8217; '
    '(Office of Space Commerce, Jan 2026, spherical + SFSH volume answer keys); '
    'Cesium ion / CesiumJS (3D globe, free tier); Three.js; Next.js; claude-opus-4-8 (LLM explainer).',small)]

doc=SimpleDocTemplate(OUT,pagesize=A4,leftMargin=1.6*cm,rightMargin=1.6*cm,topMargin=2.0*cm,bottomMargin=1.8*cm,
   title="FAR AWAY 2026 - Problem-Statement Decision Brief",author="Claude (Opus 4.8)")
doc.build(story,onFirstPage=cover,onLaterPages=later)
print("OK ->",OUT)
