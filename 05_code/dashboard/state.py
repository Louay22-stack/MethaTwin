"""MethaTwin - application state shared by every page.

Holds the design inputs (session state), the named reference designs, saved scenarios, and
cached evaluations. All numbers come from core.py (surrogates + TEA); nothing is computed here.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace

import pandas as pd
import streamlit as st

import core
from methatwin.tea import Econ

E0 = Econ()
DEFAULT_PRESET = "Verified optimum · 200 Nm³/h"
KD_OPTS = [0.05, 0.06, 0.075, 0.1, 0.13, 0.16, 0.2, 0.25, 0.32, 0.4, 0.5]
KI_OPTS = [0.0012, 0.0014, 0.0016, 0.0018, 0.0022, 0.0027, 0.0033, 0.0041, 0.005, 0.0062, 0.0075, 0.0084]
ECON_DEFAULTS = {"tariff": 152.8, "slurry": 7.3, "cive_cost": round(E0.cost_cive, 1), "maize_cost": round(E0.cost_maize, 1),
                 "el": 120.0, "capexf": 1.0, "disc": 7.0}
KIN_DEFAULTS = {"kdis": 0.1, "ki": 0.0018}
DESIGN_KEYS = {"maize_pct": "maize_share", "cive_pct": "cive_share", "feed": "feed_t_d", "hrt": "hrt_d",
               "water": "water_per_kNm3", "pflash": "p_flash_bar"}
TOL = {"maize_share": 0.006, "cive_share": 0.006, "feed_t_d": 0.6, "hrt_d": 0.6, "water_per_kNm3": 0.6, "p_flash_bar": 0.03}


@st.cache_resource(show_spinner="Loading ML surrogates (first start only)…")
def sur():
    return core.load_surrogate()


@st.cache_data(show_spinner=False)
def res() -> dict:
    return core.saved_results()


@st.cache_data(show_spinner=False)
def presets() -> dict:
    return core.presets(res())


# ------------------------------------------------------------------ inputs ---
def _design_to_state(x: dict) -> dict:
    return {"maize_pct": round(100 * x["maize_share"], 1), "cive_pct": round(100 * x["cive_share"], 1),
            "feed": round(x["feed_t_d"], 1), "hrt": round(x["hrt_d"], 1), "water": round(x["water_per_kNm3"], 1),
            "pflash": round(x["p_flash_bar"], 2)}


def apply_preset(name: str | None = None) -> None:
    name = name or st.session_state.preset
    st.session_state.preset = name
    st.session_state.update(_design_to_state(presets()[name]))


def reset_all() -> None:
    st.session_state.preset = DEFAULT_PRESET
    apply_preset(DEFAULT_PRESET)
    st.session_state.update({**KIN_DEFAULTS, **ECON_DEFAULTS})


def init() -> None:
    if "preset" not in st.session_state:
        reset_all()
    st.session_state.setdefault("scenarios", {})


def design() -> dict:
    s = st.session_state
    return {"maize_share": s.maize_pct / 100, "cive_share": s.cive_pct / 100, "feed_t_d": s.feed, "hrt_d": s.hrt,
            "water_per_kNm3": s.water, "p_flash_bar": s.pflash, "k_dis": s.kdis, "K_I_nh3": s.ki}


def econ_inputs() -> dict:
    return {k: st.session_state[k] for k in ECON_DEFAULTS}


def econ(e: dict | None = None) -> Econ:
    e = e or econ_inputs()
    return replace(E0, tariff=e["tariff"], cost_slurry=e["slurry"], cost_cive=e["cive_cost"], cost_maize=e["maize_cost"],
                   el_price=e["el"], capex_factor=e["capexf"], discount=e["disc"] / 100)


def fingerprint(x: dict | None = None, e: dict | None = None) -> str:
    payload = json.dumps({"x": x or design(), "e": e or econ_inputs()}, sort_keys=True)
    return hashlib.sha1(payload.encode()).hexdigest()[:10]


@st.cache_data(show_spinner=False, max_entries=512)
def _evaluate(xj: str, ej: str) -> dict:
    x, e = json.loads(xj), json.loads(ej)
    return core.single(sur(), x, econ(e))


def evaluate(x: dict | None = None, e: dict | None = None) -> dict:
    return _evaluate(json.dumps(x or design(), sort_keys=True), json.dumps(e or econ_inputs(), sort_keys=True))


def modified_groups() -> dict:
    """Which input groups differ from the selected reference design and default market / kinetics."""
    s, ref = st.session_state, presets()[st.session_state.preset]
    x = design()
    return {"design": any(abs(x[k] - ref[k]) > TOL[k] for k in TOL),
            "kinetics": any(abs(s[k] - v) > 1e-12 for k, v in KIN_DEFAULTS.items()),
            "market": any(abs(s[k] - v) > 1e-9 for k, v in ECON_DEFAULTS.items())}


def matches_reference() -> str | None:
    m = modified_groups()
    return None if any(m.values()) else st.session_state.preset


def full_sim(name: str) -> dict | None:
    r = res()
    if name.startswith("Verified optimum"):
        return r["opt"][name.split("· ")[1].split(" ")[0]]["final"]["simulation"]
    if name.startswith("Naive"):
        return r["unc"]["comparison_200"]["naive_scaled_base"]["simulation"]
    if name.startswith("Robust"):
        return r["rob"]["robust_design_at_nominal_kinetics"]
    if name.startswith("Base"):
        b = r["tea"]["results"]["base_case"]
        return {"bm_net_Nm3_h": b["bm_net_Nm3_h"], "LCOE_EUR_MWh": b["LCOE_EUR_MWh"], "NPV_EUR": b["NPV_EUR"]}
    return None


# --------------------------------------------------------------- scenarios ---
def save_scenario(name: str) -> None:
    st.session_state.scenarios[name] = {"x": design(), "e": econ_inputs(), "preset": st.session_state.preset}


def load_scenario(name: str) -> None:
    sc = st.session_state.scenarios[name]
    st.session_state.update(_design_to_state(sc["x"]))
    st.session_state.update({"kdis": sc["x"]["k_dis"], "ki": sc["x"]["K_I_nh3"], **sc["e"]})
    st.session_state.preset = sc["preset"]


def scenario_table() -> pd.DataFrame:
    rows = []
    for name, sc in st.session_state.scenarios.items():
        r = evaluate(sc["x"], sc["e"])
        x = sc["x"]
        rows.append({"Scenario": name, "Biomethane (Nm³/h)": r["bm_net_Nm3_h"], "LCOE (€/MWh)": r["LCOE_EUR_MWh"],
                     "NPV (M€)": r["NPV_EUR"] / 1e6, "P(stable)": r["p_stable"], "CO₂ (%)": r["BM_CO2_pct"],
                     "VFA (g/L)": r["VFA_gCOD_L"], "Feed (t/d)": x["feed_t_d"], "HRT (d)": x["hrt_d"],
                     "Maize (%)": 100 * x["maize_share"], "CIVE (%)": 100 * x["cive_share"],
                     "Water (m³/kNm³)": x["water_per_kNm3"], "Flash (bar)": x["p_flash_bar"],
                     "k_dis": x["k_dis"], "K_I,NH3": x["K_I_nh3"], "Tariff (€/MWh)": sc["e"]["tariff"],
                     "Slurry (€/t)": sc["e"]["slurry"]})
    return pd.DataFrame(rows)


def econ_dict() -> dict:
    return asdict(econ())
