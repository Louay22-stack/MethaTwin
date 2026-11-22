"""Plant cockpit - live state of the current design: verdict, readouts, process flow, constraints, economics."""
from __future__ import annotations

import json

import plotly.graph_objects as go
import streamlit as st

import core
import state as S
import theme as T
import ui

X, R, s = S.design(), S.evaluate(), st.session_state
ref = S.matches_reference()

ui.page_head("Plant cockpit", "Plant <em>performance</em> at a glance",
             "Live prediction of the whole chain for the design in the console: digester biology, gas upgrading, "
             "grid quality and economics. Change any input on the left and every value below updates.",
             f'Reference <b>{s.preset}</b><br/>Inputs <b>{"unchanged" if ref else "modified"}</b> · ID <b>{S.fingerprint()}</b>')

# ------------------------------------------------------------------ verdict ---
stable = R["p_stable"] >= 0.5 and R["pH"] >= core.STAB["pH_min"] and R["VFA_gCOD_L"] <= core.STAB["VFA_max"]
co2_ok, hhv_ok = R["BM_CO2_pct"] <= core.SPEC["CO2_max"], core.SPEC["HHV"][0] <= R["HHV"] <= core.SPEC["HHV"][1]
o2_ok = R["BM_O2_ppm"] <= core.SPEC["O2_exempt"]
issues = []
if not stable:
    issues.append("the digester is predicted <b>unstable</b> (acid build-up or ammonia inhibition)")
if not (co2_ok and hhv_ok):
    issues.append("the biomethane <b>misses the grid specification</b>")
if not o2_ok:
    issues.append("O₂ exceeds the 0.75 % exemption")
if issues:
    ui.verdict("bad", "Infeasible", "This design " + "; ".join(issues) + ". Use the Design explorer to find a stable region.")
elif R["NPV_EUR"] < 0:
    ui.verdict("warn", "Not profitable", f"Technically feasible: stable digester and grid-quality gas. But production costs "
               f"<b>{R['LCOE_EUR_MWh']:.1f} €/MWh</b>, above the {s.tariff:.0f} €/MWh tariff, so the 15-year NPV is negative.")
else:
    ui.verdict("ok", "Feasible · profitable", f"Stable digester, grid-quality biomethane and a positive 15-year NPV. Margin to "
               f"tariff: <b>{s.tariff - R['LCOE_EUR_MWh']:.1f} €/MWh</b>.")
if R["p_upg_valid"] < 0.5:
    ui.callout(f"<b>Low simulator reliability.</b> The validity classifier gives P = {R['p_upg_valid']:.2f} that the scrubber "
               "simulation converges cleanly here (typically low flash pressure with high water flow). Treat upgrading values "
               "with caution.", "warn")

# --------------------------------------------------------------------- KPIs ---
m = s.tariff - R["LCOE_EUR_MWh"]
ps = R["p_stable"]
ui.kpis([
    {"label": "Biomethane injected", "value": f"{R['bm_net_Nm3_h']:.0f}", "unit": "Nm³/h", "color": T.TEAL,
     "delta": f"{R['energy_MWh_yr'] / 1000:.1f} GWh/yr", "tip": "Net of 3.5 % self-used for heat; 8,400 h/yr"},
    {"label": "Levelised cost", "value": f"{R['LCOE_EUR_MWh']:.1f}", "unit": "€/MWh", "color": T.CORAL,
     "delta": f"{'▼' if m >= 0 else '▲'} {abs(m):.1f} vs tariff", "cls": "good" if m >= 0 else "bad",
     "tip": "LCOE = (annualised CAPEX + OPEX) / energy injected, HHV basis"},
    {"label": "NPV · 15 years", "value": f"{R['NPV_EUR'] / 1e6:+.2f}", "unit": "M€", "color": T.BLUE,
     "delta": f"at {s.disc:.1f} % discount", "cls": "good" if R["NPV_EUR"] >= 0 else "bad"},
    {"label": "Investment", "value": f"{R['capex_total'] / 1e6:.2f}", "unit": "M€",
     "delta": f"{R['capex_total'] / max(R['bm_net_Nm3_h'], 1):,.0f} € per Nm³/h"},
    {"label": "Digester stability", "value": f"{100 * ps:.0f}", "unit": "%", "color": T.VIOLET,
     "delta": "stable" if ps >= 0.9 else ("at risk" if ps >= 0.5 else "unstable"),
     "cls": "good" if ps >= 0.9 else ("warn" if ps >= 0.5 else "bad"), "tip": "Classifier probability that the digester is stable"},
])
if ref and (fs := S.full_sim(ref)):
    dev = 100 * (R["bm_net_Nm3_h"] / fs["bm_net_Nm3_h"] - 1)
    ui.callout(f"<b>Full-simulation check.</b> This saved design was run through the complete ADM1 + DWSIM model: "
               f"<b>{fs['bm_net_Nm3_h']:.1f} Nm³/h</b>, LCOE <b>{fs['LCOE_EUR_MWh']:.1f} €/MWh</b>, NPV "
               f"<b>{fs['NPV_EUR'] / 1e6:+.2f} M€</b>. The surrogate reads {dev:+.1f} % on output; optimisers favour points "
               f"where the ML is optimistic, which is why every reported design was re-verified.", "blue")

