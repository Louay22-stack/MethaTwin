"""Your plant - the verdict and three plain answers first, the settings beside them; figures, the process flow,
operating limits and costs open on click."""
from __future__ import annotations

import json

import plotly.graph_objects as go
import streamlit as st

import core
import state as S
import theme as T
import tokens as K
import ui

s = st.session_state
ui.page_head("plant", "Your plant", "Is this plant a good idea?",
             "Shape the plant in the Settings panel. The answer updates at once; open any card below for the numbers.")


def on_preset() -> None:
    S.apply_preset()
    s["_toast"] = f"Loaded {s.preset}"


def on_reset() -> None:
    S.reset_all()
    s["_toast"] = "Back to the checked 200 Nm³/h design and the default market"


left, right = st.columns([1.55, 1], gap="large")

# ------------------------------------------------------------------- settings ---
with right, st.container(key="settings"):
    mods = S.modified_groups()
    ui.md('<div class="mt-settings-head"><div class="t">Settings</div>'
          '<div class="s">Every page uses these. Changes apply instantly.</div></div>')
    st.selectbox("Start from", list(S.presets()), key="preset", on_change=on_preset,
                 help="A ready-made design. 'Verified' designs were confirmed by the full simulation (ADM1 + DWSIM).")
    t1, t2, t3, t4 = st.tabs(["Feed & tank" + (" •" if mods["design"] else ""), "Gas cleaning",
                              "Microbes" + (" •" if mods["kinetics"] else ""), "Market" + (" •" if mods["market"] else "")])
    with t1:
        st.slider("Maize silage (% of feed)", 0.0, 15.0, key="maize_pct", step=0.5, format="%.1f",
                  help="Capped at 15 % of the tonnage by French law (décret 2016-929).")
        st.slider("Cover-crop silage, CIVE (% of feed)", 5.0, 45.0, key="cive_pct", step=0.5, format="%.1f",
                  help="Crops grown between two main crops for energy; not covered by the maize cap.")
        ui.md(f'<div class="mt-derived"><span>Cattle slurry makes up the rest</span><b>{100 - s.maize_pct - s.cive_pct:.1f} %</b></div>')
        st.slider("Feed rate (tonnes per day)", 60.0, 160.0, key="feed", step=1.0, format="%.0f", help="Fresh feed going into the digester each day.")
        st.slider("Retention time (days)", 40.0, 110.0, key="hrt", step=1.0, format="%.0f",
                  help="How long the feed stays in the tank. Tank volume = feed rate × retention time.")
        ui.md(f'<div class="mt-derived"><span>Tank volume</span><b>{s.feed * s.hrt:,.0f} m³</b></div>')
    with t2:
        st.slider("Wash water (m³ per 1,000 Nm³ of raw gas)", 100.0, 200.0, key="water", step=1.0, format="%.0f",
                  help="More water removes more CO₂ but needs more pumping and can carry away some methane.")
        st.slider("Flash pressure (bar)", 2.0, 3.5, key="pflash", step=0.05, format="%.2f",
                  help="A vessel that releases methane caught in the wash water and sends it back to the compressor.")
    with t3:
        st.caption("How the microbes behave is uncertain. These two settings let you test that.")
        st.select_slider("How fast the feed breaks down, k_dis (per day)", S.KD_OPTS, key="kdis",
                         help="Calibrated value 0.1 (Bułkowska 2015); the benchmark default is 0.5.")
        st.select_slider("Ammonia tolerance, K_I,NH3 (M)", S.KI_OPTS, key="ki",
                         help="Lower means the microbes are more easily poisoned by ammonia. Nominal 0.0018 (BSM2).")
    with t4:
        st.slider("Gas price paid, tariff (€/MWh)", 100.0, 180.0, key="tariff", step=0.5, format="%.1f",
                  help="2023 farm tariffs ranged 111–169, average 152.8 (CRE 2024).")
        st.slider("Slurry cost (€/t)", 0.0, 45.0, key="slurry", step=0.5, format="%.1f",
                  help="7.3 = transport only; 43.2 = full price including transport (CRE).")
        st.slider("Cover-crop silage cost (€/t)", 20.0, 60.0, key="cive_cost", step=0.5, format="%.1f")
        st.slider("Maize silage cost (€/t)", 20.0, 60.0, key="maize_cost", step=0.5, format="%.1f")
        st.slider("Electricity price (€/MWh)", 60.0, 250.0, key="el", step=1.0, format="%.0f")
        st.slider("Building cost multiplier (×)", 0.7, 1.4, key="capexf", step=0.05, format="%.2f", help="1.0 = the CRE-based estimate.")
        st.slider("Discount rate (%)", 3.0, 12.0, key="disc", step=0.5, format="%.1f", help="The return investors expect each year.")
    b1, b2 = st.columns(2)
    if b1.button("Save design", type="primary", width="stretch", icon=":material/bookmark_add:"):
        ui.save_dialog()
    b2.button("Reset", on_click=on_reset, width="stretch", icon=":material/restart_alt:")

