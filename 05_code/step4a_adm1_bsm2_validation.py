"""
Phase 3, step 4a - Validate the ADM1 implementation against the IWA BSM2 benchmark.

Reference: Rosen C., Jeppsson U. (2006), Aspects on ADM1 implementation within the BSM2
framework, section 7 "ADM1 benchmark model steady-state results" (influent, Q = 170 m3/d,
T = 35 degC, V_liq = 3400 m3, V_gas = 300 m3; reference states to 13 significant digits).
Copy used: https://iwa-mia.org/wp-content/uploads/2019/04/bmadm1_report061127.pdf
(influent table cross-checked with https://lup.lub.lu.se/search/files/5715450/588082.pdf).

Acceptance: every state, pH and gas output within 1 % (relative) of the reference;
COD, N and C balances closed within 0.1 %.

Run from the project root:  python 05_code/step4a_adm1_bsm2_validation.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from methatwin.adm1 import (ADM1Params, IDX, balances, influent_vector,  # noqa: E402
                            steady_state)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step4_adm1"

INFLUENT = influent_vector(
    S_su=0.01, S_aa=0.001, S_fa=0.001, S_va=0.001, S_bu=0.001, S_pro=0.001, S_ac=0.001,
    S_h2=1e-8, S_ch4=1e-5, S_IC=0.04, S_IN=0.01, S_I=0.02,
    X_xc=2.0, X_ch=5.0, X_pr=20.0, X_li=5.0, X_su=0.0, X_aa=0.01, X_fa=0.01, X_c4=0.01,
    X_pro=0.01, X_ac=0.01, X_h2=0.01, X_I=25.0, S_cat=0.04, S_an=0.02)
Q_IN = 170.0

REFERENCE = {  # Rosen & Jeppsson (2006), section 7, steady-state output values
    "S_su": 0.0119548297170, "S_aa": 0.0053147401716, "S_fa": 0.0986214009308,
    "S_va": 0.0116250064639, "S_bu": 0.0132507296663, "S_pro": 0.0157836662845,
    "S_ac": 0.1976297169375, "S_h2": 0.0000002359451, "S_ch4": 0.0550887764460,
    "S_IC": 0.1526778706263, "S_IN": 0.1302298158037, "S_I": 0.3286976637215,
    "X_xc": 0.3086976637215, "X_ch": 0.0279472404350, "X_pr": 0.1025741061067,
    "X_li": 0.0294830497073, "X_su": 0.4201659824546, "X_aa": 1.1791717989237,
    "X_fa": 0.2430353447194, "X_c4": 0.4319211056360, "X_pro": 0.1373059089340,
    "X_ac": 0.7605626583132, "X_h2": 0.3170229533613, "X_I": 25.6173953274430,
    "S_cat": 0.04, "S_an": 0.02,
    "S_gas_h2": 0.0000102410356, "S_gas_ch4": 1.6256072099814, "S_gas_co2": 0.0141505346784,
}
REF_OUTPUTS = {"pH": 7.4655377698929, "S_nh3_kmolN_m3": 0.0040909284584,
               "S_hco3_kmolC_m3": 0.1427774793921, "p_gas_ch4_bar": 0.6507796328232,
               "p_gas_co2_bar": 0.3625527133281, "P_gas_bar": 1.0690164904089,
               "q_gas_m3_d": 2955.70345419378}
TOL_PCT = 1.0


def main() -> None:
    p = ADM1Params()  # BSM2 defaults: 35 degC, 3400/300 m3
    t0 = time.perf_counter()
    res = steady_state(INFLUENT, Q_IN, p)
    dt = time.perf_counter() - t0
    out = res.outputs()

    rows = []
    for k, ref in REFERENCE.items():
        v = res.y[IDX[k]]
        rows.append({"variable": k, "model": v, "reference": ref, "rel_err_pct": (v - ref) / ref * 100})
    for k, ref in REF_OUTPUTS.items():
        v = out[k]
        rows.append({"variable": k, "model": v, "reference": ref, "rel_err_pct": (v - ref) / ref * 100})
    df = pd.DataFrame(rows)
    df["pass"] = df.rel_err_pct.abs() <= TOL_PCT
    bal = balances(res)

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "bsm2_validation.csv", index=False)
    summary = {"n_variables": len(df), "n_pass": int(df["pass"].sum()),
               "max_abs_rel_err_pct": float(df.rel_err_pct.abs().max()),
               "worst_variable": df.loc[df.rel_err_pct.abs().idxmax(), "variable"],
               "balances": bal, "solve_time_s": dt, "solver_info": res.info}
    (OUT / "bsm2_validation_summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")

    pd.set_option("display.width", 160)
    print(df.to_string(index=False, float_format=lambda x: f"{x:.6g}"))
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
