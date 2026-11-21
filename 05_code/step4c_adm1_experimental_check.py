"""
Phase 3, step 4c - Check the calibrated ADM1 against measured lab-digester data.

Experiment (Klimiuk et al. 2015 Part I; Bulkowska et al. 2015 Part II, Arch. Environ. Prot. 41(3)):
  100 dm3 CSTR, 39 degC, fed 2.22 dm3/d (HRT 45 d, OLR 2.1 kg VS/m3/d) with a 49:51 (VS)
  maize silage : cattle manure mix. Influent = Part I Table 5 (measured/default values).
Measured (Part II Fig. 1, read from the figure data, so approximate):
  biogas ~65-100 dm3/d (mean of the plotted points ~78), CH4 ~55 %, pH ~6.8-7.4 (mean ~7.1),
  acetate ~0.2-0.6 kg COD/m3 after start-up, propionate ~0.3-0.9 kg COD/m3.
Parameters: the full calibrated set of Part II (including K_I,nh3 = 0.00026, valid here
because this feed has little ammonium), X_c fractions from Part I (0.111/0.048/0.500/0.341).

This is a consistency check with independent experimental data, not a fit: no parameter
is adjusted here. Run from the project root:  python 05_code/step4c_adm1_experimental_check.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from methatwin.adm1 import ADM1Params, IDX, balances, influent_vector, steady_state  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step4_adm1"

MEASURED = {"biogas_dm3_d": (65, 100, 78), "CH4_pct": (50, 58, 55), "pH": (6.8, 7.4, 7.1),
            "S_ac_kgCOD_m3": (0.2, 0.6, 0.35), "S_pro_kgCOD_m3": (0.3, 0.9, 0.65)}


def main() -> None:
    p = ADM1Params()
    for k, v in {"k_dis": 0.1, "K_S_c4": 0.23, "K_I_h2_c4": 1e-8, "k_m_pro": 8.5, "K_S_pro": 0.15,
                 "K_I_h2_pro": 2.4e-8, "k_m_ac": 7.64, "K_S_ac": 0.6, "K_I_nh3": 0.00026}.items():
        setattr(p, k, v)
    p.T_op = 273.15 + 39.0
    p.V_liq, p.V_gas = 0.100, 0.020
    q_in = 0.00222
    p.f_pr_xc, p.f_li_xc, p.f_ch_xc, p.f_xI_xc, p.f_sI_xc = 0.111, 0.048, 0.500, 0.341, 0.0
    p.N_xc = p.f_pr_xc * p.N_aa + p.f_xI_xc * p.N_I
    p.C_xc = p.f_ch_xc * p.C_ch + p.f_pr_xc * p.C_pr + p.f_li_xc * p.C_li + p.f_xI_xc * p.C_xI
    p.k_p = 0.08 / 0.05  # ~0.05 bar overpressure at ~80 dm3/d

    y_in = influent_vector(  # Klimiuk et al. 2015 Part I, Table 5
        S_su=0.24, S_aa=0.0011, S_fa=0.001, S_va=0.168, S_bu=0.39, S_pro=0.7454, S_ac=2.3467,
        S_IN=0.018571429, S_I=8.49, X_xc=118.1111, X_su=0.0855, X_aa=0.0637, X_fa=0.067,
        X_c4=0.028, X_pro=0.0135, X_ac=0.09, X_h2=0.043, S_cat=0.08, S_an=0.02, S_IC=0.0323)
    res = steady_state(y_in, q_in, p)
    o = res.outputs()
    model = {"biogas_dm3_d": o["q_gas_m3_d"] * 1000,          # wet gas, P_atm, 39 degC
             "biogas_dry_Ndm3_d": (o["CH4_Nm3_d"] + o["CO2_Nm3_d"]) * 1000,
             "CH4_pct": 100 * o["CH4_frac_dry"], "pH": o["pH"],
             "S_ac_kgCOD_m3": res.y[IDX["S_ac"]], "S_pro_kgCOD_m3": res.y[IDX["S_pro"]]}
    rows = {}
    for k, (lo, hi, mean) in MEASURED.items():
        v = model[k]
        rows[k] = {"model": v, "measured_range": [lo, hi], "measured_mean_approx": mean,
                   "within_range": bool(lo <= v <= hi), "dev_from_mean_pct": (v - mean) / mean * 100}
    out = {"comparison": rows, "model_extra": {"biogas_dry_Ndm3_d": model["biogas_dry_Ndm3_d"]},
           "balances": balances(res), "solver": res.info}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "experimental_check.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(json.dumps(out, indent=1, default=lambda x: round(float(x), 4)))


if __name__ == "__main__":
    main()