# evaluate after the widgets so the answer reflects this run's inputs
X, R = S.design(), S.evaluate()
st_ = ui.status(R)
ref = S.matches_reference()

# -------------------------------------------------------------------- verdict ---
with left:
    issues = []
    if not st_["stable"]:
        issues.append("the digester would likely turn <b>unstable</b>")
    if not (st_["co2_ok"] and st_["hhv_ok"]):
        issues.append("the gas <b>misses the grid rules</b>")
    if not st_["o2_ok"]:
        issues.append("too much <b>oxygen</b> stays in the gas")
    if issues:
        ui.verdict("bad", "Needs changes", "This plant would not work as designed.",
                   "As set up, " + "; ".join(issues) + ". Try another feed mix or a longer retention time, or start from a verified design.")
    elif R["NPV_EUR"] < 0:
        ui.verdict("warn", "Works, but does not pay", "The plant runs, but it loses money.",
                   f"The microbes are fine and the gas meets the grid rules, but over its lifetime the plant costs more than its gas earns "
                   f"(its {ui.term('NPV')} is below zero).")
    elif R["p_upg_valid"] < 0.5:
        ui.verdict("warn", "Works, with a doubt", "A good plant, but check the gas cleaning.",
                   "These scrubber settings sit outside the zone where the model was trained, so treat the gas result with care.")
    else:
        ui.verdict("ok", "A good design", "This plant works and pays for itself.",
                   "Healthy microbes, grid-quality gas, and gas sales that cover building and running it over 15 years.")
    ui.answers([("digester", "Biology", *st_["bio"]), ("scrub", "Gas", *st_["gas"]), ("money", "Money", *st_["money"])])
    if ref:
        ui.note(f"You are on the unchanged design “{ref}”.")
    else:
        ui.note("You changed the settings, so this is a new design. Save it to compare it later.")

st.write("")
# --------------------------------------------------------------------- reveals ---
with st.expander("Key figures *output, cost and value*", icon=":material/monitoring:"):
    m = s.tariff - R["LCOE_EUR_MWh"]
    ui.kpis([
        {"label": "Gas to the grid", "value": f"{R['bm_net_Nm3_h']:.0f}", "unit": "Nm³/h", "delta": f"{R['energy_MWh_yr'] / 1000:.1f} GWh a year"},
        {"label": "Cost per MWh (LCOE)", "value": f"{R['LCOE_EUR_MWh']:.1f}", "unit": "€/MWh",
         "delta": f"{abs(m):.1f} {'below' if m >= 0 else 'above'} the tariff", "cls": "good" if m >= 0 else "bad"},
        {"label": "Value over 15 years (NPV)", "value": f"{R['NPV_EUR'] / 1e6:+.2f}", "unit": "M€",
         "delta": f"at {s.disc:.1f} % discount", "cls": "good" if R["NPV_EUR"] >= 0 else "bad"},
        {"label": "Investment (CAPEX)", "value": f"{R['capex_total'] / 1e6:.2f}", "unit": "M€",
         "delta": f"{R['capex_total'] / max(R['bm_net_Nm3_h'], 1):,.0f} € per Nm³/h"},
        {"label": "Chance the digester is stable", "value": f"{100 * R['p_stable']:.0f}", "unit": "%",
         "delta": st_["bio"][1].lower(), "cls": {"ok": "good", "warn": "warn", "bad": "bad"}[st_["bio"][0]]},
    ])
    ui.note(f"{ui.term('LCOE')}: building and running costs per MWh injected. {ui.term('NPV')}: money in minus money out over "
            f"15 years in today's euros. Values come from the fast {ui.term('surrogate')} models.")
    if ref and (fs := S.full_sim(ref)):
        dev = 100 * (R["bm_net_Nm3_h"] / fs["bm_net_Nm3_h"] - 1)
        ui.callout(f"<b>Checked with the full simulation.</b> This design was also run through the complete ADM1 + DWSIM model: "
                   f"<b>{fs['bm_net_Nm3_h']:.1f} Nm³/h</b>, LCOE <b>{fs['LCOE_EUR_MWh']:.1f} €/MWh</b>, NPV "
                   f"<b>{fs['NPV_EUR'] / 1e6:+.2f} M€</b>. The fast model reads {dev:+.1f} % on output; optimisers favour points "
                   f"where the ML is optimistic, which is why every reported design was re-checked.", "accent")

