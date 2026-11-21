"""Documentation - what MethaTwin is, how to use it, methods, glossary, limitations and the report."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import core
import theme as T
import ui

ui.page_head("Documentation", "How MethaTwin <em>works</em>",
             "Workflow, methods, glossary and limitations. The full 19-page report with references is available below.",
             "Author <b>Louay Ouhibi</b><br/>Data <b>public sources only</b>")

c1, c2 = st.columns([1.6, 1], gap="large")
with c1:
    ui.section("01", "What it is", "")
    st.markdown(
        "MethaTwin is a digital twin of an agricultural biomethane plant of about **200 Nm³/h**, the size of an average French "
        "site. It digests **cattle slurry, cover-crop (CIVE) silage and maize silage**, upgrades the biogas to grid quality by "
        "**high-pressure water scrubbing**, and recovers a **biogenic CO₂** stream. It answers *what-if* questions about "
        "design, operation and market conditions before a plant is built.")
    ui.section("02", "Typical workflow", "")
    st.markdown(
        "1. **Pick a reference design** in the console (left), e.g. a verified optimum.\n"
        "2. **Adjust inputs**: feed blend and rate, retention time, scrubber settings; open *Microbial kinetics* and "
        "*Market & finance* for uncertain parameters and prices.\n"
        "3. **Read the Plant cockpit**: verdict, readouts, live process flow diagram and constraint table.\n"
        "4. **Explore** sensitivities and two-input maps in the *Design explorer*.\n"
        "5. **Quantify risk** with a Monte Carlo run on the *Risk analysis* page.\n"
        "6. **Save scenarios** and compare them on *Designs & scenarios*; export tables as CSV.")
with c2:
    with st.container(border=True):
        st.image(str(T.ASSETS / "logo.svg"), width="stretch")
        ui.md('<dl class="mt-kv"><dt>Author</dt><dd>Louay Ouhibi, Industrial Biology Engineer (INSAT, Tunisia)</dd>'
              '<dt>Engine</dt><dd>ML surrogates of ADM1 + DWSIM, CRE-anchored TEA</dd>'
              '<dt>Stack</dt><dd>Python, SciPy, scikit-learn, XGBoost, DWSIM, pythonnet, Streamlit, Plotly</dd>'
              '<dt>Data</dt><dd>Public data and published literature only</dd></dl>')
        st.write("")
        if core.REPORT.exists():
            st.download_button("Download the full report (PDF)", core.REPORT.read_bytes(), file_name="MethaTwin_Final_Report.pdf",
                               mime="application/pdf", type="primary", width="stretch")

ui.section("03", "Methods", "expand a block for details")
st.image(str(core.FIGURES / "fig02_concept_flow.png"), width="stretch",
         caption="Mechanistic chain (top) and surrogate-based optimisation loop (bottom).")
with st.expander("Feed characterisation"):
    st.markdown("TS, VS, N and methane potential from FNR (2010); composition and COD factors from Klimiuk et al. (2015). "
                "Degradability D = BMP / (0.350 Nm³ CH₄/kg COD × ThOD), inerts = 1 − D. Maize is capped at 15 % of tonnage "
                "(décret 2016-929).")
with st.expander("Digester · ADM1"):
    st.markdown("IWA Anaerobic Digestion Model No. 1 in the BSM2 form (Rosen & Jeppsson 2006): 35 states, pH from the charge "
                "balance, 29 stiff ODEs solved to steady state. Kinetics calibrated on maize silage and cattle manure "
                "(Bułkowska et al. 2015), except ammonia inhibition kept at the BSM2 value 0.0018 M. Stability screen: "
                "pH ≥ 6.8 and VFA ≤ 8 g COD/L (study assumption).")
with st.expander("Upgrading · DWSIM water scrubber"):
    st.markdown("Flowsheet built and solved in DWSIM from Python: chilling, two-stage compression to 9 bar, 10-stage absorber, "
                "intermediate flash recycled to compression, CO₂ flash at 1.05 bar, air stripper, water loop. Peng–Robinson "
                "with gas–water interaction parameters fitted to Henry's law (valid 10–15 °C).")
with st.expander("Machine-learning surrogates"):
    st.markdown("2,000 Latin-hypercube coupled simulations; runs kept only if the scrubber mass balance closes within 0.1 %. "
                "Random forest, XGBoost and neural networks tuned by 5-fold cross-validation and judged on a 20 % held-out "
                "test set. A physics-informed flash saturation index feeds the scrubber models.")
with st.expander("Economics, optimisation and risk"):
    st.markdown("CAPEX from the CRE 2024 survey (44,456 € per Nm³/h at 184 Nm³/h, six-tenths scaling by component), OPEX from "
                "CRE medians; LCOE and NPV at 7 %, 15 years, 8,400 h/yr. Optimisation by differential evolution on the "
                "surrogates, each optimum re-verified by full simulation. Monte Carlo over kinetics and nine prices.")

ui.section("04", "Glossary", "search any term")
gl = pd.DataFrame([
    ["ADM1", "Anaerobic Digestion Model No. 1, the IWA standard model of the biology in a digester."],
    ["BSM2", "Benchmark Simulation Model No. 2, a published reference implementation used to verify ADM1 code."],
    ["BMP", "Biochemical methane potential: methane a feed can yield in a long batch test (Nm³ CH₄ per t VS)."],
    ["CIVE", "Cultures intermédiaires à vocation énergétique: cover crops grown between main crops for energy."],
    ["HRT", "Hydraulic retention time: average days the feed spends in the digester; V = feed × HRT."],
    ["VFA", "Volatile fatty acids: intermediates whose build-up signals an overloaded or inhibited digester."],
    ["Free NH₃", "Un-ionised ammonia, toxic to methanogens; rises with nitrogen-rich feed, pH and temperature."],
    ["K_I,NH3", "Ammonia inhibition constant in ADM1; lower values mean more sensitive microbes."],
    ["k_dis", "Disintegration rate: how fast solid organic matter breaks down (1/day)."],
    ["HPWS", "High-pressure water scrubbing: CO₂ dissolves in water at 9 bar, methane mostly does not."],
    ["Methane slip", "Share of methane lost with the off-gas instead of reaching the grid."],
    ["HHV / Wobbe", "Higher heating value and Wobbe index: energy-quality specifications of grid gas."],
    ["LCOE", "Levelised cost of energy: annualised investment plus operating cost per MWh injected."],
    ["NPV", "Net present value of 15 years of cash flows at the discount rate, minus the investment."],
    ["CRE", "Commission de régulation de l'énergie, the French energy regulator; source of the cost data."],
    ["Surrogate", "A fast ML model trained to reproduce a slow simulator inside its sampled ranges."],
    ["Monte Carlo", "Repeating a calculation with randomly sampled uncertain inputs to get a distribution."],
], columns=["Term", "Meaning"])
q = st.text_input("Search glossary", placeholder="e.g. ammonia, LCOE, slip", label_visibility="collapsed", key="gl_q")
hit = gl[gl.Term.str.contains(q, case=False) | gl.Meaning.str.contains(q, case=False)] if q else gl
if hit.empty:
    ui.empty("No matching term", "Try another keyword.")
else:
    st.dataframe(hit, hide_index=True, width="stretch", column_config={"Term": st.column_config.TextColumn(width="small"),
                                                                       "Meaning": st.column_config.TextColumn(width="large")})

ui.section("05", "Limitations", "read before using results")
st.markdown(
    "- Validated against a benchmark, a lab digester and hand calculations, **not against a full-scale plant**.\n"
    "- **Steady state only**; start-up and feed changes are not simulated. Single CSTR, no post-digester.\n"
    "- Gas-solubility fit valid at **10–15 °C**; drying, H₂S removal and O₂ removal are not modelled.\n"
    "- Costs are **top-down** from CRE averages (2023 €); no digestate revenue, taxes or financing structure.\n"
    "- Surrogates are valid **only inside the console ranges**; their LCOE is ≈ 3 % optimistic at the optimum.")
