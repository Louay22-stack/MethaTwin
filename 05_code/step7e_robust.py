"""
Phase 3, step 7e - Robust design at 200 Nm3/h: the nominal optimum becomes unstable when the
ammonia inhibition constant is at the low end of the literature range (tornado, step 7c).
First attempt at K_I,NH3 = 0.0012 failed 6 times in the full simulation; the DoE confirms why
(only 8 % of runs stable at K_I 0.0012-0.0016, and only 2 near the edge reach 195 Nm3/h).
So: search the robustness frontier - re-optimise for increasing worst-case K_I,NH3 values with
the same verify-and-correct loop as step 7b, stop at the first confirmed design, report its cost
premium ("price of robustness") and check it also works at the nominal K_I,NH3.

Writes 04_models_and_simulations/step7_tea/robust_design.json
Run from the project root:  python 05_code/step7e_robust.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import step7b_optimise as O  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step7_tea"
KI_CANDIDATES = (0.0012, 0.0014, 0.0016, 0.0018)


def robust_at(ki: float, target: float = 200.0):
    O.NOMINAL.update({"k_dis": 0.1, "K_I_nh3": ki})   # optimise AND verify at this worst case
    t_adj, pv, vfa, hist, final = target, 0.9, 6.0, [], None
    for it in range(4):
        b = O.optimise(t_adj, pv, vfa)
        v = O.verify(b)
        hist.append({"iteration": it, "design": {k: float(b[k]) for k in O.BOUNDS}, "simulation": v,
                     "surrogate_bm": float(b["bm_net_Nm3_h"]), "surrogate_LCOE": float(b["LCOE_EUR_MWh"])})
        print(f"K_I {ki} it{it}: " + ", ".join(f"{k}={b[k]:.3g}" for k in O.BOUNDS)
              + (f" | sim BM {v['bm_net_Nm3_h']:.1f}, LCOE {v['LCOE_EUR_MWh']:.1f}, VFA {v['VFA_gCOD_L']:.1f}, "
                 f"NH3 {v['free_NH3_mgN_L']:.0f}" if v.get("status") == "ok" else f" | sim {v.get('status')}"), flush=True)
        if v.get("status") == "ok":
            if abs(v["bm_net_Nm3_h"] - target) / target <= 0.015:
                final = hist[-1]
                break
            t_adj *= target / v["bm_net_Nm3_h"]
        elif str(v.get("status")).startswith("upgrading"):
            pv = min(0.99, pv + 0.04)
        else:
            vfa = max(3.0, vfa - 0.75)
    return hist, final


def main() -> None:
    attempts, final, ki_ok = {}, None, None
    for ki in KI_CANDIDATES:
        hist, final = robust_at(ki)
        attempts[str(ki)] = {"history": hist, "confirmed": final is not None}
        if final:
            ki_ok = ki
            break
    out = {"ki_candidates": KI_CANDIDATES, "attempts": attempts, "lowest_feasible_K_I_nh3": ki_ok, "final": final}
    if final:
        O.NOMINAL.update({"k_dis": 0.1, "K_I_nh3": 0.0018})
        nom = O.verify(final["design"])         # same robust design at the nominal kinetics
        out["robust_design_at_nominal_kinetics"] = nom
        nominal_opt = json.loads((OUT / "optimisation.json").read_text())["200"]["final"]["simulation"]
        out["price_of_robustness_EUR_MWh"] = final["simulation"]["LCOE_EUR_MWh"] - nominal_opt["LCOE_EUR_MWh"]
        print(f"robust design confirmed for K_I,NH3 >= {ki_ok}: LCOE {final['simulation']['LCOE_EUR_MWh']:.1f} EUR/MWh; "
              f"at nominal kinetics: {nom.get('status')}, BM {nom.get('bm_net_Nm3_h', float('nan')):.1f}, "
              f"LCOE {nom.get('LCOE_EUR_MWh', float('nan')):.1f}; nominal optimum LCOE {nominal_opt['LCOE_EUR_MWh']:.1f}"
              f" -> price of robustness {out['price_of_robustness_EUR_MWh']:+.1f} EUR/MWh")
    (OUT / "robust_design.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
