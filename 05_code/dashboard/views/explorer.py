"""Design explorer - one-input sweeps and a two-input response map around the current design."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
import state as S
import theme as T
import ui

X, ECON, s = S.design(), S.econ(), st.session_state
SHORT = {"feed_t_d": "Feed rate", "hrt_d": "HRT", "cive_share": "CIVE share", "maize_share": "Maize share",
         "water_per_kNm3": "Scrubber water", "p_flash_bar": "Flash pressure", "k_dis": "k_dis", "K_I_nh3": "K_I,NH3"}
PCT = ("maize_share", "cive_share")
METRICS = {"LCOE_EUR_MWh": ("Levelised cost", "€/MWh"), "bm_net_Nm3_h": ("Biomethane injected", "Nm³/h"),
           "NPV_EUR": ("NPV, 15 years", "M€"), "VFA_gCOD_L": ("Volatile fatty acids", "g COD/L"),
           "BM_CO2_pct": ("CO₂ in biomethane", "%"), "p_stable": ("P(digester stable)", "–")}

ui.page_head("Design explorer", "How each lever <em>moves</em> the plant",
             "Sweep one input across its full design range with everything else held at your current design, or map two "
             "inputs at once. Grey regions are designs the digester-stability classifier rejects.",
             f'Grid <b>120 points</b> per sweep<br/>Map <b>41 × 36</b> designs')

# ------------------------------------------------------------------ sweep ---
ui.section("01", "Single-input sweep", "click an input to sweep it · hover curves for values")
var = st.pills("Input to sweep", list(SHORT), format_func=lambda k: SHORT[k], default="feed_t_d", key="sweep_var",
               label_visibility="collapsed") or "feed_t_d"
lo, hi = {**core.BOUNDS, **core.UNC_BOUNDS}[var]
grid = np.geomspace(lo, hi, 120) if var in core.UNC_BOUNDS else np.linspace(lo, hi, 120)
dfg = pd.DataFrame([X] * len(grid))
dfg[var] = grid
A = core.assess(S.sur(), dfg, ECON)
k = 100 if var in PCT else 1
xs, cur = grid * k, X[var] * k
xt = f"{core.LABELS[var]} ({core.UNITS[var]})"
unstable = (A.p_stable < 0.5).to_numpy()
best = A.loc[~unstable, "LCOE_EUR_MWh"].idxmin() if (~unstable).any() else None


def decorate(f: go.Figure) -> go.Figure:
    i = 0
    while i < len(xs):
        if unstable[i]:
            j = i
            while j + 1 < len(xs) and unstable[j + 1]:
                j += 1
            f.add_vrect(x0=xs[max(i - 1, 0)], x1=xs[j], fillcolor="#9AA6A3", opacity=0.16, line_width=0)
            i = j + 1
        else:
            i += 1
    f.add_vline(x=cur, line=dict(color=T.CORAL, width=1.6, dash="dot"))
    if var in core.UNC_BOUNDS:
        f.update_xaxes(type="log")
    f.update_layout(hovermode="x unified", showlegend=False, xaxis_title=xt, height=270,
                    margin=dict(t=34, b=8, l=6, r=10))
    return f


def line(col: str, title: str, color: str, ref: tuple | None = None, logy: bool = False, scale: float = 1.0):
    f = go.Figure(go.Scatter(x=xs, y=A[col] * scale, mode="lines", line=dict(color=color, width=2.4), name=title,
                             hovertemplate="%{y:.3g}<extra></extra>"))
    f.add_scatter(x=[cur], y=[np.interp(cur, xs, A[col] * scale)], mode="markers", hoverinfo="skip",
                  marker=dict(color=T.CORAL, size=10, line=dict(color="#fff", width=2)))
    if ref:
        f.add_hline(y=ref[0], line=dict(color=ref[2], width=1.2, dash="dash"), annotation_text=ref[1],
                    annotation_position="top left", annotation_font=dict(size=10, family="IBM Plex Mono", color=ref[2]))
    f.update_layout(title=title)
    if logy:
        f.update_yaxes(type="log")
    return decorate(f)


g1, g2 = st.columns(2, gap="medium")
with g1, st.container(border=True):
    st.plotly_chart(line("LCOE_EUR_MWh", "Levelised cost (€/MWh)", T.CORAL, (s.tariff, f"tariff {s.tariff:.0f}", T.INK)),
                    width="stretch", config=T.PLOT_CFG)
with g2, st.container(border=True):
    st.plotly_chart(line("bm_net_Nm3_h", "Biomethane injected (Nm³/h)", T.TEAL), width="stretch", config=T.PLOT_CFG)
g3, g4 = st.columns(2, gap="medium")
with g3, st.container(border=True):
    st.plotly_chart(line("VFA_gCOD_L", "Volatile fatty acids (g COD/L)", T.VIOLET, (8, "stability limit 8", T.BAD)),
                    width="stretch", config=T.PLOT_CFG)
with g4, st.container(border=True):
    st.plotly_chart(line("BM_CO2_pct", "CO₂ in biomethane (%, log scale)", T.BLUE, (2.5, "grid limit 2.5 %", T.BAD), logy=True),
                    width="stretch", config=T.PLOT_CFG)
if best is not None:
    bx = A.loc[best, var] * k
    ui.md(f'<div class="mt-note">Along this sweep the lowest stable LCOE is <b>{A.loc[best, "LCOE_EUR_MWh"]:.1f} €/MWh</b> at '
          f'{SHORT[var]} = <b>{bx:.3g} {core.UNITS[var]}</b> (current: {cur:.3g}). Coral marker = your design. '
          f'Note that a sweep ignores grid-spec and output targets; use the map below to see both.</div>')
else:
    ui.callout("Every point of this sweep is predicted unstable. Adjust the kinetics or the feed blend in the console.", "warn")


# -------------------------------------------------------------------- map ---
@st.fragment
def response_map() -> None:
    ui.section("02", "Two-input response map", "choose axes and metric · this panel updates on its own")
    keys = list(core.BOUNDS)
    m1, m2, m3 = st.columns(3)
    xa = m1.selectbox("Horizontal axis", keys, index=keys.index("feed_t_d"), format_func=lambda k: SHORT[k], key="map_x")
    ya_opts = [k for k in keys if k != xa]
    ya = m2.selectbox("Vertical axis", ya_opts, index=ya_opts.index("hrt_d") if "hrt_d" in ya_opts else 0,
                      format_func=lambda k: SHORT[k], key="map_y")
    met = m3.selectbox("Colour = metric", list(METRICS), format_func=lambda k: f"{METRICS[k][0]} ({METRICS[k][1]})", key="map_m")
    (x0, x1), (y0, y1) = core.BOUNDS[xa], core.BOUNDS[ya]
    fx, fy = np.linspace(x0, x1, 41), np.linspace(y0, y1, 36)
    FX, FY = np.meshgrid(fx, fy)
    dm = pd.DataFrame([X] * FX.size)
    dm[xa], dm[ya] = FX.ravel(), FY.ravel()
    with st.spinner("Evaluating 1,476 designs…"):
        M = core.assess(S.sur(), dm, ECON)
    z = M[met].to_numpy().astype(float) * (1e-6 if met == "NPV_EUR" else 1)
    mask = (M.p_stable < 0.5).to_numpy() | (M.BM_CO2_pct > core.SPEC["CO2_max"]).to_numpy()
    if met != "p_stable":
        z[mask] = np.nan
    Z = z.reshape(FX.shape)
    kx, ky = (100 if xa in PCT else 1), (100 if ya in PCT else 1)
    seq = T.SEQ if met in ("LCOE_EUR_MWh", "VFA_gCOD_L", "BM_CO2_pct") else T.SEQ
    rev = met in ("bm_net_Nm3_h", "NPV_EUR", "p_stable")
    scale = [[i / (len(seq) - 1), c] for i, c in enumerate(seq)]
    with st.container(border=True):
        f = go.Figure(go.Heatmap(x=fx * kx, y=fy * ky, z=Z, colorscale=scale, reversescale=False,
                                 colorbar=dict(title=dict(text=METRICS[met][1], font=dict(size=11)), thickness=10, outlinewidth=0,
                                               tickfont=dict(family="IBM Plex Mono", size=10)),
                                 hovertemplate=f"{SHORT[xa]} %{{x:.3g}} · {SHORT[ya]} %{{y:.3g}}<br>"
                                               f"{METRICS[met][0]}: %{{z:.3g}} {METRICS[met][1]}<extra></extra>"))
        if met == "LCOE_EUR_MWh":
            f.add_contour(x=fx * kx, y=fy * ky, z=Z, showscale=False, hoverinfo="skip", showlegend=False,
                          contours=dict(start=s.tariff, end=s.tariff, size=1, coloring="none", showlabels=True,
                                        labelfont=dict(size=10, color=T.INK, family="IBM Plex Mono")),
                          line=dict(color=T.INK, width=1.8, dash="dash"))
        bm = M.bm_net_Nm3_h.to_numpy().reshape(FX.shape)
        f.add_contour(x=fx * kx, y=fy * ky, z=bm, showscale=False, hoverinfo="skip", showlegend=False,
                      contours=dict(start=150, end=300, size=50, coloring="none", showlabels=True,
                                    labelfont=dict(size=10, color=T.BLUE, family="IBM Plex Mono")),
                      line=dict(color=T.BLUE, width=1.1))
        f.add_scatter(x=[X[xa] * kx], y=[X[ya] * ky], mode="markers", name="current design", hoverinfo="skip",
                      marker=dict(size=13, color=T.CORAL, symbol="diamond", line=dict(color="#fff", width=2)))
        f.update_layout(height=470, plot_bgcolor="#E4E9E5", showlegend=False, margin=dict(t=12, b=8, l=6, r=6),
                        xaxis_title=f"{core.LABELS[xa]} ({core.UNITS[xa]})", yaxis_title=f"{core.LABELS[ya]} ({core.UNITS[ya]})")
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
        direction = "darker = higher" + (" (better)" if rev else " (worse)" if met != "p_stable" else "")
        ui.md(f'<div class="mt-legend"><span><i style="background:{T.CORAL};height:8px;width:8px"></i>Current design</span>'
              f'<span><i style="background:{T.BLUE}"></i>Output contours 150 / 200 / 250 / 300 Nm³/h</span>'
              + ('<span><i style="background:#0B2622"></i>LCOE = tariff</span>' if met == "LCOE_EUR_MWh" else "")
              + f'<span><i style="background:#C9D1CC;height:8px"></i>Grey = unstable or off-spec</span><span>Colour: {direction}</span></div>')


response_map()
