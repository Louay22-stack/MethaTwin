"""
Phase 3, step 2 - Day-1 test: can Python 3.14 drive DWSIM 10?

Test case (sized for the MethaTwin reference plant)
--------------------------------------------------
Raw biogas, 55 mol% CH4 / 45 mol% CO2, 360 Nm3/h, 35 degC, 1.01325 bar
-> single-stage compressor to 10 bar(a), adiabatic efficiency 75 %
   (10 bar is in the typical feed-pressure range for water scrubbing; L7, L8).
Why 360 Nm3/h: ~200 Nm3/h of biomethane (definition PDF, section 4) at ~97 % CH4
needs 200*0.97/0.55 ~ 353 Nm3/h of raw gas at 55 % CH4; rounded to 360.

What is checked
---------------
1. Python can create a flowsheet, add compounds, a property package (Peng-Robinson),
   a stream, a compressor and an energy stream, connect and solve them.
2. Mass balance: inlet mass flow == outlet mass flow.
3. Compressor power and outlet temperature vs an independent hand calculation:
   ideal-gas isentropic compression with NIST Shomate heat capacities.
   Real-gas effects at 10 bar should keep the difference within a few percent.

Run from the project root:  python 05_code/step2_dwsim_smoke_test.py
Writes: 04_models_and_simulations/step2_smoke_test/{results.json, smoke_test.dwxmz}
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dwsim_bridge import load_dwsim  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step2_smoke_test"

# ---- Case definition --------------------------------------------------------
Y_CH4, Y_CO2 = 0.55, 0.45
FLOW_NM3H = 360.0                 # Nm3/h at 0 degC, 1.01325 bar
V_MOLAR_NORMAL = 22.414e-3        # m3/mol, ideal gas at 0 degC, 1 atm
T_IN = 35.0 + 273.15              # K (mesophilic digester gas)
P_IN = 101325.0                   # Pa
P_OUT = 10.0e5                    # Pa
ETA_AD = 0.75                     # adiabatic (isentropic) efficiency
R = 8.314462618                   # J/(mol K)
M = {"CH4": 16.043e-3, "CO2": 44.010e-3}  # kg/mol

# NIST Chemistry WebBook, gas-phase Shomate parameters (298-1300 K)
# CH4: https://webbook.nist.gov/cgi/cbook.cgi?ID=C74828&Mask=1
# CO2: https://webbook.nist.gov/cgi/cbook.cgi?ID=C124389&Mask=1
SHOMATE = {
    "CH4": (-0.703029, 108.4773, -42.52157, 5.862788, 0.678565),
    "CO2": (24.99735, 55.18696, -33.69137, 7.948387, -0.136638),
}


def cp_ig(T: float) -> float:
    """Ideal-gas molar heat capacity of the mixture, J/(mol K)."""
    t = T / 1000.0
    def one(c):
        A, B, C, D, E = c
        return A + B * t + C * t**2 + D * t**3 + E / t**2
    return Y_CH4 * one(SHOMATE["CH4"]) + Y_CO2 * one(SHOMATE["CO2"])


def hand_calculation(n_mol_s: float) -> dict:
    """Ideal-gas isentropic compression with T-dependent cp."""
    # Isentropic: integral(cp/T dT) from T1 to T2s = R ln(P2/P1)
    target = R * np.log(P_OUT / P_IN)
    f = lambda T2: quad(lambda T: cp_ig(T) / T, T_IN, T2)[0] - target
    T2s = brentq(f, T_IN, 900.0)
    w_s = quad(cp_ig, T_IN, T2s)[0]          # J/mol, isentropic work
    w = w_s / ETA_AD                          # J/mol, actual work
    T2 = brentq(lambda T2: quad(cp_ig, T_IN, T2)[0] - w, T_IN, 1000.0)
    return {"T2s_C": T2s - 273.15, "T2_C": T2 - 273.15, "power_kW": n_mol_s * w / 1000.0}


def run_dwsim(n_mol_s: float) -> dict:
    dw = load_dwsim()
    interf = dw.Automation3()
    sim = interf.CreateFlowsheet()
    for c in ["Methane", "Carbon dioxide"]:
        sim.AddCompound(c)
    sim.CreateAndAddPropertyPackage("Peng-Robinson (PR)")

    feed = sim.AddObject(dw.ObjectType.MaterialStream, 50, 50, "BIOGAS").GetAsObject()
    k101 = sim.AddObject(dw.ObjectType.Compressor, 150, 50, "K-101").GetAsObject()
    out = sim.AddObject(dw.ObjectType.MaterialStream, 250, 50, "BIOGAS-HP").GetAsObject()
    pwr = sim.AddObject(dw.ObjectType.EnergyStream, 150, 120, "W-K101").GetAsObject()
    sim.ConnectObjects(feed.GraphicObject, k101.GraphicObject, -1, -1)
    sim.ConnectObjects(k101.GraphicObject, out.GraphicObject, -1, -1)
    sim.ConnectObjects(pwr.GraphicObject, k101.GraphicObject, -1, -1)

    feed.SetOverallComposition(dw.System.Array[float]([Y_CH4, Y_CO2]))
    feed.SetTemperature(T_IN)
    feed.SetPressure(P_IN)
    feed.SetMolarFlow(n_mol_s)

    from DWSIM.UnitOperations.UnitOperations import Compressor  # type: ignore
    k101.CalcMode = Compressor.CalculationMode.OutletPressure
    k101.POut = P_OUT
    # DWSIM expects the efficiency in PERCENT (default 75.0), not as a fraction.
    # Passing 0.75 silently gives 0.75 % -> 100x power (caught by the hand calc).
    k101.AdiabaticEfficiency = ETA_AD * 100.0

    t0 = time.perf_counter()
    errors = interf.CalculateFlowsheet2(sim)
    dt = time.perf_counter() - t0
    err_list = [str(e) for e in errors] if errors is not None else []

    OUT.mkdir(parents=True, exist_ok=True)
    try:
        interf.SaveFlowsheet(sim, str(OUT / "smoke_test.dwxmz"), True)
        saved = True
    except Exception as exc:  # saving is a convenience, not part of the test
        saved = f"failed: {exc}"

    return {
        "errors": err_list,
        "solve_time_s": dt,
        "saved_flowsheet": saved,
        "T_out_C": out.GetTemperature() - 273.15,
        "P_out_bar": out.GetPressure() / 1e5,
        "power_kW": k101.DeltaQ,
        "mass_in_kg_h": feed.GetMassFlow() * 3600,
        "mass_out_kg_h": out.GetMassFlow() * 3600,
    }


def main() -> None:
    n = FLOW_NM3H / 3600.0 / V_MOLAR_NORMAL           # mol/s
    m_hand = n * (Y_CH4 * M["CH4"] + Y_CO2 * M["CO2"]) * 3600  # kg/h
    hand = hand_calculation(n)
    dws = run_dwsim(n)

    mb_err = abs(dws["mass_out_kg_h"] - dws["mass_in_kg_h"]) / dws["mass_in_kg_h"] * 100
    res = {
        "case": {"flow_Nm3_h": FLOW_NM3H, "molar_flow_mol_s": n, "y_CH4": Y_CH4,
                 "T_in_C": T_IN - 273.15, "P_in_bar": P_IN / 1e5, "P_out_bar": P_OUT / 1e5,
                 "eta_adiabatic": ETA_AD, "property_package": "Peng-Robinson (PR)"},
        "dwsim": dws,
        "hand_calc_ideal_gas": {**hand, "mass_flow_kg_h": m_hand},
        "checks": {
            "mass_balance_error_pct": mb_err,
            "feed_mass_flow_vs_hand_pct": (dws["mass_in_kg_h"] - m_hand) / m_hand * 100,
            "power_dev_pct": (dws["power_kW"] - hand["power_kW"]) / hand["power_kW"] * 100,
            "T_out_dev_K": dws["T_out_C"] - hand["T2_C"],
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
