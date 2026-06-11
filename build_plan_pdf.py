# -*- coding: utf-8 -*-
"""Renders IMPLEMENTATION_PLAN.md -> IMPLEMENTATION_PLAN.pdf (reportlab).
Regenerate any time with:  python build_plan_pdf.py
"""
import re, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, XPreformatted, HRFlowable, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

SRC = "IMPLEMENTATION_PLAN.md"
OUT = "IMPLEMENTATION_PLAN.pdf"
W, H = A4
FW = W - 3.2*cm

NAVY = colors.HexColor("#1B2A4A"); NAVY2 = colors.HexColor("#28304A")
CHERRY = colors.HexColor("#E14B5A"); CREAM = colors.HexColor("#F6F2E9")
GREY = colors.HexColor("#6B7280"); GRIDE = colors.HexColor("#E3E6EA")
PANEL = colors.HexColor("#F4F6F9"); CODEBG = colors.HexColor("#F0F2F5")
LINK = colors.HexColor("#1A5FB4")

# ---------------------------------------------------------------- fonts
FDIR = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Body", os.path.join(FDIR, "arial.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", os.path.join(FDIR, "arialbd.ttf")))
pdfmetrics.registerFont(TTFont("Body-Italic", os.path.join(FDIR, "ariali.ttf")))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", os.path.join(FDIR, "arialbi.ttf")))
pdfmetrics.registerFont(TTFont("Mono", os.path.join(FDIR, "consola.ttf")))
pdfmetrics.registerFont(TTFont("Mono-Bold", os.path.join(FDIR, "consolab.ttf")))
addMapping("Body", 0, 0, "Body"); addMapping("Body", 1, 0, "Body-Bold")
addMapping("Body", 0, 1, "Body-Italic"); addMapping("Body", 1, 1, "Body-BoldItalic")

# ---------------------------------------------------------------- styles
body = ParagraphStyle("body", fontName="Body", fontSize=9.2, leading=13.2,
                      textColor=NAVY2, spaceAfter=5)
small = ParagraphStyle("small", parent=body, fontSize=7.4, leading=10.0, textColor=NAVY2,
                       spaceAfter=0)
h1 = ParagraphStyle("h1", parent=body, fontName="Body-Bold", fontSize=15.5, leading=19,
                    textColor=NAVY, spaceBefore=14, spaceAfter=4)
h2 = ParagraphStyle("h2", parent=body, fontName="Body-Bold", fontSize=12.5, leading=16,
                    textColor=NAVY, spaceBefore=12, spaceAfter=4)
h3 = ParagraphStyle("h3", parent=body, fontName="Body-Bold", fontSize=10.5, leading=14,
                    textColor=CHERRY, spaceBefore=9, spaceAfter=3)
h4 = ParagraphStyle("h4", parent=body, fontName="Body-BoldItalic", fontSize=9.5, leading=13,
                    textColor=NAVY, spaceBefore=7, spaceAfter=3)
codeS = ParagraphStyle("code", fontName="Mono", fontSize=7.2, leading=9.4, textColor=NAVY2)
quoteS = ParagraphStyle("quote", parent=body, fontName="Body-Italic", leftIndent=10,
                        textColor=NAVY2)
bullS = ParagraphStyle("bull", parent=body, leftIndent=14, bulletIndent=3, spaceAfter=3)
numS = ParagraphStyle("num", parent=body, leftIndent=18, firstLineIndent=-12, spaceAfter=3)

SUP = {"⁻": "-", "⁰": "0", "¹": "1", "²": "2", "³": "3",
       "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8",
       "⁹": "9"}
SUB = {"₁": "1", "₂": "2", "₀": "0", "₃": "3"}

def norm(t, in_code=False):
    t = t.replace("⇒", "=>" if in_code else "→")   # double arrow
    t = t.replace("⊥", "perp" if in_code else "perpendicular to")
    t = t.replace("≪", "<<")
    if in_code:
        for k, v in SUP.items(): t = t.replace(k, "^" + v)
        for k, v in SUB.items(): t = t.replace(k, "_" + v)
    else:
        t = re.sub("[" + "".join(SUP) + "]+",
                   lambda m: "<super>" + "".join(SUP[c] for c in m.group(0)) + "</super>", t)
        t = re.sub("[" + "".join(SUB) + "]+",
                   lambda m: "<sub>" + "".join(SUB[c] for c in m.group(0)) + "</sub>", t)
    return t

