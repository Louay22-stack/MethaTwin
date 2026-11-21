"""
methatwin.tea - Techno-economic model of the biomethane plant (EUR 2023).

Main source: CRE (Dec 2024), "Bilan technique et economique des installations de production
de biomethane injecte (hors STEP et ISDND)", 2023 data  [S17 in sources.md]:
  * specific CAPEX of autonomous agricultural plants 44,456 EUR per Nm3/h of capacity,
    average plant 8.16 MEUR (=> ~184 Nm3/h); economies of scale below 300 Nm3/h of
    -700 to -1,200 EUR/(Nm3/h) per +10 Nm3/h  -> implied scaling exponent n ~ 0.61
  * agricultural CAPEX shares: digesters & annexes 28 %, upgrading 20 %, construction 17 %,
    inputs treatment 7 %, materials handling 5 %, digestate treatment 5 %, electrical 3 %,
    grid connection 3 %, technical building 2 %, development 2 %, injection 2 %, gas equipment 1 %,
    financial/legal 1 %, other 3 %
  * average OPEX 1.02 MEUR/yr; electricity use 9.2 % of the energy produced; fixed electricity
    tariff median 120 EUR/MWh; biogas self-consumption for heat median 3.5 %
  * feed costs (acquisition + transport) CIVE 32.5 + 7.1, main crops 27.9 + 7.8,
    livestock effluents 35.9 + 7.3 EUR/t
  * discount rate 7 %, 15 years; LCOE median 129.6 EUR/MWh (HHV), Q1 111.7, Q3 146.0
  * purchase tariff (arrete BI 2023) agricultural 111-169 EUR/MWh, weighted average 152.8
Method (assumptions marked A#, all listed in LOG.md step 7):
  A1 CAPEX by component, each scaled with its own driver and exponent 0.6 (six-tenths rule,
     consistent with the CRE economies of scale), anchored on a reference plant of 184 Nm3/h
     built with the MethaTwin base design (HRT 60 d, base blend, see reference_plant()).
       digester-linked (digesters 28 + construction 17)      -> digester volume
       upgrading (20)                                         -> raw biogas flow
       feed-linked (inputs 7 + handling 5 + digestate 5)      -> feed tonnage
       capacity-linked (grid 3, electrical 3, building 2, development 2, injection 2,
         gas equipment 1, financial 1, other 3 = 17)          -> biomethane capacity
     (the four groups sum to 99 % in the CRE breakdown and are renormalised to 100 %)
  A2 slurry: transport only (7.3 EUR/t); the CRE effluent acquisition price is a sensitivity
  A3 electricity: scrubber power from the DWSIM model + other plant uses = 6 % of the energy
     produced (so that the reference plant matches the CRE average of 9.2 %)
  A4 heat: 3.5 % of the biomethane production self-consumed (CRE median)
  A5 other OPEX (materials handling 7.65, maintenance 6.76, injection 4.44, personnel 4.11,
     transport & other energy 3.95, insurance 1.87, consumables 1.68, other 1.28, management 0.86,
     taxes 0.04) = 32.64 EUR/MWh injected: CRE medians for autonomous agricultural plants (2022 EUR,
     p. 72). A first attempt to back-calculate a fixed O&M % from the CRE average OPEX gave a
     negative value (feed + electricity alone exceeded it), so it was abandoned (LOG.md step 7).
  A6 8,400 h/yr operation; HHV of biomethane from the DWSIM result; digestate value and
     CO2 revenue = 0 in the base case (CO2 is a scenario)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Econ:
    spec_capex_ref: float = 44_456.0        # EUR/(Nm3/h), CRE agri autonomous
    cap_ref_Nm3h: float = 184.0             # CRE average plant (8.16 MEUR / 44,249)
    n_scale: float = 0.6
    capex_factor: float = 1.0               # multiplier for uncertainty
    share_digester: float = 0.45
    share_upgrading: float = 0.20
    share_feed: float = 0.17
    share_capacity: float = 0.17            # shares renormalised to sum 1 (CRE total 99 %)
    cost_slurry: float = 7.3                # EUR/t (A2)
    cost_cive: float = 32.5 + 7.1
    cost_maize: float = 27.9 + 7.8
    el_price: float = 120.0                 # EUR/MWh
    el_other_frac: float = 0.06             # A3
    heat_selfuse_frac: float = 0.035        # A4
    other_opex_per_MWh: float = 32.64       # A5, CRE p. 72
    tariff: float = 152.8                   # EUR/MWh HHV
    co2_net_value: float = 0.0              # EUR/t biogenic CO2 sold (scenario)
    discount: float = 0.07
    years: int = 15
    hours: float = 8400.0


def crf(i: float, n: int) -> float:
    return i * (1 + i) ** n / ((1 + i) ** n - 1)


# Reference plant drivers (MethaTwin base design scaled to the CRE average 184 Nm3/h):
# base design 88.44 t/d, HRT 60 d, V 5,306 m3, raw gas 233 Nm3/h -> 133.4 Nm3/h biomethane;
# scale factor 184/133.4.
_K = 184.0 / 133.4
REF = {"V_liq_m3": 5306.4 * _K, "raw_Nm3_h": 233.0 * _K, "feed_t_d": 88.44 * _K, "bm_Nm3_h": 184.0}


def capex(p: dict, e: Econ) -> dict:
    """CAPEX by component (EUR). p needs V_liq_m3, raw_Nm3_h, feed_t_d, bm_Nm3_h."""
    total_ref = e.spec_capex_ref * e.cap_ref_Nm3h
    s = np.array([e.share_digester, e.share_upgrading, e.share_feed, e.share_capacity])
    s = s / s.sum()
    drivers = ["V_liq_m3", "raw_Nm3_h", "feed_t_d", "bm_Nm3_h"]
    names = ["digester", "upgrading", "feed_handling", "capacity_linked"]
    out = {nm: e.capex_factor * total_ref * sh * (np.asarray(p[d]) / REF[d]) ** e.n_scale
           for nm, sh, d in zip(names, s, drivers)}
    out["total"] = sum(out[nm] for nm in names)
    return out


def evaluate(p: dict, e: Econ) -> dict:
    """LCOE, NPV and breakdown. Works with scalars or numpy arrays.
    p: feed_t_d, maize_share, cive_share, V_liq_m3, raw_Nm3_h, bm_Nm3_h (dry, before self-use),
       hhv_kWh_Nm3, P_el_upg_kW, co2_t_yr (optional)."""
    cx = capex(p, e)
    bm_gross = np.asarray(p["bm_Nm3_h"], float)
    bm_net = bm_gross * (1 - e.heat_selfuse_frac)                      # A4
    energy_MWh = bm_net * np.asarray(p["hhv_kWh_Nm3"], float) * e.hours / 1000.0
    gross_MWh = bm_gross * np.asarray(p["hhv_kWh_Nm3"], float) * e.hours / 1000.0
    feed_t = np.asarray(p["feed_t_d"], float) * 365.0
    ms, cs = np.asarray(p["maize_share"], float), np.asarray(p["cive_share"], float)
    feed_cost = feed_t * (ms * e.cost_maize + cs * e.cost_cive + (1 - ms - cs) * e.cost_slurry)
    el_MWh = np.asarray(p["P_el_upg_kW"], float) * e.hours / 1000.0 + e.el_other_frac * gross_MWh
    el_cost = el_MWh * e.el_price
    fom = e.other_opex_per_MWh * energy_MWh
    co2_rev = e.co2_net_value * np.asarray(p.get("co2_t_yr", 0.0), float)
    opex = feed_cost + el_cost + fom
    ann_capex = cx["total"] * crf(e.discount, e.years)
    lcoe = (ann_capex + opex - co2_rev) / energy_MWh
    annual_cash = e.tariff * energy_MWh + co2_rev - opex
    npv = -cx["total"] + annual_cash / crf(e.discount, e.years)
    return {"capex_total": cx["total"], "capex_breakdown": cx, "ann_capex": ann_capex,
            "feed_cost": feed_cost, "el_cost": el_cost, "fixed_om": fom, "opex_total": opex,
            "co2_revenue": co2_rev, "energy_MWh_yr": energy_MWh, "el_share_of_energy": el_MWh / gross_MWh,
            "LCOE_EUR_MWh": lcoe, "NPV_EUR": npv, "bm_net_Nm3_h": bm_net}