# -------------------------------------------------------------------- PFD ---
ui.section("01", "Process flow", "R-101 digester → K-101/102 compression → T-201 water scrubber → grid")
dg = "ok" if (ps >= 0.9 and R["VFA_gCOD_L"] <= core.STAB["VFA_margin"]) else ("warn" if stable else "bad")
up = "ok" if R["p_upg_valid"] >= 0.5 else "warn"
gr = "bad" if not (co2_ok and hhv_ok and o2_ok) else ("warn" if R["BM_O2_ppm"] > core.SPEC["O2_max"] else "ok")
ui.pfd(X, R, {"digester": dg, "upgrading": up, "grid": gr})

# ------------------------------------------------------------ constraints ---
ui.section("02", "Operating constraints", "position of each value against its limit")
c1, c2 = st.columns(2, gap="medium")
with c1, st.container(border=True):
    ui.panel_head("Digester · R-101", "ADM1 surrogate")
    vk = "ok" if R["VFA_gCOD_L"] <= 6 else ("warn" if R["VFA_gCOD_L"] <= 8 else "bad")
    ui.spec_table([
        {"name": "pH", "value": f"{R['pH']:.2f}", "limit": "≥ 6.80", "gauge": ui.gauge(R["pH"], 6.0, 8.5, 6.8, "" if R["pH"] >= 6.8 else "bad"),
         "status": ui.chip("ok", "ok") if R["pH"] >= 6.8 else ui.chip("bad", "low"), "tip": "Stability screen: pH ≥ 6.8"},
        {"name": "Volatile fatty acids", "value": f"{R['VFA_gCOD_L']:.2f} g/L", "limit": "≤ 8 (margin 6)",
         "gauge": ui.gauge(R["VFA_gCOD_L"], 0, 12, 8, "" if vk == "ok" else vk),
         "status": ui.chip(vk, {"ok": "ok", "warn": "no margin", "bad": "high"}[vk]),
         "tip": "Acid build-up indicator. Designs were optimised with a 6 g COD/L margin."},
        {"name": "Free ammonia", "value": f"{R['free_NH3_mgN_L']:.0f} mg/L", "limit": "inhibitory",
         "gauge": ui.gauge(R["free_NH3_mgN_L"], 0, 500, None, ""), "status": ui.chip("info", "monitor"),
         "tip": "Free NH₃ inhibits methanogens; strength set by K_I,NH3 in the console."},
        {"name": "Methane produced", "value": f"{R['CH4_Nm3_h']:.0f} Nm³/h", "limit": "", "gauge": "", "status": ""},
        {"name": "Biogas CH₄ content", "value": f"{100 * R['y_CH4_dry']:.1f} %", "limit": "", "gauge": "", "status": ""},
        {"name": "P(stable) · classifier", "value": f"{100 * ps:.1f} %", "limit": "≥ 90 %",
         "gauge": ui.gauge(ps, 0, 1, 0.9, "" if ps >= 0.9 else ("warn" if ps >= 0.5 else "bad")),
         "status": ui.chip("ok", "stable") if ps >= 0.9 else ui.chip("warn", "risk") if ps >= 0.5 else ui.chip("bad", "unstable")},
    ])
with c2, st.container(border=True):
    ui.panel_head("Upgrading · T-201 → grid", "DWSIM surrogate · GRDF spec")
    o2k = "ok" if R["BM_O2_ppm"] <= 100 else ("warn" if o2_ok else "bad")
    spec_kwh = R["P_el_upg_kW"] / R["biogas_dry_Nm3_h"]
    ui.spec_table([
        {"name": "CO₂ in biomethane", "value": f"{R['BM_CO2_pct']:.2f} %", "limit": "< 2.5 %",
         "gauge": ui.gauge(R["BM_CO2_pct"], 0, 5, 2.5, "" if co2_ok else "bad"),
         "status": ui.chip("ok", "ok") if co2_ok else ui.chip("bad", "high")},
        {"name": "O₂ in biomethane", "value": f"{R['BM_O2_ppm']:,.0f} ppm", "limit": "< 100 · exempt. 7,500",
         "gauge": ui.gauge(R["BM_O2_ppm"], 0, 8000, 7500, "" if o2k == "ok" else o2k),
         "status": ui.chip(o2k, {"ok": "ok", "warn": "exemption", "bad": "high"}[o2k]),
         "tip": "O₂ comes from stripping air dissolved in the recycled water; allowed up to 0.75 % under exemption."},
        {"name": "Higher heating value", "value": f"{R['HHV']:.2f} kWh/Nm³", "limit": "10.7 – 12.8",
         "gauge": ui.gauge(R["HHV"], 10.0, 13.0, 10.7, "" if hhv_ok else "bad"),
         "status": ui.chip("ok", "ok") if hhv_ok else ui.chip("bad", "out")},
        {"name": "Methane slip", "value": f"{R['CH4_slip_pct']:.2f} %", "limit": "lit. ≈ 1 %",
         "gauge": ui.gauge(R["CH4_slip_pct"], 0, 3, 1, "" if R["CH4_slip_pct"] <= 1 else "warn"),
         "status": ui.chip("ok", "low") if R["CH4_slip_pct"] <= 1 else ui.chip("warn", "high")},
        {"name": "Scrubber electricity", "value": f"{spec_kwh:.3f} kWh/Nm³", "limit": "lit. 0.20–0.30", "gauge": "", "status": "",
         "tip": "Per Nm³ of raw biogas; excludes drying and H₂S removal."},
        {"name": "P(simulator valid)", "value": f"{100 * R['p_upg_valid']:.0f} %", "limit": "≥ 50 %",
         "gauge": ui.gauge(R["p_upg_valid"], 0, 1, 0.5, "" if R["p_upg_valid"] >= 0.5 else "warn"),
         "status": ui.chip("ok", "reliable") if R["p_upg_valid"] >= 0.5 else ui.chip("warn", "caution")},
    ])

