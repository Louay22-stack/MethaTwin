"""
Phase 4 - Builds the final report 07_report/MethaTwin_Final_Report.pdf.

Numbers in the result tables are read from the saved model outputs
(04_models_and_simulations/*), so the report cannot drift from the results.
Narrative numbers come from LOG.md (each step's validated results).

Run from the project root:  python 05_code/phase4_report_pdf.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / "04_models_and_simulations"
FIGS = ROOT / "06_figures"
OUT = ROOT / "07_report" / "MethaTwin_Final_Report.pdf"

INK, MUTED, BLUE, LIGHT, PALE, RULE = "#0b0b0b", "#52514e", "#2a78d6", "#cde2fb", "#eef5fd", "#d9d8d3"
GREEN, AMBER, RED = "#1b8a5a", "#b26a00", "#b3261e"

# ------------------------------------------------------------------ fonts ---
TTF = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
for name, f in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"),
                ("DV-I", "DejaVuSans-Oblique.ttf"), ("DV-BI", "DejaVuSans-BoldOblique.ttf"),
                ("DVM", "DejaVuSansMono.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(TTF / f)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

# ----------------------------------------------------------------- styles ---
body = ParagraphStyle("body", fontName="DV", fontSize=9.2, leading=13.2, alignment=TA_JUSTIFY,
                      spaceAfter=5, textColor=colors.HexColor(INK))
bullet = ParagraphStyle("bullet", parent=body, leftIndent=12, bulletIndent=2, spaceAfter=2.5)
h1 = ParagraphStyle("h1", fontName="DV-B", fontSize=15, leading=19, textColor=colors.HexColor(INK),
                    spaceBefore=4, spaceAfter=8)
h2 = ParagraphStyle("h2", fontName="DV-B", fontSize=11, leading=14, textColor=colors.HexColor(BLUE),
                    spaceBefore=9, spaceAfter=4)
h3 = ParagraphStyle("h3", fontName="DV-B", fontSize=9.4, leading=12.5, textColor=colors.HexColor(INK),
                    spaceBefore=5, spaceAfter=2)
cap = ParagraphStyle("cap", parent=body, fontSize=7.8, leading=10.2, textColor=colors.HexColor(MUTED),
                     alignment=TA_LEFT, spaceBefore=2, spaceAfter=9)
cell = ParagraphStyle("cell", fontName="DV", fontSize=7.7, leading=9.8, textColor=colors.HexColor(INK))
cellb = ParagraphStyle("cellb", parent=cell, fontName="DV-B")
ref = ParagraphStyle("ref", parent=body, fontSize=7.9, leading=10.4, alignment=TA_LEFT,
                     leftIndent=26, firstLineIndent=-26, spaceAfter=3.2)
mono = ParagraphStyle("mono", fontName="DVM", fontSize=7.4, leading=9.6, textColor=colors.HexColor(INK))
W = A4[0] - 4.0 * cm


def P(t, s=body):
    return Paragraph(t, s)


def B(items):
    return [Paragraph(t, bullet, bulletText="•") for t in items]


def table(rows, widths, header=True, zebra=False, bold_first_col=False, status_col=None):
    data = []
    for i, r in enumerate(rows):
        line = []
        for j, c in enumerate(r):
            st = cellb if (header and i == 0) or (bold_first_col and j == 0) else cell
            line.append(P(str(c), st))
        data.append(line)
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    sty = [("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor(RULE)),
           ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
           ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5)]
    if header:
        sty += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PALE)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(BLUE))]
    if zebra:
        for i in range(2 if header else 1, len(rows), 2):
            sty.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f7f7f5")))
    t.setStyle(TableStyle(sty))
    return t


def fig(path, caption, width=W):
    from PIL import Image as PI
    w, h = PI.open(path).size
    return KeepTogether([Image(str(path), width=width, height=width * h / w), P(caption, cap)])


def box(flowables, bg=PALE, border=BLUE):
    t = Table([[flowables]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                           ("LINEBEFORE", (0, 0), (0, -1), 2.2, colors.HexColor(border)),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def status(s):
    c = {"Met": GREEN, "Partly met": AMBER, "Not met": RED}[s]
    return f'<font color="{c}"><b>{s}</b></font>'


# --------------------------------------------------------------- document ---
class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2.0 * cm,
                         bottomMargin=1.9 * cm, **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("title", [fr], onPage=self._title_page),
                               PageTemplate("body", [fr], onPageEnd=self._body_page)])
        self._sec = ""

    def handle_documentBegin(self):
        self._sec = ""
        super().handle_documentBegin()

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name == "h1toc":
            self._sec = "Contents"
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            lvl = 0 if f.style.name == "h1" else 1
            txt = f.getPlainText()
            key = f"k{id(f)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(txt, key, level=lvl, closed=lvl > 0)
            if lvl == 0:
                self._sec = txt
            self.notify("TOCEntry", (lvl, txt, self.page, key))

    @staticmethod
    def _title_page(c, d):
        c.saveState()
        c.setFillColor(colors.HexColor(BLUE))
        c.rect(0, A4[1] - 0.9 * cm, A4[0], 0.9 * cm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(MUTED))
        c.setFont("DV", 7.5)
        c.drawString(2 * cm, 1.1 * cm, "All data public; all sources cited. Code, data and figures: "
                                       "MethaTwin git repository (05_code, 03_data, 06_figures).")
        c.restoreState()

    def _body_page(self, c, d):
        c.saveState()
        c.setStrokeColor(colors.HexColor(RULE))
        c.setLineWidth(0.5)
        c.line(2 * cm, A4[1] - 1.45 * cm, A4[0] - 2 * cm, A4[1] - 1.45 * cm)
        c.setFont("DV", 7.3)
        c.setFillColor(colors.HexColor(MUTED))
        c.drawString(2 * cm, A4[1] - 1.3 * cm, "MethaTwin · ML-accelerated digital twin of an agricultural biomethane plant")
        c.drawRightString(A4[0] - 2 * cm, A4[1] - 1.3 * cm, self._sec[:70])
        c.drawString(2 * cm, 1.1 * cm, "L. Ouhibi · Final report · v1.0 · 21 November 2026")
        c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"{d.page}")
        c.restoreState()


# ------------------------------------------------------------------- data ---
def load():
    j = lambda p: json.loads((M / p).read_text(encoding="utf-8"))
    return {"tea": j("step7_tea/tea_base.json"), "opt": j("step7_tea/optimisation.json"),
            "unc": j("step7_tea/uncertainty.json"), "rob": j("step7_tea/robust_design.json"),
            "speed": j("step6_surrogate/speed.json"), "bsm2": j("step4_adm1/bsm2_validation_summary.json"),
            "metrics": pd.read_csv(M / "step6_surrogate/metrics.csv"),
            "over": pd.read_csv(M / "step6_surrogate/overfitting_check.csv"),
            "tornado": pd.read_csv(M / "step7_tea/tornado.csv")}


# ---------------------------------------------------------------- content ---
def title_page(s, D):
    s.append(Spacer(1, 2.2 * cm))
    s.append(P("FINAL REPORT · PORTFOLIO PROJECT", ParagraphStyle("k", fontName="DV-B", fontSize=8.5,
                                                              textColor=colors.HexColor(BLUE), leading=11)))
    s.append(Spacer(1, 0.25 * cm))
    s.append(P("MethaTwin", ParagraphStyle("t", fontName="DV-B", fontSize=34, leading=40,
                                           textColor=colors.HexColor(INK))))
    s.append(P("An ML-accelerated digital twin of an agricultural biomethane plant, from digester to grid",
               ParagraphStyle("st", fontName="DV", fontSize=15, leading=20, textColor=colors.HexColor(INK),
                              spaceAfter=14)))
    s.append(P("ADM1 co-digestion model · DWSIM water-scrubbing flowsheet automated from Python · "
               "2,000-run design of experiments · ML surrogates · verified optimisation · "
               "techno-economics under uncertainty",
               ParagraphStyle("s2", parent=body, fontSize=9.5, textColor=colors.HexColor(MUTED),
                              alignment=TA_LEFT, spaceAfter=18)))
    s.append(Image(str(FIGS / "fig02_concept_flow.png"), width=W, height=W * 638 / 2200))
    s.append(Spacer(1, 0.6 * cm))
    o = D["opt"]["200"]["final"]["simulation"]
    kp = [["Validated digester model", "36/36 BSM2 benchmark values within 1 % (max error 1.8×10⁻⁵ %)"],
          ["Upgrading to grid quality", "CO₂ 0.46 %, CH₄ slip 0.43 %, 0.176 kWh/Nm³ raw gas, mass closure 0.001 %"],
          ["ML surrogates", "test R² 0.992–0.999, train–test gap ≤ 0.0044, ~2,300× faster than simulation"],
          ["Economics (CRE-anchored)", f"200 Nm³/h optimum {o['LCOE_EUR_MWh']:.1f} €/MWh, NPV "
                                       f"{o['NPV_EUR'] / 1e6:+.2f} M€; break-even ≈ 180 Nm³/h"],
          ["Risk", "Monte Carlo P50 166 €/MWh, P(NPV > 0) 13 %; robust design +8.4 €/MWh"]]
    s.append(table([["Headline results", ""]] + kp, [4.6, 12.4], header=True, bold_first_col=True))
    s.append(Spacer(1, 1.4 * cm))
    s.append(P("<b>Louay Ouhibi</b><br/>Industrial Biology Engineer, INSAT (Tunisia)<br/>"
               "21 November 2026 · version 1.0",
               ParagraphStyle("au", parent=body, fontSize=9.5, leading=13.5, alignment=TA_LEFT)))
    s.append(NextPageTemplate("body"))
    s.append(PageBreak())


def exec_summary(s, D):
    s.append(P("Executive summary", h1))
    o = D["opt"]
    s.append(P(
        "<b>Problem.</b> Biomethane is the fastest-growing renewable gas in Europe, yet cost is its main "
        "brake: the median French plant produces at about 130 €/MWh [S6, S17] and new capacity added in "
        "France fell 40 % in 2025 [S1]. Designing a plant means coupling biology (how much methane a feed "
        "blend yields, and whether the digester stays stable), separation (upgrading biogas to grid "
        "quality) and economics. These are usually studied separately and with slow simulators."))
    s.append(P(
        "<b>What was built.</b> MethaTwin is an open-source digital twin of a ~200 Nm³/h agricultural "
        "plant (cattle slurry, cover-crop silage and maize silage). It chains (1) a literature-based feed "
        "characterisation, (2) the IWA Anaerobic Digestion Model No. 1 (ADM1) written in Python, (3) a "
        "high-pressure water-scrubbing flowsheet in the open-source simulator DWSIM, driven from Python, "
        "with biogenic-CO₂ recovery, (4) machine-learning surrogates trained on 2,000 coupled "
        "simulations, and (5) a techno-economic model anchored on the French regulator's 2024 cost "
        "survey [S17]. Optimisation runs on the surrogates and every reported design is re-checked with "
        "the full simulation."))
    s.append(P("<b>Key results.</b>"))
    r200, r300 = o["200"]["final"]["simulation"], o["300"]["final"]["simulation"]
    s += B([
        "<b>Validation.</b> The ADM1 reproduces all 36 BSM2 benchmark values within 1 % (maximum error "
        "1.8×10⁻⁵ %) with COD, N and C balances closed to &lt;10⁻⁶ %. Against a published lab digester it "
        "predicts CH₄ content, pH, propionate and biogas within the measured ranges (acetate is "
        "over-predicted). DWSIM compressor power matches a hand calculation within 0.26 %.",
        "<b>Upgrading.</b> The selected design (45 m³/h water, 10 stages, 3.5 bar flash) meets the grid CO₂, "
        "HHV and Wobbe specifications with 0.43 % methane slip and 0.176 kWh/Nm³ of raw gas, and yields "
        "~1,600 t/yr of 99.2 % biogenic CO₂. O₂ (1,927 ppm) is above the 100 ppm limit but within the "
        "0.75 % exemption [S18].",
        f"<b>Surrogates.</b> 13 models reach test R² 0.992–0.999 (classifier AUC 0.930–0.9998) with no "
        f"overfitting (train–test gap ≤ 0.0044) and run ~{D['speed']['speedup_batch']:,.0f}× faster than "
        "the coupled simulation in batch mode. A physics-informed feature raised the CO₂ model from "
        "R² 0.70 to 0.996.",
        "<b>Economics.</b> The cost model reproduces the CRE median (129.3 vs 129.6 €/MWh) once our "
        "higher feed tonnage is removed. Verified optima cost "
        f"{o['150']['final']['simulation']['LCOE_EUR_MWh']:.0f}, {r200['LCOE_EUR_MWh']:.0f}, "
        f"{o['250']['final']['simulation']['LCOE_EUR_MWh']:.0f} and {r300['LCOE_EUR_MWh']:.0f} €/MWh at "
        "150, 200, 250 and 300 Nm³/h; at the average 2023 tariff the break-even size is ≈ 180 Nm³/h.",
        "<b>Risk.</b> Under joint price and kinetic uncertainty (10,000 Monte Carlo samples) the 200 Nm³/h "
        "plant has a median LCOE of 166 €/MWh and only a 13 % chance of positive NPV. The slurry price is "
        "the largest driver (±40 €/MWh swing). A design robust to strong ammonia inhibition exists but "
        "costs +8.4 €/MWh."])
    s.append(P("<b>Conclusions.</b>"))
    s += B([
        "Within the feasible design window the cost surface is <b>flat</b>: the optimum is no cheaper than a "
        "well-scaled base design (149.9 vs 149.6 €/MWh). Plant size and input prices, not fine-tuning, "
        "decide profitability; the optimiser's value is that it respects the stability margin the naive "
        "design breaks.",
        "Surrogate-based optimisation must be verified: the optimiser systematically found points where "
        "the surrogates were 2–5 % optimistic (the optimiser's curse). A verify-and-correct loop fixed this.",
        "The main technical risk is <b>ammonia inhibition</b> of the slurry-rich digester; the main "
        "commercial lever is <b>free slurry supply</b>."])
    s.append(PageBreak())
    s.append(P("Contents", ParagraphStyle("h1toc", parent=h1)))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("t0", fontName="DV-B", fontSize=9.3, leading=13.5, leftIndent=0),
                       ParagraphStyle("t1", fontName="DV", fontSize=8.6, leading=11, leftIndent=14)]
    s.append(toc)
    s.append(PageBreak())


def intro(s, D):
    s.append(P("1. Introduction and market context", h1))
    s.append(P("1.1 Why biomethane", h2))
    s.append(P(
        "Biomethane, i.e. biogas upgraded to natural-gas quality and injected into the gas grid, is one of "
        "the few renewable molecules already produced at industrial scale. In 2024 Europe produced 22 bcm "
        "of biogas and biomethane, of which 5.2 bcm was biomethane [S3, secondary], and installed "
        "biomethane capacity passed 8 bcm/yr in 2026 [S4, secondary]. EU biomethane grew by about 19 % "
        "per year over 2020–2025 [S5], yet the EU is expected to reach only about 21 bcm of the 35 bcm "
        "REPowerEU goal by 2030 [S6]. The global outlook is also positive: the IEA expects global "
        "biomethane output to almost double between 2025 and 2031 [S5]."))
    s.append(P(
        "France is the reference market for this study. At the end of 2025 it had 803 injecting sites "
        "with 15.5 TWh/yr of capacity [S1, S2], and the PPE3 targets 44 TWh in 2030 [S2]. Yet the "
        "capacity added in 2025 fell 40 % compared with 2024 [S1]. Other target job markets show the same "
        "policy pull: Spain targets 20 TWh of biogas in 2030 [S11], Germany's 2025 biomass package pushes "
        "flexible operation [S10], and Quebec requires 10 % renewable natural gas in its network by 2030 "
        "[S12, secondary]."))
    s.append(P("1.2 Cost is the bottleneck", h2))
    s.append(P(
        "The obstacle is cost. IFRI estimates the average EU production cost at about 75–80 €/MWh, with "
        "strong economies of scale (about 54 €/MWh above 1,200 Nm³/h, about 87 €/MWh at ~540 Nm³/h) and a "
        "French median of about 130 €/MWh [S6]. The French regulator (CRE) reports a median levelised cost "
        "of 129.6 €/MWh for agricultural plants, with an interquartile range of 111.7–146.0 €/MWh, against "
        "purchase tariffs of 111–169 €/MWh [S17]. Typical French plants are therefore close to break-even, "
        "and small design or price changes decide profitability. A second value stream is emerging: "
        "biogenic CO₂ from upgrading, captured at 125 European plants (1.17 Mt) in 2025 [S6, S16]."))
    s.append(P("1.3 Why a digital twin, and why with machine learning", h2))
    s.append(P(
        "Plant design couples three disciplines. <b>Biology</b>: ADM1, the IWA standard model [L1, L14], "
        "predicts methane yield and process stability (pH, volatile fatty acids, ammonia) from feed "
        "composition. <b>Separation</b>: upgrading is a gas–liquid equilibrium problem normally solved in a "
        "process simulator; water scrubbing is one of the established commercial technologies "
        "[L7, L8]. <b>Economics</b>: the cost per MWh depends on both. Coupled simulation is accurate but "
        "slow (seconds per design point), which makes optimisation and Monte Carlo analysis expensive. "
        "Recent work uses machine-learning surrogates of mechanistic models and hybrid modelling to "
        "close this gap [L4, L5, L6]."))
    s.append(P(
        "The project also targets skills that employers in this field ask for: mass and energy balances, "
        "process simulation and equipment sizing [J6, J7, J8], and Python, data analysis, design of "
        "experiments and digital-twin skills in bioprocess roles [J1, J2, J4, J5]. The project was chosen "
        "from 12 candidates with a weighted decision matrix (Appendix D)."))
    s.append(P("1.4 Research question", h2))
    s.append(box([P("<b>Which feed blend, feed rate, retention time and upgrading settings minimise the "
                    "levelised cost of biomethane of an agricultural co-digestion plant, while keeping the "
                    "digester biologically stable and the gas within grid specification, and how robust "
                    "is that answer to price and kinetic uncertainty?</b>", body)]))


def objectives(s, D):
    s.append(P("2. Objectives and how far they were met", h1))
    s.append(P(
        "The project definition (02_definition/Project_Definition.pdf) set six SMART objectives. The table "
        "reports each outcome honestly, including where the work deviated from the plan."))
    sp = D["speed"]
    rows = [["#", "Objective and success metric (as defined)", "Outcome", "Status"],
            ["O1", "ADM1 in Python with literature feed characterisation. Steady state within 1 % of BSM2; "
                   "COD and N balances within 0.5 %.",
             "36/36 within 1 % (max 1.8×10⁻⁵ %); COD, N, C closures &lt;10⁻⁶ %. Lab-data check: 4 of 5 "
             "outputs in range, acetate over-predicted.", status("Met")],
            ["O2", "DWSIM upgrading flowsheet driven from Python. Mass closure &lt;0.5 %, energy &lt;1 %; "
                   "recovery, kWh/Nm³ and slip within published ranges.",
             "Mass 0.001 %. Energy residual 1.5 % of work + heat (above 1 %). Slip 0.43 % and 0.176 kWh/Nm³ "
             "are better than the literature ranges, partly because the dryer and H₂S removal are out of "
             "scope.", status("Partly met")],
            ["O3", "≥2,000 coupled runs; RF/XGBoost/MLP surrogates with test R² ≥ 0.95 for CH₄ and LCOE; "
                   "≥100× faster.",
             f"2,000 runs; all 10 regressors R² 0.992–0.999. LCOE is computed from surrogate outputs, not "
             f"learned directly. Speed-up {sp['speedup_batch']:,.0f}× in batch, but only "
             f"{sp['speedup_single']:.0f}× for a single point.", status("Met")],
            ["O4", "Multi-objective optimisation incl. temperature; Pareto front; optimum re-simulated "
                   "within 3 %; LCOE gain quantified.",
             "Single-objective (min LCOE at fixed capacity, with stability and quality constraints) at four "
             "capacities instead of a Pareto front; temperature fixed at 39 °C. Verified designs within "
             "1.5 % of target capacity; surrogate LCOE 3 % optimistic. Gain vs naive design ≈ 0.", status("Partly met")],
            ["O5", "TEA with CAPEX, OPEX, LCOE, NPV, Monte Carlo, tornado, CO₂-revenue scenario; compared "
                   "with published ranges.",
             "All delivered and anchored on CRE data; P10/P50/P90 reported. IRR not computed.", status("Met")],
            ["O6", "Reproducible package: git repository, report, figures, small interactive dashboard; full "
                   "re-run from README.",
             "Git repository, report, 7 figures and README with run order delivered. The dashboard was not "
             "built, and a re-run on a clean machine has not been tested.", status("Partly met")]]
    s.append(table(rows, [0.8, 6.2, 7.9, 2.1], zebra=True))


def methodology(s, D):
    s.append(P("3. Methodology", h1))
    s.append(P(
        "Figure 1 shows the chain. Each block was built and validated on its own before being coupled. "
        "All code is in 05_code (a small Python package, <i>methatwin</i>, plus one script per step); every "
        "decision, failure and fix is logged in LOG.md. The validation principle throughout was to "
        "compare every model with an independent reference: a published benchmark, measured data, a hand "
        "calculation, or a mass balance."))
    s.append(fig(FIGS / "fig02_concept_flow.png",
                 "<b>Figure 1.</b> MethaTwin architecture: mechanistic chain (top) and surrogate-based "
                 "optimisation loop (bottom), as drawn in the project definition. The final optimisation is "
                 "single-objective at fixed capacity (§3.8) and every optimum is re-verified on the full chain."))

    s.append(P("3.1 Plant basis", h2))
    s.append(P(
        "The plant is sized from French statistics: 15.5 TWh/yr over 803 sites [S1] is about 19 GWh/yr "
        "per site, i.e. roughly 200 Nm³/h of biomethane at ~10.9 kWh/Nm³ (HHV) and 8,400 h/yr. The feed "
        "is a typical French agricultural blend: cattle slurry, CIVE (intermediate cover-crop) silage, "
        "and maize silage capped at 15 % of gross tonnage by décret 2016-929 [S20]. The digester is a "
        "mesophilic CSTR at 39 °C."))

    s.append(P("3.2 Feed characterisation", h2))
    s.append(P(
        "Total and volatile solids, nitrogen and biochemical methane potential (BMP) come from the FNR "
        "<i>Guide to Biogas</i> [L13]; composition (protein, lipid, carbohydrate) and COD factors come "
        "from Klimiuk et al. [L11], including values those authors quote from Biernacki et al. (2013). "
        "The theoretical oxygen demand of the volatile solids (ThOD<sub>VS</sub>) is computed from "
        "composition, and the degradability is D = BMP / (0.350 Nm³ CH₄ per kg COD × ThOD<sub>VS</sub>), "
        "where 0.350 is the stoichiometric methane yield of COD at normal conditions. Proteins and lipids "
        "are taken as fully degradable and the inert fraction is 1 − D. Every value is stored with its "
        "table reference in 03_data/raw/feedstock_literature.csv. Five checks were run (Appendix A)."))

    s.append(P("3.3 Digester: ADM1", h2))
    s.append(P(
        "ADM1 [L1] was implemented in the IWA BSM2 form [L14]: 35 states, with pH and the ionic species "
        "solved algebraically from the charge balance (Brent's method), leaving 29 stiff ODEs integrated "
        "with BDF and polished to steady state. The benchmark was reproduced first, then the kinetic "
        "parameters were switched to values calibrated on maize silage and cattle manure by Bułkowska "
        "et al. [L12] (e.g. disintegration rate k<sub>dis</sub> 0.1 d⁻¹ instead of 0.5). One exception: "
        "their ammonia inhibition constant (K<sub>I,NH3</sub> = 0.00026 M) was fitted on a low-nitrogen feed "
        "and sours our slurry-rich digester, so the BSM2 value 0.0018 M was kept and the literature range "
        "carried as an uncertainty. Two implementation subtleties were found and documented: the gas-phase "
        "balances must use the headspace flow k<sub>p</sub>(P<sub>gas</sub> − P<sub>atm</sub>) rather than "
        "the reported flow, and a typo in one carbon coefficient in the text version of the report."))

    s.append(P("3.4 Upgrading: high-pressure water scrubbing in DWSIM", h2))
    s.append(P(
        "DWSIM 10.2 (a .NET 10 application) is driven from Python 3.14 through pythonnet in CoreCLR mode. "
        "The flowsheet is built entirely in code: chiller and knock-out drum, two-stage intercooled "
        "compression to 9 bar, an equilibrium-stage absorber, a flash at intermediate pressure whose gas is "
        "recycled between compressor stages, a CO₂ flash at 1.05 bar that produces biogenic CO₂, an air "
        "stripper, and the water loop (pump and chiller). The two recycle (tear) streams are closed in "
        "Python by damped successive substitution."))
    s.append(P(
        "<b>Thermodynamics.</b> No default DWSIM property package reproduced gas solubility in water: "
        "Peng–Robinson under-predicted CH₄ solubility by ~100 % (its CH₄–water interaction parameter is a "
        "placeholder), SRK and PRSV2 failed for both gases, and NRTL over-predicted CO₂ by ~2,100 %. The "
        "Peng–Robinson binary interaction parameters k<sub>ij</sub>(gas, water) were therefore fitted to "
        "Henry's-law constants [S19] at 12.5 °C. The fit is valid for 10–15 °C (every gas within 15 %, "
        "CO₂/CH₄ selectivity 23–26); all water-contacting units run at 10.0–10.3 °C, which the code checks."))
    s.append(P(
        "<b>Design selection.</b> A 36-run sweep (water flow, number of stages, flash pressure) selected the "
        "design with the lowest energy penalty (electricity plus the heating value of the slipped methane) "
        "among those meeting the CO₂, HHV and Wobbe specifications of the French grid [S18]."))

    s.append(P("3.5 Coupled plant and design of experiments", h2))
    s.append(P(
        "The coupled model runs feed blend → ADM1 → stability screen → DWSIM scrubber in 2–7 s. A digester "
        "is classed stable if pH ≥ 6.8 and total VFA ≤ 8 g COD/L; these are screening thresholds chosen for "
        "this study, not sourced values. A Latin-hypercube design of 2,000 points (seed 42) spans six "
        "design variables and two uncertain kinetic parameters (Table 1). It ran in 18.6 min on three "
        "parallel processes."))
    s.append(table([["Input", "Range", "Type / note"],
                    ["Maize share of feed", "0–0.15", "design; legal cap [S20]"],
                    ["CIVE share of feed", "0.05–0.45", "design (remainder is slurry)"],
                    ["Feed rate", "60–160 t/d", "design"],
                    ["Hydraulic retention time (HRT)", "40–110 d", "design (sets digester volume)"],
                    ["Scrubber water", "100–200 m³/h per 1,000 Nm³/h raw gas", "design"],
                    ["Flash pressure", "2.0–3.5 bar", "design"],
                    ["Disintegration rate k<sub>dis</sub>", "0.05–0.5 d⁻¹, log-uniform", "uncertain kinetics"],
                    ["Ammonia inhibition K<sub>I,NH3</sub>", "0.0012–0.0084 M, log-uniform", "uncertain kinetics"]],
                   [5.0, 6.2, 5.8], zebra=True))
    s.append(P("<b>Table 1.</b> Design-of-experiments inputs.", cap))
    s.append(P(
        "<b>Data-quality gate.</b> 117 runs labelled 'converged' had scrubber mass closures of 0.2–6.7 %, all "
        "at low flash pressure and high water flow. The cause is that DWSIM's column solver judges "
        "convergence against the water-dominated total flow; tightening its tolerances made the solver fail "
        "outright. Instead, runs are kept only if the scrubber mass closure is within 0.1 %, and a classifier "
        "learns where the simulator is reliable. The valid set is 1,224 fully upgraded runs."))

    s.append(P("3.6 Machine-learning surrogates", h2))
    s.append(P(
        "Random forest, XGBoost and a multilayer perceptron were compared for each output with "
        "RandomizedSearchCV and 5-fold cross-validation on 80 % of the data; the 20 % test set was never used "
        "for tuning. CO₂ content and methane slip were modelled on a log scale. The scrubber models form a "
        "<b>cascade</b>: they receive the predicted digester outputs plus a physics-informed feature, the "
        "flash saturation index (1 − y<sub>CH4</sub>) × 1000 / (water per 1,000 Nm³) / p<sub>flash</sub>, "
        "which measures whether the rich water can release gas at the flash. Three classifiers predict "
        "digester stability, simulator validity and grid-spec compliance."))

    s.append(P("3.7 Techno-economic model", h2))
    s.append(P(
        "Costs are anchored on the CRE survey of French biomethane plants [S17] (2023 euros). CAPEX starts "
        "from 44,456 € per Nm³/h at an average plant of 184 Nm³/h and is split into four groups, each scaled "
        "with a six-tenths law to its own driver (digester volume, raw-gas flow, feed tonnage, biomethane "
        "capacity); CRE's reported economies of scale imply an exponent of ~0.61. OPEX includes feed "
        "(CIVE 39.6 €/t, maize 35.7 €/t, slurry transport only 7.3 €/t), electricity (scrubber power from "
        "DWSIM plus 6 % of production for other uses, at 120 €/MWh), 3.5 % of production self-used for "
        "heat, and other OPEX of 32.64 €/MWh. LCOE and NPV use a 7 % discount rate over 15 years and "
        "8,400 h/yr; revenue is the average 2023 tariff of 152.8 €/MWh. All assumptions are listed in "
        "Appendix B."))

    s.append(P("3.8 Optimisation with verification", h2))
    s.append(P(
        "Differential evolution minimises LCOE on the surrogates over the six design variables, for a fixed "
        "capacity (target ± 1 %). Design margins guard against model error: P(stable) ≥ 0.97, predicted "
        "VFA ≤ 6 g COD/L, pH ≥ 7.0 and P(simulator valid) ≥ 0.9. Each optimum is then run in the full "
        "coupled simulation. A <b>verify-and-correct loop</b> rescales the capacity target if the "
        "simulation falls short, raises the validity margin if the scrubber fails, and tightens the VFA "
        "margin if the digester is unstable. Only designs confirmed by full simulation are reported."))

    s.append(P("3.9 Uncertainty and robustness", h2))
    s.append(P(
        "At the 200 Nm³/h optimum, 10,000 Monte Carlo samples propagate uncertainty in the two kinetic "
        "parameters and nine economic inputs (CAPEX ×0.8–1.25, feed costs ±30 %, slurry 7.3–43.2 €/t, "
        "electricity 120–202 €/MWh, other OPEX ±20 %, tariff 111–169 €/MWh, discount 5–9 %, heat self-use "
        "2–6 %) through the surrogates and TEA. A one-at-a-time tornado ranks the drivers. A robust design "
        "is then searched by re-optimising for increasingly severe ammonia inhibition until a design is "
        "confirmed by full simulation."))


def results(s, D):
    s.append(P("4. Results", h1))
    s.append(P("4.1 Toolchain check: DWSIM driven from Python", h2))
    s.append(P(
        "A smoke test compressed 360 Nm³/h of raw biogas to 10 bar. DWSIM gave 44.77 kW against 44.89 kW "
        "from an independent hand calculation (ideal-gas isentropic compression with NIST heat "
        "capacities): −0.26 %, with an outlet temperature within 0.9 K and exact mass closure. The hand "
        "calculation caught a unit trap: DWSIM's adiabatic efficiency is in percent, so the first run, "
        "with 0.75 instead of 75, gave 100 times the power."))

    s.append(P("4.2 Feed characterisation", h2))
    s.append(P(
        "Degradability is 0.46 for slurry, 0.69 for CIVE and 0.74 for maize (Figure 2). Checks C1–C3 pass: "
        "BMP is below the theoretical maximum, the inert fractions agree with independent fractionations "
        "within tolerance, and the code reproduces the published COD values within 0.6 %. Two checks fail "
        "and are kept as documented uncertainties, not hidden by loosening tolerances: the predicted lipid "
        "and carbohydrate split of a measured maize–manure mix (C4) is off because literature lipid contents "
        "are 2–3 times the measured value, and organic plus ammonium nitrogen does not match total nitrogen "
        "(C5) because they come from different sources."))
    s.append(fig(FIGS / "fig03_feedstock_characterisation.png",
                 "<b>Figure 2.</b> Left: ADM1 COD fractions of each feed from the BMP-based method. Right: "
                 "theoretical vs published methane potential [L13]; D is the degradable fraction."))

    s.append(P("4.3 Digester model", h2))
    b = D["bsm2"]
    s.append(P(
        f"<b>Benchmark.</b> After two diagnosed failures (a soured steady state from a low-biomass start, then "
        f"a 5 % gas-flow error from the headspace-flow subtlety), the model reproduces {b['n_pass']}/"
        f"{b['n_variables']} BSM2 reference values within 1 %, with a maximum error of "
        f"{b['max_abs_rel_err_pct']:.1e} % (Figure 3a)."))
    s.append(table([["Output (lab digester, 39 °C, HRT 45 d)", "Model", "Measured [L12]", "In range?"],
                    ["CH₄ content", "53.6 %", "50–58 %", "Yes"],
                    ["pH", "7.19", "6.8–7.4", "Yes"],
                    ["Propionate", "0.69 kg COD/m³", "0.3–0.9", "Yes"],
                    ["Biogas (dry, normal conditions)", "83 Ndm³/d", "65–100", "Yes"],
                    ["Acetate", "0.85 kg COD/m³", "0.2–0.6", "No (≈40 % above range)"]],
                   [6.2, 3.3, 3.5, 4.0], zebra=True))
    s.append(P("<b>Table 2.</b> Check against measured lab data with no parameter adjusted. Measured values "
               "were read from the paper's figures and are approximate.", cap))
    s.append(P(
        "<b>Base case.</b> With 88 t/d of feed (60 % slurry, 25 % CIVE, 15 % maize) and HRT 60 d, the "
        "digester produces 132 Nm³/h of methane at 56.9 % CH₄ and pH 7.61: only 71 % of the batch BMP, so "
        "the plant is undersized for the 200 Nm³/h target. Ammonia stress is significant (3.9 g N/L total "
        "ammonia, 214 mg N/L free NH₃, VFA 6.9 g COD/L). The sensitivity in Figure 3b already shows the "
        "two themes of the study: retention time and feed rate are the levers, and ammonia inhibition is "
        "the risk."))
    s.append(fig(FIGS / "fig04_adm1_validation_and_base_case.png",
                 "<b>Figure 3.</b> (a) MethaTwin ADM1 vs BSM2 reference values [L14]. (b) Base-case methane "
                 "production and one-at-a-time sensitivities."))

    s.append(P("4.4 Upgrading", h2))
    s.append(table([["Result (selected design)", "Value", "Specification / literature"],
                    ["CO₂ in biomethane", "0.46 %", "&lt; 2.5 % [S18] ✓"],
                    ["Higher heating value", "10.95 kWh/Nm³", "10.7–12.8 [S18] ✓"],
                    ["Wobbe index", "14.63 kWh/Nm³", "13.64–15.70 [S18] ✓"],
                    ["O₂", "1,927 ppm", "&lt; 100 ppm ✗; exemption &lt; 0.75 % ✓ [S18]"],
                    ["Methane slip", "0.43 % (recovery 99.57 %)", "≈ 1 % for water scrubbing [L7]"],
                    ["Electricity", "0.176 kWh/Nm³ raw gas", "0.20–0.30 [L7]; dryer and H₂S removal excluded"],
                    ["Biogenic CO₂ stream", "99 Nm³/h at 99.2 % (≈1,600 t/yr)", "65 % of the raw CO₂"],
                    ["Mass closure", "0.001 %", "objective &lt; 0.5 %"]],
                   [4.6, 5.2, 7.2], zebra=True))
    s.append(P("<b>Table 3.</b> Selected water-scrubbing design: 45 m³/h water, 10 equilibrium stages, "
               "3.5 bar flash, 8 Nm³ air per m³ water.", cap))
    s.append(P(
        "The sweep (Figure 4b–c) exposed a real process limit: above ~55 m³/h of water at 3.5 bar the rich "
        "water is under-saturated at the flash pressure, the flash releases no gas, and dissolved methane is "
        "lost in the stripper (slip 7–10 %). The oxygen comes from stripping air dissolved in the recycled "
        "water and released in the absorber, a known issue for water scrubbers; vacuum regeneration or a "
        "deoxygenation step would be the mitigation. A first version of the flowsheet closed its mass "
        "balance perfectly while the absorber did nothing, because of a missing factor of 1,000 in the "
        "water flow. The lesson: closed balances do not prove a model does what was intended."))
    s.append(fig(FIGS / "fig05_upgrading_hpws.png",
                 "<b>Figure 4.</b> (a) Selected flowsheet with key streams. (b) Product CO₂ and (c) energy "
                 "penalty vs circulating water for three flash pressures; the square marks the selected design.",
                 width=W * 0.92))

    s.append(P("4.5 Surrogate models", h2))
    m = D["metrics"]
    reg = m[m.block != "classifier"]
    rows = [["Output", "Best model", "Test R²", "Test RMSE"]]
    names = {"CH4_Nm3_h": "Digester CH₄ (Nm³/h)", "y_CH4_dry": "Biogas CH₄ fraction", "pH": "pH",
             "VFA_gCOD_L": "VFA (g COD/L)", "free_NH3_mgN_L": "Free NH₃ (mg N/L)",
             "biomethane_Nm3_h": "Biomethane (Nm³/h)", "BM_CO2_pct": "CO₂ in biomethane (%)",
             "BM_O2_ppm": "O₂ in biomethane (ppm)", "CH4_slip_pct": "CH₄ slip (%)",
             "P_el_upg_kW": "Scrubber electricity (kW)"}
    for r in reg.itertuples():
        r2 = f"{r.test_R2:.3f}" + (f" (log {r.test_R2_log:.3f})" if pd.notna(r.test_R2_log) else "")
        rows.append([names.get(r.target, r.target), r.best_model, r2, f"{r.test_RMSE:.3g}"])
    for r in m[m.block == "classifier"].itertuples():
        rows.append([{"digester_stable": "Classifier: digester stable", "upgrading_valid":
                      "Classifier: simulator valid", "spec_ok": "Classifier: grid spec met"}[r.target],
                     r.best_model, f"AUC {r.test_AUC:.4f}", f"accuracy {100 * r.test_accuracy:.1f} %"])
    s.append(table(rows, [5.8, 2.6, 4.4, 4.2], zebra=True))
    s.append(P("<b>Table 4.</b> Held-out test performance (20 % of data, never used for tuning).", cap))
    o = D["over"]
    s.append(P(
        "<b>Is R² ≥ 0.99 overfitting?</b> No. Overfitting shows up as a gap between training and unseen data, "
        "not as a high test score. Training R² is 0.998–1.000, 5-fold cross-validation 0.982–0.998 and test "
        "0.995–0.999, so the train–test gap is at most 0.0044. High scores are expected because the data "
        "come from a deterministic simulator with no measurement noise. Feeding the scrubber models the "
        "<i>predicted</i> instead of the true digester outputs left test R² unchanged (e.g. biomethane 0.9958 "
        "vs 0.9959), so errors do not accumulate along the cascade. The physics-informed saturation index "
        "was decisive: it raised R² for CO₂ from 0.70 to 0.996 and for slip from 0.39 to 0.968 (log scale), "
        "and it is the most important input of the CO₂ model (Figure 5). These scores measure fidelity to "
        "the simulator, not accuracy against real plants."))
    s.append(fig(FIGS / "fig06_surrogate_test_performance.png",
                 "<b>Figure 5.</b> Top: parity plots on the test set. Bottom: permutation importance for "
                 "digester methane and product CO₂; the right panel lists all test metrics and the speed-up."))

    s.append(P("4.6 Techno-economics and verified optimisation", h2))
    t = D["tea"]["results"]["reference_184"]
    s.append(P(
        f"<b>Benchmarking.</b> The base design scaled to the CRE average size (184 Nm³/h) gives an LCOE of "
        f"{t['LCOE_EUR_MWh']:.1f} €/MWh, 4 % above CRE's upper quartile. Electricity is "
        f"{100 * t['el_share_of_energy']:.1f} % of energy produced (CRE 9.2 %) and CAPEX is 36 % of the full "
        "cost (CRE ~40 %). The gap is explained by feed: our slurry-rich blend needs ~242 t of input per "
        "Nm³/h of capacity against ~83 t for the average French plant, so feed costs 53.5 instead of "
        "30.7 €/MWh. Removing that excess gives 129.3 €/MWh, matching the CRE median of 129.6. An early "
        "attempt to back-calculate fixed O&amp;M gave a negative value and was replaced by CRE's measured "
        "per-MWh figure. A CO₂-sales scenario (160 €/t net) lowers the reference LCOE to 137.5 €/MWh."))
    rows = [["Target", "Net biomethane", "LCOE (€/MWh)", "NPV (M€)", "Maize / CIVE", "Feed (t/d)", "HRT (d)",
             "VFA (g/L)"]]
    for k in ("150", "200", "250", "300"):
        f = D["opt"][k]["final"]
        d, v = f["design"], f["simulation"]
        rows.append([f"{k} Nm³/h", f"{v['bm_net_Nm3_h']:.1f}", f"{v['LCOE_EUR_MWh']:.1f}",
                     f"{v['NPV_EUR'] / 1e6:+.2f}", f"{100 * d['maize_share']:.0f} / {100 * d['cive_share']:.0f} %",
                     f"{d['feed_t_d']:.0f}", f"{d['hrt_d']:.0f}", f"{v['VFA_gCOD_L']:.1f}"])
    s.append(table(rows, [1.9, 2.3, 2.1, 1.8, 2.5, 1.8, 1.5, 1.6], zebra=True))
    s.append(P("<b>Table 5.</b> Optimal designs, all confirmed by full coupled simulation. All meet the grid "
               "CO₂ specification. The 300 Nm³/h design sits at the upper feed bound and its simulated VFA "
               "(6.4 g/L) slightly exceeds the 6.0 g/L design margin applied to the surrogate.", cap))
    s.append(P(
        "<b>What the optimisation taught.</b> (1) With economies of scale, a 'capacity ≥ target' constraint "
        "never binds and the optimiser always chose the largest plant, so capacity was fixed instead. (2) "
        "The first optima sat on the stability boundary and three of four failed in full simulation, hence "
        "the design margins. (3) The surrogates over-predicted biomethane by 2–5 % at the optima: the "
        "optimiser seeks out regions where the model is optimistic. The verify-and-correct loop converged in "
        "2–5 iterations. (4) The naive scale-up of the base design to 200 Nm³/h, run in full simulation, "
        "costs 149.6 €/MWh against 149.9 for the optimum: the cost surface is flat. The optimum's value is "
        "that it keeps VFA within the margin (6.0 vs 6.7 g/L). At the average tariff, plants below "
        "≈180 Nm³/h lose money (Figure 6a)."))

    s.append(P("4.7 Uncertainty and robustness", h2))
    mc = D["unc"]["montecarlo"]
    L = mc["LCOE_stable"]
    s.append(P(
        f"Over 10,000 samples, {100 * mc['share_predicted_unstable']:.0f} % are predicted unstable. "
        f"For stable samples the LCOE is P10 "
        f"{L['P10']:.0f}, P50 {L['P50']:.0f} and P90 {L['P90']:.0f} €/MWh, and the probability of a "
        f"positive NPV is {100 * mc['P_NPV_positive_stable']:.0f} %. The median is pessimistic mainly because "
        "slurry is sampled up to the full CRE effluent price; at the surrogate optimum the surrogate LCOE "
        "is also 3 % optimistic (145.3 vs 149.9 €/MWh), a bias the Monte Carlo inherits."))
    tor = D["tornado"].head(6)
    rows = [["Input (low / high)", "LCOE low", "LCOE high", "Swing (€/MWh)"]]
    for r in tor.itertuples():
        rows.append([r.input, f"{r.LCOE_low:.1f}", f"{r.LCOE_high:.1f}", f"{r.swing:.1f}"])
    s.append(table(rows, [7.6, 2.8, 2.8, 3.8], zebra=True))
    s.append(P(f"<b>Table 6.</b> Six largest drivers in the one-at-a-time tornado around the surrogate "
               f"nominal LCOE of {D['unc']['tornado_nominal_LCOE']:.1f} €/MWh (full list in "
               "04_models_and_simulations/step7_tea/tornado.csv).", cap))
    rb = D["rob"]
    s.append(P(
        "<b>The ammonia cliff.</b> At K<sub>I,NH3</sub> = 0.0012 M the nominal optimum's probability of "
        "stability drops to zero. Re-optimising for that worst case found no design confirmed by full "
        "simulation, and the DoE explains why: only 8 % of runs with K<sub>I,NH3</sub> 0.0012–0.0016 are "
        "stable, and only two reach 195 Nm³/h. At 0.0014 the best design had no VFA margin. At "
        f"<b>{rb['lowest_feasible_K_I_nh3']}</b> a robust design was confirmed: "
        f"{rb['final']['simulation']['bm_net_Nm3_h']:.1f} Nm³/h at {rb['final']['simulation']['LCOE_EUR_MWh']:.1f}"
        f" €/MWh, using the largest digester (HRT 108 d), less CIVE (13 %) and more slurry (160 t/d). The "
        f"same design works at nominal kinetics ({rb['robust_design_at_nominal_kinetics']['LCOE_EUR_MWh']:.1f}"
        f" €/MWh). The <b>price of robustness</b> is +{rb['price_of_robustness_EUR_MWh']:.1f} €/MWh "
        "(+5.6 %)."))
    s.append(fig(FIGS / "fig07_tea_optimisation.png",
                 "<b>Figure 6.</b> (a) LCOE of verified optima vs size with CRE benchmark and tariff [S17]. "
                 "(b) Three 200 Nm³/h designs by full simulation. (c) Monte Carlo LCOE distribution. "
                 "(d) Tornado of LCOE drivers."))


def discussion(s, D):
    s.append(P("5. Discussion", h1))
    s.append(P("5.1 What the results mean for a plant developer", h2))
    s += B([
        "<b>Size first.</b> Economies of scale dominate: LCOE falls from 157 to 140 €/MWh between 150 and "
        "300 Nm³/h, and the break-even at the average tariff is ≈180 Nm³/h. This matches the scale effect "
        "reported by IFRI and CRE [S6, S17].",
        "<b>Secure the inputs.</b> The slurry price swings LCOE by 40 €/MWh, more than CAPEX (25). A "
        "slurry-rich plant is only viable if slurry is supplied at transport cost, e.g. by farmer-partners.",
        "<b>Fine-tuning is not where the money is.</b> Within the stable, specification-meeting window, "
        "design choices change LCOE by only a few €/MWh. Optimisation earns its keep by keeping the design "
        "away from the stability edge, not by cutting cost.",
        "<b>Ammonia is the technical risk.</b> The kinetic uncertainty most likely to sink the plant is "
        "ammonia inhibition, and the best defence available in this design space (a bigger digester, less "
        "nitrogen-rich silage) costs 8.4 €/MWh.",
        "<b>Biogenic CO₂ is a real option.</b> The scrubber delivers a 99.2 % CO₂ stream of ≈1,600 t/yr at no "
        "extra separation cost; at a net value of 160 €/t it would lower LCOE by ≈15 €/MWh, though the "
        "liquefaction cost and market access are not modelled here."])
    s.append(P("5.2 Methodological lessons", h2))
    s += B([
        "<b>Independent checks catch real bugs.</b> A hand calculation caught a 100× unit error in DWSIM; "
        "stream inspection caught a 1,000× water-flow error that the balances could not see; a hand COD "
        "balance of the benchmark itself revealed the headspace-flow subtlety.",
        "<b>A solver that says 'converged' is not a data-quality guarantee.</b> 8.7 % of 'converged' "
        "scrubber runs violated mass balance by up to 6.7 %. Filtering by physics (mass closure) and "
        "learning simulator validity was more reliable than tightening tolerances.",
        "<b>Physics-informed features beat model tuning.</b> One dimensionless index built from "
        "flash thermodynamics did more for the CO₂ model (R² 0.70 → 0.996) than any hyperparameter search.",
        "<b>Surrogate optimisation needs a verification loop.</b> An optimiser exploits model error; the "
        "2–5 % bias found here would have been reported as a result without full-simulation checks."])
    s.append(P("5.3 Comparison with literature", h2))
    s.append(P(
        "The MethaTwin LCOE (140–157 €/MWh for 150–300 Nm³/h) lies in the upper half of the French "
        "distribution (interquartile range 112–146 €/MWh [S17]) and well above the EU average of "
        "75–80 €/MWh [S6], which includes much larger plants and cheaper feeds. Specific electricity "
        "(0.176 kWh/Nm³) is below the 0.20–0.30 kWh/Nm³ reported for water scrubbing [L7], as expected "
        "because drying, H₂S removal and motor efficiencies are excluded. Methane slip (0.43 %) is below "
        "the ≈1 % reported in the same review, thanks to the intermediate flash recycle; real plants also "
        "lose methane through leaks and off-design operation, which are not modelled."))


def limitations(s, D):
    s.append(P("6. Limitations", h1))
    s += B([
        "<b>Validation against real plants.</b> The models are validated against a benchmark, a lab digester "
        "and hand calculations, not against full-scale plant data. Acetate is over-predicted by ≈40 %.",
        "<b>Feed data.</b> Feed properties come from literature tables, with two failed consistency checks "
        "(lipid/carbohydrate split; nitrogen). CIVE is represented by grass-silage data. Feed variability over "
        "the year is not modelled.",
        "<b>Steady state only.</b> The ADM1 is solved to steady state; start-up, feed changes and dynamic "
        "stability are not studied. The stability thresholds (pH ≥ 6.8, VFA ≤ 8 g COD/L) are screening "
        "assumptions. A single CSTR is modelled; no post-digester, although 34 kg COD/m³ remains undigested.",
        "<b>Thermodynamics.</b> The fitted k<sub>ij</sub> are valid only at 10–15 °C. The energy residual of "
        "the scrubber (1.5 % of work plus heat) is above the 1 % objective.",
        "<b>Scope of upgrading.</b> H₂S removal, drying to −5 °C dew point, O₂ removal, motor efficiencies "
        "and grid-injection compression are not modelled. The product O₂ (1,927 ppm) relies on the 0.75 % "
        "exemption.",
        "<b>Economics.</b> Costs are top-down (CRE averages scaled with a six-tenths law), not equipment-level "
        "quotes. Digestate value, subsidies other than the tariff, taxes, financing structure and IRR are not "
        "included. Prices are 2023 euros.",
        "<b>Surrogates.</b> They are accurate only inside the sampled ranges; the 300 Nm³/h optimum sits on "
        "the feed-rate bound. Their LCOE is ≈3 % optimistic at the optimum, which biases the Monte Carlo.",
        "<b>Optimisation.</b> Single-objective at fixed capacities rather than a Pareto front; digester "
        "temperature was not a decision variable; ammonia-mitigation options were not in the design space."])


def conclusions(s, D):
    s.append(P("7. Conclusions and future work", h1))
    s.append(P("7.1 Conclusions", h2))
    s += B([
        "An open-source, end-to-end digital twin of an agricultural biomethane plant was built from public "
        "data only: ADM1 in Python, a DWSIM water-scrubbing flowsheet automated from Python, ML surrogates "
        "and a CRE-anchored cost model.",
        "Each block was validated independently: BSM2 to 1.8×10⁻⁵ %, a published lab digester (4 of 5 "
        "outputs in range), a hand-calculated compressor within 0.26 %, and the CRE cost median within "
        "0.3 €/MWh after correcting for feed.",
        "Surrogates reproduce the simulator with test R² 0.992–0.999 and no overfitting, ~2,300× faster.",
        "Verified optima give 140–157 €/MWh for 300–150 Nm³/h; break-even ≈180 Nm³/h at the average tariff. "
        "The cost optimum is flat, so size and input prices decide viability.",
        "Under uncertainty the 200 Nm³/h plant has only a 13 % chance of positive NPV; slurry price and "
        "ammonia inhibition are the two risks that matter, and robustness to ammonia costs +8.4 €/MWh."])
    s.append(P("7.2 Future work", h2))
    s += B([
        "<b>Ammonia mitigation</b> in the design space: dilution water, side-stream NH₃ stripping, "
        "low-nitrogen co-substrates.",
        "<b>Dynamic simulation</b> of start-up and feed changes, plus a <b>post-digester</b> to recover the "
        "undigested COD.",
        "<b>Calibration</b> against full-scale plant time series if open data become available.",
        "<b>Upgrading alternatives</b>: a membrane unit (written as a Python unit model, since DWSIM has "
        "none) and vacuum regeneration to remove the O₂ problem; temperature-dependent k<sub>ij</sub>.",
        "<b>Multi-objective optimisation</b> (LCOE vs methane slip vs CO₂ revenue) with NSGA-II, temperature "
        "as a variable, and a bottom-up equipment cost model; IRR and financing scenarios.",
        "<b>Interactive dashboard</b> (Streamlit) on top of the surrogates, as planned in objective O6."])


def references(s, D):
    s.append(P("References", h1))
    s.append(P("All sources were consulted between 20 and 21 November 2026. 'Secondary' marks press "
               "coverage of a primary document that could not be opened. The full list, with how each fact "
               "was verified, is in 01_research/sources.md.", cap))
    refs = [
        ("S1", "SDES (French Ministry statistics). <i>Tableau de bord : biométhane injecté dans les réseaux de gaz, T4 2025.</i> https://www.statistiques.developpement-durable.gouv.fr/tableau-de-bord-biomethane-injecte-dans-les-reseaux-de-gaz-quatrieme-trimestre-2025"),
        ("S2", "NaTran, GRDF et al. <i>Panorama des gaz renouvelables 2025</i>, press conference, 9 Apr 2026. https://www.natrangroupe.com/sites/default/files/co/conference-presse-panorama-gaz-renouvelables-2025-natran-09042026.pdf"),
        ("S3", "Renewable Energy Magazine. Coverage of the EBA Statistical Report 2025, 10 Dec 2025 (secondary). https://www.renewableenergymagazine.com/biogas/european-biogas-association-unveils-15th-edition-of-20251210"),
        ("S4", "gasworld. <i>Europe biomethane passes 8 bcm production capacity</i>, 1 Jul 2026 (secondary). https://www.gasworld.com/story/europe-biomethane-passes-8bcm-production-capacity/2253418.article/"),
        ("S5", "IEA. <i>Renewables 2026 – Biogases.</i> https://www.iea.org/reports/renewables-2026/biogases"),
        ("S6", "Cornot-Gandolphe S. <i>The European Biomethane Sector at a Critical Juncture.</i> IFRI, June 2026. https://www.ifri.org/sites/default/files/2026-06/ifri_cornot-gandolphe_european_biomethane_sector_june2026.pdf"),
        ("S10", "BDEW. <i>Bundestag hat Biogaspaket verabschiedet.</i> https://www.bdew.de/energie/bundestag-hat-biogaspaket-verabschiedet/"),
        ("S11", "MITECO (Spain). Press release, May 2026. https://www.miteco.gob.es/es/prensa/ultimas-noticias/2026/mayo/el-miteco-propone-impulsar-el-biometano-con-cuotas-minimas-en-la.html"),
        ("S12", "Waste Dive. <i>Canada's clean fuel programs sees 417 % jump in RNG in 2024</i>, 13 Aug 2025 (secondary). https://www.wastedive.com/news/canada-clean-fuels-market-rng-increase/757558/"),
        ("S16", "Bioenergy International. Coverage of the EBA white paper on biogenic CO₂, Sept 2025 (secondary). https://bioenergyinternational.com/biogenic-carbon-dioxide-from-rng-is-key-to-europes-carbon-strategy-eba/"),
        ("S17", "CRE. <i>Bilan technique et économique des installations de production de biométhane injecté (hors STEP et ISDND)</i>, Dec 2024. https://cre.fr/fileadmin/Documents/Rapports_et_etudes/2024/Rapport_Bilan_technique_economique_biomethane_injecte.pdf"),
        ("S18", "GRDF. <i>Biomethane quality</i>, ENTSOG gas-quality workshop, 19 Nov 2025. https://www.entsog.eu/sites/default/files/2025-12/S1.2%20GRDF%20-%20Biomethane%20Quality.pdf"),
        ("S19", "Henry's-law constants (Sander 2023 compilation), via https://en.wikipedia.org/wiki/Henry%27s_law ; NIST Chemistry WebBook, methane: https://webbook.nist.gov/cgi/cbook.cgi?ID=C74828&amp;Mask=10"),
        ("S20", "Décret n° 2016-929 du 7 juillet 2016 (main crops ≤ 15 % of input tonnage), INERIS AIDA. https://aida.ineris.fr/reglementation/decret-ndeg-2016-929-070716-pris-lapplication-larticle-541-39-code-lenvironnement"),
        ("L1", "Batstone D.J. et al. (2002). <i>Anaerobic Digestion Model No. 1 (ADM1).</i> IWA Scientific and Technical Report No. 13. IWA Publishing."),
        ("L4", "Tisocco et al. (2026). Machine learning vs. ADM1: reliable biogas prediction with minimal data requirements in full-scale plants. <i>Environmental Science and Ecotechnology</i> 29, 100662. https://doi.org/10.1016/j.ese.2026.100662"),
        ("L5", "Wang et al. (2026). AI-driven digital twin and delay-aware surrogate MPC framework. <i>Computers &amp; Chemical Engineering.</i> https://pure.uj.ac.za/en/publications/ai-driven-digital-twin-and-delay-aware-surrogate-mpc-framework-fo/"),
        ("L6", "Caccavale F. et al. (2024). Navigating Industry 4.0 and 5.0: the role of hybrid modelling in (bio)chemical engineering's digital transition. <i>Frontiers in Chemical Engineering.</i> https://doi.org/10.3389/fceng.2024.1494244"),
        ("L7", "Persson T. (2013). <i>Biogas upgrading – technical review.</i> IEA Bioenergy Task 37 workshop. https://task37.ieabioenergy.com/wp-content/uploads/sites/32/2022/03/7_Persson_Biogas_Up-grading_Technical_Review_Task_37_Biogas_Workshop_Seoul_11-2013.pdf"),
        ("L8", "Bauer F., Hulteberg C., Persson T., Tamm D. (2013). <i>Biogas upgrading – review of commercial technologies.</i> SGC Rapport 270. https://lup.lub.lu.se/record/3512502"),
        ("L11", "Klimiuk E. et al. (2015). ADM1-based modeling of anaerobic codigestion of maize silage and cattle manure, Part I. <i>Archives of Environmental Protection</i> 41(3). https://www.journals.pan.pl/Content/86065/PDF/10265-Volume41-Issue3_paper_02.pdf"),
        ("L12", "Bułkowska K. et al. (2015). ADM1-based modeling of anaerobic codigestion of maize silage and cattle manure, Part II: calibration. <i>Archives of Environmental Protection</i> 41(3). https://www.journals.pan.pl//Content/86068/PDF/10265-Volume41-Issue3_paper_03.pdf"),
        ("L13", "FNR (2010). <i>Guide to Biogas – From production to use</i>, 5th ed. https://energypedia.info/images/4/46/Guide_to_Biogas-_From_Production_to_Use.pdf"),
        ("L14", "Rosen C., Jeppsson U. (2006). <i>Aspects on ADM1 implementation within the BSM2 framework.</i> Lund University. https://iwa-mia.org/wp-content/uploads/2019/04/bmadm1_report061127.pdf"),
        ("J1", "COLIPI (Hamburg). Bioprocess Engineer – fermentation, process engineering &amp; automation (job posting). https://startupcity.hamburg/jobs-cofounder/startup-jobs/bioprocess-engineer-fermentation-process-engineering-and-automation-mfd-1788875564"),
        ("J2", "Fermify (Vienna). Bioprocess Engineer (job posting). https://www.viennabiocenter.org/fileadmin/user_upload/VBC/Career/Jobs/BioprocessEngineer_JobAd.pdf"),
        ("J4", "MicroHarvest (Lisbon). Bioprocess data engineer in fermentation (job posting). https://freehire.me/jobs/bioprocess-data-engineer-in-fermentation-microharvest-43npgrqb"),
        ("J5", "NMBU (Norway). PhD – AI-controlled fermentation and digital twins (posting). https://www.applykite.com/positions/phd-scholarship-in-bioprocess-engineering-ai-controlled-fermentation-and-digital-twins-i43o8s6nf8"),
        ("J6", "Vitol BioMethane. Facility Engineer (job posting). https://www.wayup.com/i-j-Facility-Engineer-Vitol-BioMethane-274751239496477/"),
        ("J7", "Aventa (France). Process Engineer for Bio-Methane Project (job posting). https://www.aventa.fr/jobs/process-engineer-for-bio-methane-project-h-f/"),
        ("J8", "Symbioz (France). Ingénieur génie des procédés (job posting). https://www.jobteaser.com/fr/job-offers/4ba4236d-08ea-4da5-a250-1d1fd5fb8d0d-symbioz-ingenieur-genie-des-procedes"),
    ]
    for k, v in refs:
        s.append(P(f"<b>[{k}]</b>&nbsp; {v}", ref))
    s.append(P("Software: Python 3.14, NumPy, SciPy, pandas, scikit-learn, XGBoost, matplotlib, reportlab, "
               "pythonnet and DWSIM 10.2.11 (all free and open source; versions pinned in requirements.txt).", cap))


def appendices(s, D):
    s.append(P("Appendix A. Validation checklist", h1))
    rows = [["Check", "Reference", "Result", "Pass"],
            ["DWSIM compressor power", "hand calculation (NIST cp)", "−0.26 %, ΔT 0.9 K", "✓"],
            ["C1 BMP ≤ theoretical maximum", "physics", "all three feeds", "✓"],
            ["C2 inert fractions", "Biernacki 2013 / Koch 2010 via [L11]", "maize 0.26 vs 0.14 (tol. ±0.15); CIVE in range", "✓"],
            ["C3 COD values", "[L11] Table 3", "within 0.6 %", "✓"],
            ["C4 lipid / carbohydrate split", "[L11] measured mix", "X_li 0.105 vs 0.048; X_ch 0.34 vs 0.50", "✗ (documented)"],
            ["C5 nitrogen consistency", "[L13] total N", "+36 % / −32 % / −41 %", "✗ (documented)"],
            ["ADM1 vs BSM2", "[L14]", "36/36 within 1 %, max 1.8×10⁻⁵ %", "✓"],
            ["ADM1 COD / N / C balances", "conservation", "&lt;10⁻⁶ %", "✓"],
            ["ADM1 vs lab digester", "[L12]", "4 of 5 outputs in range", "partly"],
            ["Gas solubility (fitted k<sub>ij</sub>)", "Henry's law [S19]", "within 15 % at 10–15 °C", "✓"],
            ["Scrubber mass / energy balance", "conservation", "0.001 % / 1.5 %", "✓ / ✗"],
            ["Surrogate generalisation", "held-out test, 5-fold CV", "gap ≤ 0.0044", "✓"],
            ["Cascade error propagation", "predicted vs true features", "R² unchanged", "✓"],
            ["TEA vs CRE median", "[S17]", "129.3 vs 129.6 €/MWh (feed-corrected)", "✓"],
            ["Optima", "full coupled simulation", "all four confirmed within 1.5 % of target", "✓"]]
    s.append(table(rows, [4.6, 4.3, 5.9, 2.2], zebra=True))

    s.append(P("Appendix B. Assumptions", h1))
    rows = [["ID", "Assumption", "Basis"],
            ["Plant", "~200 Nm³/h target; 8,400 h/yr; mesophilic CSTR at 39 °C", "[S1] average site size"],
            ["Feed", "Slurry, CIVE (grass-silage data), maize ≤ 15 %; slurry NH₄-N 0.178 kmol/m³ (midpoint of range)", "[L13], [S20]"],
            ["Kinetics", "Bułkowska calibration, except K<sub>I,NH3</sub> = 0.0018 M (BSM2)", "[L12], [L14]"],
            ["Start", "Inoculated initial state (biomass 1 kg COD/m³, S_IC = S_IN = 0.1)", "generic, not tuned"],
            ["Stability", "pH ≥ 6.8 and VFA ≤ 8 g COD/L", "study assumption"],
            ["Thermo", "Peng–Robinson with fitted k<sub>ij</sub>; valid 10–15 °C", "[S19]"],
            ["Upgrading", "H₂S removal and drying upstream/downstream, not modelled; shaft power reported; chiller COP 3", "study assumption"],
            ["A1", "CAPEX split 45/20/17/17 % over digester, upgrading, feed handling, capacity; six-tenths scaling", "[S17]"],
            ["A2", "Slurry charged transport only (7.3 €/t)", "[S17]; full effluent price as a scenario"],
            ["A3", "Electricity = DWSIM scrubber power + 6 % of production; 120 €/MWh", "[S17]"],
            ["A4", "Heat self-use 3.5 % of production", "[S17] median"],
            ["A5", "Other OPEX 32.64 €/MWh", "[S17]"],
            ["A6", "No digestate revenue; CO₂ sales only as a scenario", "study assumption; [S6]"],
            ["A7–A8", "Uncertainty ranges for CAPEX, feed, OPEX, discount and heat (see §3.9)", "around CRE values"],
            ["Finance", "7 % discount rate, 15 years, tariff 152.8 €/MWh (range 111–169)", "[S17]"]]
    s.append(table(rows, [1.6, 10.2, 5.2], zebra=True))

    s.append(P("Appendix C. Code structure and reproduction", h1))
    s.append(P("The package <i>methatwin</i> (05_code/methatwin) holds the reusable models; one script per "
               "step reproduces each result. Run from the project root after "
               "<font name='DVM'>pip install -r requirements.txt</font>; steps 2, 5, 6a and 7 also need "
               "DWSIM 10.2 installed."))
    rows = [["Module / script", "Purpose"],
            ["methatwin/feedstock.py", "Feed dataclass, ThOD, BMP-based fractionation, blending"],
            ["methatwin/adm1.py", "ADM1 (BSM2 form): parameters, speciation, rates, steady state, balances"],
            ["methatwin/dwsim_thermo.py", "Henry's-law data, k<sub>ij</sub> fitting, property package"],
            ["methatwin/upgrading.py", "Water-scrubbing flowsheet built and solved in DWSIM, KPIs, balances"],
            ["methatwin/plant.py", "Coupled plant: digester → stability screen → upgrading, quality gate"],
            ["methatwin/surrogate.py", "Loads and runs the cascaded surrogates"],
            ["methatwin/tea.py", "CAPEX, OPEX, LCOE and NPV (CRE-anchored)"],
            ["dwsim_bridge.py", "Loads DWSIM (.NET 10) into Python via pythonnet / CoreCLR"],
            ["step2 … step7e", "One script per step; outputs in 04_models_and_simulations, figures in 06_figures"],
            ["phase1, phase2, phase4", "Decision matrix, definition PDF, this report"]]
    s.append(table(rows, [5.0, 12.0], zebra=True))
    s.append(P("Run order: step3 → step4a–d → step5a–c → step6a (≈19 min) → step6b–d → step7a → step7b → "
               "step7c → step7e → step7d → phase4. The trained models (66 MB) are not in git; step6b "
               "regenerates them.", body))

    s.append(P("Appendix D. Project selection and data policy", h1))
    s.append(P("Twelve candidate projects were scored on market relevance (25 %), wow factor (20 %), feasibility "
               "(20 %), skills fit (15 %), technical depth (10 %) and outputs (10 %). The biomethane digital "
               "twin scored 4.80/5 and the ranking is robust to ±5-point weight changes (Figure D1; details "
               "in 01_research/project_selection.md)."))
    s.append(fig(FIGS / "fig01_decision_matrix.png", "<b>Figure D1.</b> Weighted decision matrix of the 12 "
                 "candidate projects."))
    s.append(P("<b>Data policy.</b> Only public data and published literature were used. The machine-learning "
               "component is a surrogate of a mechanistic model trained on simulated data; no empirical plant "
               "data and no unpublished manuscript data were used. Facts that could not be verified (e.g. the "
               "exact 2025 number of European biomethane plants, Canadian national RNG capacity) were not "
               "used; they are listed in 01_research/sources.md."))


def main() -> None:
    D = load()
    s: list = []
    title_page(s, D)
    exec_summary(s, D)
    intro(s, D)
    objectives(s, D)
    s.append(PageBreak())
    methodology(s, D)
    s.append(CondPageBreak(9 * cm))
    results(s, D)
    s.append(PageBreak())
    discussion(s, D)
    limitations(s, D)
    s.append(CondPageBreak(8 * cm))
    conclusions(s, D)
    s.append(PageBreak())
    references(s, D)
    s.append(PageBreak())
    appendices(s, D)
    OUT.parent.mkdir(exist_ok=True)
    doc = Doc(str(OUT), title="MethaTwin – Final report", author="Louay Ouhibi",
              subject="ML-accelerated digital twin of an agricultural biomethane plant")
    doc.multiBuild(s)
    print("written", OUT)


if __name__ == "__main__":
    main()
