"""
Phase 3, step 5a - Gas solubility in water: test DWSIM property packages, then fit
Peng-Robinson gas-water kij to Henry's law.

Water scrubbing works because CO2 is ~25x more soluble in water than CH4, so the
thermodynamics must reproduce Henry's law before any column is built.

Part 1 - default packages: flash water + CO2 + CH4 at 9 bar, 10 and 25 degC.
Part 2 - fit kij(gas, water) for CO2, CH4, O2, N2 at 12.5 degC, 9 bar (binary flashes).
         A constant kij cannot follow the T-dependence (tested at 15 degC: -26 % at 5 degC,
         +46 % at 25 degC), so the fit is centred on the water-loop design window 10-15 degC.
Part 3 - verify the fitted PR on 5-25 degC.
k_H,model = m_gas / p_gas with m = x_gas/(x_water * 0.018015) mol/kg and p = y_gas * P.
References and constants: see methatwin/dwsim_thermo.py.
Acceptance (part 3): within +/-15 % inside the 10-15 degC validity window (scatter between literature sources ~10 %).
DWSIM note: kij are cached at the first flash, so they must be set before any calculation.

Run from the project root:  python 05_code/step5a_thermo_check.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dwsim_bridge import load_dwsim  # noqa: E402
from methatwin.dwsim_thermo import HENRY, KIJ_FILE, k_henry, set_kij  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "04_models_and_simulations" / "step5_upgrading"
P_BAR = 9.0
DEFAULT_PACKAGES = ["Peng-Robinson (PR)", "Soave-Redlich-Kwong (SRK)", "Peng-Robinson 1978 (PR78) Advanced",
                    "Soave-Redlich-Kwong (SRK) Advanced", "Peng-Robinson-Stryjek-Vera 2 (PRSV2-M)", "NRTL"]
GAS_FEED = {"CO2": 0.05, "CH4": 0.03, "O2": 0.03, "N2": 0.03}  # gas mole fraction in binary feed

dw = load_dwsim()
interf = dw.Automation3()


def kh_model(gases: list[str], feed: list[float], T: float, package: str, kij: dict | None = None) -> dict:
    """Flash water + gases; return model Henry constant of each gas (mol/(kg bar))."""
    sim = interf.CreateFlowsheet()
    names = [HENRY[g][2] for g in gases] + ["Water"]
    for c in names:
        sim.AddCompound(c)
    pp = sim.CreateAndAddPropertyPackage(package)
    for g, v in (kij or {}).items():          # must happen before the first flash
        set_kij(pp, HENRY[g][2], "Water", v)
    s = sim.AddObject(dw.ObjectType.MaterialStream, 0, 0, "S").GetAsObject()
    s.SetOverallComposition(dw.System.Array[float](feed + [1.0 - sum(feed)]))
    s.SetTemperature(T)
    s.SetPressure(P_BAR * 1e5)
    s.SetMolarFlow(1.0)
    interf.CalculateFlowsheet2(sim)
    xw = s.Phases[3].Compounds["Water"].MoleFraction
    out = {}
    for g in gases:
        x = s.Phases[3].Compounds[HENRY[g][2]].MoleFraction
        y = s.Phases[2].Compounds[HENRY[g][2]].MoleFraction
        out[g] = x / (xw * 0.018015) / (y * P_BAR)
    return out


def part1_defaults() -> pd.DataFrame:
    rows = []
    for pp in DEFAULT_PACKAGES:
        for tc in (10.0, 25.0):
            T = tc + 273.15
            r = kh_model(["CH4", "CO2"], [0.004, 0.016], T, pp)
            rows.append({"package": pp, "T_C": tc,
                         "err_CO2_pct": (r["CO2"] / k_henry("CO2", T) - 1) * 100,
                         "err_CH4_pct": (r["CH4"] / k_henry("CH4", T) - 1) * 100,
                         "selectivity_model": r["CO2"] / max(r["CH4"], 1e-30),
                         "selectivity_ref": k_henry("CO2", T) / k_henry("CH4", T)})
    return pd.DataFrame(rows)


def part2_fit(T_fit: float = 285.65) -> dict:
    kij = {}
    for g, yf in GAS_FEED.items():
        target = k_henry(g, T_fit)
        f = lambda k: kh_model([g], [yf], T_fit, "Peng-Robinson (PR)", {g: k})[g] / target - 1.0
        kij[g] = brentq(f, -0.9, 0.5, xtol=1e-5)
        print(f"  fitted kij({g}, water) = {kij[g]:+.5f}")
    return kij


def part3_verify(kij: dict) -> pd.DataFrame:
    rows = []
    for tc in (5.0, 10.0, 15.0, 20.0, 25.0):
        T = tc + 273.15
        gases = ["CH4", "CO2", "N2", "O2"]
        r = kh_model(gases, [0.01, 0.03, 0.005, 0.005], T, "Peng-Robinson (PR)", kij)  # multicomponent check
        row = {"T_C": tc}
        for g in gases:
            row[f"err_{g}_pct"] = (r[g] / k_henry(g, T) - 1) * 100
        row["selectivity_model"] = r["CO2"] / r["CH4"]
        row["selectivity_ref"] = k_henry("CO2", T) / k_henry("CH4", T)
        rows.append(row)
    df = pd.DataFrame(rows)
    df["in_validity_window"] = df.T_C.between(10.0, 15.0)
    df["pass"] = df[[c for c in df if c.startswith("err_")]].abs().max(axis=1) <= 15.0
    return df


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 220, "display.max_columns", 20)
    d1 = part1_defaults()
    d1.to_csv(OUT / "thermo_check_defaults.csv", index=False)
    print("Part 1 - default packages\n", d1.round(2).to_string(index=False))
    print("Part 2 - fitting kij at 12.5 degC, 9 bar")
    kij = part2_fit()
    KIJ_FILE.write_text(json.dumps({"kij": kij, "T_fit_K": 285.65, "validity_window_C": [10.0, 15.0], "P_bar": P_BAR,
                                    "package": "Peng-Robinson (PR)", "note": "gas-water kij fitted to Henry's law, "
                                    "see methatwin/dwsim_thermo.py for references"}, indent=2), encoding="utf-8")
    d3 = part3_verify(kij)
    d3.to_csv(OUT / "thermo_check_fitted.csv", index=False)
    print("Part 3 - fitted PR, multicomponent, 5-25 degC\n", d3.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
