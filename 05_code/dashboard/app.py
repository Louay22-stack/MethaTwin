"""
MethaTwin dashboard - interactive front end to the digital twin.

Every number on the "Simulator", "Explore" and "Risk" tabs comes from the trained ML surrogates
of the ADM1 + DWSIM chain (step 6) and the CRE-anchored TEA (step 7); no DWSIM install needed.
The "Optimisation" and "Validation" tabs show saved full-simulation results.

Run from the project root:
    streamlit run 05_code/dashboard/app.py
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402
import theme as T  # noqa: E402
from methatwin.tea import Econ  # noqa: E402

st.set_page_config(page_title="MethaTwin · Biomethane digital twin", page_icon=str(T.ASSETS / "logo_mark.svg"),
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(T.CSS, unsafe_allow_html=True)
PLOT_CFG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}


@st.cache_resource(show_spinner="Loading the ML surrogates…")
def get_sur():
    return core.load_surrogate()


@st.cache_data
def get_res():
    return core.saved_results()


try:
    SUR = get_sur()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()
RES = get_res()
PRESETS = core.presets(RES)
DEFAULT_PRESET = "Verified optimum · 200 Nm³/h"
KD_OPTS = [0.05, 0.06, 0.075, 0.1, 0.13, 0.16, 0.2, 0.25, 0.32, 0.4, 0.5]
KI_OPTS = [0.0012, 0.0014, 0.0016, 0.0018, 0.0022, 0.0027, 0.0033, 0.0041, 0.005, 0.0062, 0.0075, 0.0084]
E0 = Econ()
ECON_DEFAULTS = {"tariff": 152.8, "slurry": 7.3, "cive_cost": round(E0.cost_cive, 1), "maize_cost": round(E0.cost_maize, 1),
                 "el": 120.0, "capexf": 1.0, "disc": 7.0}


# ------------------------------------------------------------------------- state ----------
def apply_preset(name: str | None = None) -> None:
    x = PRESETS[name or st.session_state.preset]
    st.session_state.update({"maize_pct": round(100 * x["maize_share"], 1), "cive_pct": round(100 * x["cive_share"], 1),
                             "feed": round(x["feed_t_d"], 1), "hrt": round(x["hrt_d"], 1),
                             "water": round(x["water_per_kNm3"], 1), "pflash": round(x["p_flash_bar"], 2)})


def reset_all() -> None:
    st.session_state.preset = DEFAULT_PRESET
    apply_preset(DEFAULT_PRESET)
    st.session_state.update({"kdis": 0.1, "ki": 0.0018, **ECON_DEFAULTS})


if "preset" not in st.session_state:
    reset_all()


def load_design(name: str) -> None:
    st.session_state.preset = name
    apply_preset(name)


# ----------------------------------------------------------------------- sidebar ----------
with st.sidebar:
    st.markdown(f'<div class="mt-side-brand"><img src="{T.svg_data_uri("logo_mark.svg")}"/>'
                f'<div>Metha<span>Twin</span></div></div>', unsafe_allow_html=True)
    st.caption("Set a plant design and market conditions. Results update instantly.")
    st.selectbox("Start from a design", list(PRESETS), key="preset", on_change=apply_preset,
                 help="Verified designs were confirmed by the full ADM1 + DWSIM simulation.")
    with st.expander("Feed & digester", expanded=True):
        st.slider("Maize silage share (%)", 0.0, 15.0, key="maize_pct", step=0.5,
                  help="Capped at 15 % of tonnage by French décret 2016-929.")
        st.slider("Cover-crop (CIVE) silage share (%)", 5.0, 45.0, key="cive_pct", step=0.5)
        st.caption(f"Cattle slurry share: **{100 - st.session_state.maize_pct - st.session_state.cive_pct:.1f} %**")
        st.slider("Feed rate (t/day)", 60.0, 160.0, key="feed", step=1.0)
        st.slider("Hydraulic retention time (days)", 40.0, 110.0, key="hrt", step=1.0)
        st.caption(f"Digester volume: **{st.session_state.feed * st.session_state.hrt:,.0f} m³**")
    with st.expander("Water scrubber (upgrading)", expanded=False):
        st.slider("Water flow (m³ per 1,000 Nm³ raw gas)", 100.0, 200.0, key="water", step=1.0)
        st.slider("Flash pressure (bar)", 2.0, 3.5, key="pflash", step=0.05)
    with st.expander("Biology · uncertain kinetics", expanded=False):
        st.select_slider("Disintegration rate k_dis (1/d)", KD_OPTS, key="kdis",
                         help="How fast solids break down. Calibrated value 0.1; BSM2 default 0.5.")
        st.select_slider("Ammonia inhibition K_I,NH3 (M)", KI_OPTS, key="ki",
                         help="Lower = microbes more sensitive to ammonia. Nominal 0.0018 (BSM2).")
    with st.expander("Market & finance", expanded=False):
        st.slider("Purchase tariff (€/MWh)", 100.0, 180.0, key="tariff", step=0.5,
                  help="2023 agricultural tariff range 111–169, average 152.8 (CRE).")
        st.slider("Slurry cost (€/t)", 0.0, 45.0, key="slurry", step=0.5,
                  help="7.3 = transport only; 43.2 = full CRE effluent price incl. transport.")
        st.slider("CIVE silage cost (€/t)", 20.0, 60.0, key="cive_cost", step=0.5)
        st.slider("Maize silage cost (€/t)", 20.0, 60.0, key="maize_cost", step=0.5)
        st.slider("Electricity price (€/MWh)", 60.0, 250.0, key="el", step=1.0)
        st.slider("CAPEX multiplier (×)", 0.7, 1.4, key="capexf", step=0.05)
        st.slider("Discount rate (%)", 3.0, 12.0, key="disc", step=0.5)
    st.button("↺  Reset everything", on_click=reset_all, width="stretch")

S = st.session_state
X = {"maize_share": S.maize_pct / 100, "cive_share": S.cive_pct / 100, "feed_t_d": S.feed, "hrt_d": S.hrt,
     "water_per_kNm3": S.water, "p_flash_bar": S.pflash, "k_dis": S.kdis, "K_I_nh3": S.ki}
ECON = replace(E0, tariff=S.tariff, cost_slurry=S.slurry, cost_cive=S.cive_cost, cost_maize=S.maize_cost,
               el_price=S.el, capex_factor=S.capexf, discount=S.disc / 100)
R = core.single(SUR, X, ECON)


# ------------------------------------------------------------------------ helpers ---------
def chip(kind: str, text: str) -> str:
    icon = {"ok": "✓", "warn": "!", "bad": "✕"}[kind]
    return f'<span class="chip {kind}">{icon} {text}</span>'


def rows_html(rows: list[tuple]) -> str:
    h = '<table class="mt-table">'
    for k, v, lim, st_ in rows:
        h += f'<tr><td class="k">{k}</td><td class="v">{v}</td><td class="l">{lim}</td><td class="s">{st_}</td></tr>'
    return h + "</table>"


def panel(title: str, sub: str) -> None:
    st.markdown(f'<div class="mt-panel-title">{title}</div><div class="mt-panel-sub">{sub}</div>',
                unsafe_allow_html=True)


def section(title: str, sub: str) -> None:
    st.markdown(f'<div class="mt-section">{title}</div><div class="mt-section-sub">{sub}</div>', unsafe_allow_html=True)


def matches_preset() -> str | None:
    """Name of the preset if the current inputs are exactly a saved, fully simulated case."""
    name = S.preset
    x = PRESETS[name]
    same = all(abs(X[k] - x[k]) <= {"maize_share": 0.006, "cive_share": 0.006, "feed_t_d": 0.6, "hrt_d": 0.6,
                                    "water_per_kNm3": 0.6, "p_flash_bar": 0.03}[k] for k in core.BOUNDS)
    nominal = abs(S.kdis - 0.1) < 1e-9 and abs(S.ki - 0.0018) < 1e-9
    econ_default = all(abs(S[k] - v) < 1e-6 for k, v in ECON_DEFAULTS.items())
    return name if (same and nominal and econ_default) else None


def full_sim(name: str) -> dict | None:
    if name.startswith("Verified optimum"):
        return RES["opt"][name.split("· ")[1].split(" ")[0]]["final"]["simulation"]
    if name.startswith("Naive"):
        return RES["unc"]["comparison_200"]["naive_scaled_base"]["simulation"]
    if name.startswith("Robust"):
        return RES["rob"]["robust_design_at_nominal_kinetics"]
    if name.startswith("Base"):
        b = RES["tea"]["results"]["base_case"]
        return {"bm_net_Nm3_h": b["bm_net_Nm3_h"], "LCOE_EUR_MWh": b["LCOE_EUR_MWh"], "NPV_EUR": b["NPV_EUR"]}
    return None


# ------------------------------------------------------------------------- header ---------
st.markdown(f"""
<div class="mt-hero">
  <div class="mt-hero-left">
    <img class="mt-hero-mark" src="{T.svg_data_uri('logo_mark.svg')}"/>
    <div><div class="ttl">Metha<span>Twin</span></div>
    <p>ML-accelerated digital twin of an agricultural biomethane plant, from digester to grid</p></div>
  </div>
  <div class="mt-tags"><span class="mt-tag">ADM1 digester model</span><span class="mt-tag">DWSIM water scrubbing</span>
  <span class="mt-tag">ML surrogates · R² ≥ 0.99</span><span class="mt-tag">CRE-anchored economics</span>
  <span class="mt-tag">Monte Carlo risk</span></div>
