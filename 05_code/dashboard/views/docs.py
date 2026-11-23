"""How it works - what MethaTwin is in four steps, then methods, glossary, limitations and the report on click."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import core
import ui

ui.page_head("book", "How it works", "What is MethaTwin?",
             "A digital twin of a farm biomethane plant: a faithful copy you can try ideas on before anything is built.")

ui.verdict("info", "In one sentence", "MethaTwin answers “what if?” questions about a biomethane plant in seconds.",
           "It copies a plant of about 200 Nm³/h, the size of an average French farm site, from the feed to the gas grid, "
           "using public data and open tools only.")
ui.md(f"""
<div class="mt-answers" style="grid-template-columns:repeat(4,minmax(0,1fr))">
 <div class="mt-answer"><div class="top"><span class="l">{ui.icon("plant")}1 · Pick a start</span></div>
  <div class="d">On <b>Your plant</b>, start from a checked design.</div></div>
 <div class="mt-answer"><div class="top"><span class="l">{ui.icon("sliders")}2 · Change it</span></div>
  <div class="d">Move the feed, tank, gas-cleaning or market settings.</div></div>
 <div class="mt-answer"><div class="top"><span class="l">{ui.icon("ok")}3 · Read the answer</span></div>
  <div class="d">Biology, gas and money, in plain words. Numbers open on click.</div></div>
 <div class="mt-answer"><div class="top"><span class="l">{ui.icon("futures")}4 · Stress-test</span></div>
  <div class="d">Replay thousands of futures, then save and compare designs.</div></div>
</div>
<style>@media (max-width:860px){{.mt-answers{{grid-template-columns:1fr !important}}}}</style>
""")
st.write("")
if core.REPORT.exists():
    st.download_button("Download the full report (PDF)", core.REPORT.read_bytes(), file_name="MethaTwin_Final_Report.pdf",
                       mime="application/pdf", type="primary", icon=":material/download:")
st.write("")

with st.expander("What is inside *the models, step by step*", icon=":material/account_tree:"):
    st.image(str(core.FIGURES / "fig02_concept_flow.png"), width="stretch",
             caption="Mechanistic chain (top) and the optimisation loop with the fast models (bottom).")
    st.markdown(
        "- **Feed.** Dry matter, nitrogen and methane potential from FNR (2010); composition and COD factors from Klimiuk et al. "
        "(2015). Degradability D = BMP / (0.350 Nm³ CH₄/kg COD × ThOD), inerts = 1 − D. Maize is capped at 15 % of the tonnage "
        "(décret 2016-929).\n"
        "- **Digester (ADM1).** The international Anaerobic Digestion Model No. 1 in its BSM2 form (Rosen & Jeppsson 2006): 35 "
        "states, pH from the charge balance, 29 stiff equations solved to steady state. Kinetics calibrated on maize silage and "
        "cattle manure (Bułkowska et al. 2015); ammonia inhibition kept at the BSM2 value 0.0018 M. Stable means pH ≥ 6.8 and "
        "VFA ≤ 8 g COD/L.\n"
        "- **Gas cleaning (DWSIM).** Built and solved in DWSIM from Python: chilling, two-stage compression to 9 bar, a 10-stage "
        "water absorber, a flash recycled to compression, a CO₂ flash at 1.05 bar, an air stripper and the water loop. "
        "Peng–Robinson with gas–water parameters fitted to Henry's law (valid 10–15 °C).\n"
        "- **Fast models (surrogates).** 2,000 coupled simulations; runs kept only if the scrubber mass balance closes within "
        "0.1 %. Random forest, XGBoost and neural networks tuned by 5-fold cross-validation and judged on a 20 % held-out test set.\n"
        "- **Economics, optimisation and risk.** Building costs from the CRE 2024 survey (44,456 € per Nm³/h at 184 Nm³/h, "
        "six-tenths scaling), running costs from CRE medians; cost per MWh and NPV at 7 %, 15 years, 8,400 h a year. "
        "Optimisation by differential evolution on the fast models, each optimum re-checked by full simulation. Monte Carlo "
        "over the microbe settings and nine prices.")

with st.expander("Glossary *every term, in plain words*", icon=":material/menu_book:"):
    gl = pd.DataFrame([
        ["ADM1", "Anaerobic Digestion Model No. 1, the international standard model of the biology in a digester."],
        ["BSM2", "Benchmark Simulation Model No. 2, a published reference used to check ADM1 code."],
        ["BMP", "Biochemical methane potential: the methane a feed can give in a long lab test (Nm³ CH₄ per t VS)."],
        ["CIVE", "Cover crops grown between two main crops and harvested for energy."],
        ["HRT", "Hydraulic retention time: the days the feed spends in the digester; tank volume = feed × HRT."],
        ["VFA", "Volatile fatty acids: their build-up shows an overloaded or poisoned digester."],
        ["Free NH₃", "Un-ionised ammonia, toxic to the methane-making microbes; rises with nitrogen-rich feed, pH and heat."],
        ["K_I,NH3", "Ammonia tolerance of the microbes in ADM1; lower values mean more sensitive microbes."],
        ["k_dis", "Disintegration rate: how fast the solid feed falls apart (per day)."],
        ["HPWS", "High-pressure water scrubbing: CO₂ dissolves in water at 9 bar, methane mostly does not."],
        ["Methane slip", "Methane lost with the off-gas instead of reaching the grid."],
        ["HHV / Wobbe", "Heating value and Wobbe index: energy-quality rules for grid gas."],
        ["LCOE", "Levelised cost of energy: yearly building and running costs per MWh injected."],
        ["NPV", "Net present value: 15 years of money in minus money out at the discount rate, minus the investment."],
        ["CRE", "The French energy regulator; source of the cost data."],
        ["Surrogate", "A fast ML model trained to copy a slow simulator inside its sampled ranges."],
        ["Monte Carlo", "Repeating a calculation with randomly drawn uncertain inputs to see the spread of outcomes."],
    ], columns=["Term", "Meaning"])
    q = st.text_input("Search the glossary", placeholder="e.g. ammonia, LCOE, slip", key="gl_q")
    hit = gl[gl.Term.str.contains(q, case=False, regex=False) | gl.Meaning.str.contains(q, case=False, regex=False)] if q else gl
    if hit.empty:
        ui.empty("No matching term", "Try another word.", "info")
    else:
        st.dataframe(hit, hide_index=True, width="stretch", column_config={"Term": st.column_config.TextColumn(width="small"),
                                                                           "Meaning": st.column_config.TextColumn(width="large")})

with st.expander("Limits *read before using the results*", icon=":material/report:"):
    st.markdown(
        "- Checked against a benchmark, a lab digester and hand calculations, **not against a full-scale plant**.\n"
        "- **Steady state only**: start-up and feed changes are not simulated. One mixed tank, no post-digester.\n"
        "- The gas-solubility fit is valid at **10–15 °C**; drying, H₂S removal and O₂ removal are not modelled.\n"
        "- Costs are **top-down** from CRE averages (2023 €); no digestate revenue, taxes or financing structure.\n"
        "- The fast models are valid **only inside the setting ranges**; their cost is about 3 % optimistic at the optimum.")

with st.expander("Built with *tools and data*", icon=":material/build:"):
    ui.md('<dl class="mt-kv"><dt>Engine</dt><dd>ML surrogates of ADM1 + DWSIM, CRE-anchored techno-economics</dd>'
          '<dt>Tools</dt><dd>Python, SciPy, scikit-learn, XGBoost, DWSIM, pythonnet, Streamlit, Plotly, three.js</dd>'
          '<dt>Data</dt><dd>Public data and published literature only</dd></dl>')
