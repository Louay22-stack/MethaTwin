"""
methatwin.plant - Coupled plant model: feed blend -> ADM1 digester -> DWSIM water scrubbing.

One call = one steady-state plant simulation. Inputs are design/operating variables and two
uncertain kinetic parameters; outputs are the physical KPIs needed downstream (surrogate,
optimisation, techno-economics).

Inputs (dict `x`)
    maize_share, cive_share  fresh-mass shares of the blend (slurry = remainder)
    feed_t_d                 total fresh feed (t/d, density 1 t/m3)
    hrt_d                    hydraulic retention time of the single CSTR (d)
    water_per_kNm3           circulating scrubber water per 1000 Nm3/h of dry raw biogas (m3/h)
    p_flash_bar              intermediate flash pressure of the scrubber (bar)
    k_dis                    ADM1 disintegration constant (1/d)      - uncertain
    K_I_nh3                  ADM1 free-ammonia inhibition constant    - uncertain
Fixed: 39 degC, calibrated kinetics (Bulkowska et al. 2015) otherwise, 10 absorber stages,
air 8 Nm3/m3 water, other scrubber settings as in UpgradingDesign defaults.
"""
from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .adm1 import ADM1Params, IDX, balances, influent_vector, steady_state
from .upgrading import HPWSFlowsheet, UpgradingDesign

ROOT = Path(__file__).resolve().parents[2]
FEEDS = pd.read_csv(ROOT / "03_data" / "processed" / "feedstock_adm1.csv").set_index("feedstock")
VS_PER_T = FEEDS["VS_kg_per_t_FM"].to_dict()
CALIBRATED = {"K_S_c4": 0.23, "K_I_h2_c4": 1e-8, "k_m_pro": 8.5, "K_S_pro": 0.15,
              "K_I_h2_pro": 2.4e-8, "k_m_ac": 7.64, "K_S_ac": 0.6}
T_OP_C = 39.0
HOURS = 8400.0
MASS_CLOSURE_GATE_PCT = 0.1   # data-quality gate on the scrubber mass balance


def digester(x: dict) -> dict:
    """ADM1 steady state for the blend and operating point in x."""
    shares = {"maize_silage": x["maize_share"], "cive_silage": x["cive_share"],
              "cattle_slurry": 1.0 - x["maize_share"] - x["cive_share"]}
    col = {"X_pr": "X_pr_kgCOD_m3", "X_li": "X_li_kgCOD_m3", "X_ch": "X_ch_kgCOD_m3",
           "X_I": "X_I_kgCOD_m3", "S_IN": "S_IN_kmolN_m3"}
    b = {k: sum(shares[f] * FEEDS.loc[f, c] for f in shares) for k, c in col.items()}
    cod = b["X_pr"] + b["X_li"] + b["X_ch"] + b["X_I"]
    p = ADM1Params()
    for k, v in CALIBRATED.items():
        setattr(p, k, v)
    p.k_dis, p.K_I_nh3 = x["k_dis"], x["K_I_nh3"]
    p.T_op = 273.15 + T_OP_C
    q_in = x["feed_t_d"]
    p.V_liq = q_in * x["hrt_d"]
    p.V_gas = 0.10 * p.V_liq
    p.f_ch_xc, p.f_pr_xc = b["X_ch"] / cod, b["X_pr"] / cod
    p.f_li_xc, p.f_xI_xc, p.f_sI_xc = b["X_li"] / cod, b["X_I"] / cod, 0.0
    p.N_xc = p.f_pr_xc * p.N_aa + p.f_xI_xc * p.N_I
    p.C_xc = p.f_ch_xc * p.C_ch + p.f_pr_xc * p.C_pr + p.f_li_xc * p.C_li + p.f_xI_xc * p.C_xI
    vs_t_d = q_in * sum(shares[f] * VS_PER_T[f] for f in shares) / 1000.0
    p.k_p = max(vs_t_d * 1000 * 0.35 / 0.05, 1e3)   # ~0.05 bar overpressure at a typical yield
    y_in = influent_vector(X_xc=cod, S_IN=b["S_IN"], S_IC=0.0323, S_cat=0.08, S_an=0.02)
    res = steady_state(y_in, q_in, p)
    o = res.outputs()
    bal = balances(res)
    ch4_Nm3_h = o["CH4_Nm3_d"] / 24
    return {
        "V_liq_m3": p.V_liq, "OLR_kgVS_m3_d": vs_t_d * 1000 / p.V_liq, "VS_t_d": vs_t_d,
        "CH4_Nm3_h": ch4_Nm3_h, "biogas_dry_Nm3_h": (o["CH4_Nm3_d"] + o["CO2_Nm3_d"]) / 24,
        "y_CH4_dry": o["CH4_frac_dry"], "pH": o["pH"], "VFA_gCOD_L": o["VFA_total_kgCOD_m3"],
        "free_NH3_mgN_L": o["S_nh3_kmolN_m3"] * 14007, "TAN_gN_L": res.y[IDX["S_IN"]] * 14.007,
        "CH4_yield_Nm3_tVS": ch4_Nm3_h * 24 / vs_t_d if vs_t_d > 0 else 0.0,
        "residual_Xc_kgCOD_m3": res.y[IDX["X_xc"]],
        "adm1_COD_closure_pct": bal["COD_closure_pct"], "adm1_max_abs_rhs": res.info["max_abs_rhs"],
    }


