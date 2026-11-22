"""
MethaTwin - interactive digital twin of an agricultural biomethane plant (application entry point).

Architecture
  app.py        application shell: page config, app bar, navigation, design console (sidebar)
  state.py      shared session state, reference designs, scenarios, cached evaluations
  core.py       model layer: ML surrogates of the ADM1 + DWSIM chain and the CRE-anchored TEA
  ui.py         interface components (KPI strip, spec tables, process flow diagram, ...)
  theme.py      design tokens, global CSS, Plotly template
  views/*.py    one file per page

Run from the project root:
    streamlit run 05_code/dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import theme as T  # noqa: E402

st.set_page_config(page_title="MethaTwin · Biomethane digital twin", page_icon=str(T.ASSETS / "logo_mark_dark.svg"),
                   layout="wide", initial_sidebar_state="auto")
st.markdown(T.CSS, unsafe_allow_html=True)

import state as S  # noqa: E402
import ui  # noqa: E402

try:
    S.sur()
except FileNotFoundError as e:                       # error state: models missing
    ui.md(f'<div class="mt-appbar"><div class="mt-brand"><img src="{T.svg_data_uri("logo_mark_dark.svg")}"/>'
          f'<span class="nm">Metha<span>Twin</span></span></div></div>')
    st.error("**The trained ML surrogates were not found.**\n\n" + str(e))
    st.code("python 05_code/step6b_surrogate.py", language="powershell")
    st.stop()

S.init()

# ------------------------------------------------------------------ pages ---
PAGES = [
    st.Page(str(HERE / "views" / "cockpit.py"), title="Plant cockpit", default=True),
    st.Page(str(HERE / "views" / "explorer.py"), title="Design explorer", url_path="explorer"),
    st.Page(str(HERE / "views" / "risk.py"), title="Risk analysis", url_path="risk"),
    st.Page(str(HERE / "views" / "library.py"), title="Designs & scenarios", url_path="designs"),
    st.Page(str(HERE / "views" / "validation.py"), title="Model validation", url_path="validation"),
    st.Page(str(HERE / "views" / "docs.py"), title="Documentation", url_path="docs"),
]
pg = st.navigation(PAGES, position="hidden")


# ------------------------------------------------------------ save dialog ---
@st.dialog("Save scenario")
def save_dialog() -> None:
    st.caption("Stores the current design, kinetics and market settings so you can compare and reload them "
               "on the Designs & scenarios page. Scenarios live for this browser session.")
    default = f"Scenario {len(st.session_state.scenarios) + 1}"
    name = st.text_input("Scenario name", value=default, max_chars=40)
    if name in st.session_state.scenarios:
        st.warning("A scenario with this name exists; saving will overwrite it.")
    c1, c2 = st.columns(2)
    if c1.button("Save", type="primary", width="stretch", disabled=not name.strip()):
        S.save_scenario(name.strip())
        st.session_state["_toast"] = f"Scenario “{name.strip()}” saved"
        st.rerun()
    if c2.button("Cancel", width="stretch"):
        st.rerun()


def on_preset() -> None:
    S.apply_preset()
    st.session_state["_toast"] = f"Loaded reference design: {st.session_state.preset}"


def on_reset() -> None:
    S.reset_all()
    st.session_state["_toast"] = "All inputs reset to the verified 200 Nm³/h optimum and default market"


# ------------------------------------------------------- design console -----
mods = S.modified_groups()
mod = lambda g: '<span class="mt-mod">modified</span>' if mods[g] else ""
with st.sidebar:
    ui.md('<div class="mt-console-head"><div class="k">Design console</div><div class="t">Plant configuration</div>'
          '<div class="s">Every page updates from these inputs.</div></div>')
    st.selectbox("Reference design", list(S.presets()), key="preset", on_change=on_preset,
                 help="Start from a saved design. 'Verified' designs were confirmed by the full ADM1 + DWSIM simulation.")
    ui.md(f'<div class="mt-group"><span class="n">01</span>Feed &amp; digester{mod("design")}</div>')
    st.slider("Maize silage (% of feed)", 0.0, 15.0, key="maize_pct", step=0.5,
              help="Capped at 15 % of tonnage by French décret 2016-929.")
    st.slider("Cover-crop silage, CIVE (% of feed)", 5.0, 45.0, key="cive_pct", step=0.5,
              help="Intermediate energy crops; exempt from the maize cap. CIVE data = grass-silage proxy.")
    s = st.session_state
    ui.md(f'<div class="mt-derived"><span>Cattle slurry</span><b>{100 - s.maize_pct - s.cive_pct:.1f} %</b></div>')
    st.slider("Feed rate (t/day)", 60.0, 160.0, key="feed", step=1.0, help="Fresh-matter feed to the digester.")
    st.slider("Hydraulic retention time (days)", 40.0, 110.0, key="hrt", step=1.0,
              help="Sets the digester volume: V = feed × HRT.")
    ui.md(f'<div class="mt-derived"><span>Digester volume</span><b>{s.feed * s.hrt:,.0f} m³</b></div>')
    ui.md('<div class="mt-group"><span class="n">02</span>Upgrading · water scrubber</div>')
    st.slider("Scrubber water (m³ per 1,000 Nm³ raw gas)", 100.0, 200.0, key="water", step=1.0,
              help="More water absorbs more CO₂ but costs pumping power and can lose methane.")
    st.slider("Flash pressure (bar)", 2.0, 3.5, key="pflash", step=0.05,
              help="Intermediate flash that recovers dissolved methane back to the compressor.")
    with st.expander(f"03 · Microbial kinetics{' · modified' if mods['kinetics'] else ''}", expanded=mods["kinetics"]):
        st.select_slider("Disintegration rate k_dis (1/d)", S.KD_OPTS, key="kdis",
                         help="Speed of solids breakdown. Calibrated 0.1 (Bułkowska 2015); BSM2 default 0.5.")
        st.select_slider("Ammonia inhibition K_I,NH3 (M)", S.KI_OPTS, key="ki",
                         help="Lower = microbes more sensitive to free ammonia. Nominal 0.0018 (BSM2).")
    with st.expander(f"04 · Market & finance{' · modified' if mods['market'] else ''}", expanded=mods["market"]):
        st.slider("Purchase tariff (€/MWh)", 100.0, 180.0, key="tariff", step=0.5,
                  help="2023 agricultural tariffs 111–169, average 152.8 (CRE 2024).")
        st.slider("Slurry cost (€/t)", 0.0, 45.0, key="slurry", step=0.5,
                  help="7.3 = transport only; 43.2 = full CRE effluent price including transport.")
        st.slider("CIVE silage cost (€/t)", 20.0, 60.0, key="cive_cost", step=0.5)
        st.slider("Maize silage cost (€/t)", 20.0, 60.0, key="maize_cost", step=0.5)
        st.slider("Electricity price (€/MWh)", 60.0, 250.0, key="el", step=1.0)
        st.slider("CAPEX multiplier (×)", 0.7, 1.4, key="capexf", step=0.05, help="1.0 = CRE-anchored estimate.")
        st.slider("Discount rate (%)", 3.0, 12.0, key="disc", step=0.5)
    st.write("")
    c1, c2 = st.columns(2)
    if c1.button("Save scenario", type="primary", width="stretch"):
        save_dialog()
    c2.button("Reset", on_click=on_reset, width="stretch")

if msg := st.session_state.pop("_toast", None):
    st.toast(msg, icon="✅")

# ------------------------------------------------------------- app bar ------
R = S.evaluate()
stable = R["p_stable"] >= 0.5 and R["pH"] >= 6.8 and R["VFA_gCOD_L"] <= 8
spec = R["BM_CO2_pct"] <= 2.5 and 10.7 <= R["HHV"] <= 12.8
valid = R["p_upg_valid"] >= 0.5
dot, txt = ("", "Design feasible") if (stable and spec and valid) else \
           ("warn", "Low simulator reliability") if (stable and spec) else ("bad", "Constraint violated")
ref = S.matches_reference()
ui.md(f'<div class="mt-appbar"><div class="mt-brand"><img src="{T.svg_data_uri("logo_mark_dark.svg")}"/>'
      f'<span class="nm">Metha<span>Twin</span></span><span class="ver">v2.0</span></div>'
      f'<div class="mt-appbar-right"><span class="mt-status"><span class="mt-dot {dot}"></span><span class="txt">{txt}</span></span>'
      f'<span class="mt-status"><span class="txt">Design · {"reference" if ref else "custom"}</span></span>'
      f'<span class="mt-status"><span class="txt">Engine · ML surrogate</span></span></div></div>')

with st.container(key="mtnav"):
    cols = st.columns(len(PAGES))
    for c, p in zip(cols, PAGES):
        c.page_link(p, label=p.title)

pg.run()

ui.md('<div class="mt-foot"><span>MethaTwin · open-source digital twin · public data only</span>'
      '<span>Results are model predictions, not investment advice</span></div>')
