"""Designs - designs checked by the full simulation, and the user's saved designs (load, compare, delete, export)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core
import state as S
import theme as T
import tokens as K
import ui

RES, s = S.res(), st.session_state

ui.page_head("bookmark", "Designs", "Start from a proven design, or keep your own.",
             "Checked designs were found by optimisation and confirmed by the full simulation. Your own designs are the ones you save.")

ref = S.matches_reference()
nsc = len(s.scenarios)
ui.verdict("info", "Where you are",
           f"You are working from “{s.preset}”" + ("." if ref else ", with your own changes."),
           (f"You have saved {nsc} design{'s' if nsc != 1 else ''} in this session." if nsc else "You have not saved a design yet.")
           + " Save the current one to compare it with others.")
with st.container(horizontal=True, gap="small"):
    if st.button("Save the current design", type="primary", icon=":material/bookmark_add:"):
        ui.save_dialog()
st.write("")

tab_v, tab_s = st.tabs(["Checked designs", f"My designs ({nsc})"])

# ------------------------------------------------------------------------- checked ---
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
    ui.md('<p class="mt-sec-sub" style="margin-top:12px">Pick a row, then load it into Your plant. Values are from the full simulation.</p>')
    ev = st.dataframe(df, hide_index=True, width="stretch", height=36 * (len(df) + 1) + 4, on_select="rerun",
                      selection_mode="single-row", key="vtab",
                      column_config={
                          "Design": st.column_config.TextColumn(width="medium", pinned=True),
                          "Output (Nm³/h)": st.column_config.NumberColumn(format="%.1f"),
                          "LCOE (€/MWh)": st.column_config.ProgressColumn(format="%.1f", min_value=130, max_value=165,
                                                                         help="Cost per MWh: building and running costs per MWh injected"),
                          "NPV (M€)": st.column_config.NumberColumn(format="%+.2f", help="Value over 15 years; above zero = pays"),
                          "VFA (g/L)": st.column_config.NumberColumn(format="%.1f", help="Acids in the tank; design margin 6 g COD/L"),
                          "CO₂ (%)": st.column_config.NumberColumn(format="%.2f"),
                          "Maize (%)": st.column_config.NumberColumn(format="%.1f"),
                          "CIVE (%)": st.column_config.NumberColumn(format="%.1f"),
                          "Feed (t/d)": st.column_config.NumberColumn(format="%.0f"),
                          "HRT (d)": st.column_config.NumberColumn(format="%.0f", help="Retention time"),
                          "Water (m³/kNm³)": st.column_config.NumberColumn(format="%.0f"),
                          "Flash (bar)": st.column_config.NumberColumn(format="%.2f")})
    sel = ev.selection.rows

    def _load_verified(name: str) -> None:            # callback: runs before the settings widgets are drawn
        S.apply_preset(name)
        s.update({**S.KIN_DEFAULTS, **S.ECON_DEFAULTS})
        s["_toast"] = f"Loaded {name}"

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        if st.button("Load into Your plant", type="primary", disabled=not sel, icon=":material/upload:", key="load_checked",
                     on_click=_load_verified, args=(df.iloc[sel[0]]["Design"],) if sel else ("",)):
            st.switch_page("views/cockpit.py")
        st.caption("Loading also resets the microbe and market settings to the defaults used in the full simulation."
                   if sel else "Select a row to enable loading.")

    with st.expander("What the checked designs show *two charts and key findings*", icon=":material/insights:"):
        c1, c2 = st.columns(2, gap="medium")
        opt = df[df.Design.str.startswith("Verified")]
        with c1, st.container(border=True):
            f = go.Figure()
            f.add_hrect(y0=core.CRE["q1"], y1=core.CRE["q3"], fillcolor=K.rgba("text-primary", 0.05), line_width=0, layer="below")
            f.add_hline(y=core.CRE["median"], line=dict(color=T.D3, width=1.2, dash="dot"), annotation_text="CRE median 129.6",
                        annotation_position="bottom right", annotation_font=dict(size=12, color=T.D3))
            f.add_hline(y=152.8, line=dict(color=T.INK, width=1.4, dash="dash"), annotation_text="average tariff 152.8",
                        annotation_position="top right", annotation_font=dict(size=12))
            f.add_scatter(x=opt["Output (Nm³/h)"], y=opt["LCOE (€/MWh)"], mode="lines+markers+text",
                          text=[f"{v:.0f}" for v in opt["LCOE (€/MWh)"]], textposition="top center",
                          textfont=dict(size=12, color=T.INK), line=dict(color=T.D1, width=2.6),
                          marker=dict(size=10, color=T.D1, line=dict(color=T.SURFACE, width=2)),
                          customdata=opt["NPV (M€)"], hovertemplate="%{x:.0f} Nm³/h<br>LCOE %{y:.1f} €/MWh<br>NPV %{customdata:+.2f} M€<extra></extra>")
            f.update_layout(title="Bigger is cheaper · break-even ≈ 180 Nm³/h", height=340, showlegend=False,
                            xaxis_title="Gas to the grid (Nm³/h)", yaxis_title="Cost per MWh (€/MWh)", yaxis_range=[105, 165])
            st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
        with c2, st.container(border=True):
            items = [("Naive scale-up", nv["simulation"], T.DMUTED), ("Optimum", RES["unc"]["comparison_200"]["optimum"]["simulation"], T.D2),
                     ("Robust (K_I ≥ 0.0016)", rb["final"]["simulation"], T.D1)]
            f = go.Figure(go.Bar(x=[i[0] for i in items], y=[i[1]["LCOE_EUR_MWh"] for i in items], marker_color=[i[2] for i in items],
                                 text=[f"{i[1]['LCOE_EUR_MWh']:.1f}" for i in items], textposition="outside", cliponaxis=False,
                                 textfont=dict(size=12, color=T.INK),
                                 customdata=[[i[1]["VFA_gCOD_L"], i[1]["NPV_EUR"] / 1e6] for i in items],
                                 hovertemplate="<b>%{x}</b><br>LCOE %{y:.1f} €/MWh<br>VFA %{customdata[0]:.1f} g/L"
                                               "<br>NPV %{customdata[1]:+.2f} M€<extra></extra>"))
            f.update_layout(title="200 Nm³/h: robustness costs +8.4 €/MWh", height=340, yaxis_title="Cost per MWh (€/MWh)",
                            yaxis_range=[0, 180], showlegend=False)
            st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
        st.markdown(
            "- **Size beats fine-tuning.** The cost falls from 157 to 140 €/MWh between 150 and 300 Nm³/h; at the average 2023 "
            "tariff the plant breaks even at about 180 Nm³/h.\n"
            "- **The optimum is flat.** Simply scaling up the base design costs 149.6 €/MWh against 149.9 for the optimum; the "
            "optimum's value is that it keeps the acids within the 6 g/L safety margin (6.0 vs 6.7).\n"
            "- **Optimiser's curse.** The search lands where the ML is 2–5 % optimistic, so every design was re-simulated until "
            "the full model confirmed it.\n"
            "- **Price of robustness.** A design that survives strong ammonia poisoning (K_I,NH3 ≥ 0.0016 M) costs +8.4 €/MWh; "
            "at K_I,NH3 = 0.0012 no stable 200 Nm³/h design exists in this design space.\n"
            "- **Caveat.** The 300 Nm³/h design sits at the feed-rate limit and its simulated acids (6.4 g/L) slightly exceed the margin.")

# ------------------------------------------------------------------------- mine ---
with tab_s:
    if not s.scenarios:
        ui.empty("No saved designs yet", "Set up a design on Your plant and press <b>Save design</b>. Saved designs appear here "
                 "to compare side by side, reload and export.", "bookmark")
    else:
        df = S.scenario_table()
        ui.md('<p class="mt-sec-sub" style="margin-top:12px">Select one row to load or delete it, or several rows to compare them.</p>')
        ev = st.dataframe(df, hide_index=True, width="stretch", on_select="rerun", selection_mode="multi-row", key="stab",
                          column_config={
                              "Scenario": st.column_config.TextColumn("Design", pinned=True),
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
        one = len(sel) == 1

        def _load_scn(name: str) -> None:
            S.load_scenario(name)
            s["_toast"] = f"Loaded {name}"

        with st.container(horizontal=True, gap="small"):
            if st.button("Load into Your plant", type="primary", disabled=not one, icon=":material/upload:", key="load_mine",
                         on_click=_load_scn, args=(df.iloc[sel[0]]["Scenario"],) if one else ("",)):
                st.switch_page("views/cockpit.py")
            if st.button("Delete", disabled=not sel, icon=":material/delete:", key="delete_mine"):
                for i in sel:
                    s.scenarios.pop(df.iloc[i]["Scenario"], None)
                st.toast(f"Deleted {len(sel)} design(s)", icon=":material/delete:")
                st.rerun()
            st.download_button("Export table (CSV)", df.to_csv(index=False).encode(), file_name="methatwin_scenarios.csv",
                               mime="text/csv", icon=":material/download:")
        cmp_ = df.iloc[sel] if len(sel) >= 2 else df
        with st.expander("Side by side *cost and value*" + (" · selected" if len(sel) >= 2 else " · all"), icon=":material/compare:"):
            g1, g2 = st.columns(2, gap="medium")
            for col, metric, color, ttl in ((g1, "LCOE (€/MWh)", T.D1, "Cost per MWh (€/MWh)"), (g2, "NPV (M€)", T.D2, "Value over 15 years (M€)")):
                with col, st.container(border=True):
                    f = go.Figure(go.Bar(x=cmp_["Scenario"], y=cmp_[metric], marker_color=color,
                                         text=[f"{v:.1f}" if "LCOE" in metric else f"{v:+.2f}" for v in cmp_[metric]],
                                         textposition="outside", cliponaxis=False, textfont=dict(size=12, color=T.INK),
                                         hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>"))
                    if "LCOE" in metric:
                        f.add_hline(y=152.8, line=dict(color=T.INK, width=1.2, dash="dash"), annotation_text="average tariff",
                                    annotation_font=dict(size=12))
                    f.update_layout(title=ttl, height=300, showlegend=False)
                    st.plotly_chart(f, width="stretch", config=T.PLOT_CFG)
