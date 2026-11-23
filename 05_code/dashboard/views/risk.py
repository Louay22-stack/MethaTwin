"""What could go wrong - Monte Carlo and main drivers for the current design, run on demand; a plain verdict first."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import core
import state as S
import theme as T
import tokens as K
import ui

X, ECON, s = S.design(), S.econ(), st.session_state
fp = S.fingerprint()

ui.page_head("futures", "What could go wrong", "How sure can you be?",
             f"Prices move and microbes surprise. Replay your design through thousands of possible futures (a {ui.term('Monte Carlo')} "
             "run) and see how often it still pays.")

with st.container(horizontal=True, vertical_alignment="bottom", gap="small"):
    n = st.segmented_control("Number of futures", [500, 1000, 2000, 5000], default=2000, key="mc_n") or 2000
    run = st.button("Replay the futures", type="primary", icon=":material/play_arrow:")
    with st.popover("What is varied", icon=":material/help:"):
        st.markdown("""
| Input | How it is drawn |
|---|---|
| Breakdown speed k_dis | log-uniform 0.05–0.5 per day |
| Ammonia tolerance K_I,NH3 | log-uniform 0.0012–0.0084 M |
| Building cost | triangular ×0.8 / 1.0 / 1.25 |
| Cover-crop and maize cost | uniform ±30 % |
| Slurry cost | uniform 7.3–43.2 €/t |
| Electricity | uniform 120–202 €/MWh |
| Other running costs | triangular ±20 % |
| Tariff | uniform 111–169 €/MWh |
| Discount rate | uniform 5–9 % |
| Heat used on site | uniform 2–6 % |
""")

if run:
    with st.status("Replaying the futures…", expanded=False) as stt:
        stt.update(label=f"Running {n:,} futures through the fast models…")
        mc = core.monte_carlo(S.sur(), X, ECON, n=int(n))
        stt.update(label="Finding the main drivers (20 runs)…")
        lc0, tor = core.tornado(S.sur(), X, ECON)
        s["risk"] = {"fp": fp, "n": int(n), "mc": mc, "lc0": lc0, "tor": tor}
        stt.update(label=f"Done: {n:,} futures", state="complete")
    st.toast("Replay complete", icon=":material/check_circle:")

res = s.get("risk")
if res is None:
    ui.verdict("info", "Not run yet", "Press “Replay the futures” to test your design.",
               "It takes about a second for 2,000 futures. Nothing is shown until you ask, so the page stays calm.")
    st.stop()

mc, lc0, tor = res["mc"], res["lc0"], res["tor"]
stab = mc.p_stable >= 0.5
if not stab.any():
    ui.verdict("bad", "No stable future", "In every future the digester turns unstable.",
               "This design has no safe operating window under the uncertain biology. Lengthen the retention time or lower the "
               "nitrogen-rich share of the feed on Your plant.")
    st.stop()
L = mc.LCOE_EUR_MWh[stab]
q = L.quantile([0.1, 0.5, 0.9])
p_pos = float((mc.NPV_EUR[stab] > 0).mean())
fail = float(1 - stab.mean())
in10 = round(10 * p_pos)
kind = "ok" if p_pos >= 0.5 else ("warn" if p_pos >= 0.2 else "bad")
title = (f"It pays in about {in10} of 10 futures." if in10 >= 1 else "It pays in fewer than 1 in 10 futures.")
driver = tor.sort_values("swing", ascending=False).iloc[0]["input"].split(" (")[0]
ui.verdict(kind, {"ok": "Likely to pay", "warn": "A gamble", "bad": "Unlikely to pay"}[kind], title,
           f"The single input that moves the cost most is <b>{driver.lower()}</b>. "
           + (f"The digester fails in about {round(100 * fail)} % of the futures." if fail >= 0.01 else "The digester stays stable in almost every future."))
if res["fp"] != fp:
    ui.callout("<b>These results are out of date.</b> The design or the market changed since this replay. "
               "Press <b>Replay the futures</b> to refresh.", "warn")
st.write("")

with st.expander("Key figures *cost range, chance of profit, output*", icon=":material/monitoring:"):
    ui.kpis([
        {"label": "Middle cost (P50)", "value": f"{q[0.5]:.0f}", "unit": "€/MWh",
         "delta": f"P10 {q[0.1]:.0f} · P90 {q[0.9]:.0f}"},
        {"label": "Chance of profit", "value": f"{100 * p_pos:.0f}", "unit": "%", "delta": "NPV above zero, stable futures",
         "cls": "good" if p_pos >= 0.5 else "bad"},
        {"label": "Digester failure", "value": f"{100 * fail:.0f}", "unit": "%", "delta": "of futures predicted unstable"},
        {"label": "Middle output", "value": f"{mc.bm_net_Nm3_h[stab].median():.0f}", "unit": "Nm³/h",
         "delta": f"P10 {mc.bm_net_Nm3_h[stab].quantile(.1):.0f} · P90 {mc.bm_net_Nm3_h[stab].quantile(.9):.0f}"},
        {"label": "Futures", "value": f"{res['n']:,}", "unit": "", "delta": f"{int(stab.sum()):,} stable"},
    ])
    ui.note(f"Half the futures cost less than the middle value. {ui.term('P10')}: 1 in 10 futures is cheaper. "
            f"{ui.term('P90')}: 9 in 10 futures are cheaper.")

with st.expander("The range of possible costs *two histograms*", icon=":material/bar_chart:"):
    v1, v2 = st.columns(2, gap="medium")
    with v1, st.container(border=True):
        f = go.Figure(go.Histogram(x=L, nbinsx=55, marker=dict(color=T.D1, line=dict(color=T.SURFACE, width=1)),
                                   hovertemplate="%{x} €/MWh<br>%{y} futures<extra></extra>"))
        f.add_vrect(x0=111, x1=169, fillcolor=K.rgba("text-primary", 0.05), line_width=0, layer="below")
        for qq, lab in ((0.1, "P10"), (0.5, "P50"), (0.9, "P90")):
            f.add_vline(x=q[qq], line=dict(color=T.INK, width=1.6 if qq == 0.5 else 1, dash="solid" if qq == 0.5 else "dot"))
            f.add_annotation(x=q[qq], y=1, yref="paper", yanchor="bottom", showarrow=False, text=f"{lab} {q[qq]:.0f}", font=dict(size=12, color=T.INK))
        f.update_layout(title="Cost per MWh (€/MWh)", height=330, bargap=0.03, showlegend=False,
                        xaxis_title="€/MWh · light band = tariff range 111–169", yaxis_title="futures", margin=dict(t=52))
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
    with v2, st.container(border=True):
        npv = mc.NPV_EUR[stab] / 1e6
        f = go.Figure()
        f.add_histogram(x=npv[npv < 0], nbinsx=40, marker=dict(color=T.D4, line=dict(color=T.SURFACE, width=1)), name="loses money",
                        hovertemplate="%{x} M€<br>%{y} futures<extra>loss</extra>")
        f.add_histogram(x=npv[npv >= 0], nbinsx=20, marker=dict(color=T.D3, line=dict(color=T.SURFACE, width=1)), name="pays",
                        hovertemplate="%{x} M€<br>%{y} futures<extra>profit</extra>")
        f.add_vline(x=0, line=dict(color=T.INK, width=1.4))
        f.update_layout(title="Value over 15 years, NPV (M€)", height=330, bargap=0.03, barmode="overlay",
                        xaxis_title="M€", yaxis_title="futures", margin=dict(t=52), legend=dict(x=0.6, y=1.0))
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)

with st.expander("What moves the cost most *main drivers*", icon=":material/swap_horiz:"):
    d1, d2 = st.columns([1.25, 1], gap="medium")
    with d1, st.container(border=True):
        f = go.Figure()
        f.add_bar(y=tor.input, x=tor.low - lc0, base=lc0, orientation="h", name="input at its low value", marker_color=T.D2,
                  customdata=tor.low, hovertemplate="<b>%{y}</b><br>low → %{customdata:.1f} €/MWh<extra></extra>")
        f.add_bar(y=tor.input, x=tor.high - lc0, base=lc0, orientation="h", name="input at its high value", marker_color=T.D1,
                  customdata=tor.high, hovertemplate="<b>%{y}</b><br>high → %{customdata:.1f} €/MWh<extra></extra>")
        f.add_vline(x=lc0, line=dict(color=T.INK, width=1.4))
        f.update_layout(title=f"Around your cost of {lc0:.1f} €/MWh", barmode="overlay", height=420, xaxis_title="Cost per MWh (€/MWh)",
                        margin=dict(t=60), legend=dict(y=1.0, yanchor="bottom", x=0))
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
    with d2, st.container(border=True):
        ui.panel_head("Swing table", "click a column to sort")
        tt = tor.sort_values("swing", ascending=False)[["input", "low", "high", "swing"]]
        st.dataframe(tt, hide_index=True, width="stretch", height=400,
                     column_config={"input": st.column_config.TextColumn("Input (low / high)", width="medium"),
                                    "low": st.column_config.NumberColumn("Cost at low", format="%.1f"),
                                    "high": st.column_config.NumberColumn("Cost at high", format="%.1f"),
                                    "swing": st.column_config.ProgressColumn("Swing €/MWh", format="%.1f", min_value=0,
                                                                             max_value=float(tt.swing.max()))})

with st.expander("Explore every future *scatter and CSV*", icon=":material/scatter_plot:"):
    e1, e2 = st.columns([1, 3])
    INPUTS = {"mc_cost_slurry": "Slurry cost (€/t)", "mc_capex_factor": "Building cost factor", "mc_tariff": "Tariff (€/MWh)",
              "mc_el_price": "Electricity (€/MWh)", "mc_discount": "Discount rate", "K_I_nh3": "Ammonia tolerance K_I,NH3 (M)",
              "k_dis": "Breakdown speed k_dis (1/d)"}
    xin = e1.radio("Plot the cost against", list(INPUTS), format_func=INPUTS.get, key="mc_x")
    e1.download_button("Download all futures (CSV)", mc.to_csv(index=False).encode(), file_name=f"methatwin_mc_{res['fp']}.csv",
                       mime="text/csv", width="stretch", icon=":material/download:")
    with e2, st.container(border=True):
        sub = mc.sample(min(len(mc), 2500), random_state=1)
        okm = sub.p_stable >= 0.5
        f = go.Figure()
        f.add_scattergl(x=sub[xin][okm], y=sub.LCOE_EUR_MWh[okm], mode="markers", name="stable",
                        marker=dict(size=5, color=T.D1, opacity=0.6), hovertemplate=f"{INPUTS[xin]} %{{x:.3g}}<br>cost %{{y:.1f}} €/MWh<extra></extra>")
        f.add_scattergl(x=sub[xin][~okm], y=sub.LCOE_EUR_MWh[~okm], mode="markers", name="unstable",
                        marker=dict(size=6, color=T.DMUTED, symbol="x", opacity=0.8), hovertemplate="unstable<extra></extra>")
        f.add_hline(y=lc0, line=dict(color=T.INK, width=1, dash="dot"))
        if xin in ("K_I_nh3", "k_dis"):
            f.update_xaxes(type="log")
        f.update_layout(height=340, xaxis_title=INPUTS[xin], yaxis_title="Cost per MWh (€/MWh)", margin=dict(t=30), showlegend=True)
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
        ui.note("Dots: stable futures. Crosses: futures where the digester is predicted unstable. Dotted line: your cost with today's inputs.")
