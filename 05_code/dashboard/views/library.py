"""Designs & scenarios - verified designs from the full simulation, and the user's saved scenarios."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
import state as S
import theme as T
import ui

RES, s = S.res(), st.session_state

ui.page_head("Designs & scenarios", "Verified designs and your <em>scenarios</em>",
             "Reference designs found by optimisation and confirmed by the full ADM1 + DWSIM simulation, plus the "
             "scenarios you save from the console. Select rows to load or compare them.",
             f'Verified designs <b>{sum(1 for k in RES["opt"] if RES["opt"][k]["final"])}</b><br/>'
             f'Saved scenarios <b>{len(s.scenarios)}</b>')

tab_v, tab_s = st.tabs(["Verified designs", f"My scenarios ({len(s.scenarios)})"])

# ------------------------------------------------------------ verified ---
with tab_v:
    rows = []
    for k in ("150", "200", "250", "300"):
        f = RES["opt"][k]["final"]
        if f:
            d, v = f["design"], f["simulation"]
            rows.append({"Design": f"Verified optimum · {k} Nm³/h", "Output (Nm³/h)": v["bm_net_Nm3_h"],
                         "LCOE (€/MWh)": v["LCOE_EUR_MWh"], "NPV (M€)": v["NPV_EUR"] / 1e6, "VFA (g/L)": v["VFA_gCOD_L"],
                         "CO₂ (%)": v["BM_CO2_pct"], "Maize (%)": 100 * d["maize_share"], "CIVE (%)": 100 * d["cive_share"],
                         "Feed (t/d)": d["feed_t_d"], "HRT (d)": d["hrt_d"], "Water (m³/kNm³)": d["water_per_kNm3"],
                         "Flash (bar)": d["p_flash_bar"]})
    nv = RES["unc"]["comparison_200"]["naive_scaled_base"]
    rb = RES["rob"]
    for name, d, v in (("Naive scale-up · 200 Nm³/h", nv["design"], nv["simulation"]),
                       ("Robust design · 200 Nm³/h", rb["final"]["design"], rb["robust_design_at_nominal_kinetics"])):
        rows.append({"Design": name, "Output (Nm³/h)": v["bm_net_Nm3_h"], "LCOE (€/MWh)": v["LCOE_EUR_MWh"],
                     "NPV (M€)": v["NPV_EUR"] / 1e6, "VFA (g/L)": v["VFA_gCOD_L"], "CO₂ (%)": v["BM_CO2_pct"],
                     "Maize (%)": 100 * d["maize_share"], "CIVE (%)": 100 * d["cive_share"], "Feed (t/d)": d["feed_t_d"],
                     "HRT (d)": d["hrt_d"], "Water (m³/kNm³)": d["water_per_kNm3"], "Flash (bar)": d["p_flash_bar"]})
    df = pd.DataFrame(rows)
    ui.section("01", "Design register", "full-simulation results · click a row, then load it")
    ev = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row", key="vtab",
                      column_config={
                          "Design": st.column_config.TextColumn(width="medium", pinned=True),
                          "Output (Nm³/h)": st.column_config.NumberColumn(format="%.1f"),
                          "LCOE (€/MWh)": st.column_config.ProgressColumn(format="%.1f", min_value=130, max_value=165),
                          "NPV (M€)": st.column_config.NumberColumn(format="%+.2f"),
                          "VFA (g/L)": st.column_config.NumberColumn(format="%.1f", help="Design margin 6 g COD/L"),
                          "CO₂ (%)": st.column_config.NumberColumn(format="%.2f"),
                          "Maize (%)": st.column_config.NumberColumn(format="%.1f"),
                          "CIVE (%)": st.column_config.NumberColumn(format="%.1f"),
                          "Feed (t/d)": st.column_config.NumberColumn(format="%.0f"),
                          "HRT (d)": st.column_config.NumberColumn(format="%.0f"),
                          "Water (m³/kNm³)": st.column_config.NumberColumn(format="%.0f"),
                          "Flash (bar)": st.column_config.NumberColumn(format="%.2f")})
    sel = ev.selection.rows
    b1, b2 = st.columns([1, 3], vertical_alignment="center")
    def _load_verified(name: str) -> None:            # callback: runs before the console widgets are drawn
        S.apply_preset(name)
        s.update({**S.KIN_DEFAULTS, **S.ECON_DEFAULTS})
        s["_toast"] = f"Loaded {name}"

    if b1.button("Load selected into console", type="primary", disabled=not sel, width="stretch",
                 on_click=_load_verified, args=(df.iloc[sel[0]]["Design"],) if sel else ("",)):
        st.switch_page("views/cockpit.py")
    b2.caption("Loading resets kinetics and market to the defaults used in the full simulation, so the cockpit can show "
               "the simulated values next to the surrogate prediction." if sel else "Select a row in the table to enable loading.")

    ui.section("02", "What the register shows", "")
    c1, c2 = st.columns(2, gap="medium")
    opt = df[df.Design.str.startswith("Verified")]
    with c1, st.container(border=True):
        f = go.Figure()
        f.add_hrect(y0=core.CRE["q1"], y1=core.CRE["q3"], fillcolor="rgba(94,242,200,0.08)", line_width=0, layer="below")
        f.add_hline(y=core.CRE["median"], line=dict(color=T.MINT, width=1.1, dash="dot"), annotation_text="CRE median 129.6",
                    annotation_position="bottom right", annotation_font=dict(size=10, family="IBM Plex Mono"))
        f.add_hline(y=152.8, line=dict(color=T.INK, width=1.4, dash="dash"), annotation_text="average tariff 152.8",
                    annotation_position="top right", annotation_font=dict(size=10, family="IBM Plex Mono"))
        f.add_scatter(x=opt["Output (Nm³/h)"], y=opt["LCOE (€/MWh)"], mode="lines+markers+text",
                      text=[f"{v:.0f}" for v in opt["LCOE (€/MWh)"]], textposition="top center",
                      textfont=dict(family="IBM Plex Mono", size=11), line=dict(color=T.CORAL, width=2.4),
                      marker=dict(size=10, color=T.CORAL, line=dict(color=T.SURFACE, width=2)),
                      customdata=opt["NPV (M€)"], hovertemplate="%{x:.0f} Nm³/h<br>LCOE %{y:.1f} €/MWh<br>NPV %{customdata:+.2f} M€<extra></extra>")
        f.update_layout(title="Economies of scale · break-even ≈ 180 Nm³/h", height=340, showlegend=False,
                        xaxis_title="Biomethane injected (Nm³/h)", yaxis_title="LCOE (€/MWh)", yaxis_range=[105, 165])
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
    with c2, st.container(border=True):
        items = [("Naive scale-up", nv["simulation"], T.BLUE_SOFT), ("Nominal optimum", RES["unc"]["comparison_200"]["optimum"]["simulation"], T.BLUE),
                 ("Robust (K_I ≥ 0.0016)", rb["final"]["simulation"], T.TEAL)]
        f = go.Figure(go.Bar(x=[i[0] for i in items], y=[i[1]["LCOE_EUR_MWh"] for i in items], marker_color=[i[2] for i in items],
                             text=[f"{i[1]['LCOE_EUR_MWh']:.1f}" for i in items], textposition="outside", cliponaxis=False,
                             textfont=dict(family="IBM Plex Mono", size=11),
                             customdata=[[i[1]["VFA_gCOD_L"], i[1]["NPV_EUR"] / 1e6] for i in items],
                             hovertemplate="<b>%{x}</b><br>LCOE %{y:.1f} €/MWh<br>VFA %{customdata[0]:.1f} g/L"
                                           "<br>NPV %{customdata[1]:+.2f} M€<extra></extra>"))
        f.update_layout(title="200 Nm³/h: flat optimum, robustness +8.4 €/MWh", height=340, yaxis_title="LCOE (€/MWh)",
                        yaxis_range=[0, 180], showlegend=False)
        st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
    with st.expander("Key findings from the optimisation study", expanded=False):
        st.markdown(
            "- **Size beats fine-tuning.** LCOE falls from 157 to 140 €/MWh between 150 and 300 Nm³/h; break-even at the "
            "average 2023 tariff is ≈ 180 Nm³/h.\n"
            "- **The optimum is flat.** A naive scale-up of the base design costs 149.6 €/MWh against 149.9 for the optimum; the "
            "optimum's value is that it keeps VFA within the 6 g/L design margin (6.0 vs 6.7).\n"
            "- **Optimiser's curse.** The search lands where the ML is 2–5 % optimistic, so a verify-and-correct loop "
            "re-simulated every design until the full model confirmed it.\n"
            "- **Price of robustness.** A design that survives strong ammonia inhibition (K_I,NH3 ≥ 0.0016 M) costs +8.4 €/MWh; "
            "at K_I,NH3 = 0.0012 no stable 200 Nm³/h design exists in this design space.\n"
            "- **Caveat.** The 300 Nm³/h design sits at the feed-rate bound and its simulated VFA (6.4 g/L) slightly exceeds the margin.")

# ----------------------------------------------------------- scenarios ---
with tab_s:
    if not s.scenarios:
        ui.empty("No saved scenarios yet",
                 "Set up a design in the console and press <b>Save scenario</b>. Saved scenarios appear here for side-by-side "
                 "comparison, reloading and CSV export.")
    else:
        df = S.scenario_table()
        ui.section("01", "Scenario comparison", "select one row to load or delete · several rows to compare")
        ev = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun", selection_mode="multi-row", key="stab",
                          column_config={
                              "Scenario": st.column_config.TextColumn(pinned=True),
                              "Biomethane (Nm³/h)": st.column_config.NumberColumn(format="%.1f"),
                              "LCOE (€/MWh)": st.column_config.NumberColumn(format="%.1f"),
                              "NPV (M€)": st.column_config.NumberColumn(format="%+.2f"),
                              "P(stable)": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
                              "CO₂ (%)": st.column_config.NumberColumn(format="%.2f"),
                              "VFA (g/L)": st.column_config.NumberColumn(format="%.1f"),
                              "Feed (t/d)": st.column_config.NumberColumn(format="%.0f"),
                              "HRT (d)": st.column_config.NumberColumn(format="%.0f"),
                              "Maize (%)": st.column_config.NumberColumn(format="%.1f"),
                              "CIVE (%)": st.column_config.NumberColumn(format="%.1f"),
                              "Water (m³/kNm³)": st.column_config.NumberColumn(format="%.0f"),
                              "Flash (bar)": st.column_config.NumberColumn(format="%.2f"),
                              "k_dis": st.column_config.NumberColumn(format="%.3f"),
                              "K_I,NH3": st.column_config.NumberColumn(format="%.4f"),
                              "Tariff (€/MWh)": st.column_config.NumberColumn(format="%.1f"),
                              "Slurry (€/t)": st.column_config.NumberColumn(format="%.1f")})
        sel = ev.selection.rows
        a1, a2, a3, _ = st.columns([1, 1, 1.3, 1.7])
        one = len(sel) == 1
        def _load_scn(name: str) -> None:
            S.load_scenario(name)
            s["_toast"] = f"Loaded scenario {name}"

        if a1.button("Load into console", type="primary", disabled=not one, width="stretch",
                     on_click=_load_scn, args=(df.iloc[sel[0]]["Scenario"],) if one else ("",)):
            st.switch_page("views/cockpit.py")
        if a2.button("Delete", disabled=not sel, width="stretch"):
            for i in sel:
                s.scenarios.pop(df.iloc[i]["Scenario"], None)
            st.toast(f"Deleted {len(sel)} scenario(s)", icon="🗑️")
            st.rerun()
        a3.download_button("Export table (CSV)", df.to_csv(index=False).encode(), file_name="methatwin_scenarios.csv",
                           mime="text/csv", width="stretch")
        cmp_ = df.iloc[sel] if len(sel) >= 2 else df
        ui.section("02", "Side-by-side", "selected scenarios" if len(sel) >= 2 else "all scenarios · select rows to narrow")
        g1, g2 = st.columns(2, gap="medium")
        for col, metric, color, ttl in ((g1, "LCOE (€/MWh)", T.CORAL, "Levelised cost (€/MWh)"),
                                        (g2, "NPV (M€)", T.BLUE, "NPV, 15 years (M€)")):
            with col, st.container(border=True):
                f = go.Figure(go.Bar(x=cmp_["Scenario"], y=cmp_[metric], marker_color=color,
                                     text=[f"{v:.1f}" if "LCOE" in metric else f"{v:+.2f}" for v in cmp_[metric]],
                                     textposition="outside", cliponaxis=False, textfont=dict(family="IBM Plex Mono", size=11),
                                     hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>"))
                if "LCOE" in metric:
                    f.add_hline(y=152.8, line=dict(color=T.INK, width=1.2, dash="dash"), annotation_text="avg tariff",
                                annotation_font=dict(size=10, family="IBM Plex Mono"))
                f.update_layout(title=ttl, height=300, showlegend=False)
                st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
