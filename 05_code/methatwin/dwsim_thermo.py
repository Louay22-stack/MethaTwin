"""
methatwin.dwsim_thermo - Peng-Robinson package for biogas/water systems with
gas-water binary interaction parameters (kij) fitted to Henry's law.

Why: DWSIM's default PR kij give essentially zero CH4 solubility (kij = 0.5 placeholder)
and under-predict CO2 solubility (kij = -0.12155); N2-H2O and O2-H2O have no value.
See 05_code/step5a_thermo_check.py and LOG.md (step 5).

Reference Henry's law constants (molality / partial pressure, mol/(kg bar)),
van 't Hoff form k_H(T) = k_H0 * exp(B (1/T - 1/298.15)):
    CO2 0.0336, 2400 K | O2 0.00128, 1700 K | N2 0.000602, 1300 K
        Sander (2023) compilation, Wikipedia "Henry's law" table (M/atm converted to mol/(kg bar))
    CH4 0.0014, 1700 K  NIST Chemistry WebBook (methane, Henry's law data)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ATM_PER_BAR = 1.0 / 1.01325
HENRY = {  # gas: (k_H0 in mol/(kg bar), B in K, DWSIM compound name)
    "CO2": (3.4e-2 * ATM_PER_BAR, 2400.0, "Carbon dioxide"),
    "CH4": (1.4e-3, 1700.0, "Methane"),
    "O2": (1.3e-3 * ATM_PER_BAR, 1700.0, "Oxygen"),
    "N2": (6.1e-4 * ATM_PER_BAR, 1300.0, "Nitrogen"),
}
KIJ_FILE = Path(__file__).resolve().parents[2] / "04_models_and_simulations" / "step5_upgrading" / "fitted_kij.json"


def k_henry(gas: str, T: float) -> float:
    k0, B, _ = HENRY[gas]
    return k0 * np.exp(B * (1.0 / T - 1.0 / 298.15))


def set_kij(pp, comp_a: str, comp_b: str, kij: float) -> None:
    """Set kij on a DWSIM PR package for both orderings (creates the entry if missing)."""
    impl = pp.__implementation__
    ip = impl.m_pr.InteractionParameters
    from DWSIM.Thermodynamics.PropertyPackages.Auxiliary import PR_IPData  # type: ignore
    from System.Collections.Generic import Dictionary  # type: ignore
    for a, b in [(comp_a, comp_b), (comp_b, comp_a)]:
        if not ip.ContainsKey(a):
            ip.Add(a, Dictionary[str, PR_IPData]())
        if ip[a].ContainsKey(b):
            ip[a][b].kij = kij
        else:
            d = PR_IPData()
            d.kij = kij
            ip[a].Add(b, d)


def load_fitted_kij() -> dict:
    return json.loads(KIJ_FILE.read_text(encoding="utf-8"))["kij"]


def create_pr_package(sim, kij: dict | None = None):
    """Add a Peng-Robinson package to `sim` and apply the fitted gas-water kij."""
    pp = sim.CreateAndAddPropertyPackage("Peng-Robinson (PR)")
    kij = kij if kij is not None else load_fitted_kij()
    for gas, value in kij.items():
        set_kij(pp, HENRY[gas][2], "Water", value)
    return pp