def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = norm(t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
               r'<a href="\2" color="#1A5FB4"><u>\1</u></a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r'<font name="Mono" size="8">\1</font>', t)
    # bare URLs (bibliography)
    t = re.sub(r"(?<![\"=>])(https?://[^\s<]+)",
               r'<a href="\1" color="#1A5FB4"><u>\1</u></a>', t)
    return t

def code_panel(lines):
    txt = "\n".join(norm(l, in_code=True).replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;") for l in lines)
    pre = XPreformatted(txt, codeS)
    t = Table([[pre]], colWidths=[FW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODEBG),
                           ("BOX", (0, 0), (-1, -1), 0.6, GRIDE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t

def md_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{3,}:?", c or "---") for c in r)]
    ncol = max(len(r) for r in cells)
    for r in cells: r += [""] * (ncol - len(r))
    weights = [max(min(len(r[i]), 60) for r in cells) or 1 for i in range(ncol)]
    weights = [max(w, 6) for w in (max((min(len(r[i]), 60)) for r in cells) for i in range(ncol))]
    tot = sum(weights)
    widths = [FW * w / tot for w in weights]
    data = []
    hdr = ParagraphStyle("th", parent=small, fontName="Body-Bold", textColor=colors.white)
    for ri, r in enumerate(cells):
        data.append([Paragraph(inline(c), hdr if ri == 0 else small) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), NAVY),
          ("GRID", (0, 0), (-1, -1), 0.5, GRIDE),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
          ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL])]
    t.setStyle(TableStyle(st))
    return t

# ---------------------------------------------------------------- parse
with open(SRC, encoding="utf-8") as f:
    lines = f.read().splitlines()

story = [PageBreak()]
i = 0
first_h1_done = False
while i < len(lines):
    ln = lines[i]
    s = ln.strip()
    if not s:
        i += 1; continue
    if s.startswith("```"):
        j = i + 1; block = []
        while j < len(lines) and not lines[j].strip().startswith("```"):
            block.append(lines[j]); j += 1
        story.append(Spacer(1, 3)); story.append(code_panel(block)); story.append(Spacer(1, 5))
        i = j + 1; continue
    if s.startswith("|"):
        j = i; rows = []
        while j < len(lines) and lines[j].strip().startswith("|"):
            rows.append(lines[j]); j += 1
        story.append(Spacer(1, 3)); story.append(md_table(rows)); story.append(Spacer(1, 6))
        i = j; continue
    if re.fullmatch(r"-{3,}", s):
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=0.8, color=GRIDE))
        story.append(Spacer(1, 4)); i += 1; continue
    m = re.match(r"(#{1,4})\s+(.*)", s)
    if m:
        lvl, txt = len(m.group(1)), m.group(2)
        if lvl == 1:
            if first_h1_done: story.append(PageBreak())
            first_h1_done = True
            story.append(Paragraph(inline(txt), h1))
            story.append(HRFlowable(width="100%", thickness=1.4, color=CHERRY))
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(inline(txt), {2: h2, 3: h3, 4: h4}[lvl]))
        i += 1; continue
    if s.startswith(">"):
        j = i; q = []
        while j < len(lines) and lines[j].strip().startswith(">"):
            q.append(lines[j].strip().lstrip(">").strip()); j += 1
        para = Paragraph(inline(" ".join(q)), quoteS)
        t = Table([[para]], colWidths=[FW])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CREAM),
                               ("LINEBEFORE", (0, 0), (0, -1), 3, CHERRY),
                               ("LEFTPADDING", (0, 0), (-1, -1), 10),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                               ("TOPPADDING", (0, 0), (-1, -1), 6),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story.append(Spacer(1, 3)); story.append(t); story.append(Spacer(1, 5))
        i = j; continue
    mb = re.match(r"[-*]\s+(.*)", s)
    mn = re.match(r"(\d+)\.\s+(.*)", s)
    if mb or mn:
        j = i + 1; item = (mb.group(1) if mb else mn.group(2))
        while j < len(lines):
            nxt = lines[j]
            if (not nxt.strip() or re.match(r"\s*[-*]\s+", nxt) or
                    re.match(r"\s*\d+\.\s+", nxt) or nxt.strip().startswith(("#", "|", "```", ">"))
                    or re.fullmatch(r"-{3,}", nxt.strip())):
                break
            item += " " + nxt.strip(); j += 1
        if mb:
            story.append(Paragraph(inline(item), bullS,
                                   bulletText='<font color="#E14B5A">•</font>'))
        else:
            story.append(Paragraph("<b>%s.</b>  %s" % (mn.group(1), inline(item)), numS))
        i = j; continue
    # paragraph: join wrapped lines
    j = i + 1; para = s
    while j < len(lines):
        nxt = lines[j]
        if (not nxt.strip() or nxt.strip().startswith(("#", "|", "```", ">", "- ", "* "))
                or re.match(r"\d+\.\s", nxt.strip()) or re.fullmatch(r"-{3,}", nxt.strip())):
            break
        para += " " + nxt.strip(); j += 1
    story.append(Paragraph(inline(para), body))
    i = j