with st.expander("Follow the gas *process diagram*", icon=":material/account_tree:"):
    ps = R["p_stable"]
    dg = "ok" if (ps >= 0.9 and R["VFA_gCOD_L"] <= core.STAB["VFA_margin"]) else ("warn" if st_["stable"] else "bad")
    up = "ok" if R["p_upg_valid"] >= 0.5 else "warn"
    gr = "bad" if not st_["spec"] else ("warn" if R["BM_O2_ppm"] > core.SPEC["O2_max"] else "ok")
    ui.pfd(X, R, {"digester": dg, "upgrading": up, "grid": gr})

with st.expander("Operating limits *how close to the edge*", icon=":material/speed:"):
    ps = R["p_stable"]
    c1, c2 = st.columns(2, gap="medium")
    with c1, st.container(border=True):
        ui.panel_head("Digester", "ADM1 fast model")
        vk = "ok" if R["VFA_gCOD_L"] <= 6 else ("warn" if R["VFA_gCOD_L"] <= 8 else "bad")
        pk = "ok" if ps >= 0.9 else ("warn" if ps >= 0.5 else "bad")
        ui.spec_table([
            {"name": "pH", "value": f"{R['pH']:.2f}", "limit": "≥ 6.80", "gauge": ui.gauge(R["pH"], 6.0, 8.5, 6.8, "" if R["pH"] >= 6.8 else "bad"),
             "status": ui.pill("ok", "OK") if R["pH"] >= 6.8 else ui.pill("bad", "Low")},
            {"name": f"Acids ({ui.term('VFA')})", "value": f"{R['VFA_gCOD_L']:.2f} g/L", "limit": "≤ 8 (margin 6)",
             "gauge": ui.gauge(R["VFA_gCOD_L"], 0, 12, 8, "" if vk == "ok" else vk),
             "status": ui.pill(vk, {"ok": "OK", "warn": "No margin", "bad": "High"}[vk])},
            {"name": "Free ammonia", "value": f"{R['free_NH3_mgN_L']:.0f} mg/L", "limit": "inhibits microbes",
             "gauge": ui.gauge(R["free_NH3_mgN_L"], 0, 500, None, ""), "status": ui.pill("info", "Watch")},
            {"name": "Methane made", "value": f"{R['CH4_Nm3_h']:.0f} Nm³/h"},
            {"name": "Methane in biogas", "value": f"{100 * R['y_CH4_dry']:.1f} %"},
            {"name": f"Stable ({ui.term('P(stable)')})", "value": f"{100 * ps:.1f} %", "limit": "≥ 90 %",
             "gauge": ui.gauge(ps, 0, 1, 0.9, "" if pk == "ok" else pk),
             "status": ui.pill(pk, {"ok": "Stable", "warn": "At risk", "bad": "Unstable"}[pk])},
        ])
    with c2, st.container(border=True):
        ui.panel_head("Gas cleaning and grid", "DWSIM fast model · GRDF rules")
        o2k = "ok" if R["BM_O2_ppm"] <= 100 else ("warn" if st_["o2_ok"] else "bad")
        ui.spec_table([
            {"name": "CO₂ in the gas", "value": f"{R['BM_CO2_pct']:.2f} %", "limit": "< 2.5 %",
             "gauge": ui.gauge(R["BM_CO2_pct"], 0, 5, 2.5, "" if st_["co2_ok"] else "bad"),
             "status": ui.pill("ok", "OK") if st_["co2_ok"] else ui.pill("bad", "High")},
            {"name": "O₂ in the gas", "value": f"{R['BM_O2_ppm']:,.0f} ppm", "limit": "< 100 · exemption 7,500",
             "gauge": ui.gauge(R["BM_O2_ppm"], 0, 8000, 7500, "" if o2k == "ok" else o2k),
             "status": ui.pill(o2k, {"ok": "OK", "warn": "Exemption", "bad": "High"}[o2k])},
            {"name": f"Heating value ({ui.term('HHV')})", "value": f"{R['HHV']:.2f} kWh/Nm³", "limit": "10.7 – 12.8",
             "gauge": ui.gauge(R["HHV"], 10.0, 13.0, 10.7, "" if st_["hhv_ok"] else "bad"),
             "status": ui.pill("ok", "OK") if st_["hhv_ok"] else ui.pill("bad", "Out")},
            {"name": ui.term("methane slip").replace(">methane slip<", ">Methane slip<"), "value": f"{R['CH4_slip_pct']:.2f} %", "limit": "literature ≈ 1 %",
             "gauge": ui.gauge(R["CH4_slip_pct"], 0, 3, 1, "" if R["CH4_slip_pct"] <= 1 else "warn"),
             "status": ui.pill("ok", "Low") if R["CH4_slip_pct"] <= 1 else ui.pill("warn", "High")},
            {"name": "Scrubber electricity", "value": f"{R['P_el_upg_kW'] / R['biogas_dry_Nm3_h']:.3f} kWh/Nm³", "limit": "literature 0.20–0.30"},
            {"name": "Model reliability", "value": f"{100 * R['p_upg_valid']:.0f} %", "limit": "≥ 50 %",
             "gauge": ui.gauge(R["p_upg_valid"], 0, 1, 0.5, "" if R["p_upg_valid"] >= 0.5 else "warn"),
             "status": ui.pill("ok", "Reliable") if R["p_upg_valid"] >= 0.5 else ui.pill("warn", "Caution")},
        ])