# -------------------------------------------------------------- economics ---
ui.section("03", "Economics", "CRE-anchored cost model · 2023 €")
E = R["energy_MWh_yr"]
parts = [("Capital (annuity)", R["ann_capex"] / E, T.TEAL), ("Feedstock", R["feed_cost"] / E, T.BLUE),
         ("Electricity", R["el_cost"] / E, T.CORAL), ("Other OPEX", R["fixed_om"] / E, T.VIOLET)]
c3, c4 = st.columns([1.45, 1], gap="medium")
with c3, st.container(border=True):
    ui.panel_head("Cost build-up per MWh", f"LCOE {R['LCOE_EUR_MWh']:.1f} €/MWh")
    f = go.Figure()
    for name, v, c in parts:
        f.add_bar(y=[""], x=[v], name=name, orientation="h", marker=dict(color=c, line=dict(color=T.SURFACE, width=2)),
                  text=[f"{v:.0f}"], textposition="inside", insidetextanchor="middle", textangle=0,
                  textfont=dict(color="#FFFFFF", size=12, family="IBM Plex Mono"),
                  hovertemplate=f"<b>{name}</b><br>%{{x:.1f}} €/MWh · {100 * v / R['LCOE_EUR_MWh']:.0f} % of LCOE<extra></extra>")
    f.add_vline(x=s.tariff, line=dict(color=T.INK, width=1.6, dash="dash"))
    f.add_annotation(x=s.tariff, y=1, yref="paper", yanchor="bottom", showarrow=False, text=f"tariff {s.tariff:.0f}",
                     font=dict(size=10.5, family="IBM Plex Mono", color=T.INK))
    f.add_vrect(x0=core.CRE["q1"], x1=core.CRE["q3"], fillcolor="rgba(94,242,200,0.08)", line_width=0, layer="below")
    f.add_annotation(x=core.CRE["q1"], y=0, yref="paper", yanchor="top", xanchor="left", showarrow=False,
                     text="French plants, CRE interquartile range", font=dict(size=10, color=T.MUTED))
    f.update_layout(barmode="stack", height=190, uniformtext=dict(minsize=9, mode="hide"), margin=dict(t=24, b=46, l=4, r=10),
                    xaxis=dict(title="€/MWh", range=[0, max(s.tariff, R["LCOE_EUR_MWh"], core.CRE["q3"]) * 1.06]),
                    legend=dict(orientation="h", y=-0.62, yanchor="top", traceorder="normal"))
    st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
with c4, st.container(border=True):
    ui.panel_head("Investment breakdown", f"total {R['capex_total'] / 1e6:.2f} M€")
    cx = [("Digester & civil", R["capex_digester"]), ("Upgrading unit", R["capex_upgrading"]),
          ("Feed & digestate", R["capex_feed_handling"]), ("Grid, electrical, other", R["capex_capacity_linked"])]
    f = go.Figure(go.Bar(x=[v / 1e6 for _, v in cx], y=[n for n, _ in cx], orientation="h", marker_color=T.TEAL,
                         text=[f"{v / 1e6:.2f}" for _, v in cx], textposition="outside", cliponaxis=False,
                         textfont=dict(family="IBM Plex Mono", size=11),
                         hovertemplate="<b>%{y}</b><br>%{x:.2f} M€<extra></extra>"))
    f.update_layout(height=190, margin=dict(t=8, b=8, l=4, r=40), xaxis=dict(title="M€"), yaxis=dict(autorange="reversed"))
    st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)

# ------------------------------------------------------------ next actions ---
ui.section("04", "Next steps", "")
nx = st.container(key="nextsteps")
a1, a2, a3, a4 = nx.columns(4)
a1.page_link("views/explorer.py", label="Explore sensitivities →", width="stretch")
a2.page_link("views/risk.py", label="Run a risk analysis →", width="stretch")
a3.page_link("views/library.py", label="Compare with verified designs →", width="stretch")
export = {"inputs": X, "market": S.econ_inputs(), "results": {k: float(v) for k, v in R.items()}}
a4.download_button("Export this evaluation (JSON)", json.dumps(export, indent=2), file_name=f"methatwin_{S.fingerprint()}.json",
                   mime="application/json", width="stretch")
