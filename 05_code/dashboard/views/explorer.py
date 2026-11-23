"""Try changes - which setting matters most (plain verdict), then one-setting curves and a two-setting map on click."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
import state as S
import theme as T
import tokens as K
import ui

X, ECON, s = S.design(), S.econ(), st.session_state
SHORT = {"feed_t_d": "Feed rate", "hrt_d": "Retention time", "cive_share": "Cover-crop share", "maize_share": "Maize share",
         "water_per_kNm3": "Wash water", "p_flash_bar": "Flash pressure", "k_dis": "Breakdown speed k_dis", "K_I_nh3": "Ammonia tolerance K_I,NH3"}
PCT = ("maize_share", "cive_share")
METRICS = {"LCOE_EUR_MWh": ("Cost per MWh (LCOE)", "€/MWh"), "bm_net_Nm3_h": ("Gas to the grid", "Nm³/h"),
           "NPV_EUR": ("Value over 15 years (NPV)", "M€"), "VFA_gCOD_L": ("Acids in the tank (VFA)", "g COD/L"),
           "BM_CO2_pct": ("CO₂ in the gas", "%"), "p_stable": ("Chance the digester is stable", "–")}
SHADE = K.rgba("surface-hover", 0.9)

ui.page_head("sliders", "Try changes", "What happens if I change one thing?",
             "Everything else stays as in your current design. Start with the answer below, then open the curves or the map.")


# ---------------------------------------------------------------- verdict: biggest lever ---
@st.cache_data(show_spinner=False, max_entries=64)
def levers(xj: tuple, fp: str) -> pd.DataFrame:
    x = dict(xj)
    rows = []
    for v, (lo, hi) in core.BOUNDS.items():
        g = np.linspace(lo, hi, 25)
        d = pd.DataFrame([x] * len(g))
        d[v] = g
        A = core.assess(S.sur(), d, S.econ())
        ok = (A.p_stable >= 0.5) & (A.BM_CO2_pct <= core.SPEC["CO2_max"])
        L = A.LCOE_EUR_MWh[ok]
        rows.append({"var": v, "swing": float(L.max() - L.min()) if len(L) else 0.0,
                     "best": float(L.min()) if len(L) else np.nan, "at": float(g[L.idxmin()]) if len(L) else np.nan})
    return pd.DataFrame(rows).sort_values("swing", ascending=False)


with st.spinner("Comparing the settings…"):
    LV = levers(tuple(sorted(X.items())), S.fingerprint())
top = LV.iloc[0]
lc_now = S.evaluate()["LCOE_EUR_MWh"]
if np.isnan(top.best):
    ui.verdict("bad", "No safe room", "No single change keeps this plant stable.",
               "Every point along each setting is predicted unstable or off-spec. Start from a verified design on Your plant.")
elif top.best < lc_now - 0.5:
    ui.verdict("info", "Biggest lever", f"{SHORT[top['var']]} matters most for the cost of your gas.",
               f"Changing it, while keeping the digester stable and the gas within the grid rules, could make each MWh cheaper. "
               f"Open the curves to see in which direction, and by how much.")
else:
    ui.verdict("ok", "Already well tuned", f"{SHORT[top['var']]} matters most, and you are near its best value.",
               "Along each single setting, your design already sits close to the cheapest stable point. Try the two-setting map "
               "to look for combinations.")
ui.md('<div class="mt-answers">' + "".join(
    f'<div class="mt-answer"><div class="top"><span class="l">{ui.icon("sliders")}{SHORT[r.var]}</span>'
    f'{ui.pill("info", ["Biggest lever", "Second", "Third"][i])}</div></div>' for i, r in enumerate(LV.head(3).itertuples())) + "</div>")
st.write("")

# ------------------------------------------------------------------------------- sweep ---
with st.expander("One setting at a time *four curves*", icon=":material/show_chart:"):
    var = st.pills("Setting to move", list(SHORT), format_func=lambda k: SHORT[k], default="feed_t_d", key="sweep_var") or "feed_t_d"
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
                f.add_vrect(x0=xs[max(i - 1, 0)], x1=xs[j], fillcolor=SHADE, line_width=0, layer="below")
                i = j + 1
            else:
                i += 1
        f.add_vline(x=cur, line=dict(color=T.INK, width=1.4, dash="dot"))
        if var in core.UNC_BOUNDS:
            f.update_xaxes(type="log")
        f.update_layout(hovermode="x unified", showlegend=False, xaxis_title=xt, height=280, margin=dict(t=40, b=8, l=6, r=10))
        return f

    def line(col: str, title: str, color: str, ref: tuple | None = None, logy: bool = False):
        f = go.Figure(go.Scatter(x=xs, y=A[col], mode="lines", line=dict(color=color, width=2.6), name=title,
                                 hovertemplate="%{y:.3g}<extra></extra>"))
        f.add_scatter(x=[cur], y=[np.interp(cur, xs, A[col])], mode="markers", hoverinfo="skip",
                      marker=dict(color=T.INK, size=11, symbol="diamond", line=dict(color=T.SURFACE, width=2)))
        if ref:
            f.add_hline(y=ref[0], line=dict(color=ref[2], width=1.3, dash="dash"), annotation_text=ref[1],
                        annotation_position="top left", annotation_font=dict(size=12, color=ref[2]))
        f.update_layout(title=title)
        if logy:
            f.update_yaxes(type="log")
        return decorate(f)

    g1, g2 = st.columns(2, gap="medium")
    with g1, st.container(border=True):
        st.plotly_chart(line("LCOE_EUR_MWh", "Cost per MWh (€/MWh)", T.D1, (s.tariff, f"tariff {s.tariff:.0f}", T.INK)), width="stretch", config=T.PLOT_CFG)
    with g2, st.container(border=True):
        st.plotly_chart(line("bm_net_Nm3_h", "Gas to the grid (Nm³/h)", T.D2), width="stretch", config=T.PLOT_CFG)
    g3, g4 = st.columns(2, gap="medium")
    with g3, st.container(border=True):
        st.plotly_chart(line("VFA_gCOD_L", "Acids in the tank, VFA (g COD/L)", T.D3, (8, "stability limit 8", T.BAD)), width="stretch", config=T.PLOT_CFG)
    with g4, st.container(border=True):
        st.plotly_chart(line("BM_CO2_pct", "CO₂ in the gas (%, log scale)", T.D4, (2.5, "grid limit 2.5 %", T.BAD), logy=True),
                        width="stretch", config=T.PLOT_CFG)
    ui.md(f'<div class="mt-legend"><span><i style="background:{T.INK};width:10px;height:10px;transform:rotate(45deg)"></i>Your design</span>'
          f'<span><i style="background:{SHADE};height:12px;border:1px solid {T.CONTROL}"></i>Shaded: digester predicted unstable</span></div>')
    if best is not None:
        bx = A.loc[best, var] * k
        ui.note(f'Along this curve the cheapest stable point is <b>{A.loc[best, "LCOE_EUR_MWh"]:.1f} €/MWh</b> at '
                f'{SHORT[var]} = <b>{bx:.3g} {core.UNITS[var]}</b> (yours: {cur:.3g}). A single curve ignores the grid rules and the '
                f'output target; the map below shows both.')
    else:
        ui.callout("Every point of this curve is predicted unstable. Change the microbe settings or the feed blend on Your plant.", "warn")


# --------------------------------------------------------------------------------- map ---
@st.fragment
def response_map() -> None:
    with st.expander("Two settings at once *a map of 1,476 designs*", icon=":material/grid_on:"):
        keys = list(core.BOUNDS)
        m1, m2, m3 = st.columns(3)
        xa = m1.selectbox("Across", keys, index=keys.index("feed_t_d"), format_func=lambda k: SHORT[k], key="map_x")
        ya_opts = [k for k in keys if k != xa]
        ya = m2.selectbox("Up", ya_opts, index=ya_opts.index("hrt_d") if "hrt_d" in ya_opts else 0,
                          format_func=lambda k: SHORT[k], key="map_y")
        met = m3.selectbox("Colour shows", list(METRICS), format_func=lambda k: f"{METRICS[k][0]} ({METRICS[k][1]})", key="map_m")
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
        scale = [[i / (len(T.SEQ) - 1), c] for i, c in enumerate(T.SEQ)]
        better_high = met in ("bm_net_Nm3_h", "NPV_EUR", "p_stable")
        with st.container(border=True):
            f = go.Figure(go.Heatmap(x=fx * kx, y=fy * ky, z=Z, colorscale=scale,
                                     colorbar=dict(title=dict(text=METRICS[met][1], font=dict(size=12)), thickness=10, outlinewidth=0,
                                                   tickfont=dict(size=12)),
                                     hovertemplate=f"{SHORT[xa]} %{{x:.3g}} · {SHORT[ya]} %{{y:.3g}}<br>"
                                                   f"{METRICS[met][0]}: %{{z:.3g}} {METRICS[met][1]}<extra></extra>"))
            if met == "LCOE_EUR_MWh":
                f.add_contour(x=fx * kx, y=fy * ky, z=Z, showscale=False, hoverinfo="skip", showlegend=False,
                              contours=dict(start=s.tariff, end=s.tariff, size=1, coloring="none", showlabels=True,
                                            labelfont=dict(size=12, color=T.INK)),
                              line=dict(color=T.INK, width=1.8, dash="dash"))
            bm = M.bm_net_Nm3_h.to_numpy().reshape(FX.shape)
            f.add_contour(x=fx * kx, y=fy * ky, z=bm, showscale=False, hoverinfo="skip", showlegend=False,
                          contours=dict(start=150, end=300, size=50, coloring="none", showlabels=True, labelfont=dict(size=12, color=T.D2)),
                          line=dict(color=T.D2, width=1.2))
            f.add_scatter(x=[X[xa] * kx], y=[X[ya] * ky], mode="markers", name="your design", hoverinfo="skip",
                          marker=dict(size=14, color=T.INK, symbol="diamond", line=dict(color=T.SUNKEN, width=2)))
            f.update_layout(height=480, plot_bgcolor=T.SUNKEN, showlegend=False, margin=dict(t=12, b=8, l=6, r=6),
                            xaxis_title=f"{core.LABELS[xa]} ({core.UNITS[xa]})", yaxis_title=f"{core.LABELS[ya]} ({core.UNITS[ya]})")
            st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
            ui.md(f'<div class="mt-legend"><span><i style="background:{T.INK};width:10px;height:10px;transform:rotate(45deg)"></i>Your design</span>'
                  f'<span><i style="background:{T.D2}"></i>Output lines 150 / 200 / 250 / 300 Nm³/h</span>'
                  + (f'<span><i style="background:{T.INK}"></i>Dashed: cost equals the tariff</span>' if met == "LCOE_EUR_MWh" else "")
                  + f'<span><i style="background:{T.SUNKEN};height:12px;border:1px solid {T.CONTROL}"></i>Black: unstable or off-spec</span>'
                  f'<span>Brighter = higher{" (better)" if better_high else " (worse)" if met != "p_stable" else ""}</span></div>')


response_map()