with st.expander("Where the money goes *cost build-up and investment*", icon=":material/payments:"):
    E = R["energy_MWh_yr"]
    parts = [("Building (annual share)", R["ann_capex"] / E, T.D1), ("Feed", R["feed_cost"] / E, T.D2),
             ("Electricity", R["el_cost"] / E, T.D3), ("Other running costs", R["fixed_om"] / E, T.D4)]
    c3, c4 = st.columns([1.45, 1], gap="medium")
    with c3, st.container(border=True):
        ui.panel_head("Cost of one MWh", f"LCOE {R['LCOE_EUR_MWh']:.1f} €/MWh vs tariff {s.tariff:.0f}")
        f = go.Figure()
        for name, v, c in parts:
            f.add_bar(y=[""], x=[v], name=name, orientation="h", marker=dict(color=c, line=dict(color=T.SURFACE, width=2)),
                      text=[f"{v:.0f}"], textposition="inside", insidetextanchor="middle", textangle=0,
                      textfont=dict(color=T.ON_ACCENT, size=13, family=T.FONT_BODY),
                      hovertemplate=f"<b>{name}</b><br>%{{x:.1f}} €/MWh · {100 * v / R['LCOE_EUR_MWh']:.0f} % of the cost<extra></extra>")
        f.add_vline(x=s.tariff, line=dict(color=T.INK, width=1.6, dash="dash"))
        f.add_annotation(x=s.tariff, y=1, yref="paper", yanchor="bottom", showarrow=False, text=f"tariff {s.tariff:.0f}",
                         font=dict(size=12, color=T.INK))
        f.add_vrect(x0=core.CRE["q1"], x1=core.CRE["q3"], fillcolor=K.rgba("accent", 0.08), line_width=0, layer="below")
        f.add_annotation(x=core.CRE["q1"], y=0, yref="paper", yanchor="top", xanchor="left", showarrow=False,
                         text="shaded: middle half of French plants (CRE)", font=dict(size=12, color=T.MUTED))
        f.update_layout(barmode="stack", height=210, uniformtext=dict(minsize=10, mode="hide"), margin=dict(t=26, b=50, l=4, r=10),
                        xaxis=dict(title="€/MWh", range=[0, max(s.tariff, R["LCOE_EUR_MWh"], core.CRE["q3"]) * 1.06]),
                        legend=dict(orientation="h", y=-0.7, yanchor="top", traceorder="normal"))
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
    with c4, st.container(border=True):
        ui.panel_head("Investment", f"total {R['capex_total'] / 1e6:.2f} M€")
        cx = [("Digester & civil works", R["capex_digester"]), ("Gas cleaning unit", R["capex_upgrading"]),
              ("Feed & digestate", R["capex_feed_handling"]), ("Grid, electrical, other", R["capex_capacity_linked"])]
        f = go.Figure(go.Bar(x=[v / 1e6 for _, v in cx], y=[n for n, _ in cx], orientation="h", marker_color=T.D1,
                             text=[f"{v / 1e6:.2f}" for _, v in cx], textposition="outside", cliponaxis=False,
                             textfont=dict(family=T.FONT_BODY, size=12, color=T.INK),
                             hovertemplate="<b>%{y}</b><br>%{x:.2f} M€<extra></extra>"))
        f.update_layout(height=210, margin=dict(t=8, b=8, l=4, r=44), xaxis=dict(title="M€"), yaxis=dict(autorange="reversed"))
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)

# ----------------------------------------------------------------- next steps ---
ui.section("Where next")
with st.container(key="doors"):
    a1, a2, a3, a4 = st.columns(4)
    a1.page_link("views/explorer.py", label="Try changes", icon=":material/tune:", width="stretch")
    a2.page_link("views/risk.py", label="What could go wrong", icon=":material/casino:", width="stretch")
    a3.page_link("views/library.py", label="Compare with checked designs", icon=":material/bookmarks:", width="stretch")
    export = {"inputs": X, "market": S.econ_inputs(), "results": {k: float(v) for k, v in R.items()}}
    a4.download_button("Export this result (JSON)", json.dumps(export, indent=2), file_name=f"methatwin_{S.fingerprint()}.json",
                       mime="application/json", width="stretch", icon=":material/download:")
