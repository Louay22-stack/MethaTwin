"""
Phase 1 - Weighted decision matrix for project selection.

Builds the candidate-project scoring table, writes it to
01_research/decision_matrix.csv and 01_research/decision_matrix.xlsx
(the .xlsx keeps live Excel formulas for the weighted total so a reviewer
can change a weight or a score and see the ranking update), and draws
06_figures/fig01_decision_matrix.png.

Run from the project root:  python 05_code/phase1_decision_matrix.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]

# --- Criteria and weights (sum = 1.00) -------------------------------------
CRITERIA = [
    ("market", "Relevance to 2026 market & job postings", 0.25),
    ("wow", "Recruiter impact / wow factor", 0.20),
    ("feasibility", "Feasibility (laptop, open tools, public data)", 0.20),
    ("fit", "Fit with skills (biogas, fermentation, ML, DWSIM)", 0.15),
    ("depth", "Technical depth & novelty", 0.10),
    ("outputs", "Clear demonstrable outputs", 0.10),
]
assert abs(sum(w for *_, w in CRITERIA) - 1.0) < 1e-9

# --- Candidates: (id, short name, description, scores, scoring rationale) ----
# Scores 1-5 per criterion in the order of CRITERIA.
CANDIDATES = [
    ("P01", "Biomethane plant digital twin + ML surrogate + TEA",
     "ADM1 co-digestion model (Python) coupled to a DWSIM biogas-upgrading flowsheet "
     "with biogenic-CO2 recovery; ML surrogate trained on simulated data for fast "
     "feed-blend/HRT optimisation; techno-economics (LCOE, NPV) benchmarked to literature.",
     [5, 5, 4, 5, 5, 5],
     "Hits the biggest job pool for the profile (biomethane: FR/DE/ES/CA policy targets); "
     "combines mass/energy balances, simulator, Python automation, ML and TEA in one story. "
     "Feasibility 4 (not 5): ADM1 stiffness and DWSIM-pythonnet coupling are real risks."),
    ("P02", "Fed-batch fermentation soft sensor & fault detection (IndPenSim)",
     "ML soft sensors (PLS on Raman, XGBoost/MLP on process data) and batch fault detection "
     "on the public 100-batch, 100 m3 IndPenSim penicillin dataset.",
     [4, 4, 5, 4, 3, 5],
     "Real public industrial-scale dataset, strong digital-biomanufacturing signal. "
     "Novelty 3: the dataset is already widely used for soft-sensor studies; no process "
     "design / balances / TEA, so it under-uses DWSIM and process-engineering skills."),
    ("P03", "Precision-fermentation protein TEA (BioSTEAM)",
     "Open-source process model and cost of goods for a recombinant food protein; "
     "titre-rate-yield sensitivity and scale-up economics.",
     [5, 4, 4, 3, 4, 4],
     "Very topical (EU Biotech Act, capacity gap) but strain/process data are mostly "
     "proprietary, so results rest on literature assumptions; weaker link to biogas background."),
    ("P04", "Biogas upgrading technology comparison (DWSIM)",
     "Water scrubbing vs amine vs membranes vs PSA: energy use, methane slip, cost.",
     [4, 3, 5, 5, 2, 4],
     "Directly useful for biomethane jobs, but well-trodden topic; becomes a sub-module of P01."),
    ("P05", "Biogenic CO2 from upgrading to e-methane / liquid CO2 (TEA)",
     "Capture, liquefaction or methanation of the upgrading off-gas with green H2.",
     [4, 4, 4, 4, 4, 4],
     "Rising topic (biogenic CO2 capture growing fast in EU) but H2 cost assumptions dominate; "
     "best included as a scenario inside P01."),
    ("P06", "Biogas CHP flexibilisation scheduling (Germany)",
     "MILP scheduling of gas storage + CHP against public day-ahead prices.",
     [4, 4, 4, 3, 4, 4],
     "Policy-driven (German Biomassepaket) but closer to energy-trading optimisation than bioprocess."),
    ("P07", "Lignocellulosic lactic-acid biorefinery TEA",
     "BioSTEAM model of pretreatment, fermentation, purification; MSP and LCA.",
     [3, 3, 4, 3, 3, 4],
     "Classic academic TEA; fewer matching job postings for a junior profile."),
    ("P08", "Fed-batch feeding optimisation with Bayesian optimisation",
     "Mechanistic E. coli / yeast fed-batch model; BO + DoE to maximise productivity.",
     [4, 4, 4, 4, 4, 4],
     "Good modelling showcase, but kinetic parameters come from literature only and the "
     "story is less tied to a concrete industrial asset."),
    ("P09", "Regional biomethane feedstock potential & plant siting (France)",
     "GIS of agricultural/agri-food residues and optimal plant siting.",
     [3, 3, 3, 3, 2, 4],
     "Data assembly heavy (heterogeneous public datasets), mostly GIS rather than process engineering."),
    ("P10", "Bioethanol plant heat integration (pinch analysis)",
     "DWSIM flowsheet + pinch analysis and heat-exchanger network.",
     [2, 2, 5, 4, 2, 4],
     "Solid engineering exercise but mature topic with low 2026 market pull."),
    ("P11", "Wastewater plant energy optimisation on BSM2 + ML",
     "Benchmark Simulation Model no. 2 with ML-based aeration/digester control.",
     [3, 3, 5, 4, 3, 4],
     "Well documented benchmark; job market is water utilities rather than bioprocess."),
    ("P12", "Microalgae biorefinery TEA",
     "Photobioreactor cultivation, harvesting, product split and economics.",
     [2, 3, 4, 3, 3, 4],
     "Interesting but commercially marginal; few junior postings."),
]


def build_dataframe() -> pd.DataFrame:
    rows = []
    for pid, name, desc, scores, why in CANDIDATES:
        row = {"id": pid, "project": name, "description": desc}
        for (key, _, _), s in zip(CRITERIA, scores):
            row[key] = s
        row["weighted_score"] = round(sum(s * w for (_, _, w), s in zip(CRITERIA, scores)), 2)
        row["rationale"] = why
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("weighted_score", ascending=False)
    df.insert(1, "rank", range(1, len(df) + 1))
    return df


def write_xlsx(df: pd.DataFrame, path: Path) -> None:
    """Excel version with live SUMPRODUCT formulas and the weights row on top."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Decision matrix"
    bold = Font(bold=True)
    head_fill = PatternFill("solid", fgColor="DCE8F7")
    ws["A1"] = "Weights (edit to test robustness)"
    ws["A1"].font = bold
    keys = [k for k, *_ in CRITERIA]
    first_col = 4  # D
    for j, (key, label, w) in enumerate(CRITERIA):
        c = first_col + j
        ws.cell(row=2, column=c, value=label).alignment = Alignment(wrap_text=True)
        ws.cell(row=3, column=c, value=w).number_format = "0%"
    ws.cell(row=3, column=3, value="weight").font = bold
    last_col_letter = get_column_letter(first_col + len(keys) - 1)
    hdr = ["ID", "Rank (static)", "Project"] + keys + ["Weighted score (formula)", "Rationale"]
    for j, h in enumerate(hdr, start=1):
        cell = ws.cell(row=5, column=j, value=h)
        cell.font = bold
        cell.fill = head_fill
    for i, r in enumerate(df.itertuples(index=False), start=6):
        ws.cell(row=i, column=1, value=r.id)
        ws.cell(row=i, column=2, value=r.rank)
        ws.cell(row=i, column=3, value=r.project)
        for j, key in enumerate(keys):
            ws.cell(row=i, column=first_col + j, value=getattr(r, key))
        f = (f"=SUMPRODUCT({get_column_letter(first_col)}{i}:{last_col_letter}{i},"
             f"${get_column_letter(first_col)}$3:${last_col_letter}$3)")
        ws.cell(row=i, column=first_col + len(keys), value=f).number_format = "0.00"
        ws.cell(row=i, column=first_col + len(keys) + 1, value=r.rationale)
    ws.column_dimensions["C"].width = 55
    for j in range(len(keys)):
        ws.column_dimensions[get_column_letter(first_col + j)].width = 16
    ws.column_dimensions[get_column_letter(first_col + len(keys) + 1)].width = 100
    ws.row_dimensions[2].height = 45
    # Second sheet: descriptions
    ws2 = wb.create_sheet("Descriptions")
    ws2.append(["ID", "Project", "Description"])
    for r in df.itertuples(index=False):
        ws2.append([r.id, r.project, r.description])
    ws2.column_dimensions["B"].width = 55
    ws2.column_dimensions["C"].width = 120
    wb.save(path)


