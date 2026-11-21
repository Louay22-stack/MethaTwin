"""Model validation - evidence that each block of the twin reproduces an independent reference."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import core
import state as S
import theme as T
import ui

RES = S.res()
b, sp = RES["bsm2"], RES["speed"]

ui.page_head("Model validation", "Can the twin be <em>trusted</em>?",
             "Every block was checked against an independent reference before being coupled: a published benchmark, measured "
             "lab data, a hand calculation, French market data, and a held-out test set for the ML surrogates.",
             "Scope <b>simulator fidelity</b><br/>Not validated <b>against a full-scale plant</b>")

ui.kpis([
    {"label": "ADM1 vs BSM2", "value": f"{b['n_pass']}/{b['n_variables']}", "unit": "within 1 %", "color": T.TEAL,
     "delta": f"max error {b['max_abs_rel_err_pct']:.1e} %", "cls": "good"},
    {"label": "DWSIM vs hand calc.", "value": "−0.26", "unit": "%", "color": T.BLUE, "delta": "compressor power 44.77 / 44.89 kW", "cls": "good"},
    {"label": "Surrogates · min test R²", "value": "0.992", "unit": "", "color": T.VIOLET, "delta": "train–test gap ≤ 0.0044", "cls": "good"},
    {"label": "TEA vs CRE median", "value": "129.3", "unit": "€/MWh", "color": T.CORAL, "delta": "CRE 129.6 (feed-corrected)", "cls": "good"},
    {"label": "Speed-up", "value": f"{sp['speedup_batch']:,.0f}", "unit": "×",
     "delta": f"{1000 * sp['surrogate_batch_per_point_s']:.2f} ms vs {sp['mean_coupled_simulation_s']:.1f} s"},
])

ui.section("01", "Validation chain", "each check, its reference and the outcome")
chain = pd.DataFrame([
    ["Toolchain", "DWSIM compressor power", "Hand calculation, NIST cp", "−0.26 %, ΔT 0.9 K", "Pass"],
    ["Feed", "BMP ≤ theoretical maximum", "Stoichiometry", "All three feeds", "Pass"],
    ["Feed", "Inert fractions", "Biernacki 2013 / Koch 2010 (via Klimiuk 2015)", "Maize 0.26 vs 0.14 (tol. ±0.15)", "Pass"],
    ["Feed", "COD values", "Klimiuk 2015, Table 3", "Within 0.6 %", "Pass"],
    ["Feed", "Lipid / carbohydrate split", "Klimiuk 2015 measured mix", "X_li 0.105 vs 0.048", "Fail · documented"],
    ["Feed", "Nitrogen consistency", "FNR 2010 total N", "+36 / −32 / −41 %", "Fail · documented"],
    ["Digester", "ADM1 vs BSM2 benchmark", "Rosen & Jeppsson 2006", "36/36 within 1 %", "Pass"],
    ["Digester", "COD / N / C balances", "Conservation", "< 10⁻⁶ %", "Pass"],
    ["Digester", "Lab digester, 5 outputs", "Bułkowska 2015", "4 of 5 in range (acetate high)", "Partial"],
    ["Upgrading", "Gas solubility, fitted kij", "Henry's law (Sander 2023, NIST)", "Within 15 % at 10–15 °C", "Pass"],
    ["Upgrading", "Mass balance", "Conservation", "0.001 %", "Pass"],
    ["Upgrading", "Energy balance", "Conservation", "1.5 % (objective 1 %)", "Fail · documented"],
    ["Surrogates", "Generalisation", "Held-out test + 5-fold CV", "Gap ≤ 0.0044", "Pass"],
    ["Surrogates", "Cascade error propagation", "Predicted vs true features", "R² unchanged", "Pass"],
    ["Economics", "LCOE benchmark", "CRE 2024 survey", "129.3 vs 129.6 €/MWh", "Pass"],
    ["Optimisation", "Optima re-simulated", "Full ADM1 + DWSIM", "4 / 4 within 1.5 % of target", "Pass"],
], columns=["Block", "Check", "Reference", "Result", "Outcome"])
f1, f2 = st.columns([2, 3], vertical_alignment="bottom")
blocks = f1.multiselect("Filter by block", sorted(chain.Block.unique()), placeholder="All blocks", key="val_blocks")
only_issues = f2.toggle("Show only checks that did not fully pass", key="val_issues")
view = chain[chain.Block.isin(blocks)] if blocks else chain
if only_issues:
    view = view[view.Outcome != "Pass"]
if view.empty:
    ui.empty("No checks match these filters", "Clear the block filter or switch off the toggle.")
else:
    st.dataframe(view, hide_index=True, width="stretch",
                 column_config={"Block": st.column_config.TextColumn(width="small"),
                                "Check": st.column_config.TextColumn(width="medium"),
                                "Reference": st.column_config.TextColumn(width="medium"),
                                "Outcome": st.column_config.TextColumn(width="small")})

ui.section("02", "Surrogate accuracy", "20 % held-out test set, never used for tuning · sortable")
m, ov = RES["metrics"], RES["over"].set_index("target")
nice = {"digester_stable": "Digester stable", "upgrading_valid": "Simulator valid", "spec_ok": "Grid spec met",
        "CH4_Nm3_h": "Methane production", "y_CH4_dry": "Biogas CH₄ fraction", "pH": "Digester pH",
        "VFA_gCOD_L": "Volatile fatty acids", "free_NH3_mgN_L": "Free ammonia", "biomethane_Nm3_h": "Biomethane flow",
        "BM_CO2_pct": "CO₂ in biomethane", "BM_O2_ppm": "O₂ in biomethane", "CH4_slip_pct": "Methane slip",
        "P_el_upg_kW": "Scrubber electricity"}
rows = []
for r in m.itertuples():
    o = ov.loc[r.target] if r.target in ov.index else None
    rows.append({"Output": nice[r.target], "Block": r.block.capitalize(), "Model": r.best_model,
                 "Metric": "AUC" if r.block == "classifier" else "R²",
                 "Test score": r.test_AUC if r.block == "classifier" else r.test_R2,
                 "Train R²": None if o is None else o.R2_train, "CV R²": None if o is None else o.R2_cv,
                 "Train–test gap": None if o is None else o.gap_train_minus_test, "n train": r.n_train, "n test": r.n_test})
sdf = pd.DataFrame(rows)
blk = st.segmented_control("Show", ["All", "Digester", "Upgrading", "Classifier"], default="All", key="sur_blk") or "All"
sv = sdf if blk == "All" else sdf[sdf.Block == blk]
st.dataframe(sv, hide_index=True, width="stretch",
             column_config={"Test score": st.column_config.ProgressColumn(format="%.4f", min_value=0.9, max_value=1.0),
                            "Train R²": st.column_config.NumberColumn(format="%.4f"),
                            "CV R²": st.column_config.NumberColumn(format="%.4f"),
                            "Train–test gap": st.column_config.NumberColumn(format="%.4f",
                                                                            help="Overfitting shows up as a large gap, not a high score")})
ui.md('<div class="mt-note"><b>Why R² ≥ 0.99 is not overfitting:</b> the data come from a deterministic simulator with no '
      'measurement noise, and training, cross-validation and test scores agree (gap ≤ 0.0044). These scores measure fidelity to '
      'the simulator, not accuracy against real plants.</div>')

ui.section("03", "Against measured and market data", "")
c1, c2 = st.columns(2, gap="medium")
with c1, st.container(border=True):
    ui.panel_head("Lab digester · Bułkowska et al. 2015", "no parameter adjusted")
    ui.spec_table([
        {"name": "CH₄ content", "value": "53.6 %", "limit": "50–58 %", "status": ui.chip("ok", "in range")},
        {"name": "pH", "value": "7.19", "limit": "6.8–7.4", "status": ui.chip("ok", "in range")},
        {"name": "Propionate", "value": "0.69 kg/m³", "limit": "0.3–0.9", "status": ui.chip("ok", "in range")},
        {"name": "Biogas (dry)", "value": "83 Ndm³/d", "limit": "65–100", "status": ui.chip("ok", "in range")},
        {"name": "Acetate", "value": "0.85 kg/m³", "limit": "0.2–0.6", "status": ui.chip("bad", "over-predicted")},
    ])
with c2, st.container(border=True):
    ui.panel_head("Cost model · CRE 2024 survey", "French biomethane plants")
    ui.spec_table([
        {"name": "LCOE, feed-corrected", "value": "129.3 €/MWh", "limit": "median 129.6", "status": ui.chip("ok", "match")},
        {"name": "LCOE, reference plant", "value": "152.1 €/MWh", "limit": "Q3 146.0", "status": ui.chip("warn", "feed-driven")},
        {"name": "Electricity share", "value": "8.8 %", "limit": "9.2 %", "status": ui.chip("ok", "close")},
        {"name": "CAPEX share of cost", "value": "36 %", "limit": "≈ 40 %", "status": ui.chip("ok", "close")},
        {"name": "Feed cost", "value": "53.5 €/MWh", "limit": "median 30.7", "status": ui.chip("info", "slurry-rich blend")},
    ])

with st.expander("Validation figures from the report"):
    st.image(str(core.FIGURES / "fig04_adm1_validation_and_base_case.png"), width="stretch")
    st.image(str(core.FIGURES / "fig06_surrogate_test_performance.png"), width="stretch")
