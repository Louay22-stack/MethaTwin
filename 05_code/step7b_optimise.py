"""
Phase 3, step 7b - Surrogate-based design optimisation, verified by full simulation.

Problem (uncertain kinetics at nominal: k_dis 0.1, K_I,NH3 0.0018):
  minimise LCOE (EUR/MWh HHV)   over the 6 design variables, within the DoE bounds
  s.t. net biomethane = target +/- 1 % (after 3.5 % self-used for heat),
       P(digester stable) >= 0.97, predicted VFA <= 6 g COD/L, predicted pH >= 7.0 (design margins),
       P(scrubber simulation valid) >= 0.9, P(grid spec) >= 0.9,
       predicted CO2 <= 2.0 % (margin under 2.5 %), O2 <= 7,500 ppm (GRDF derogation).
Method: scipy differential evolution (vectorised, seed 42) on the surrogates + quadratic
penalties. Each optimum is re-simulated with the full ADM1 + DWSIM model and the deviation
reported (objective O4: < 3 %).
Also: optimal LCOE vs plant size (economies of scale) for targets 150-300 Nm3/h.

Writes 04_models_and_simulations/step7_tea/optimisation.json
Run from the project root:  python 05_code/step7b_optimise.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

sys.path.insert(0, str(Path(__file__).resolve().parent))
from methatwin.surrogate import Surrogate  # noqa: E402
from methatwin.tea import Econ, evaluate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step7_tea"
BOUNDS = {"maize_share": (0.0, 0.15), "cive_share": (0.05, 0.45), "feed_t_d": (60.0, 160.0),
          "hrt_d": (40.0, 110.0), "water_per_kNm3": (100.0, 200.0), "p_flash_bar": (2.0, 3.5)}
NOMINAL = {"k_dis": 0.1, "K_I_nh3": 0.0018}
HHV_CH4 = 11.06
SUR = Surrogate()
ECON = Econ()


def assess(X: np.ndarray, econ: Econ = ECON, unc: dict | None = None) -> pd.DataFrame:
    """Vectorised: rows of 6 design variables -> surrogate outputs + TEA."""
    df = pd.DataFrame(X, columns=list(BOUNDS))
    for k, v in (unc or NOMINAL).items():
        df[k] = v
    p = SUR.predict(df)
    hhv = HHV_CH4 * (1 - p.BM_CO2_pct / 100 - 2.7 * p.BM_O2_ppm / 1e6)
    tea = evaluate({"feed_t_d": df.feed_t_d, "maize_share": df.maize_share, "cive_share": df.cive_share,
                    "V_liq_m3": df.feed_t_d * df.hrt_d, "raw_Nm3_h": p.biogas_dry_Nm3_h,
                    "bm_Nm3_h": p.biomethane_Nm3_h, "hhv_kWh_Nm3": hhv, "P_el_upg_kW": p.P_el_upg_kW}, econ)
    out = pd.concat([df, p], axis=1)
    for k in ["LCOE_EUR_MWh", "NPV_EUR", "capex_total", "opex_total", "feed_cost", "energy_MWh_yr", "bm_net_Nm3_h"]:
        out[k] = np.asarray(tea[k])
    out["HHV"] = hhv
    return out


def penalised(target: float, pvalid_min: float = 0.9, vfa_max: float = 6.0):
    def f(Xt: np.ndarray) -> np.ndarray:       # scipy vectorised: Xt has shape (n_var, n_pop)
        a = assess(Xt.T)
        # plant sized FOR the target (equality, +/-1 %): with economies of scale a ">=" constraint
        # never binds and every target returned the largest plant (first run, LOG.md step 7)
        pen = (np.maximum(0, np.abs(a.bm_net_Nm3_h - target) / target - 0.01)) ** 2 * 1e6
        # stability with a design margin: the first run sat on P(stable) = 0.90 and 3 of 4 optima
        # were unstable in the full simulation
        pen += np.maximum(0, 0.97 - a.p_stable) ** 2 * 1e5 + np.maximum(0, pvalid_min - a.p_upg_valid) ** 2 * 1e5
        pen += np.maximum(0, a.VFA_gCOD_L - vfa_max) ** 2 * 1e3 + np.maximum(0, 7.0 - a.pH) ** 2 * 1e5
        pen += np.maximum(0, 0.9 - a.p_spec) ** 2 * 1e5 + np.maximum(0, a.BM_CO2_pct - 2.0) ** 2 * 1e4
        pen += np.maximum(0, a.BM_O2_ppm - 7500) ** 2 * 1e-2
        return (a.LCOE_EUR_MWh + pen).to_numpy()
    return f


def optimise(target: float, pvalid_min: float = 0.9, vfa_max: float = 6.0) -> dict:
    t0 = time.perf_counter()
    r = differential_evolution(penalised(target, pvalid_min, vfa_max), list(BOUNDS.values()), seed=42, popsize=40, maxiter=300,
                               tol=1e-7, polish=False, vectorized=True, updating="deferred")
    best = assess(r.x[None, :]).iloc[0].to_dict()
    best.update({"objective": float(r.fun), "n_evaluations": int(r.nfev), "opt_time_s": time.perf_counter() - t0,
                 "constraints_met": bool(r.fun - best["LCOE_EUR_MWh"] < 1e-3)})
    return best


def verify(x: dict) -> dict:
    """Full ADM1 + DWSIM simulation of a design and TEA on the simulated outputs."""
    from dwsim_bridge import load_dwsim
    from methatwin.plant import simulate_plant
    s = simulate_plant({**{k: x[k] for k in BOUNDS}, **NOMINAL}, load_dwsim())
    if s["status"] != "ok":
        return {"status": s["status"]}
    t = evaluate({"feed_t_d": s["feed_t_d"], "maize_share": s["maize_share"], "cive_share": s["cive_share"],
                  "V_liq_m3": s["V_liq_m3"], "raw_Nm3_h": s["biogas_dry_Nm3_h"], "bm_Nm3_h": s["biomethane_Nm3_h"],
                  "hhv_kWh_Nm3": s["BM_HHV_kWh_Nm3"], "P_el_upg_kW": s["P_el_upg_kW"]}, ECON)
    return {"status": "ok", "bm_net_Nm3_h": float(t["bm_net_Nm3_h"]), "LCOE_EUR_MWh": float(t["LCOE_EUR_MWh"]),
            "NPV_EUR": float(t["NPV_EUR"]), "BM_CO2_pct": s["BM_CO2_pct"], "BM_O2_ppm": s["BM_O2_ppm"],
            "CH4_slip_pct": s["CH4_slip_pct"], "pH": s["pH"], "VFA_gCOD_L": s["VFA_gCOD_L"],
            "free_NH3_mgN_L": s["free_NH3_mgN_L"], "upg_mass_closure_pct": s["upg_mass_closure_pct"],
            "capex_total": float(t["capex_total"]), "feed_cost": float(t["feed_cost"])}


def main() -> None:
    """Verify-and-correct loop: optimise on the surrogates, re-simulate with ADM1 + DWSIM, then
    (a) if the simulated output misses the target, rescale the surrogate target by the shortfall;
    (b) if the scrubber fails, raise the required P(valid); (c) if the digester is unstable,
    tighten the VFA margin. Only designs confirmed by the full simulation are reported."""
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for target in (150.0, 200.0, 250.0, 300.0):
        t_adj, pv, vfa, hist, final = target, 0.9, 6.0, [], None
        for it in range(5):
            b = optimise(t_adj, pv, vfa)
            v = verify(b)
            rec = {"iteration": it, "surrogate_target": t_adj, "pvalid_min": pv, "vfa_max": vfa,
                   "design": {k: float(b[k]) for k in BOUNDS},
                   "surrogate": {k: float(b[k]) for k in ("bm_net_Nm3_h", "LCOE_EUR_MWh", "BM_CO2_pct", "VFA_gCOD_L",
                                                          "p_stable", "p_upg_valid")},
                   "simulation": v}
            if v.get("status") == "ok":
                rec["deviation_pct"] = {k: (v[k] - b[k]) / b[k] * 100 for k in ("bm_net_Nm3_h", "LCOE_EUR_MWh")}
            hist.append(rec)
            print(f"target {target:.0f} it{it}: sur-target {t_adj:.1f}, pValid>={pv:.2f}, VFA<={vfa:.1f} | "
                  + ", ".join(f"{k}={b[k]:.3g}" for k in BOUNDS)
                  + (f" | sim BM {v['bm_net_Nm3_h']:.1f}, LCOE {v['LCOE_EUR_MWh']:.1f}, CO2 {v['BM_CO2_pct']:.2f}, "
                     f"VFA {v['VFA_gCOD_L']:.1f}" if v.get("status") == "ok" else f" | sim {v.get('status')}"), flush=True)
            if v.get("status") == "ok":
                if abs(v["bm_net_Nm3_h"] - target) / target <= 0.015 and v["BM_CO2_pct"] <= 2.5:
                    final = rec
                    break
                t_adj *= target / v["bm_net_Nm3_h"]
            elif str(v.get("status")).startswith("upgrading"):
                pv = min(0.99, pv + 0.04)
            else:
                vfa = max(3.0, vfa - 0.75)
        results[f"{target:.0f}"] = {"history": hist, "final": final}
        if final:
            print(f"  -> CONFIRMED by full simulation: BM {final['simulation']['bm_net_Nm3_h']:.1f} Nm3/h, "
                  f"LCOE {final['simulation']['LCOE_EUR_MWh']:.1f} EUR/MWh, NPV {final['simulation']['NPV_EUR']/1e6:.2f} MEUR",
                  flush=True)
        else:
            print("  -> no design confirmed within 5 iterations", flush=True)
    (OUT / "optimisation.json").write_text(json.dumps(results, indent=2, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
