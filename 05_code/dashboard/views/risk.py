"""Risk analysis - Monte Carlo and tornado for the current design, run on demand with explicit states."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import core
import state as S
import theme as T
import ui

X, ECON, s = S.design(), S.econ(), st.session_state
fp = S.fingerprint()

ui.page_head("Risk analysis", "How <em>certain</em> is this design?",
             "Monte Carlo propagates uncertainty in two microbial parameters and nine prices through the surrogates and the "
             "cost model; the tornado ranks which single input moves the cost most. Distributions match the report (step 7c), "
             "centred on your market settings.",
             f'Design ID <b>{fp}</b><br/>Seed <b>42</b> (reproducible)')

c1, c2, c3 = st.columns([2.2, 1, 1.3], vertical_alignment="bottom")
n = c1.segmented_control("Number of Monte Carlo samples", [500, 1000, 2000, 5000], default=2000, key="mc_n") or 2000
run = c2.button("Run analysis", type="primary", width="stretch")
with c3.popover("Sampled distributions", width="stretch"):
    st.markdown("""
| Input | Distribution |
|---|---|
| k_dis | log-uniform 0.05–0.5 d⁻¹ |
| K_I,NH3 | log-uniform 0.0012–0.0084 M |
| CAPEX | triangular ×0.8 / 1.0 / 1.25 |
| CIVE, maize cost | uniform ±30 % |
| Slurry cost | uniform 7.3–43.2 €/t |
| Electricity | uniform 120–202 €/MWh |
| Other OPEX | triangular ±20 % |
| Tariff | uniform 111–169 €/MWh |
| Discount rate | uniform 5–9 % |
| Heat self-use | uniform 2–6 % |
""")

if run:
    with st.status("Running risk analysis…", expanded=False) as stt:
        stt.update(label=f"Sampling {n:,} scenarios through the surrogates…")
        mc = core.monte_carlo(S.sur(), X, ECON, n=int(n))
        stt.update(label="Computing one-at-a-time tornado (20 evaluations)…")
        lc0, tor = core.tornado(S.sur(), X, ECON)
        s["risk"] = {"fp": fp, "n": int(n), "mc": mc, "lc0": lc0, "tor": tor}
        stt.update(label=f"Done: {n:,} scenarios evaluated", state="complete")
    st.toast("Risk analysis complete", icon="✅")

res = s.get("risk")
if res is None:
    ui.empty("No analysis yet for this session",
             "Press <b>Run analysis</b> to sample the uncertain inputs around the design in the console. "
             "2,000 samples take about one second.")
    st.stop()
if res["fp"] != fp:
    ui.callout("<b>Results are out of date.</b> The design or market inputs changed since this analysis was run "
               f"(analysed ID {res['fp']}, current ID {fp}). Press <b>Run analysis</b> to refresh.", "warn")

mc, lc0, tor = res["mc"], res["lc0"], res["tor"]
stab = mc.p_stable >= 0.5
if not stab.any():
    ui.empty("Every sampled scenario is predicted unstable", "This design has no stable operating window under the sampled "
             "kinetics. Increase retention time or lower the nitrogen-rich share of the feed.")
    st.stop()
L = mc.LCOE_EUR_MWh[stab]
q = L.quantile([0.1, 0.5, 0.9])
p_pos = float((mc.NPV_EUR[stab] > 0).mean())
ui.kpis([
    {"label": "Median LCOE · P50", "value": f"{q[0.5]:.0f}", "unit": "€/MWh", "color": T.CORAL,
     "delta": f"P10 {q[0.1]:.0f} · P90 {q[0.9]:.0f}"},
    {"label": "Chance of profit", "value": f"{100 * p_pos:.0f}", "unit": "%", "color": T.BLUE,
     "delta": "P(NPV > 0), stable runs", "cls": "good" if p_pos >= 0.5 else "bad"},
    {"label": "Digester failure risk", "value": f"{100 * (1 - stab.mean()):.0f}", "unit": "%", "color": T.VIOLET,
     "delta": "of samples predicted unstable"},
    {"label": "Median output", "value": f"{mc.bm_net_Nm3_h[stab].median():.0f}", "unit": "Nm³/h", "color": T.TEAL,
     "delta": f"P10 {mc.bm_net_Nm3_h[stab].quantile(.1):.0f} · P90 {mc.bm_net_Nm3_h[stab].quantile(.9):.0f}"},
    {"label": "Samples", "value": f"{res['n']:,}", "unit": "", "delta": f"{int(stab.sum()):,} stable"},
])

ui.section("01", "Distributions", "stable samples only · hover bars for counts")
v1, v2 = st.columns(2, gap="medium")
with v1, st.container(border=True):
    f = go.Figure(go.Histogram(x=L, nbinsx=55, marker=dict(color=T.TEAL, line=dict(color=T.SURFACE, width=1)),
                               hovertemplate="%{x} €/MWh<br>%{y} samples<extra></extra>"))
    f.add_vrect(x0=111, x1=169, fillcolor="rgba(94,242,200,0.07)", line_width=0, layer="below")
    for qq, lab in ((0.1, "P10"), (0.5, "P50"), (0.9, "P90")):
        f.add_vline(x=q[qq], line=dict(color=T.INK, width=1.4 if qq == 0.5 else 1, dash="solid" if qq == 0.5 else "dot"))
        f.add_annotation(x=q[qq], y=1, yref="paper", yanchor="bottom", showarrow=False, text=f"{lab} {q[qq]:.0f}",
                         font=dict(size=10, family="IBM Plex Mono", color=T.INK))
    f.update_layout(title="Levelised cost (€/MWh)", height=320, bargap=0.03, showlegend=False, xaxis_title="€/MWh · shaded = tariff range 111–169",
                    yaxis_title="samples", margin=dict(t=46))
    st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
with v2, st.container(border=True):
    npv = mc.NPV_EUR[stab] / 1e6
    f = go.Figure()
    f.add_histogram(x=npv[npv < 0], nbinsx=40, marker=dict(color=T.CORAL, line=dict(color=T.SURFACE, width=1)), name="loss",
                    hovertemplate="%{x} M€<br>%{y} samples<extra>loss</extra>")
    f.add_histogram(x=npv[npv >= 0], nbinsx=20, marker=dict(color=T.TEAL, line=dict(color=T.SURFACE, width=1)), name="profit",
                    hovertemplate="%{x} M€<br>%{y} samples<extra>profit</extra>")
    f.add_vline(x=0, line=dict(color=T.INK, width=1.4))
    f.update_layout(title="Net present value, 15 years (M€)", height=320, bargap=0.03, barmode="overlay",
                    xaxis_title="M€", yaxis_title="samples", margin=dict(t=46), legend=dict(x=0.72, y=1.0))
    st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)

ui.section("02", "Drivers", "one input at a time, others at your settings")
d1, d2 = st.columns([1.25, 1], gap="medium")
with d1, st.container(border=True):
    f = go.Figure()
    f.add_bar(y=tor.input, x=tor.low - lc0, base=lc0, orientation="h", name="input at low value", marker_color=T.TEAL,
              customdata=tor.low, hovertemplate="<b>%{y}</b><br>low → %{customdata:.1f} €/MWh<extra></extra>")
    f.add_bar(y=tor.input, x=tor.high - lc0, base=lc0, orientation="h", name="input at high value", marker_color=T.CORAL,
              customdata=tor.high, hovertemplate="<b>%{y}</b><br>high → %{customdata:.1f} €/MWh<extra></extra>")
    f.add_vline(x=lc0, line=dict(color=T.INK, width=1.4))
    f.update_layout(title=f"Tornado around {lc0:.1f} €/MWh", barmode="overlay", height=400, xaxis_title="LCOE (€/MWh)",
                    margin=dict(t=56), legend=dict(y=1.0, yanchor="bottom", x=0))
    st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
with d2, st.container(border=True):
    ui.panel_head("Swing table", "sortable")
    tt = tor.sort_values("swing", ascending=False)[["input", "low", "high", "swing"]]
    st.dataframe(tt, hide_index=True, width="stretch", height=400,
                 column_config={"input": st.column_config.TextColumn("Input (low / high)", width="medium"),
                                "low": st.column_config.NumberColumn("LCOE low", format="%.1f"),
                                "high": st.column_config.NumberColumn("LCOE high", format="%.1f"),
                                "swing": st.column_config.ProgressColumn("Swing €/MWh", format="%.1f", min_value=0,
                                                                         max_value=float(tt.swing.max()))})

ui.section("03", "Sample explorer", "relationship between an uncertain input and the outcome")
e1, e2 = st.columns([1, 3])
INPUTS = {"mc_cost_slurry": "Slurry cost (€/t)", "mc_capex_factor": "CAPEX factor", "mc_tariff": "Tariff (€/MWh)",
          "mc_el_price": "Electricity (€/MWh)", "mc_discount": "Discount rate", "K_I_nh3": "K_I,NH3 (M)", "k_dis": "k_dis (1/d)"}
xin = e1.radio("Colour-coded scatter of", list(INPUTS), format_func=INPUTS.get, key="mc_x")
e1.download_button("Download samples (CSV)", mc.to_csv(index=False).encode(), file_name=f"methatwin_mc_{res['fp']}.csv",
                   mime="text/csv", width="stretch")
with e2, st.container(border=True):
    sub = mc.sample(min(len(mc), 2500), random_state=1)
    f = go.Figure(go.Scattergl(x=sub[xin], y=sub.LCOE_EUR_MWh, mode="markers",
                               marker=dict(size=5, color=np.where(sub.p_stable >= 0.5, T.TEAL, "#3A475E"), opacity=0.65),
                               hovertemplate=f"{INPUTS[xin]} %{{x:.3g}}<br>LCOE %{{y:.1f}} €/MWh<extra></extra>"))
    f.add_hline(y=lc0, line=dict(color=T.INK, width=1, dash="dot"))
    if xin in ("K_I_nh3", "k_dis"):
        f.update_xaxes(type="log")
    f.update_layout(height=330, xaxis_title=INPUTS[xin], yaxis_title="LCOE (€/MWh)", margin=dict(t=14))
    st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
    ui.md('<div class="mt-legend"><span><i style="background:#14AA82;height:8px;width:8px"></i>stable sample</span>'
          '<span><i style="background:#3A475E;height:8px;width:8px"></i>predicted unstable</span><span>dotted = nominal LCOE</span></div>')