</div>""", unsafe_allow_html=True)

tab_sim, tab_exp, tab_risk, tab_opt, tab_val, tab_about = st.tabs(
    ["Plant simulator", "Design explorer", "Risk analysis", "Optimisation", "Model validation", "About"])

# ====================================================================== SIMULATOR ==========
with tab_sim:
    stable = R["p_stable"] >= 0.5 and R["pH"] >= core.STAB["pH_min"] and R["VFA_gCOD_L"] <= core.STAB["VFA_max"]
    co2_ok = R["BM_CO2_pct"] <= core.SPEC["CO2_max"]
    o2_ok = R["BM_O2_ppm"] <= core.SPEC["O2_exempt"]
    hhv_ok = core.SPEC["HHV"][0] <= R["HHV"] <= core.SPEC["HHV"][1]
    valid = R["p_upg_valid"] >= 0.5
    issues = []
    if not stable:
        issues.append("the digester is predicted to be <b>unstable</b> (acid build-up / ammonia inhibition)")
    if not (co2_ok and hhv_ok):
        issues.append("the biomethane <b>misses the grid specification</b>")
    if not o2_ok:
        issues.append("O₂ exceeds even the 0.75 % exemption")
    if not issues and R["NPV_EUR"] < 0:
        kind, msg = "warn", (f"<b>Technically feasible, but not profitable.</b> The digester is stable and the gas meets "
                             f"grid spec, but production costs {R['LCOE_EUR_MWh']:.0f} €/MWh against a tariff of "
                             f"{S.tariff:.0f} €/MWh.")
    elif not issues:
        kind, msg = "ok", ("<b>Feasible and profitable design.</b> Stable digester, grid-quality biomethane and a "
                           "positive 15-year NPV at the chosen prices.")
    else:
        kind, msg = "bad", "<b>Infeasible design:</b> " + "; ".join(issues) + "."
    icon = {"ok": "✓", "warn": "!", "bad": "✕"}[kind]
    st.markdown(f'<div class="mt-banner {kind}"><span class="ico">{icon}</span><div>{msg}</div></div>',
                unsafe_allow_html=True)
    if not valid:
        st.markdown('<div class="mt-banner warn"><span class="ico">!</span><div><b>Low simulator reliability here.</b> '
                    f'The validity classifier gives P = {R["p_upg_valid"]:.2f} that the scrubber simulation converges '
                    'cleanly in this region (low flash pressure with high water flow). Treat upgrading results with '
                    'caution.</div></div>', unsafe_allow_html=True)

    margin = S.tariff - R["LCOE_EUR_MWh"]
    lc_cls = "good" if margin >= 0 else "bad"
    npv_cls = "good" if R["NPV_EUR"] >= 0 else "bad"
    ps = R["p_stable"]
    ps_cls = "good" if ps >= 0.9 else ("warn" if ps >= 0.5 else "bad")
    st.markdown(f"""
    <div class="mt-kpis">
      <div class="mt-kpi"><div class="lbl">Biomethane injected</div>
        <div class="val">{R['bm_net_Nm3_h']:.0f}<small>Nm³/h</small></div>
        <div class="sub">{R['energy_MWh_yr'] / 1000:.1f} GWh/yr · {R['BM_CO2_pct']:.2f} % CO₂</div></div>
      <div class="mt-kpi amber"><div class="lbl">Levelised cost (LCOE)</div>
        <div class="val">{R['LCOE_EUR_MWh']:.1f}<small>€/MWh</small></div>
        <div class="sub {lc_cls}">{'▼' if margin >= 0 else '▲'} {abs(margin):.1f} €/MWh {'below' if margin >= 0 else 'above'} tariff</div></div>
      <div class="mt-kpi blue"><div class="lbl">Net present value (15 yr)</div>
        <div class="val">{R['NPV_EUR'] / 1e6:+.2f}<small>M€</small></div>
        <div class="sub {npv_cls}">CAPEX {R['capex_total'] / 1e6:.1f} M€ · {S.disc:.1f} % discount</div></div>
      <div class="mt-kpi violet"><div class="lbl">Digester stability</div>
        <div class="val">{100 * ps:.0f}<small>% probability</small></div>
        <div class="sub {ps_cls}">pH {R['pH']:.2f} · VFA {R['VFA_gCOD_L']:.1f} g/L</div></div>
    </div>""", unsafe_allow_html=True)

    ref = matches_preset()
    if ref and (fs := full_sim(ref)):
        st.markdown(f'<div class="mt-banner ok" style="background:#EEF5FD;border-color:#C9DBF5;color:#1E3A6B">'
                    f'<span class="ico">◆</span><div><b>Full-simulation check for this saved design</b> (ADM1 + DWSIM): '
                    f'{fs["bm_net_Nm3_h"]:.1f} Nm³/h, LCOE {fs["LCOE_EUR_MWh"]:.1f} €/MWh, NPV '
                    f'{fs["NPV_EUR"] / 1e6:+.2f} M€. The surrogate values above differ by '
                    f'{100 * (R["bm_net_Nm3_h"] / fs["bm_net_Nm3_h"] - 1):+.1f} % on output: the optimiser picked '
                    f'a point where the ML is slightly optimistic, which is why every design was re-verified.</div></div>',
                    unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1, st.container(border=True):
        panel("Digester health", "Anaerobic digestion (ADM1 surrogate), 39 °C CSTR")
        vfa_s = (chip("ok", "OK") if R["VFA_gCOD_L"] <= core.STAB["VFA_margin"] else
                 chip("warn", "No margin") if R["VFA_gCOD_L"] <= core.STAB["VFA_max"] else chip("bad", "Too high"))
        st.markdown(rows_html([
            ("Methane produced", f"{R['CH4_Nm3_h']:.0f} Nm³/h", "", ""),
            ("Biogas (dry) · CH₄ content", f"{R['biogas_dry_Nm3_h']:.0f} Nm³/h · {100 * R['y_CH4_dry']:.1f} %", "", ""),
            ("pH", f"{R['pH']:.2f}", "≥ 6.8", chip("ok", "OK") if R["pH"] >= 6.8 else chip("bad", "Too low")),
            ("Volatile fatty acids", f"{R['VFA_gCOD_L']:.1f} g COD/L", "margin 6 · limit 8", vfa_s),
            ("Free ammonia", f"{R['free_NH3_mgN_L']:.0f} mg N/L", "inhibitory", ""),
            ("Probability of stability", f"{100 * ps:.1f} %", "classifier",
             chip("ok", "Stable") if ps >= 0.9 else chip("warn", "At risk") if ps >= 0.5 else chip("bad", "Unstable")),
        ]), unsafe_allow_html=True)
    with c2, st.container(border=True):
        panel("Gas quality vs grid specification", "High-pressure water scrubbing (DWSIM surrogate) · GRDF spec")
        o2s = (chip("ok", "OK") if R["BM_O2_ppm"] <= 100 else chip("warn", "Exemption") if o2_ok else chip("bad", "Too high"))
        spec_kwh = R["P_el_upg_kW"] / R["biogas_dry_Nm3_h"]
        st.markdown(rows_html([
            ("CO₂ in biomethane", f"{R['BM_CO2_pct']:.2f} %", "< 2.5 %", chip("ok", "OK") if co2_ok else chip("bad", "Too high")),
            ("O₂ in biomethane", f"{R['BM_O2_ppm']:,.0f} ppm", "< 100 (exempt. 0.75 %)", o2s),
            ("Higher heating value", f"{R['HHV']:.2f} kWh/Nm³", "10.7 – 12.8", chip("ok", "OK") if hhv_ok else chip("bad", "Out")),
            ("Methane slip", f"{R['CH4_slip_pct']:.2f} %", "lit. ≈ 1 %", chip("ok", "Low") if R["CH4_slip_pct"] <= 1 else chip("warn", "High")),
            ("Scrubber electricity", f"{spec_kwh:.3f} kWh/Nm³ raw", "lit. 0.20–0.30", ""),
            ("Probability spec met", f"{100 * R['p_spec']:.1f} %", "classifier",
             chip("ok", "Likely") if R["p_spec"] >= 0.9 else chip("warn", "Uncertain") if R["p_spec"] >= 0.5 else chip("bad", "Unlikely")),
        ]), unsafe_allow_html=True)

    c3, c4 = st.columns([1.35, 1], gap="medium")
    with c3, st.container(border=True):
        panel("Where the money goes", "Cost per MWh injected vs the purchase tariff and the French median (CRE 2024)")
        E = R["energy_MWh_yr"]
        parts = [("Capital (annuity)", R["ann_capex"] / E, T.TEAL), ("Feedstock", R["feed_cost"] / E, T.BLUE),
                 ("Electricity", R["el_cost"] / E, T.AMBER), ("Other OPEX", R["fixed_om"] / E, T.VIOLET)]
        fig = go.Figure()
        for name, v, col in parts:
            fig.add_bar(y=["This design"], x=[v], name=name, orientation="h", marker=dict(color=col, line=dict(color="#fff", width=2)),
                        text=[f"<b>{v:.0f}</b>"], textposition="inside", insidetextanchor="middle", textangle=0,
                        textfont=dict(color="white", size=12),
                        hovertemplate=f"{name}: %{{x:.1f}} €/MWh<extra></extra>")
        fig.add_vline(x=S.tariff, line=dict(color=T.INK, width=2, dash="dash"))
        fig.add_annotation(x=S.tariff, y=1.0, yref="paper", text=f"tariff {S.tariff:.0f}", showarrow=False,
                           yanchor="bottom", font=dict(size=11, color=T.INK))
        fig.add_vline(x=core.CRE["median"], line=dict(color=T.MUTED, width=1.5, dash="dot"))
        fig.add_annotation(x=core.CRE["median"], y=0, yref="paper", text=f"CRE median {core.CRE['median']}",
                           showarrow=False, yanchor="top", font=dict(size=10.5, color=T.MUTED))
        fig.update_layout(barmode="stack", height=250, showlegend=True, margin=dict(l=4, r=14, t=24, b=10),
                          uniformtext=dict(minsize=9, mode="hide"),
                          legend=dict(orientation="h", y=-0.38, x=0, yanchor="top", traceorder="normal"),
                          xaxis=dict(title="€/MWh", range=[0, max(S.tariff, R["LCOE_EUR_MWh"]) * 1.08]),
                          yaxis=dict(showticklabels=False))
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG)
    with c4, st.container(border=True):
        panel("Investment breakdown", f"Total CAPEX {R['capex_total'] / 1e6:.2f} M€ (six-tenths scaling, CRE anchor)")
        cx = [("Digester & civil works", R["capex_digester"]), ("Upgrading unit", R["capex_upgrading"]),
              ("Feed & digestate handling", R["capex_feed_handling"]), ("Grid, electrical, other", R["capex_capacity_linked"])]
        fig = go.Figure(go.Bar(x=[v / 1e6 for _, v in cx], y=[n for n, _ in cx], orientation="h", marker_color=T.TEAL,
                               text=[f"{v / 1e6:.2f} M€" for _, v in cx], textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}: %{x:.2f} M€<extra></extra>"))
        fig.update_layout(height=230, margin=dict(l=4, r=50, t=10, b=34), xaxis=dict(title="M€"),
                          yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG)
    st.markdown('<div class="mt-note">Values are predictions of ML surrogates trained on 2,000 coupled ADM1 + DWSIM '
                'simulations (test R² 0.992–0.999). They are valid inside the slider ranges only and describe the model, '
                'not a measured plant.</div>', unsafe_allow_html=True)

# ======================================================================= EXPLORER ==========
with tab_exp:
    section("Design explorer", "Sweep one input across its full range while keeping everything else at your current "
                               "design. Grey bands mark where the digester is predicted to be unstable.")
    var = st.selectbox("Input to sweep", list(core.LABELS), format_func=lambda k: f"{core.LABELS[k]} ({core.UNITS[k]})",
                       index=2)
    lo, hi = {**core.BOUNDS, **core.UNC_BOUNDS}[var]
    grid = np.geomspace(lo, hi, 120) if var in core.UNC_BOUNDS else np.linspace(lo, hi, 120)
    dfg = pd.DataFrame([X] * len(grid))
    dfg[var] = grid
    A = core.assess(SUR, dfg, ECON)
    xs = grid * (100 if var in ("maize_share", "cive_share") else 1)
    cur = X[var] * (100 if var in ("maize_share", "cive_share") else 1)
    unstable = (A.p_stable < 0.5).to_numpy()

    def shade(fig):
        i = 0
        while i < len(xs):
            if unstable[i]:
                j = i
                while j + 1 < len(xs) and unstable[j + 1]:
                    j += 1
                fig.add_vrect(x0=xs[max(i - 1, 0)], x1=xs[j], fillcolor="#9AA6A3", opacity=0.18, line_width=0)
                i = j + 1
            else:
                i += 1
        fig.add_vline(x=cur, line=dict(color=T.INK, width=1.5, dash="dot"))
        fig.add_annotation(x=cur, y=1, yref="paper", text="current", showarrow=False, yanchor="bottom",
                           font=dict(size=10.5, color=T.INK))
        if var in core.UNC_BOUNDS:
            fig.update_xaxes(type="log")
        return fig

    xt = f"{core.LABELS[var]} ({core.UNITS[var]})"
    e1, e2 = st.columns(2, gap="medium")
    with e1, st.container(border=True):
        f = go.Figure(go.Scatter(x=xs, y=A.LCOE_EUR_MWh, mode="lines", line=dict(color=T.AMBER, width=2.5),
                                 hovertemplate="%{x:.3g} → %{y:.1f} €/MWh<extra></extra>", name="LCOE"))
        f.add_hline(y=S.tariff, line=dict(color=T.INK, width=1.5, dash="dash"),
                    annotation_text=f"tariff {S.tariff:.0f}", annotation_position="top left")
        f.update_layout(title="Levelised cost (€/MWh)", height=340, xaxis_title=xt, showlegend=False)
        st.plotly_chart(shade(f), width="stretch", config=PLOT_CFG)
    with e2, st.container(border=True):
        f = go.Figure(go.Scatter(x=xs, y=A.bm_net_Nm3_h, mode="lines", line=dict(color=T.TEAL, width=2.5),
                                 hovertemplate="%{x:.3g} → %{y:.0f} Nm³/h<extra></extra>", name="Biomethane"))
        f.update_layout(title="Biomethane injected (Nm³/h)", height=340, xaxis_title=xt, showlegend=False)
        st.plotly_chart(shade(f), width="stretch", config=PLOT_CFG)
    e3, e4 = st.columns(2, gap="medium")
    with e3, st.container(border=True):
        f = go.Figure(go.Scatter(x=xs, y=A.VFA_gCOD_L, mode="lines", line=dict(color=T.VIOLET, width=2.5),
                                 hovertemplate="%{x:.3g} → %{y:.2f} g/L<extra></extra>"))
        f.add_hline(y=core.STAB["VFA_max"], line=dict(color=T.BAD, width=1.2, dash="dash"),
                    annotation_text="stability limit 8", annotation_position="top left")
        f.update_layout(title="Volatile fatty acids (g COD/L)", height=300, xaxis_title=xt, showlegend=False)
        st.plotly_chart(shade(f), width="stretch", config=PLOT_CFG)
    with e4, st.container(border=True):
        f = go.Figure(go.Scatter(x=xs, y=A.BM_CO2_pct, mode="lines", line=dict(color=T.BLUE, width=2.5),
                                 hovertemplate="%{x:.3g} → %{y:.2f} %<extra></extra>"))
        f.add_hline(y=core.SPEC["CO2_max"], line=dict(color=T.BAD, width=1.2, dash="dash"),
                    annotation_text="grid limit 2.5 %", annotation_position="top left")
        f.update_layout(title="CO₂ in biomethane (%)", height=300, xaxis_title=xt, showlegend=False,
                        yaxis=dict(type="log"))
        st.plotly_chart(shade(f), width="stretch", config=PLOT_CFG)

    st.markdown("<br/>", unsafe_allow_html=True)
    section("Design map: feed rate × retention time",
            "LCOE over the two main sizing levers, other inputs at your current design. Blank cells are unstable digesters "
            "or designs that miss the grid CO₂ limit. The contour marks break-even with the tariff.")
    with st.container(border=True):
        fg, hg = np.linspace(60, 160, 41), np.linspace(40, 110, 36)
        FF, HH = np.meshgrid(fg, hg)
        dm = pd.DataFrame([X] * FF.size)
        dm["feed_t_d"], dm["hrt_d"] = FF.ravel(), HH.ravel()
        M = core.assess(SUR, dm, ECON)
        Z = M.LCOE_EUR_MWh.to_numpy().copy()
        Z[(M.p_stable < 0.5).to_numpy() | (M.BM_CO2_pct > core.SPEC["CO2_max"]).to_numpy()] = np.nan
        Z = Z.reshape(FF.shape)
        scale = [[i / (len(T.SEQ) - 1), c] for i, c in enumerate(T.SEQ)]
        hm = go.Figure(go.Heatmap(x=fg, y=hg, z=Z, colorscale=scale, colorbar=dict(title="€/MWh", thickness=12),
                                  hovertemplate="feed %{x:.0f} t/d · HRT %{y:.0f} d<br>LCOE %{z:.1f} €/MWh<extra></extra>"))
        hm.add_contour(x=fg, y=hg, z=Z, contours=dict(start=S.tariff, end=S.tariff, size=1, coloring="none",
                                                     showlabels=True, labelfont=dict(color=T.INK, size=11)),
                       line=dict(color=T.INK, width=2, dash="dash"), showscale=False, hoverinfo="skip", showlegend=False)
        bm = M.bm_net_Nm3_h.to_numpy().reshape(FF.shape)
        hm.add_contour(x=fg, y=hg, z=bm, contours=dict(start=150, end=300, size=50, coloring="none", showlabels=True,
                                                      labelfont=dict(color=T.BLUE, size=10.5)),
                       line=dict(color=T.BLUE, width=1.2), showscale=False, hoverinfo="skip", showlegend=False)
        hm.add_scatter(x=[X["feed_t_d"]], y=[X["hrt_d"]], mode="markers", marker=dict(size=13, color=T.FLAME,
                       line=dict(color="white", width=2), symbol="diamond"), name="current design",
                       hovertemplate="current design<extra></extra>")
        hm.update_layout(height=460, xaxis_title="Feed rate (t/day)", yaxis_title="Retention time (days)",
                         legend=dict(y=1.02), margin=dict(l=10, r=10, t=30, b=10),
                         plot_bgcolor="#E6EBEA")
        st.plotly_chart(hm, width="stretch", config=PLOT_CFG)
        st.markdown('<div class="mt-note">Darker = more expensive. Grey = infeasible (unstable digester or CO₂ above spec). Dashed black line: LCOE = tariff. Blue lines: '
                    'biomethane output 150 / 200 / 250 / 300 Nm³/h. Diamond: your current design.</div>',
                    unsafe_allow_html=True)

# =========================================================================== RISK ==========
with tab_risk:
    section("Risk analysis of your current design",
            "Monte Carlo propagates uncertainty in microbial kinetics and in nine prices; the tornado shows which input "
            "moves the cost most. Same distributions as the report (step 7c), centred on your market settings.")
    r1, r2 = st.columns([1, 3])
    with r1:
        n = st.select_slider("Number of samples", [500, 1000, 2000, 5000], value=2000)
    with st.spinner("Running Monte Carlo…"):
        mc = core.monte_carlo(SUR, X, ECON, n=n)
    stab = mc.p_stable >= 0.5
    L = mc.LCOE_EUR_MWh[stab]
    p_pos = float((mc.NPV_EUR[stab] > 0).mean()) if stab.any() else 0.0
    q = L.quantile([0.1, 0.5, 0.9]) if stab.any() else pd.Series([np.nan] * 3, index=[0.1, 0.5, 0.9])
    st.markdown(f"""
    <div class="mt-kpis">
      <div class="mt-kpi amber"><div class="lbl">Median LCOE (P50)</div><div class="val">{q[0.5]:.0f}<small>€/MWh</small></div>
        <div class="sub">P10 {q[0.1]:.0f} · P90 {q[0.9]:.0f} €/MWh</div></div>
      <div class="mt-kpi blue"><div class="lbl">Chance of profit</div><div class="val">{100 * p_pos:.0f}<small>%</small></div>
        <div class="sub {'good' if p_pos >= 0.5 else 'bad'}">P(NPV &gt; 0) among stable runs</div></div>
      <div class="mt-kpi violet"><div class="lbl">Digester failure risk</div><div class="val">{100 * (1 - stab.mean()):.0f}<small>%</small></div>
        <div class="sub">of samples predicted unstable</div></div>
      <div class="mt-kpi"><div class="lbl">Median output</div><div class="val">{mc.bm_net_Nm3_h[stab].median():.0f}<small>Nm³/h</small></div>
        <div class="sub">P10 {mc.bm_net_Nm3_h[stab].quantile(0.1):.0f} · P90 {mc.bm_net_Nm3_h[stab].quantile(0.9):.0f}</div></div>
    </div>""", unsafe_allow_html=True)
    k1, k2 = st.columns(2, gap="medium")
    with k1, st.container(border=True):
        f = go.Figure(go.Histogram(x=L, nbinsx=50, marker=dict(color=T.TEAL, line=dict(color="white", width=1)),
                                   hovertemplate="%{x} €/MWh: %{y} samples<extra></extra>"))
        f.add_vrect(x0=111, x1=169, fillcolor=T.TEAL_LIGHT, opacity=0.45, line_width=0, layer="below")
        f.add_annotation(x=112, y=1, yref="paper", text="tariff range 111–169", showarrow=False, xanchor="left",
                         yanchor="top", font=dict(size=10.5, color=T.MUTED))
        for qq, lab in ((0.1, "P10"), (0.5, "P50"), (0.9, "P90")):
            f.add_vline(x=q[qq], line=dict(color=T.INK, width=1.3 if qq == 0.5 else 1, dash="solid" if qq == 0.5 else "dot"))
            f.add_annotation(x=q[qq], y=1.0, yref="paper", text=f"{lab} {q[qq]:.0f}", showarrow=False, yanchor="bottom",
                             font=dict(size=10.5, color=T.INK))
        f.update_layout(title="LCOE distribution, stable samples", height=360, xaxis_title="€/MWh",
                        yaxis_title="samples", bargap=0.02, showlegend=False, margin=dict(t=56))
        st.plotly_chart(f, width="stretch", config=PLOT_CFG)
    with k2, st.container(border=True):
        lc0, tor = core.tornado(SUR, X, ECON)
        f = go.Figure()
        f.add_bar(y=tor.input, x=tor.low - lc0, base=lc0, orientation="h", name="low value",
                  marker_color=T.TEAL, hovertemplate="%{y}<br>low: %{customdata:.1f} €/MWh<extra></extra>",
                  customdata=tor.low)
        f.add_bar(y=tor.input, x=tor.high - lc0, base=lc0, orientation="h", name="high value",
                  marker_color=T.AMBER, hovertemplate="%{y}<br>high: %{customdata:.1f} €/MWh<extra></extra>",
                  customdata=tor.high)
        f.add_vline(x=lc0, line=dict(color=T.INK, width=1.5))
        f.update_layout(title=f"What drives the cost (around {lc0:.0f} €/MWh)", barmode="overlay", height=360,
                        xaxis_title="LCOE (€/MWh)", margin=dict(t=56), legend=dict(orientation="h", y=-0.2, x=0, yanchor="top"))
        st.plotly_chart(f, width="stretch", config=PLOT_CFG)
    st.markdown('<div class="mt-note">Sampled: k_dis 0.05–0.5 and K_I,NH3 0.0012–0.0084 (log-uniform), CAPEX ×0.8–1.25, '
                'CIVE and maize ±30 %, slurry 7.3–43.2 €/t, electricity 120–202 €/MWh, other OPEX ±20 %, tariff 111–169 '
                '€/MWh, discount 5–9 %, heat self-use 2–6 %. Fixed seed, so results are reproducible.</div>',
                unsafe_allow_html=True)

# =================================================================== OPTIMISATION ==========
with tab_opt:
    section("Verified optimal designs", "Lowest-cost design for each plant size, found by differential evolution on the "
                                        "surrogates and then confirmed by the full ADM1 + DWSIM simulation.")
    rows = []
    for k in ("150", "200", "250", "300"):
        fdat = RES["opt"][k]["final"]
        if not fdat:
            continue
        d, v = fdat["design"], fdat["simulation"]
        rows.append({"Target": f"{k} Nm³/h", "Simulated output (Nm³/h)": round(v["bm_net_Nm3_h"], 1),
                     "LCOE (€/MWh)": round(v["LCOE_EUR_MWh"], 1), "NPV (M€)": round(v["NPV_EUR"] / 1e6, 2),
                     "Maize %": round(100 * d["maize_share"], 1), "CIVE %": round(100 * d["cive_share"], 1),
                     "Feed (t/d)": round(d["feed_t_d"]), "HRT (d)": round(d["hrt_d"]),
                     "Water (m³/kNm³)": round(d["water_per_kNm3"]), "Flash (bar)": round(d["p_flash_bar"], 2),
                     "CO₂ (%)": round(v["BM_CO2_pct"], 2), "VFA (g/L)": round(v["VFA_gCOD_L"], 1)})
    o1, o2 = st.columns([1.1, 1], gap="medium")
    with o1, st.container(border=True):
        dd = pd.DataFrame(rows)
        f = go.Figure()
        f.add_hrect(y0=core.CRE["q1"], y1=core.CRE["q3"], fillcolor=T.TEAL_LIGHT, opacity=0.6, line_width=0, layer="below")
        f.add_hline(y=core.CRE["median"], line=dict(color=T.TEAL_DARK, width=1.2, dash="dot"),
                    annotation_text="CRE median 129.6 (IQR shaded)", annotation_position="bottom right")
        f.add_hline(y=152.8, line=dict(color=T.INK, width=1.5, dash="dash"),
                    annotation_text="average tariff 152.8", annotation_position="top right")
        f.add_scatter(x=dd["Simulated output (Nm³/h)"], y=dd["LCOE (€/MWh)"], mode="lines+markers+text",
                      line=dict(color=T.AMBER, width=2.5), marker=dict(size=10, color=T.AMBER, line=dict(color="white", width=2)),
                      text=[f"{v:.0f}" for v in dd["LCOE (€/MWh)"]], textposition="top center",
                      hovertemplate="%{x:.0f} Nm³/h → %{y:.1f} €/MWh<extra></extra>", name="verified optimum")
        f.update_layout(title="Economies of scale", height=380, xaxis_title="Biomethane injected (Nm³/h)",
                        yaxis_title="LCOE (€/MWh)", yaxis_range=[105, 165], showlegend=False)
        st.plotly_chart(f, width="stretch", config=PLOT_CFG)
    with o2, st.container(border=True):
        cmp_ = RES["unc"]["comparison_200"]
        items = [("Naive scale-up", cmp_["naive_scaled_base"]["simulation"], "#9EC5F4"),
                 ("Optimum", cmp_["optimum"]["simulation"], T.BLUE),
                 ("Robust (ammonia)", RES["rob"]["final"]["simulation"], T.TEAL)]
        f = go.Figure(go.Bar(x=[i[0] for i in items], y=[i[1]["LCOE_EUR_MWh"] for i in items],
                             marker_color=[i[2] for i in items], text=[f"{i[1]['LCOE_EUR_MWh']:.1f}" for i in items],
                             textposition="outside", cliponaxis=False,
                             customdata=[[i[1]["VFA_gCOD_L"], i[1]["NPV_EUR"] / 1e6] for i in items],
                             hovertemplate="%{x}<br>LCOE %{y:.1f} €/MWh<br>VFA %{customdata[0]:.1f} g/L"
                                           "<br>NPV %{customdata[1]:+.2f} M€<extra></extra>"))
        f.update_layout(title="Three 200 Nm³/h designs (full simulation)", height=380, yaxis_title="LCOE (€/MWh)",
                        yaxis_range=[0, 180], showlegend=False)
        st.plotly_chart(f, width="stretch", config=PLOT_CFG)
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown("**Load a verified design into the simulator:**")
    bc = st.columns(6)
    names = [n for n in PRESETS if n != "Base case (88 t/d, HRT 60 d)"]
    for col, name in zip(bc, names):
        col.button(name.replace("Verified optimum · ", "Optimum "), on_click=load_design, args=(name,),
                   width="stretch", key=f"load_{name}")
    with st.container(border=True):
        panel("What the optimisation taught", "Key findings from step 7 of the project")
        st.markdown(
            "- **Size beats fine-tuning.** Cost falls from 157 to 140 €/MWh between 150 and 300 Nm³/h; break-even at the "
            "average tariff is ≈ 180 Nm³/h.\n"
            "- **The optimum is flat.** A naive scale-up of the base design costs 149.6 €/MWh vs 149.9 for the optimum; the "
            "optimum's value is that it keeps acids within the safety margin (6.0 vs 6.7 g/L).\n"
            "- **The optimiser's curse.** The search lands where the ML is optimistic (by 2–5 %), so a verify-and-correct loop "
            "re-simulated every design until the full model confirmed it.\n"
            "- **Price of robustness.** A design that survives strong ammonia inhibition (K_I,NH3 ≥ 0.0016) costs "
            "+8.4 €/MWh.")

# ===================================================================== VALIDATION ==========
with tab_val:
    section("Can the model be trusted?", "Every block was checked against an independent reference before being used.")
    b = RES["bsm2"]
    sp = RES["speed"]
    st.markdown(f"""
    <div class="mt-kpis">
      <div class="mt-kpi"><div class="lbl">ADM1 vs BSM2 benchmark</div><div class="val">{b['n_pass']}/{b['n_variables']}<small>within 1 %</small></div>
        <div class="sub">max error {b['max_abs_rel_err_pct']:.1e} %</div></div>
      <div class="mt-kpi blue"><div class="lbl">DWSIM vs hand calculation</div><div class="val">−0.26<small>%</small></div>
        <div class="sub">compressor power, 44.77 vs 44.89 kW</div></div>
      <div class="mt-kpi amber"><div class="lbl">Surrogate accuracy</div><div class="val">0.992<small>min test R²</small></div>
        <div class="sub">train–test gap ≤ 0.0044 (no overfitting)</div></div>
      <div class="mt-kpi violet"><div class="lbl">Speed-up</div><div class="val">{sp['speedup_batch']:,.0f}<small>×</small></div>
        <div class="sub">{1000 * sp['surrogate_batch_per_point_s']:.2f} ms vs {sp['mean_coupled_simulation_s']:.1f} s per design</div></div>
    </div>""", unsafe_allow_html=True)
    v1, v2 = st.columns([1.05, 1], gap="medium")
    with v1, st.container(border=True):
        panel("Surrogate test performance", "20 % held-out test set, never used for tuning")
        m = RES["metrics"]
        nice = {"digester_stable": "Digester stable (classifier)", "upgrading_valid": "Simulator valid (classifier)",
                "spec_ok": "Grid spec met (classifier)", "CH4_Nm3_h": "Methane production", "y_CH4_dry": "Biogas CH₄ fraction",
                "pH": "Digester pH", "VFA_gCOD_L": "Volatile fatty acids", "free_NH3_mgN_L": "Free ammonia",
                "biomethane_Nm3_h": "Biomethane flow", "BM_CO2_pct": "CO₂ in biomethane", "BM_O2_ppm": "O₂ in biomethane",
                "CH4_slip_pct": "Methane slip", "P_el_upg_kW": "Scrubber electricity"}
        tab = []
        for r_ in m.itertuples():
            if r_.block == "classifier":
                tab.append({"Output": nice[r_.target], "Model": r_.best_model, "Score": f"AUC {r_.test_AUC:.3f}"})
            else:
                tab.append({"Output": nice[r_.target], "Model": r_.best_model, "Score": f"R² {r_.test_R2:.3f}"})
        st.dataframe(pd.DataFrame(tab), hide_index=True, width="stretch", height=490)
    with v2, st.container(border=True):
        panel("Digester model vs measured lab data", "Bułkowska et al. 2015 lab digester, no parameter adjusted")
        st.markdown(rows_html([
            ("CH₄ content", "53.6 %", "50–58 %", chip("ok", "In range")),
            ("pH", "7.19", "6.8–7.4", chip("ok", "In range")),
            ("Propionate", "0.69 kg COD/m³", "0.3–0.9", chip("ok", "In range")),
            ("Biogas (dry)", "83 Ndm³/d", "65–100", chip("ok", "In range")),
            ("Acetate", "0.85 kg COD/m³", "0.2–0.6", chip("bad", "Over-predicted")),
        ]), unsafe_allow_html=True)
        st.markdown("<br/>", unsafe_allow_html=True)
        panel("Economics vs French market data", "CRE 2024 survey of biomethane plants")
        st.markdown(rows_html([
            ("LCOE, feed-corrected", "129.3 €/MWh", "median 129.6", chip("ok", "Match")),
            ("Electricity share", "8.8 %", "9.2 %", chip("ok", "Close")),
            ("CAPEX share of cost", "36 %", "≈ 40 %", chip("ok", "Close")),
        ]), unsafe_allow_html=True)
    with st.expander("Validation figures from the report", expanded=False):
        st.image(str(core.FIGURES / "fig04_adm1_validation_and_base_case.png"), width="stretch")
        st.image(str(core.FIGURES / "fig06_surrogate_test_performance.png"), width="stretch")

# ========================================================================== ABOUT ==========
with tab_about:
    a1, a2 = st.columns([1.5, 1], gap="large")
    with a1:
        section("What is MethaTwin?", "A digital twin answers 'what if?' questions about a plant before it is built.")
        st.markdown(
            "MethaTwin models an agricultural biomethane plant of about **200 Nm³/h** (the size of an average French "
            "site) that digests **cattle slurry, cover-crop silage and maize silage**, upgrades the biogas to grid "
            "quality by **high-pressure water scrubbing**, and recovers a **biogenic CO₂** stream.\n\n"
            "**How it is built**\n"
            "1. **Feed characterisation** from published data (FNR 2010, Klimiuk et al. 2015).\n"
            "2. **Digester:** the IWA Anaerobic Digestion Model No. 1 in Python, matched to the BSM2 benchmark.\n"
            "3. **Upgrading:** a DWSIM flowsheet built and solved from Python, with fitted gas-solubility parameters.\n"
            "4. **Machine learning:** 2,000 coupled simulations train fast surrogates (XGBoost, random forest, neural network).\n"
            "5. **Economics:** CAPEX/OPEX anchored on the French regulator's 2024 survey, LCOE and NPV, Monte Carlo.\n\n"
            "**Limitations:** steady-state model; validated on a benchmark, a lab digester and hand calculations, not on "
            "a full-scale plant; costs are top-down; gas-solubility fit valid at 10–15 °C. The full list is in the report.")
    with a2:
        with st.container(border=True):
            st.image(str(T.ASSETS / "logo.svg"), width="stretch")
            st.markdown("**Author:** Louay Ouhibi, Industrial Biology Engineer (INSAT, Tunisia)\n\n"
                        "**Data policy:** public data and published literature only.\n\n"
                        "**Stack:** Python, SciPy, scikit-learn, XGBoost, DWSIM, pythonnet, Streamlit, Plotly.")
            if core.REPORT.exists():
                st.download_button("⬇  Download the full report (PDF)", core.REPORT.read_bytes(),
                                   file_name="MethaTwin_Final_Report.pdf", mime="application/pdf",
                                   width="stretch")
    st.image(str(core.FIGURES / "fig02_concept_flow.png"), width="stretch",
             caption="Architecture: mechanistic chain (top) and surrogate-based optimisation loop (bottom).")

st.markdown('<div class="mt-foot">MethaTwin · open-source digital twin · results are model predictions, not '
            'investment advice</div>', unsafe_allow_html=True)
