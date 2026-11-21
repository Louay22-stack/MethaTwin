"""MethaTwin dashboard - model layer.

Runs the trained surrogates (step 6) and the TEA model (step 7) for any design, with the same
feature engineering, HHV formula and Monte Carlo distributions as 05_code/step7b and step7c.
No DWSIM needed: everything here is surrogate-based and takes milliseconds.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))
from methatwin.surrogate import MODEL_FILE, Surrogate  # noqa: E402
from methatwin.tea import Econ, evaluate  # noqa: E402

RESULTS = ROOT / "04_models_and_simulations"
FIGURES = ROOT / "06_figures"
REPORT = ROOT / "07_report" / "MethaTwin_Final_Report.pdf"

# design space = DoE bounds (step 6a); the surrogates are only valid inside it
BOUNDS = {"maize_share": (0.0, 0.15), "cive_share": (0.05, 0.45), "feed_t_d": (60.0, 160.0),
          "hrt_d": (40.0, 110.0), "water_per_kNm3": (100.0, 200.0), "p_flash_bar": (2.0, 3.5)}
UNC_BOUNDS = {"k_dis": (0.05, 0.5), "K_I_nh3": (0.0012, 0.0084)}
NOMINAL = {"k_dis": 0.1, "K_I_nh3": 0.0018}
HHV_CH4 = 11.06            # kWh/Nm3, as in step 7b

# grid specification (GRDF, S18) and study thresholds (LOG.md steps 5-7)
SPEC = {"CO2_max": 2.5, "O2_max": 100.0, "O2_exempt": 7500.0, "HHV": (10.7, 12.8)}
STAB = {"pH_min": 6.8, "VFA_max": 8.0, "VFA_margin": 6.0}
CRE = {"median": 129.6, "q1": 111.7, "q3": 146.0}

LABELS = {"maize_share": "Maize share of feed", "cive_share": "Cover-crop (CIVE) share", "feed_t_d": "Feed rate",
          "hrt_d": "Retention time (HRT)", "water_per_kNm3": "Scrubber water", "p_flash_bar": "Flash pressure",
          "k_dis": "Disintegration rate k_dis", "K_I_nh3": "Ammonia inhibition K_I,NH3"}
UNITS = {"maize_share": "%", "cive_share": "%", "feed_t_d": "t/d", "hrt_d": "d", "water_per_kNm3": "m³ per 1,000 Nm³",
         "p_flash_bar": "bar", "k_dis": "1/d", "K_I_nh3": "M"}


def load_surrogate() -> Surrogate:
    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"Trained surrogates not found at {MODEL_FILE}. "
                                "Run: python 05_code/step6b_surrogate.py")
    return Surrogate()


def assess(sur: Surrogate, design: pd.DataFrame, econ: Econ, econs: list[Econ] | None = None) -> pd.DataFrame:
    """design: columns = 6 design variables + k_dis + K_I_nh3. Returns surrogate outputs + TEA.
    econs: optional one Econ per row (Monte Carlo); otherwise econ is used for all rows."""
    df = design.reset_index(drop=True)
    p = sur.predict(df)
    hhv = HHV_CH4 * (1 - p.BM_CO2_pct / 100 - 2.7 * p.BM_O2_ppm / 1e6)
    drv = {"feed_t_d": df.feed_t_d, "maize_share": df.maize_share, "cive_share": df.cive_share,
           "V_liq_m3": df.feed_t_d * df.hrt_d, "raw_Nm3_h": p.biogas_dry_Nm3_h,
           "bm_Nm3_h": p.biomethane_Nm3_h, "hhv_kWh_Nm3": hhv, "P_el_upg_kW": p.P_el_upg_kW}
    out = pd.concat([df, p], axis=1)
    out["HHV"] = hhv
    keys = ["LCOE_EUR_MWh", "NPV_EUR", "capex_total", "ann_capex", "opex_total", "feed_cost", "el_cost",
            "fixed_om", "energy_MWh_yr", "bm_net_Nm3_h", "el_share_of_energy"]
    if econs is None:
        t = evaluate(drv, econ)
        for k in keys:
            out[k] = np.asarray(t[k], float)
        for k, v in t["capex_breakdown"].items():
            out[f"capex_{k}"] = np.asarray(v, float)
    else:
        rows = []
        for i, e in enumerate(econs):
            t = evaluate({k: (np.asarray(v)[i] if hasattr(v, "__len__") else v) for k, v in drv.items()}, e)
            rows.append({k: float(t[k]) for k in keys})
        out = pd.concat([out, pd.DataFrame(rows)], axis=1)
    return out


def single(sur: Surrogate, x: dict, econ: Econ) -> dict:
    return assess(sur, pd.DataFrame([x]), econ).iloc[0].to_dict()


# ------------------------------------------------------------------ Monte Carlo (as step 7c) ---
def monte_carlo(sur: Surrogate, x: dict, base: Econ, n: int = 2000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    lu = lambda lo, hi: np.exp(rng.uniform(np.log(lo), np.log(hi), n))
    df = pd.DataFrame([{k: x[k] for k in BOUNDS}] * n).assign(k_dis=lu(0.05, 0.5), K_I_nh3=lu(0.0012, 0.0084))
    samp = pd.DataFrame({
        "capex_factor": base.capex_factor * rng.triangular(0.8, 1.0, 1.25, n),
        "cost_cive": base.cost_cive * rng.uniform(0.7, 1.3, n), "cost_maize": base.cost_maize * rng.uniform(0.7, 1.3, n),
        "cost_slurry": rng.uniform(7.3, 43.2, n), "el_price": rng.uniform(120, 202, n),
        "other_opex_per_MWh": base.other_opex_per_MWh * rng.triangular(0.8, 1.0, 1.2, n),
        "tariff": rng.uniform(111, 169, n), "discount": rng.uniform(0.05, 0.09, n),
        "heat_selfuse_frac": rng.uniform(0.02, 0.06, n)})
    econs = [replace(base, **r) for r in samp.to_dict("records")]
    a = assess(sur, df, base, econs=econs)
    return pd.concat([a, samp.add_prefix("mc_")], axis=1)


def tornado(sur: Surrogate, x: dict, base: Econ) -> tuple[float, pd.DataFrame]:
    def lc(xx=None, **kw):
        r = single(sur, xx or x, replace(base, **kw))
        return r["LCOE_EUR_MWh"]
    lc0 = lc()
    cases = {"Slurry cost (7.3 / 43.2 €/t)": ({"cost_slurry": 7.3}, {"cost_slurry": 43.2}),
             "CAPEX (×0.8 / ×1.25)": ({"capex_factor": base.capex_factor * 0.8}, {"capex_factor": base.capex_factor * 1.25}),
             "CIVE cost (−30 / +30 %)": ({"cost_cive": base.cost_cive * 0.7}, {"cost_cive": base.cost_cive * 1.3}),
             "Maize cost (−30 / +30 %)": ({"cost_maize": base.cost_maize * 0.7}, {"cost_maize": base.cost_maize * 1.3}),
             "Electricity (120 / 202 €/MWh)": ({"el_price": 120.0}, {"el_price": 202.0}),
             "Other OPEX (−20 / +20 %)": ({"other_opex_per_MWh": base.other_opex_per_MWh * 0.8},
                                         {"other_opex_per_MWh": base.other_opex_per_MWh * 1.2}),
             "Discount rate (5 / 9 %)": ({"discount": 0.05}, {"discount": 0.09}),
             "Heat self-use (2 / 6 %)": ({"heat_selfuse_frac": 0.02}, {"heat_selfuse_frac": 0.06})}
    rows = [{"input": k, "low": lc(**lo), "high": lc(**hi)} for k, (lo, hi) in cases.items()]
    for name, key, lo, hi in (("k_dis (0.05 / 0.5 1/d)", "k_dis", 0.05, 0.5),
                              ("K_I,NH3 (0.0012 / 0.0084 M)", "K_I_nh3", 0.0012, 0.0084)):
        rows.append({"input": name, "low": lc({**x, key: lo}), "high": lc({**x, key: hi})})
    t = pd.DataFrame(rows)
    t["swing"] = (t.high - t.low).abs()
    return lc0, t.sort_values("swing")


# ------------------------------------------------------------------------ saved results -------
def _j(p: str) -> dict:
    return json.loads((RESULTS / p).read_text(encoding="utf-8"))


def saved_results() -> dict:
    return {"opt": _j("step7_tea/optimisation.json"), "unc": _j("step7_tea/uncertainty.json"),
            "rob": _j("step7_tea/robust_design.json"), "tea": _j("step7_tea/tea_base.json"),
            "bsm2": _j("step4_adm1/bsm2_validation_summary.json"), "speed": _j("step6_surrogate/speed.json"),
            "metrics": pd.read_csv(RESULTS / "step6_surrogate/metrics.csv"),
            "over": pd.read_csv(RESULTS / "step6_surrogate/overfitting_check.csv")}


def presets(res: dict) -> dict[str, dict]:
    """Named designs: base case (steps 4-5), verified optima (step 7b), naive and robust (7c, 7e)."""
    base = {"maize_share": 0.15, "cive_share": 0.25, "feed_t_d": 88.44, "hrt_d": 60.0, "water_per_kNm3": 130.0,
            "p_flash_bar": 3.5}
    out = {"Base case (88 t/d, HRT 60 d)": base}
    for k in ("150", "200", "250", "300"):
        f = res["opt"][k]["final"]
        if f:
            out[f"Verified optimum · {k} Nm³/h"] = {kk: float(f["design"][kk]) for kk in BOUNDS}
    out["Naive scale-up · 200 Nm³/h"] = {kk: float(v) for kk, v in
                                         res["unc"]["comparison_200"]["naive_scaled_base"]["design"].items()}
    if res["rob"]["final"]:
        out["Robust design · 200 Nm³/h"] = {kk: float(res["rob"]["final"]["design"][kk]) for kk in BOUNDS}
    return out