# ---------------------------------------------------------------- furniture
def cover(c, doc):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(CHERRY); c.rect(0, H-150, W, 6, fill=1, stroke=0)
    c.setFillColor(CHERRY); c.setFont("Body-Bold", 12)
    c.drawCentredString(W/2, H-110, "F A R   A W A Y   ·   2 0 2 6")
    c.setFillColor(colors.white); c.setFont("Body-Bold", 34)
    c.drawCentredString(W/2, H-210, "OrbitGuard")
    c.setFont("Body-Bold", 19)
    c.drawCentredString(W/2, H-245, "Implementation Plan")
    c.setFillColor(CREAM); c.setFont("Body", 12)
    c.drawCentredString(W/2, H-278, "Free, explainable, validated conjunction screening for small operators")
    c.setFont("Body-Italic", 10.5)
    c.drawCentredString(W/2, H-298, "Empty repo → polished, TraCSS-validated, demoable product")
    bx, bw, bh = 58, W-116, 168; by = H-510
    c.setFillColor(CREAM); c.roundRect(bx, by, bw, bh, 10, fill=1, stroke=0)
    c.setFillColor(CHERRY); c.setFont("Body-Bold", 10.5)
    c.drawString(bx+20, by+bh-26, "WHAT THIS PLAN COMMITS TO")
    c.setFillColor(NAVY2); c.setFont("Body", 9.8)
    for k, txt in enumerate([
        "Screening sieve with a provable no-miss guarantee (padded coarse grid + KD-tree + Brent TCA)",
        "Real 2D-Pc (Foster + Chan), unit-tested against NASA CARA's published test cases",
        "PcMax worst-case bound when covariance is absent — TLE data proves safety, never danger",
        "Validation scorecard vs the official U.S. TraCSS answer key (recall / precision, published)",
        "Groq-narrated explanations under a strict narrate-only contract ($0 LLM budget)",
        "Live CesiumJS 3D globe + Encounter Inspector with the covariance-ellipse money shot"]):
        c.drawString(bx+20, by+bh-50-k*19, "•  " + txt)
    c.setFillColor(GREY); c.setFont("Body", 8.5)
    c.drawString(bx+20, by+12, "Sections: architecture · data · algorithms (math) · validation · phases · team · demo · risks · references")
    px = 60
    for p in ["$0 budget", "Software-only", "Team of 4-5", "Resume-first"]:
        pw = 8 + c.stringWidth(p, "Body-Bold", 10) + 8
        c.setFillColor(colors.HexColor("#2C3B5C")); c.roundRect(px, 118, pw, 24, 6, fill=1, stroke=0)
        c.setFillColor(CREAM); c.setFont("Body-Bold", 10); c.drawString(px+8, 125, p)
        px += pw + 10
    c.setFillColor(CREAM); c.setFont("Body", 9)
    c.drawCentredString(W/2, 70, "Prepared by Fable 5 (lead architect)  ·  12 June 2026  ·  regenerate: python build_plan_pdf.py")
    c.restoreState()

def later(c, doc):
    c.saveState()
    c.setFillColor(CHERRY); c.rect(0, H-6, W, 6, fill=1, stroke=0)
    c.setFillColor(GREY); c.setFont("Body", 8)
    c.drawString(1.6*cm, H-22, "OrbitGuard  —  Implementation Plan")
    c.drawRightString(W-1.6*cm, H-22, "Page %d" % doc.page)
    c.setStrokeColor(GRIDE); c.setLineWidth(0.5); c.line(1.6*cm, 24, W-1.6*cm, 24)
    c.setFillColor(GREY); c.setFont("Body", 8)
    c.drawString(1.6*cm, 14, "FAR AWAY 2026  ·  Space & Aerospace")
    c.drawRightString(W-1.6*cm, 14, "fable-5")
    c.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=1.6*cm, rightMargin=1.6*cm,
                        topMargin=1.9*cm, bottomMargin=1.7*cm,
                        title="OrbitGuard - Implementation Plan", author="Fable 5")
doc.build(story, onFirstPage=cover, onLaterPages=later)
print("OK ->", OUT)
