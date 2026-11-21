"""
Phase 3, step 7a - Techno-economics of the reference and base-case plants (full simulation),
calibration of fixed O&M (assumption A5) and consistency check against CRE (Dec 2024).

Reference plant: MethaTwin base design scaled to the CRE average capacity (~184 Nm3/h):
  base blend (60/25/15), HRT 60 d, feed 88.44 x 184/133.4 t/d, scrubber water 130 m3/kNm3,
  flash 3.5 bar.
Base case: the step-4/5 plant (88.44 t/d), which only reaches ~133 Nm3/h.
Writes 04_models_and_simulations/step7_tea/tea_base.json
Run from the project root:  python 05_code/step7a_tea_base.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dwsim_bridge import load_dwsim  # noqa: E402
from methatwin.plant import simulate_plant  # noqa: E402
from methatwin.tea import Econ, evaluate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step7_tea"
CRE = {"LCOE_median": 129.6, "LCOE_Q1": 111.7, "LCOE_Q3": 146.0, "el_share": 0.092, "opex_avg": 1.02e6,
       "opex_agri_EUR_MWh": 71.06, "feed_agri_EUR_MWh": 30.74, "capex_share_full_cost": 0.40}


def tea_point(sim: dict) -> dict:
    return {"feed_t_d": sim["feed_t_d"], "maize_share": sim["maize_share"], "cive_share": sim["cive_share"],
            "V_liq_m3": sim["V_liq_m3"], "raw_Nm3_h": sim["biogas_dry_Nm3_h"], "bm_Nm3_h": sim["biomethane_Nm3_h"],
            "hhv_kWh_Nm3": sim["BM_HHV_kWh_Nm3"], "P_el_upg_kW": sim["P_el_upg_kW"], "co2_t_yr": sim["CO2_stream_t_yr"]}


def summary(r: dict) -> dict:
    keys = ["capex_total", "ann_capex", "feed_cost", "el_cost", "fixed_om", "opex_total", "energy_MWh_yr",
            "el_share_of_energy", "LCOE_EUR_MWh", "NPV_EUR", "bm_net_Nm3_h"]
    out = {k: float(r[k]) for k in keys}
    out["capex_breakdown"] = {k: float(v) for k, v in r["capex_breakdown"].items()}
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dw = load_dwsim()
    base_x = dict(maize_share=0.15, cive_share=0.25, feed_t_d=88.44, hrt_d=60.0, water_per_kNm3=130.0,
                  p_flash_bar=3.5, k_dis=0.1, K_I_nh3=0.0018)
    ref_x = dict(base_x, feed_t_d=88.44 * 184.0 / 133.4)
    sims = {"reference_184": simulate_plant(ref_x, dw), "base_case": simulate_plant(base_x, dw)}
    for k, s in sims.items():
        assert s["status"] == "ok", (k, s["status"])
    e = Econ()
    res = {k: summary(evaluate(tea_point(s), e)) for k, s in sims.items()}
    # Scenario: biogenic CO2 sold. IFRI (2026): industrial CO2 0.25-0.35 EUR/kg, capture 25-90 EUR/t.
    # Net value taken as the low price minus the high capture cost: 250 - 90 = 160 EUR/t (scenario).
    res["reference_184_with_CO2_sales"] = summary(evaluate(tea_point(sims["reference_184"]),
                                                           replace(e, co2_net_value=160.0)))
    out = {"econ": asdict(e), "cre_benchmarks": CRE,
           "simulations": {k: {kk: (float(v) if not isinstance(v, str) else v) for kk, v in s.items()}
                           for k, s in sims.items()},
           "results": res}
    (OUT / "tea_base.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for k, r in res.items():
        print(f"\n{k}: biomethane net {r['bm_net_Nm3_h']:.1f} Nm3/h, CAPEX {r['capex_total']/1e6:.2f} MEUR, "
              f"OPEX {r['opex_total']/1e6:.3f} MEUR/yr (feed {r['feed_cost']/1e3:.0f} k, el {r['el_cost']/1e3:.0f} k, "
              f"other {r['fixed_om']/1e3:.0f} k), el share {100*r['el_share_of_energy']:.1f} %, "
              f"LCOE {r['LCOE_EUR_MWh']:.1f} EUR/MWh, NPV {r['NPV_EUR']/1e6:.2f} MEUR")
    print(f"\nCRE: LCOE median {CRE['LCOE_median']} (Q1 {CRE['LCOE_Q1']}, Q3 {CRE['LCOE_Q3']}), el share 9.2 %, "
          f"OPEX ~71 EUR/MWh, feed median 30.7 EUR/MWh, CAPEX ~40 % of full cost")
    for k, r in res.items():
        E = r["energy_MWh_yr"]
        full = r["ann_capex"] + r["opex_total"]
        feed_excess = r["feed_cost"] / E - CRE["feed_agri_EUR_MWh"]
        print(f"  {k}: OPEX {r['opex_total']/E:.1f} EUR/MWh, feed {r['feed_cost']/E:.1f} EUR/MWh, "
              f"CAPEX share {100*r['ann_capex']/full:.0f} %, LCOE without the feed-cost excess vs CRE median "
              f"{r['LCOE_EUR_MWh'] - feed_excess:.1f} EUR/MWh")


if __name__ == "__main__":
    main()
