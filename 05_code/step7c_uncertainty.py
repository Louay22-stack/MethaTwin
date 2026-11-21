"""
Phase 3, step 7c - (1) value of optimisation at 200 Nm3/h: naive scaled-up base design vs the
confirmed optimum, both by full simulation; (2) Monte Carlo uncertainty of the optimum
(10,000 samples through the surrogates + TEA); (3) one-at-a-time tornado on LCOE.

Uncertain inputs (A# = assumption, see LOG.md step 7):
  k_dis        log-uniform 0.05-0.5 1/d          (DoE range; calibrated 0.1, BSM2 0.5)
  K_I,NH3      log-uniform 0.0012-0.0084         (literature range, Bulkowska 2015 Tab. 5)
  CAPEX factor triangular 0.8 / 1.0 / 1.25        (A7; CRE mean 8.16 vs median 6.54 MEUR shows the spread)
  CIVE, maize cost  uniform +/-30 %               (A8)
  slurry cost  uniform 7.3-43.2 EUR/t             (transport only -> CRE effluent price incl. transport)
  electricity  uniform 120-202 EUR/MWh            (CRE fixed median -> variable mean)
  other OPEX   triangular 0.8 / 1.0 / 1.2 x 32.64 (A8)
  tariff       uniform 111-169 EUR/MWh            (CRE, arrete BI 2023, agricultural range Q4 2024)
  discount     uniform 5-9 %                      (A8, around the CRE 7 %)
  heat self-use uniform 2-6 %                     (A8, around the CRE median 3.5 %)
Writes 04_models_and_simulations/step7_tea/{uncertainty.json, montecarlo.csv, tornado.csv}
Run from the project root:  python 05_code/step7c_uncertainty.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import step7b_optimise as O  # noqa: E402
from methatwin.tea import Econ, evaluate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step7_tea"
N = 10_000
RNG = np.random.default_rng(42)


def tea_from_sur(a: pd.DataFrame, econs: list[Econ] | None = None, econ: Econ | None = None) -> pd.DataFrame:
    """TEA on surrogate predictions; econs = one Econ per row (Monte Carlo) or a single econ."""
    rows = []
    for i, r in a.iterrows():
        e = econs[i] if econs is not None else econ
        t = evaluate({"feed_t_d": r.feed_t_d, "maize_share": r.maize_share, "cive_share": r.cive_share,
                      "V_liq_m3": r.feed_t_d * r.hrt_d, "raw_Nm3_h": r.biogas_dry_Nm3_h,
                      "bm_Nm3_h": r.biomethane_Nm3_h, "hhv_kWh_Nm3": r.HHV, "P_el_upg_kW": r.P_el_upg_kW}, e)
        rows.append({k: float(t[k]) for k in ("LCOE_EUR_MWh", "NPV_EUR", "bm_net_Nm3_h", "capex_total", "opex_total")})
    return pd.DataFrame(rows)


def main() -> None:
    opt = json.loads((OUT / "optimisation.json").read_text())["200"]["final"]
    x_opt = opt["design"]

    # (1) naive design: base blend & settings, feed scaled to 200 Nm3/h net (base: 128.7 net at 88.44 t/d)
    x_naive = {"maize_share": 0.15, "cive_share": 0.25, "feed_t_d": 88.44 * 200.0 / 128.7, "hrt_d": 60.0,
               "water_per_kNm3": 130.0, "p_flash_bar": 3.5}
    naive_sim = O.verify(x_naive)
    comparison = {"naive_scaled_base": {"design": x_naive, "simulation": naive_sim},
                  "optimum": {"design": x_opt, "simulation": opt["simulation"]}}
    print("naive:", {k: round(v, 2) for k, v in naive_sim.items() if isinstance(v, float)})
    print("optimum:", {k: round(v, 2) for k, v in opt["simulation"].items() if isinstance(v, float)})

    # (2) Monte Carlo at the optimum design
    lu = lambda lo, hi, n: np.exp(RNG.uniform(np.log(lo), np.log(hi), n))
    kd, ki = lu(0.05, 0.5, N), lu(0.0012, 0.0084, N)
    X = np.tile([x_opt[k] for k in O.BOUNDS], (N, 1))
    df = pd.DataFrame(X, columns=list(O.BOUNDS)).assign(k_dis=kd, K_I_nh3=ki)
    p = O.SUR.predict(df)
    a = pd.concat([df, p], axis=1)
    a["HHV"] = O.HHV_CH4 * (1 - a.BM_CO2_pct / 100 - 2.7 * a.BM_O2_ppm / 1e6)
    base = Econ()
    samp = pd.DataFrame({
        "capex_factor": RNG.triangular(0.8, 1.0, 1.25, N),
        "cost_cive": base.cost_cive * RNG.uniform(0.7, 1.3, N), "cost_maize": base.cost_maize * RNG.uniform(0.7, 1.3, N),
        "cost_slurry": RNG.uniform(7.3, 43.2, N), "el_price": RNG.uniform(120, 202, N),
        "other_opex_per_MWh": base.other_opex_per_MWh * RNG.triangular(0.8, 1.0, 1.2, N),
        "tariff": RNG.uniform(111, 169, N), "discount": RNG.uniform(0.05, 0.09, N),
        "heat_selfuse_frac": RNG.uniform(0.02, 0.06, N)})
    econs = [replace(base, **r) for r in samp.to_dict("records")]
    t = tea_from_sur(a, econs=econs)
    mc = pd.concat([df[["k_dis", "K_I_nh3"]], samp, p[["p_stable", "VFA_gCOD_L", "pH", "biomethane_Nm3_h",
                                                       "BM_CO2_pct"]], t], axis=1)
    mc.to_csv(OUT / "montecarlo.csv", index=False)
    feas = mc.p_stable >= 0.5
    q = lambda s: {f"P{int(k*100)}": float(s.quantile(k)) for k in (0.1, 0.5, 0.9)}
    summ = {"n": N, "share_predicted_unstable": float(1 - feas.mean()),
            "LCOE_all": q(mc.LCOE_EUR_MWh), "LCOE_stable": q(mc.LCOE_EUR_MWh[feas]),
            "NPV_stable_MEUR": {k: v / 1e6 for k, v in q(mc.NPV_EUR[feas]).items()},
            "P_NPV_positive_stable": float((mc.NPV_EUR[feas] > 0).mean()),
            "biomethane_net_stable": q(mc.bm_net_Nm3_h[feas]),
            "share_biomethane_below_190": float((mc.bm_net_Nm3_h[feas] < 190).mean())}
    print(json.dumps(summ, indent=1))

    # (3) tornado: one input at a time at its low / high value, others nominal
    nominal_unc = {"k_dis": 0.1, "K_I_nh3": 0.0018}
    def lcoe_at(unc=None, **econ_kw):
        aa = O.assess(np.array([[x_opt[k] for k in O.BOUNDS]]), replace(base, **econ_kw), unc or nominal_unc)
        return float(aa.LCOE_EUR_MWh.iloc[0]), float(aa.p_stable.iloc[0])
    lc0, _ = lcoe_at()
    cases = {"CAPEX (x0.8 / x1.25)": ({"capex_factor": 0.8}, {"capex_factor": 1.25}),
             "CIVE cost (-30 / +30 %)": ({"cost_cive": base.cost_cive * 0.7}, {"cost_cive": base.cost_cive * 1.3}),
             "maize cost (-30 / +30 %)": ({"cost_maize": base.cost_maize * 0.7}, {"cost_maize": base.cost_maize * 1.3}),
             "slurry cost (7.3 / 43.2 EUR/t)": ({"cost_slurry": 7.3}, {"cost_slurry": 43.2}),
             "electricity (120 / 202 EUR/MWh)": ({"el_price": 120.0}, {"el_price": 202.0}),
             "other OPEX (-20 / +20 %)": ({"other_opex_per_MWh": 32.64 * 0.8}, {"other_opex_per_MWh": 32.64 * 1.2}),
             "discount rate (5 / 9 %)": ({"discount": 0.05}, {"discount": 0.09}),
             "heat self-use (2 / 6 %)": ({"heat_selfuse_frac": 0.02}, {"heat_selfuse_frac": 0.06})}
    rows = []
    for name, (lo, hi) in cases.items():
        rows.append({"input": name, "LCOE_low": lcoe_at(**lo)[0], "LCOE_high": lcoe_at(**hi)[0]})
    for name, key, lo, hi in (("k_dis (0.05 / 0.5 1/d)", "k_dis", 0.05, 0.5),
                              ("K_I,NH3 (0.0012 / 0.0084)", "K_I_nh3", 0.0012, 0.0084)):
        rl, pl = lcoe_at({**nominal_unc, key: lo})
        rh, ph = lcoe_at({**nominal_unc, key: hi})
        rows.append({"input": name, "LCOE_low": rl, "LCOE_high": rh, "p_stable_low": pl, "p_stable_high": ph})
    tor = pd.DataFrame(rows)
    tor["swing"] = (tor.LCOE_high - tor.LCOE_low).abs()
    tor = tor.sort_values("swing", ascending=False)
    tor.to_csv(OUT / "tornado.csv", index=False)
    print(f"tornado (nominal LCOE {lc0:.1f}):\n", tor.round(2).to_string(index=False))
    (OUT / "uncertainty.json").write_text(json.dumps({"comparison_200": comparison, "montecarlo": summ,
                                                      "tornado_nominal_LCOE": lc0}, indent=2, default=float),
                                          encoding="utf-8")


if __name__ == "__main__":
    main()
