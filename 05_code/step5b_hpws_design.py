"""
Phase 3, step 5b - Size the water scrubber: sweep circulating water, absorber stages and
flash pressure (stripping air ratio was shown to be non-limiting: 8 vs 15 Nm3/m3
changed product CO2 by <0.01 %-pt); keep designs that meet the grid specification; choose the lowest total energy penalty
(electricity + LHV of the methane slip, 9.97 kWh/Nm3).

Grid specification (GRDF, ENTSOG gas-quality workshop, 19 Nov 2025):
  CO2 < 2.5 mol% (design target 2.0 % for margin), HHV 10.7-12.8 kWh/Nm3, Wobbe 13.64-15.70,
  O2 < 100 ppm (derogation up to 0.75 %), water dew point < -5 degC (dryer, not modelled).
Raw gas: design capacity 345 Nm3/h dry at 56.9 % CH4 (ADM1 base-case composition; flow sized
for ~200 Nm3/h biomethane).

Writes 04_models_and_simulations/step5_upgrading/{design_sweep.csv, final_design.json,
       hpws_final.dwxmz}. Run from the project root:  python 05_code/step5b_hpws_design.py
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dwsim_bridge import load_dwsim  # noqa: E402
from methatwin.upgrading import HPWSFlowsheet, UpgradingDesign  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step5_upgrading"
CO2_TARGET = 2.0

dw = load_dwsim()


def run(design: UpgradingDesign) -> dict:
    t0 = time.perf_counter()
    try:
        r = HPWSFlowsheet(dw, design).solve()
    except Exception as exc:
        return {"error": str(exc)[:200]}
    k = r.kpi
    return {"converged": r.converged, "iters": r.iterations, "time_s": time.perf_counter() - t0,
            **{x: k[x] for x in ["CH4_pct_dry", "CO2_pct_dry", "O2_ppm_dry", "N2_pct_dry", "HHV_kWh_Nm3",
                                 "Wobbe_kWh_Nm3", "CH4_slip_pct", "biomethane_Nm3_h_dry", "P_el_total_kW",
                                 "specific_el_kWh_per_Nm3_raw", "CO2_stream_Nm3_h", "recycle_Nm3_h",
                                 "water_units_in_validity_window", "energy_penalty_kW"]},
            "mass_closure_pct": r.balances["mass_closure_pct"],
            "energy_closure_pct": r.balances["energy_closure_pct_of_work_plus_heat"]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = UpgradingDesign()
    rows = []
    grid = itertools.product([40.0, 45.0, 50.0, 55.0, 60.0, 70.0], [6, 10], [2.0, 2.5, 3.5])
    for water, n_abs, p_flash in grid:
        d = replace(base, water_m3_h=water, n_abs_stages=n_abs, P_flash_bar=p_flash)
        r = run(d)
        rows.append({"water_m3_h": water, "n_abs_stages": n_abs, "P_flash_bar": p_flash, **r})
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()
               if k in ["water_m3_h", "n_abs_stages", "P_flash_bar", "energy_penalty_kW", "CO2_pct_dry", "O2_ppm_dry",
                        "CH4_slip_pct", "specific_el_kWh_per_Nm3_raw", "converged", "error"]}, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "design_sweep.csv", index=False)

    ok = df[(df.get("converged") == True) & (df.CO2_pct_dry <= CO2_TARGET)
            & df.HHV_kWh_Nm3.between(10.7, 12.8) & df.Wobbe_kWh_Nm3.between(13.64, 15.70)]
    if ok.empty:
        print("No design in the grid meets the CO2/HHV/Wobbe specification.")
        return
    best = ok.sort_values("energy_penalty_kW").iloc[0]   # electricity + LHV of methane slip
    d = replace(base, water_m3_h=float(best.water_m3_h), n_abs_stages=int(best.n_abs_stages),
                P_flash_bar=float(best.P_flash_bar))
    fs = HPWSFlowsheet(dw, d)
    res = fs.solve()
    try:
        fs.interf.SaveFlowsheet(fs.sim, str(OUT / "hpws_final.dwxmz"), True)
    except Exception as exc:
        print("save failed:", exc)
    out = {"design": res.design, "converged": res.converged, "iterations": res.iterations,
           "kpi": res.kpi, "balances": res.balances, "streams": res.streams,
           "spec_check": {"CO2_lt_2.5": bool(res.kpi["CO2_pct_dry"] < 2.5),
                          "HHV_in_10.7_12.8": bool(10.7 <= res.kpi["HHV_kWh_Nm3"] <= 12.8),
                          "Wobbe_in_13.64_15.70": bool(13.64 <= res.kpi["Wobbe_kWh_Nm3"] <= 15.70),
                          "O2_lt_100ppm": bool(res.kpi["O2_ppm_dry"] < 100),
                          "O2_lt_0.75pct_derogation": bool(res.kpi["O2_ppm_dry"] < 7500)}}
    (OUT / "final_design.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print("\nSelected design:", {k: out["design"][k] for k in ["water_m3_h", "n_abs_stages", "P_flash_bar"]})
    print(json.dumps({k: v for k, v in res.kpi.items()}, indent=1, default=lambda x: round(float(x), 4)))
    print(json.dumps(out["balances"], default=lambda x: round(float(x), 5)))
    print(json.dumps(out["spec_check"]))


if __name__ == "__main__":
    main()
