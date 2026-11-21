"""
Phase 3, step 4b - ADM1 simulation of the MethaTwin base-case digester.

Feed      : base-case blend from step 3 (60 % cattle slurry, 25 % CIVE silage, 15 % maize
            silage by fresh mass; 32,281 t/yr), fed as ADM1 composite X_xc whose
            disintegration fractions are the blend's BMP-based COD fractions.
Kinetics  : BSM2 set (Rosen & Jeppsson 2006) with the values calibrated for maize silage +
            cattle manure by Bulkowska et al. (2015, Arch. Environ. Prot. 41(3), Part II,
            Tables 2, 4, 5): k_dis, k_m/K_S of c4, pro, ac and H2 inhibition constants.
            Exception: K_I,nh3 kept at the BSM2 value (see PARAM_NOTES).
Reactor   : single mesophilic CSTR, 39 degC (as in the calibration), HRT 60 d.

Writes 04_models_and_simulations/step4_adm1/base_case_*.json and prints the results.
Run from the project root:  python 05_code/step4b_adm1_base_case.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from methatwin.adm1 import ADM1Params, IDX, balances, influent_vector, steady_state  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "03_data" / "processed"
OUT = ROOT / "04_models_and_simulations" / "step4_adm1"

HRT_D = 60.0
T_OP_C = 39.0
Y_CH4_BIOMETHANE = 0.97
HOURS = 8400.0

# Bulkowska et al. 2015 (Part II) calibrated values for maize silage + cattle manure
CALIBRATED = {"k_dis": 0.1, "K_S_c4": 0.23, "K_I_h2_c4": 1e-8, "k_m_pro": 8.5, "K_S_pro": 0.15,
              "K_I_h2_pro": 2.4e-8, "k_m_ac": 7.64, "K_S_ac": 0.6}
PARAM_NOTES = {
    "source": "Bulkowska et al. (2015) Part II, Tables 2, 4, 5 (39 degC, HRT 45 d, OLR 2.1 kg VS/m3/d)",
    "K_I_nh3": ("Kept at BSM2 0.0018 kmol N/m3. The calibrated 0.00026 was identified on a feed with "
                "only 0.019 kmol NH4-N/m3 and would wash out acetoclastic methanogens at slurry-blend "
                "ammonia levels; literature range 0.00026-0.0084 (Bulkowska Tab. 5) -> sensitivity."),
    "ions": ("S_cat 0.08, S_an 0.02 kmol/m3 and S_IC 0.0323 kmol C/m3 = measured maize+manure feed "
             "of Klimiuk et al. 2015 Part I Table 5 (proxy; key sensitivity)."),
    "k_p": "Scaled so the headspace overpressure stays ~0.05 bar, as in BSM2.",
}


def build_case(hrt: float = HRT_D, T_c: float = T_OP_C, overrides: dict | None = None):
    feeds = pd.read_csv(PROC / "feedstock_adm1.csv").set_index("feedstock")
    plan = json.loads((PROC / "base_case_feed_plan.json").read_text(encoding="utf-8"))
    shares = plan["fm_shares"]

    # Blend influent per m3 (density 1 t/m3): COD of each class and NH4-N
    col = {"X_pr": "X_pr_kgCOD_m3", "X_li": "X_li_kgCOD_m3", "X_ch": "X_ch_kgCOD_m3",
           "X_I": "X_I_kgCOD_m3", "S_IN": "S_IN_kmolN_m3"}
    blend = {k: sum(shares[f] * feeds.loc[f, c] for f in shares) for k, c in col.items()}
    cod = blend["X_pr"] + blend["X_li"] + blend["X_ch"] + blend["X_I"]
    f = {k: blend[k] / cod for k in ["X_pr", "X_li", "X_ch", "X_I"]}

    p = ADM1Params()
    for k, v in CALIBRATED.items():
        setattr(p, k, v)
    p.T_op = 273.15 + T_c
    q_in = plan["feed_t_per_yr"] / 365.0                      # m3/d (1 t/m3)
    p.V_liq = q_in * hrt
    p.V_gas = 0.10 * p.V_liq
    # Disintegration fractions = blend fractions; no soluble inerts in this fractionation
    p.f_ch_xc, p.f_pr_xc, p.f_li_xc, p.f_xI_xc, p.f_sI_xc = f["X_ch"], f["X_pr"], f["X_li"], f["X_I"], 0.0
    # N and C content of the composite chosen so that disintegration conserves N and C
    p.N_xc = p.f_pr_xc * p.N_aa + p.f_xI_xc * p.N_I
    p.C_xc = p.f_ch_xc * p.C_ch + p.f_pr_xc * p.C_pr + p.f_li_xc * p.C_li + p.f_xI_xc * p.C_xI
    # Gas outlet constant: ~0.05 bar overpressure at the expected gas flow (BSM2-like)
    expected_gas_m3_d = plan["CH4_needed_Nm3_yr"] / HOURS * 24 / 0.55
    p.k_p = expected_gas_m3_d / 0.05
    for k, v in (overrides or {}).items():
        setattr(p, k, v)

    y_in = influent_vector(X_xc=cod, S_IN=blend["S_IN"], S_IC=0.0323, S_cat=0.08, S_an=0.02)
    return p, y_in, q_in, plan, cod


def summarize(res, plan, cod_in) -> dict:
    o = res.outputs()
    y, p, q_in = res.y, res.p, res.q_in
    vs_in_t_d = q_in * plan["blend_VS_kg_per_t"] / 1000.0
    ch4_Nm3_h = o["CH4_Nm3_d"] / 24
    tan = y[IDX["S_IN"]]
    return {
        "HRT_d": p.V_liq / q_in, "V_liq_m3": p.V_liq, "T_C": p.T_op - 273.15,
        "feed_m3_d": q_in, "OLR_kgVS_m3_d": vs_in_t_d * 1000 / p.V_liq, "COD_in_kg_m3": cod_in,
        "biogas_Nm3_h_dry": (o["CH4_Nm3_d"] + o["CO2_Nm3_d"]) / 24, "CH4_Nm3_h": ch4_Nm3_h,
        "CH4_pct_dry": 100 * o["CH4_frac_dry"],
        "biomethane_equiv_Nm3_h": ch4_Nm3_h / Y_CH4_BIOMETHANE,
        "CH4_yield_Nm3_per_tVS": o["CH4_Nm3_d"] / vs_in_t_d,
        "CH4_yield_vs_batch_BMP_pct": 100 * (o["CH4_Nm3_d"] / q_in) / plan["blend_CH4_Nm3_per_t"],
        "pH": o["pH"], "TAN_g_N_L": tan * 14.007, "free_NH3_mg_N_L": o["S_nh3_kmolN_m3"] * 14007,
        "VFA_g_COD_L": o["VFA_total_kgCOD_m3"], "S_ac_g_COD_L": y[IDX["S_ac"]], "S_pro_g_COD_L": y[IDX["S_pro"]],
        "undisintegrated_Xc_kgCOD_m3": y[IDX["X_xc"]], "inhibition_factors": o["inhibition"],
        "balances": balances(res), "solver": res.info,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    p, y_in, q_in, plan, cod = build_case()
    res = steady_state(y_in, q_in, p)
    base = summarize(res, plan, cod)

    # Quick one-at-a-time sensitivity of the most uncertain inputs (full study comes later)
    sens = {}
    for name, ov in {"K_I_nh3=0.00026 (calibrated value)": {"K_I_nh3": 0.00026},
                     "K_I_nh3=0.0084 (Wichern 2009)": {"K_I_nh3": 0.0084},
                     "k_dis=0.5 (BSM2 default)": {"k_dis": 0.5},
                     "HRT 45 d": {"_hrt": 45.0}, "HRT 90 d": {"_hrt": 90.0}}.items():
        hrt = ov.pop("_hrt", HRT_D)
        pp, yi, qi, pl, cd = build_case(hrt=hrt, overrides=ov)
        try:
            r = summarize(steady_state(yi, qi, pp), pl, cd)
            sens[name] = {k: r[k] for k in ["CH4_Nm3_h", "CH4_pct_dry", "pH", "VFA_g_COD_L",
                                            "free_NH3_mg_N_L", "CH4_yield_vs_batch_BMP_pct"]}
        except Exception as exc:  # report, do not hide
            sens[name] = {"error": str(exc)}

    (OUT / "base_case_results.json").write_text(json.dumps(base, indent=2, default=float), encoding="utf-8")
    (OUT / "base_case_sensitivity.json").write_text(json.dumps(sens, indent=2, default=float), encoding="utf-8")
    params = {k: v for k, v in asdict(p).items()}
    (OUT / "base_case_parameters.json").write_text(json.dumps({"parameters": params, "notes": PARAM_NOTES},
                                                              indent=2, default=float), encoding="utf-8")
    print(json.dumps(base, indent=1, default=lambda x: round(float(x), 5)))
    print(json.dumps(sens, indent=1, default=lambda x: round(float(x), 4)))


if __name__ == "__main__":
    main()