def plot(df: pd.DataFrame, path: Path) -> None:
    """Horizontal bars (weighted score) + score heatmap, single blue ramp."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    d = df.sort_values("weighted_score")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.2),
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    fig.patch.set_facecolor("#fcfcfb")
    colors = ["#2a78d6" if r <= 3 else "#9ec5f4" for r in d["rank"]]
    labels = [f"{i}  {p}" for i, p in zip(d["id"], d["project"])]
    ax1.barh(labels, d["weighted_score"], color=colors, height=0.62)
    for y, v in enumerate(d["weighted_score"]):
        ax1.text(v + 0.04, y, f"{v:.2f}", va="center", color="#0b0b0b", fontsize=8)
    ax1.set_xlim(0, 5.4)
    ax1.set_xlabel("Weighted score (1-5)", color="#52514e")
    ax1.set_title("Weighted score (top 3 in dark blue)", loc="left", fontsize=10)
    for s in ["top", "right"]:
        ax1.spines[s].set_visible(False)
    ax1.tick_params(colors="#52514e", labelsize=8)
    ax1.xaxis.grid(True, color="#e6e5e0", linewidth=0.6)
    ax1.set_axisbelow(True)

    keys = [k for k, *_ in CRITERIA]
    mat = d[keys].to_numpy(dtype=float)
    cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list(
        "blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
    ax2.imshow(mat, cmap=cmap, vmin=1, vmax=5, aspect="auto",
               origin="lower")  # row order matches the bar chart
    for (i, j), v in np.ndenumerate(mat):
        ax2.text(j, i, int(v), ha="center", va="center", fontsize=8,
                 color="white" if v >= 4 else "#0b0b0b")
    ax2.set_xticks(range(len(keys)))
    ax2.set_xticklabels([f"{k}\n{int(w*100)}%" for k, _, w in CRITERIA], fontsize=8)
    ax2.set_yticks(range(len(d)))
    ax2.set_yticklabels(d["id"], fontsize=8)
    ax2.set_title("Criterion scores (1 = poor, 5 = excellent)", loc="left", fontsize=10)
    for s in ax2.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    df = build_dataframe()
    out = ROOT / "01_research"
    df.to_csv(out / "decision_matrix.csv", index=False)
    write_xlsx(df, out / "decision_matrix.xlsx")
    plot(df, ROOT / "06_figures" / "fig01_decision_matrix.png")
    # Robustness check: does the winner survive +-5 percentage-point weight shifts?
    keys = [k for k, *_ in CRITERIA]
    base_w = np.array([w for *_, w in CRITERIA])
    winners = set()
    for i in range(len(keys)):
        for j in range(len(keys)):
            if i == j:
                continue
            w = base_w.copy()
            w[i] += 0.05
            w[j] -= 0.05
            if (w < 0).any():
                continue
            s = df[keys].to_numpy() @ w
            winners.add(df.iloc[int(np.argmax(s))]["id"])
    print(df[["rank", "id", "project", "weighted_score"]].to_string(index=False))
    print("Winners under all +-5 pp pairwise weight shifts:", sorted(winners))


if __name__ == "__main__":
    main()