def digester_stable(d: dict) -> bool:
    """Operational stability screen (common practice thresholds; see LOG.md step 6)."""
    return d["pH"] >= 6.8 and d["VFA_gCOD_L"] <= 8.0 and d["CH4_Nm3_h"] > 1.0


def upgrading(dw, d: dict, x: dict) -> dict:
    des = replace(UpgradingDesign(), raw_dry_Nm3_h=d["biogas_dry_Nm3_h"], y_ch4_dry=d["y_CH4_dry"],
                  water_m3_h=x["water_per_kNm3"] * d["biogas_dry_Nm3_h"] / 1000.0,
                  P_flash_bar=x["p_flash_bar"], n_abs_stages=10)
    r = HPWSFlowsheet(dw, des).solve()
    k = r.kpi
    return {"upg_converged": r.converged, "upg_iterations": r.iterations,
            "water_m3_h": des.water_m3_h, "biomethane_Nm3_h": k["biomethane_Nm3_h_dry"],
            "BM_CH4_pct": k["CH4_pct_dry"], "BM_CO2_pct": k["CO2_pct_dry"], "BM_O2_ppm": k["O2_ppm_dry"],
            "BM_HHV_kWh_Nm3": k["HHV_kWh_Nm3"], "BM_Wobbe": k["Wobbe_kWh_Nm3"],
            "CH4_slip_pct": k["CH4_slip_pct"], "P_el_upg_kW": k["P_el_total_kW"],
            "spec_el_kWh_Nm3_raw": k["specific_el_kWh_per_Nm3_raw"],
            "CO2_stream_Nm3_h": k["CO2_stream_Nm3_h"], "CO2_stream_t_yr": k["CO2_stream_t_per_yr_at_8400h"],
            "upg_mass_closure_pct": r.balances["mass_closure_pct"],
            "upg_in_validity_window": k["water_units_in_validity_window"]}


def simulate_plant(x: dict, dw=None) -> dict:
    """Full coupled simulation. dw=None runs the digester only."""
    t0 = time.perf_counter()
    out = {**x, "status": "ok"}
    try:
        d = digester(x)
    except Exception as exc:
        return {**out, "status": f"adm1_error: {str(exc)[:120]}", "time_s": time.perf_counter() - t0}
    out.update(d)
    out["digester_stable"] = digester_stable(d)
    if not out["digester_stable"]:
        out["status"] = "digester_unstable"
    elif dw is not None:
        try:
            out.update(upgrading(dw, d, x))
            if not out["upg_converged"]:
                out["status"] = "upgrading_not_converged"
            elif abs(out["upg_mass_closure_pct"]) > MASS_CLOSURE_GATE_PCT:
                # DWSIM's column solver converges on total (water-dominated) flow; at low flash
                # pressure + high water it can leave a gas-phase imbalance of several % (step 6).
                out["status"] = "upgrading_balance_not_closed"
        except Exception as exc:
            out["status"] = f"upgrading_error: {str(exc)[:120]}"
    out["time_s"] = time.perf_counter() - t0
    return out
