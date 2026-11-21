"""
Phase 2 - Builds the project-definition PDF (02_definition/Project_Definition.pdf)
and the concept block-flow figure (06_figures/fig02_concept_flow.png).

Run from the project root:  python 05_code/phase2_definition_pdf.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "06_figures" / "fig02_concept_flow.png"
PDF = ROOT / "02_definition" / "Project_Definition.pdf"

INK, MUTED, BLUE, LIGHT = "#0b0b0b", "#52514e", "#2a78d6", "#cde2fb"


# ---------------------------------------------------------------- figure ----
def concept_figure() -> None:
    """Block-flow diagram of the digital-twin chain."""
    fig, ax = plt.subplots(figsize=(10, 2.9))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 30)
    ax.axis("off")

    def box(x, y, w, h, title, sub, strong=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc=BLUE if strong else LIGHT, ec="none"))
        c = "white" if strong else INK
        ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
                fontsize=8.5, weight="bold", color=c)
        ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center", fontsize=7, color=c)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=10, color=MUTED, lw=1.1))

    y = 17
    box(1, y, 14, 10, "Feedstock mix", "manure / silage /\nagri-food residues")
    box(20, y, 15, 10, "Anaerobic digestion", "ADM1 (Python,\nBSM2-validated)", strong=True)
    box(40, y, 15, 10, "Biogas upgrading", "DWSIM flowsheet\n(pythonnet automation)", strong=True)
    box(60, y, 15, 10, "Products", "grid biomethane\n+ biogenic CO2 + digestate")
    box(80, y, 18, 10, "Techno-economics", "CAPEX/OPEX, LCOE,\nNPV, Monte Carlo")
    for x1, x2 in [(15.4, 19.6), (35.4, 39.6), (55.4, 59.6), (75.4, 79.6)]:
        arrow(x1, y + 5, x2, y + 5)

    box(20, 1.5, 35, 9, "Design of experiments -> ML surrogate",
        "Latin hypercube runs; RF / XGBoost / MLP; held-out test")
    box(62, 1.5, 36, 9, "Multi-objective optimisation",
        "min LCOE, max CH4 yield, stability constraints;\noptimum re-verified on full model")
    arrow(37.5, 16.6, 37.5, 11.0)
    arrow(55.4, 6, 61.6, 6)
    fig.tight_layout(pad=0.2)
    fig.savefig(FIG, dpi=220)
    plt.close(fig)


# ------------------------------------------------------------------- pdf ----
def build_pdf() -> None:
    ss = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica",
                          fontSize=8.6, leading=11.2, alignment=TA_JUSTIFY, spaceAfter=3)
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontName="Helvetica-Bold",
                        fontSize=14.5, leading=18, textColor=colors.HexColor(INK), spaceAfter=2)
    sub = ParagraphStyle("sub", parent=body, fontSize=8.6, textColor=colors.HexColor(MUTED),
                         alignment=1, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=10,
                        leading=12, textColor=colors.HexColor(BLUE), spaceBefore=6, spaceAfter=2)
    cell = ParagraphStyle("cell", parent=body, fontSize=7.6, leading=9.4, alignment=0, spaceAfter=0)
    cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
    small = ParagraphStyle("small", parent=body, fontSize=6.9, leading=8.6, alignment=0)

    def P(t, s=body):
        return Paragraph(t, s)

    def table(rows, widths, header=True):
        data = [[P(c, cellb if (header and i == 0) else cell) for c in r]
                for i, r in enumerate(rows)]
        t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
        style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9d8d3")),
                 ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
        if header:
            style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1fc")))
        t.setStyle(TableStyle(style))
        return t

    W = A4[0] - 3.2 * cm
    s = []
    s.append(P("MethaTwin: an ML-accelerated digital twin of an agricultural "
               "biomethane plant, from digester to grid", h1))
    s.append(P("Project definition &middot; Louay Ouhibi, Industrial Biology Engineer (INSAT) "
               "&middot; 20 November 2026 &middot; v1.0 for approval", sub))

    s.append(P("1. Context and market motivation", h2))
    s.append(P(
        "Biomethane is the bioprocess segment with the most active policy pull in the target job "
        "markets. France had <b>803 injecting sites and 15.5 TWh/yr of capacity</b> at the end of "
        "2025 [S1]. Its PPE3 targets <b>44 TWh in 2030</b> [S2]. Yet the capacity added in 2025 "
        "fell <b>40 %</b> [S1]. Spain targets 20 TWh of biogas in 2030 [S11]. Germany's 2025 "
        "Biomassepaket pushes flexible operation [S10]. Quebec requires 10 % RNG in its gas "
        "network by 2030 [S12]. At EU level, biomethane grew 19 %/yr over 2020-2025 [S5] and "
        "European capacity passed 8 bcm/yr in 2026 [S4]. Even so, only about 21 bcm of the "
        "35 bcm REPowerEU goal is expected by 2030 [S6]. The main brake is <b>cost</b>. The "
        "average EU production cost is about EUR 75-80/MWh, small plants are far more expensive "
        "than large ones, and the French median LCOE is about EUR 130/MWh [S6]. Meanwhile, "
        "<b>biogenic CO2</b> from upgrading is becoming a co-product. 125 plants captured "
        "1.17 Mt in 2025 [S6]. Employers in this field ask for mass and energy balances, "
        "process simulation and sizing [J6-J8]. In bioprocess roles they increasingly ask for "
        "Python, data analysis and digital-twin skills [J1, J2, J4, J5, L6]. This project is "
        "built to show all of these on one realistic plant."))

    s.append(P("2. Problem statement", h2))
    s.append(P(
        "Designing or retrofitting a biomethane plant means choosing the feedstock blend, "
        "retention time, temperature and upgrading conditions together. These choices interact "
        "non-linearly through digester biology (ADM1), gas separation and economics. "
        "Mechanistic chains are accurate but too slow to explore thousands of options. Purely "
        "empirical models need plant data that is not public. <b>Question:</b> can a validated "
        "mechanistic digital twin, accelerated by a machine-learning surrogate, identify "
        "operating and design points that lower the levelised cost of biomethane while staying "
        "biologically stable and meeting grid-injection quality?"))

    s.append(P("3. SMART objectives", h2))
    s.append(table([
        ["#", "Objective (specific, measurable)", "Success metric", "Due"],
        ["O1", "Implement a steady-state and dynamic ADM1 (Python) for a CSTR co-digester, "
               "with feedstock characterisation from literature.",
         "Steady state within 1 % of the BSM2 ADM1 reference values [L2]; COD and N balances "
         "close within 0.5 %.", "W1-W2"],
        ["O2", "Build the upgrading flowsheet in DWSIM (pre-treatment, compression, CO2 "
               "removal, biogenic-CO2 stream), driven from Python.",
         "Mass balance closure &lt; 0.5 %, energy &lt; 1 %; CH4 recovery, specific energy "
         "(kWh/Nm3) and methane slip within published ranges [L7, L8].", "W2-W3"],
        ["O3", "Run a design of experiments of 2,000 or more coupled simulations and train ML "
               "surrogates (RF, XGBoost, MLP).",
         "R2 of at least 0.95 on a held-out test set for CH4 output and LCOE; inference at "
         "least 100x faster than the full chain.", "W3-W4"],
        ["O4", "Multi-objective optimisation of blend, HRT, temperature and upgrading "
               "pressure, under stability and gas-quality constraints.",
         "Pareto front; optimum re-simulated on the full model with less than 3 % deviation; "
         "LCOE gain versus the base case quantified.", "W4-W5"],
        ["O5", "Techno-economic and uncertainty analysis (CAPEX, OPEX, LCOE, NPV, Monte Carlo, "
               "CO2-revenue scenario).",
         "Base-case LCOE compared with the EU ranges in [S6]; tornado and Monte Carlo P10/P50/P90.",
         "W5"],
        ["O6", "Publish a reproducible package: git repository, report, figures and a small "
               "interactive dashboard.",
         "Full re-run from README instructions on a clean environment.", "W6"],
    ], [0.8 * cm, 7.0 * cm, 7.0 * cm, 1.0 * cm]))

    s.append(P("4. Scope and limits", h2))
    s.append(P(
        "<b>In scope:</b> one agricultural co-digestion plant sized from public statistics. "
        "15.5 TWh/yr over 803 sites [S1] gives about 19 GWh/yr per site. At about 10.9 kWh "
        "(HHV) per Nm3 of biomethane and about 8,400 h/yr, that is roughly 200 Nm3/h of "
        "biomethane. The scope covers a mesophilic CSTR (with thermophilic as a sensitivity), "
        "membrane or water-scrubbing upgrading, biogenic-CO2 recovery as a scenario, and a "
        "European (French) cost basis. <b>Out of scope:</b> lab work, detailed mechanical "
        "design, permitting, and digestate agronomy beyond a mass value. <b>Data rule:</b> "
        "public data and literature only, with every source traced in 03_data. The user's "
        "unpublished ML-for-AD manuscript and its data are not used. The ML here is a "
        "<i>surrogate of a mechanistic model</i>, not an empirical predictor of plant data."))

    s.append(Image(str(FIG), width=W, height=W * 2.9 / 10))
    s.append(P("Figure 1: Concept of the digital-twin chain and the surrogate-based optimisation loop.",
               small))

    s.append(P("5. Methodology", h2))
    meth = [
        ("Feed characterisation.", "Literature composition data (solids, volatile solids, "
         "carbohydrates, proteins, lipids, methane potential) converted to ADM1 input "
         "fractions. Each value is logged with its source and a range for the uncertainty analysis."),
        ("Digester model.", "ADM1 in Python, cross-checked against the BSM2 formulation and "
         "the open PyADM1 code [L1-L3]. Outputs: biogas flow and composition, pH, VFA, free "
         "ammonia, and stability indicators."),
        ("Upgrading.", "DWSIM flowsheet automated through pythonnet. If a unit operation is "
         "missing (for example a gas-permeation membrane), it is written as a documented "
         "Python unit model and cross-validated."),
        ("Balances.", "COD, carbon, nitrogen and energy balances closed at every step "
         "(digester heat demand and compression power)."),
        ("Machine learning.", "Latin-hypercube design over the decision variables. Surrogates "
         "(RF, XGBoost, MLP) are tuned by cross-validation and judged only on a held-out test "
         "set. Feature importance and partial dependence are used for interpretation."),
        ("Optimisation.", "NSGA-II or differential evolution on the surrogate. The selected "
         "optimum is re-verified on the full mechanistic chain."),
        ("TEA.", "Equipment cost by scaling laws from cited references, OPEX, feedstock and "
         "utility prices, LCOE, NPV and IRR. Sensitivity (tornado chart) and Monte Carlo. "
         "Hand calculations are compared with the model at each validation step."),
    ]
    for k, v in meth:
        s.append(P(f"<b>{k}</b> {v}"))

    s.append(P("6. Tools", h2))
    s.append(P(
        "Python 3.14 (numpy, scipy for stiff ODEs, pandas, scikit-learn, xgboost, pymoo, "
        "matplotlib), DWSIM with pythonnet, openpyxl and reportlab for the deliverables, "
        "Streamlit for the dashboard, and git. All are free and open source."))

    s.append(P("7. Expected deliverables", h2))
    s.append(P(
        "Validated ADM1 module and DWSIM flowsheet (04_models_and_simulations); a documented "
        "simulation dataset with its origin (03_data); trained surrogates with test metrics; "
        "a Pareto front and optimal operating window; a TEA workbook; about 10 "
        "publication-quality figures (06_figures); a reusable Python package with tests "
        "(05_code); a final PDF report (07_report); a README for reproduction; a git "
        "repository ready for GitHub; and three CV and LinkedIn bullet points."))

    s.append(P("8. Timeline (6 work-weeks, after approval)", h2))
    s.append(table([
        ["Week", "W1", "W2", "W3", "W4", "W5", "W6"],
        ["Work", "Data, feed characterisation, ADM1", "ADM1 validation; DWSIM build",
         "Coupling, balances, DoE runs", "Surrogates, test metrics", "Optimisation, TEA, Monte Carlo",
         "Report, dashboard, repository"],
    ], [1.2 * cm] + [2.43 * cm] * 6))

    s.append(P("9. Risks and mitigation", h2))
    s.append(table([
        ["Risk", "Likelihood / impact", "Mitigation"],
        ["ADM1 stiffness makes runs slow or unstable", "Medium / High",
         "Implicit BDF/LSODA solver, DAE treatment of the pH and gas states as in BSM2, "
         "steady-state solve for the DoE, numba if needed."],
        ["DWSIM (Avalonia build) automation fails with pythonnet on Python 3.14",
         "Medium / Medium",
         "Test on day 1; fall back to a separate Python 3.12 environment, or to Python unit "
         "models validated against DWSIM GUI runs. Logged in LOG.md."],
        ["Feedstock data uncertain or inconsistent", "High / Medium",
         "Use ranges rather than point values; Monte Carlo; report P10/P50/P90; cite every value."],
        ["Cost data dated or not comparable", "Medium / Medium",
         "Index to a common year with CEPCI; report uncertainty bands; compare with the IFRI "
         "ranges [S6]."],
        ["Surrogate extrapolates outside the training domain", "Medium / High",
         "Bounded design space, out-of-domain checks, and re-verification on the full model."],
        ["Overlap with the unpublished manuscript", "Low / High",
         "Simulated and literature data only; different research question; explicit statement "
         "in the README and report."],
    ], [5.0 * cm, 2.6 * cm, 8.2 * cm]))

    s.append(P("10. Project selection (summary of Phase 1)", h2))
    s.append(P(
        "Twelve candidate projects were scored 1-5 on six weighted criteria: market relevance "
        "25 %, recruiter impact 20 %, feasibility 20 %, skills fit 15 %, depth 10 % and outputs "
        "10 %. The full matrix is in 01_research/decision_matrix.xlsx. This project (P01) "
        "scored <b>4.80</b>, ahead of an IndPenSim fermentation soft sensor (P02, 4.20) and a "
        "precision-fermentation TEA (P03, 4.10). P01 stays first under every pairwise "
        "+/-5-point weight shift. P02 is strong on data but offers little novelty and no "
        "process design, balances or economics. P03 is topical but depends on proprietary "
        "process data. P01 combines simulation, balances, ML and TEA, and can be validated "
        "against published benchmarks."))
    s.append(Image(str(ROOT / "06_figures" / "fig01_decision_matrix.png"), width=W, height=W * 1040 / 2200))
    s.append(P("Figure 2: Weighted decision matrix for the 12 candidate projects.", small))

    s.append(P("References", h2))
    refs = [
        "[S1] SDES, Tableau de bord biométhane injecté, T4 2025 - statistiques.developpement-durable.gouv.fr",
        "[S2] NaTran et al., Panorama des gaz renouvelables 2025, conférence de presse 09/04/2026 - natrangroupe.com",
        "[S4] gasworld, Europe biomethane passes 8 bcm production capacity, 01/07/2026",
        "[S5] IEA, Renewables 2026 - Biogases - iea.org/reports/renewables-2026/biogases",
        "[S6] IFRI (Cornot-Gandolphe), The European Biomethane Sector at a Critical Juncture, June 2026 - ifri.org",
        "[S10] BDEW, Bundestag hat Biogaspaket verabschiedet - bdew.de",
        "[S11] MITECO, nota de prensa, mayo 2026 - miteco.gob.es",
        "[S12] Waste Dive, Canada's clean fuel programs sees 417% jump in RNG in 2024, 13/08/2025",
        "[J1-J8] Job postings: COLIPI, Fermify, MicroHarvest, NMBU, Vitol BioMethane, Aventa, Symbioz (URLs in sources.md)",
        "[L1] Batstone et al. (2002) ADM1, IWA STR 13. [L2] Rosen &amp; Jeppsson (2006) ADM1 in BSM2, Lund Univ. "
        "[L3] PyADM1, bioRxiv 2021.03.03.433746. [L6] Caccavale et al. (2024) Front. Chem. Eng., "
        "doi:10.3389/fceng.2024.1494244. [L7] Persson (2013) IEA Task 37. [L8] Bauer et al. (2013) SGC 270.",
        "Full URLs and verification status: 01_research/sources.md",
    ]
    for r in refs:
        s.append(P(r, small))

    doc = SimpleDocTemplate(str(PDF), pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                            topMargin=1.3 * cm, bottomMargin=1.3 * cm,
                            title="MethaTwin - Project definition",
                            author="Louay Ouhibi")

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawRightString(A4[0] - 1.6 * cm, 0.8 * cm, f"MethaTwin - project definition - p. {d.page}")
        canvas.restoreState()

    doc.build(s, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    concept_figure()
    build_pdf()
    print("written:", PDF)
