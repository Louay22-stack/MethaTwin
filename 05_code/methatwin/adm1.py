"""
methatwin.adm1 - Anaerobic Digestion Model No. 1 (IWA ADM1) for one CSTR.

Implementation follows the IWA benchmark version:
    Rosen C., Jeppsson U. (2006). Aspects on ADM1 implementation within the BSM2
    framework. Lund University (IEA), report LUTEDX/(TEIE-7224)/1-35/(2006).
    Sections 3.2 (equations), 4 (DAE form) and 6 (parameters).

Design choices
--------------
* DAE form (report section 4): the acid-base speciation (VFA ions, HCO3-, NH3) and
  the H+ concentration are solved ALGEBRAICALLY at every call from the charge
  balance, instead of the six very stiff acid-base ODEs. 29 ODE states remain.
* pH inhibition: hydrogen-ion based Hill functions, as chosen for BSM2.
* Gas flow: q_gas = kp (P_gas - P_atm) P_gas/P_atm (BSM2 choice).
* Known typo: in the converted report text the carbon coefficient s5 reads "+Y_ac";
  the correct term (and the one required for carbon conservation) is "+Y_su*C_bac".

Units (as in ADM1): kg COD/m3, kmol C/m3, kmol N/m3, kmol/m3 (M), days, bar, m3.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, fsolve

STATE_NAMES = [
    "S_su", "S_aa", "S_fa", "S_va", "S_bu", "S_pro", "S_ac", "S_h2", "S_ch4", "S_IC", "S_IN", "S_I",
    "X_xc", "X_ch", "X_pr", "X_li", "X_su", "X_aa", "X_fa", "X_c4", "X_pro", "X_ac", "X_h2", "X_I",
    "S_cat", "S_an", "S_gas_h2", "S_gas_ch4", "S_gas_co2",
]
IDX = {n: i for i, n in enumerate(STATE_NAMES)}
N_LIQ = 26  # liquid states (everything except the 3 gas states)


@dataclass
class ADM1Params:
    """BSM2 benchmark parameter set (Rosen & Jeppsson 2006, section 6)."""
    # stoichiometry
    f_sI_xc: float = 0.1; f_xI_xc: float = 0.2; f_ch_xc: float = 0.2; f_pr_xc: float = 0.2; f_li_xc: float = 0.3
    N_xc: float = 0.0376 / 14; N_I: float = 0.06 / 14; N_aa: float = 0.007; N_bac: float = 0.08 / 14
    C_xc: float = 0.02786; C_sI: float = 0.03; C_ch: float = 0.0313; C_pr: float = 0.03; C_li: float = 0.022
    C_xI: float = 0.03; C_su: float = 0.0313; C_aa: float = 0.03; C_fa: float = 0.0217; C_bu: float = 0.025
    C_pro: float = 0.0268; C_ac: float = 0.0313; C_bac: float = 0.0313; C_va: float = 0.024; C_ch4: float = 0.0156
    f_fa_li: float = 0.95
    f_h2_su: float = 0.19; f_bu_su: float = 0.13; f_pro_su: float = 0.27; f_ac_su: float = 0.41
    f_h2_aa: float = 0.06; f_va_aa: float = 0.23; f_bu_aa: float = 0.26; f_pro_aa: float = 0.05; f_ac_aa: float = 0.40
    Y_su: float = 0.1; Y_aa: float = 0.08; Y_fa: float = 0.06; Y_c4: float = 0.06; Y_pro: float = 0.04
    Y_ac: float = 0.05; Y_h2: float = 0.06
    # biochemical kinetics (d-1, kg COD/m3, M)
    k_dis: float = 0.5; k_hyd_ch: float = 10.0; k_hyd_pr: float = 10.0; k_hyd_li: float = 10.0
    K_S_IN: float = 1e-4
    k_m_su: float = 30.0; K_S_su: float = 0.5
    k_m_aa: float = 50.0; K_S_aa: float = 0.3
    k_m_fa: float = 6.0; K_S_fa: float = 0.4; K_I_h2_fa: float = 5e-6
    k_m_c4: float = 20.0; K_S_c4: float = 0.2; K_I_h2_c4: float = 1e-5
    k_m_pro: float = 13.0; K_S_pro: float = 0.1; K_I_h2_pro: float = 3.5e-6
    k_m_ac: float = 8.0; K_S_ac: float = 0.15; K_I_nh3: float = 0.0018
    k_m_h2: float = 35.0; K_S_h2: float = 7e-6
    pH_UL_aa: float = 5.5; pH_LL_aa: float = 4.0
    pH_UL_ac: float = 7.0; pH_LL_ac: float = 6.0
    pH_UL_h2: float = 6.0; pH_LL_h2: float = 5.0
    k_dec: float = 0.02
    # physico-chemical
    R: float = 0.083145; T_base: float = 298.15; T_op: float = 308.15; P_atm: float = 1.013
    k_p: float = 5e4; k_La: float = 200.0
    # reactor
    V_liq: float = 3400.0; V_gas: float = 300.0

    # --- temperature-dependent constants (computed) ---
    def thermo(self) -> dict:
        R100 = self.R * 100.0
        dT = 1.0 / self.T_base - 1.0 / self.T_op
        return {
            "K_w": 1e-14 * np.exp(55900 / R100 * dT),
            "K_a_va": 10 ** -4.86, "K_a_bu": 10 ** -4.82, "K_a_pro": 10 ** -4.88, "K_a_ac": 10 ** -4.76,
            "K_a_co2": 10 ** -6.35 * np.exp(7646 / R100 * dT),
            "K_a_IN": 10 ** -9.25 * np.exp(51965 / R100 * dT),
            "p_gas_h2o": 0.0313 * np.exp(5290 * dT),
            "K_H_co2": 0.035 * np.exp(-19410 / R100 * dT),
            "K_H_ch4": 0.0014 * np.exp(-14240 / R100 * dT),
            "K_H_h2": 7.8e-4 * np.exp(-4180 / R100 * dT),
        }


def _hill_inhibition(S_H: float, ul: float, ll: float) -> float:
    n = 3.0 / (ul - ll)
    K = 10 ** (-(ul + ll) / 2.0)
    return K ** n / (S_H ** n + K ** n)


def speciation(y: np.ndarray, p: ADM1Params, th: dict) -> dict:
    """Solve the charge balance for S_H+ and return all ionic species."""
    S_va, S_bu, S_pro, S_ac = y[IDX["S_va"]], y[IDX["S_bu"]], y[IDX["S_pro"]], y[IDX["S_ac"]]
    S_IC, S_IN, S_cat, S_an = y[IDX["S_IC"]], y[IDX["S_IN"]], y[IDX["S_cat"]], y[IDX["S_an"]]

    def ions(S_H):
        return {
            "S_va_ion": th["K_a_va"] * S_va / (th["K_a_va"] + S_H),
            "S_bu_ion": th["K_a_bu"] * S_bu / (th["K_a_bu"] + S_H),
            "S_pro_ion": th["K_a_pro"] * S_pro / (th["K_a_pro"] + S_H),
            "S_ac_ion": th["K_a_ac"] * S_ac / (th["K_a_ac"] + S_H),
            "S_hco3": th["K_a_co2"] * S_IC / (th["K_a_co2"] + S_H),
            "S_nh3": th["K_a_IN"] * S_IN / (th["K_a_IN"] + S_H),
        }

    def charge(logH):
        S_H = 10.0 ** logH
        i = ions(S_H)
        S_nh4 = S_IN - i["S_nh3"]
        return (S_cat + S_nh4 + S_H - i["S_hco3"] - i["S_ac_ion"] / 64 - i["S_pro_ion"] / 112
                - i["S_bu_ion"] / 160 - i["S_va_ion"] / 208 - th["K_w"] / S_H - S_an)

    logH = brentq(charge, -14.0, 0.0, xtol=1e-14)
    S_H = 10.0 ** logH
    out = ions(S_H)
    out.update(S_H=S_H, pH=-logH, S_nh4=S_IN - out["S_nh3"], S_co2=S_IC - out["S_hco3"])
    return out


def rates(y: np.ndarray, p: ADM1Params, th: dict, sp: dict) -> dict:
    """Biochemical (rho 1-19) and gas-transfer (rho_T 8-10) rates."""
    g = lambda n: y[IDX[n]]
    S_H = sp["S_H"]
    I_pH_aa = _hill_inhibition(S_H, p.pH_UL_aa, p.pH_LL_aa)
    I_pH_ac = _hill_inhibition(S_H, p.pH_UL_ac, p.pH_LL_ac)
    I_pH_h2 = _hill_inhibition(S_H, p.pH_UL_h2, p.pH_LL_h2)
    I_IN_lim = 1.0 / (1.0 + p.K_S_IN / max(g("S_IN"), 1e-20))
    S_h2 = g("S_h2")
    I_h2_fa = 1.0 / (1.0 + S_h2 / p.K_I_h2_fa)
    I_h2_c4 = 1.0 / (1.0 + S_h2 / p.K_I_h2_c4)
    I_h2_pro = 1.0 / (1.0 + S_h2 / p.K_I_h2_pro)
    I_nh3 = 1.0 / (1.0 + sp["S_nh3"] / p.K_I_nh3)
    I5 = I_pH_aa * I_IN_lim; I7 = I5 * I_h2_fa; I8 = I5 * I_h2_c4; I10 = I5 * I_h2_pro
    I11 = I_pH_ac * I_IN_lim * I_nh3; I12 = I_pH_h2 * I_IN_lim

    S_va, S_bu = g("S_va"), g("S_bu")
    r = np.zeros(20)  # index 1..19 used
    r[1] = p.k_dis * g("X_xc")
    r[2] = p.k_hyd_ch * g("X_ch")
    r[3] = p.k_hyd_pr * g("X_pr")
    r[4] = p.k_hyd_li * g("X_li")
    r[5] = p.k_m_su * g("S_su") / (p.K_S_su + g("S_su")) * g("X_su") * I5
    r[6] = p.k_m_aa * g("S_aa") / (p.K_S_aa + g("S_aa")) * g("X_aa") * I5
    r[7] = p.k_m_fa * g("S_fa") / (p.K_S_fa + g("S_fa")) * g("X_fa") * I7
    r[8] = p.k_m_c4 * S_va / (p.K_S_c4 + S_va) * g("X_c4") * S_va / (S_bu + S_va + 1e-6) * I8
    r[9] = p.k_m_c4 * S_bu / (p.K_S_c4 + S_bu) * g("X_c4") * S_bu / (S_bu + S_va + 1e-6) * I8
    r[10] = p.k_m_pro * g("S_pro") / (p.K_S_pro + g("S_pro")) * g("X_pro") * I10
    r[11] = p.k_m_ac * g("S_ac") / (p.K_S_ac + g("S_ac")) * g("X_ac") * I11
    r[12] = p.k_m_h2 * S_h2 / (p.K_S_h2 + S_h2) * g("X_h2") * I12
    for j, n in zip(range(13, 20), ["X_su", "X_aa", "X_fa", "X_c4", "X_pro", "X_ac", "X_h2"]):
        r[j] = p.k_dec * g(n)

    RT = p.R * p.T_op
    p_h2 = g("S_gas_h2") * RT / 16.0
    p_ch4 = g("S_gas_ch4") * RT / 64.0
    p_co2 = g("S_gas_co2") * RT
    P_gas = p_h2 + p_ch4 + p_co2 + th["p_gas_h2o"]
    # Gas leaves the headspace at P_gas: this volumetric flow is used in the gas-phase
    # mass balances. The BSM2 "q_gas" output is the same gas expressed at P_atm
    # (x P_gas/P_atm, ideal gas). Using the corrected flow inside the balances would
    # remove ~5 % too much gas (found in validation step 4a, see LOG.md).
    q_gas_head = max(p.k_p * (P_gas - p.P_atm), 0.0)
    q_gas = q_gas_head * P_gas / p.P_atm
    rT8 = p.k_La * (S_h2 - 16.0 * th["K_H_h2"] * p_h2)
    rT9 = p.k_La * (g("S_ch4") - 64.0 * th["K_H_ch4"] * p_ch4)
    rT10 = p.k_La * (sp["S_co2"] - th["K_H_co2"] * p_co2)
    return {"rho": r, "rT8": rT8, "rT9": rT9, "rT10": rT10, "q_gas": q_gas, "q_gas_head": q_gas_head,
            "p_h2": p_h2, "p_ch4": p_ch4, "p_co2": p_co2, "P_gas": P_gas,
            "I": {"pH_aa": I_pH_aa, "pH_ac": I_pH_ac, "pH_h2": I_pH_h2, "IN_lim": I_IN_lim,
                  "h2_fa": I_h2_fa, "h2_c4": I_h2_c4, "h2_pro": I_h2_pro, "nh3": I_nh3}}


def carbon_coefficients(p: ADM1Params) -> np.ndarray:
    """s_1..s_13 of the S_IC balance (Rosen & Jeppsson 2006, Eq. 10)."""
    s = np.zeros(14)
    s[1] = -p.C_xc + p.f_sI_xc * p.C_sI + p.f_ch_xc * p.C_ch + p.f_pr_xc * p.C_pr + p.f_li_xc * p.C_li + p.f_xI_xc * p.C_xI
    s[2] = -p.C_ch + p.C_su
    s[3] = -p.C_pr + p.C_aa
    s[4] = -p.C_li + (1 - p.f_fa_li) * p.C_su + p.f_fa_li * p.C_fa
    s[5] = -p.C_su + (1 - p.Y_su) * (p.f_bu_su * p.C_bu + p.f_pro_su * p.C_pro + p.f_ac_su * p.C_ac) + p.Y_su * p.C_bac
    s[6] = -p.C_aa + (1 - p.Y_aa) * (p.f_va_aa * p.C_va + p.f_bu_aa * p.C_bu + p.f_pro_aa * p.C_pro + p.f_ac_aa * p.C_ac) + p.Y_aa * p.C_bac
    s[7] = -p.C_fa + (1 - p.Y_fa) * 0.7 * p.C_ac + p.Y_fa * p.C_bac
    s[8] = -p.C_va + (1 - p.Y_c4) * 0.54 * p.C_pro + (1 - p.Y_c4) * 0.31 * p.C_ac + p.Y_c4 * p.C_bac
    s[9] = -p.C_bu + (1 - p.Y_c4) * 0.8 * p.C_ac + p.Y_c4 * p.C_bac
    s[10] = -p.C_pro + (1 - p.Y_pro) * 0.57 * p.C_ac + p.Y_pro * p.C_bac
    s[11] = -p.C_ac + (1 - p.Y_ac) * p.C_ch4 + p.Y_ac * p.C_bac
    s[12] = (1 - p.Y_h2) * p.C_ch4 + p.Y_h2 * p.C_bac
    s[13] = -p.C_bac + p.C_xc
    return s


def rhs(t: float, y: np.ndarray, p: ADM1Params, y_in: np.ndarray, q_in: float, th: dict, s: np.ndarray) -> np.ndarray:
    """dy/dt for the 29 states. y_in holds the 26 liquid influent concentrations."""
    sp = speciation(y, p, th)
    R = rates(y, p, th, sp)
    r, rT8, rT9, rT10, q_gas = R["rho"], R["rT8"], R["rT9"], R["rT10"], R["q_gas_head"]
    D = q_in / p.V_liq
    dy = np.zeros_like(y)
    dy[:N_LIQ] = D * (y_in - y[:N_LIQ])
    dec = r[13:20].sum()

    dy[IDX["S_su"]] += r[2] + (1 - p.f_fa_li) * r[4] - r[5]
    dy[IDX["S_aa"]] += r[3] - r[6]
    dy[IDX["S_fa"]] += p.f_fa_li * r[4] - r[7]
    dy[IDX["S_va"]] += (1 - p.Y_aa) * p.f_va_aa * r[6] - r[8]
    dy[IDX["S_bu"]] += (1 - p.Y_su) * p.f_bu_su * r[5] + (1 - p.Y_aa) * p.f_bu_aa * r[6] - r[9]
    dy[IDX["S_pro"]] += ((1 - p.Y_su) * p.f_pro_su * r[5] + (1 - p.Y_aa) * p.f_pro_aa * r[6]
                         + (1 - p.Y_c4) * 0.54 * r[8] - r[10])
    dy[IDX["S_ac"]] += ((1 - p.Y_su) * p.f_ac_su * r[5] + (1 - p.Y_aa) * p.f_ac_aa * r[6]
                        + (1 - p.Y_fa) * 0.7 * r[7] + (1 - p.Y_c4) * 0.31 * r[8]
                        + (1 - p.Y_c4) * 0.8 * r[9] + (1 - p.Y_pro) * 0.57 * r[10] - r[11])
    dy[IDX["S_h2"]] += ((1 - p.Y_su) * p.f_h2_su * r[5] + (1 - p.Y_aa) * p.f_h2_aa * r[6]
                        + (1 - p.Y_fa) * 0.3 * r[7] + (1 - p.Y_c4) * 0.15 * r[8]
                        + (1 - p.Y_c4) * 0.2 * r[9] + (1 - p.Y_pro) * 0.43 * r[10] - r[12] - rT8)
    dy[IDX["S_ch4"]] += (1 - p.Y_ac) * r[11] + (1 - p.Y_h2) * r[12] - rT9
    dy[IDX["S_IC"]] += -(s[1:13] @ r[1:13] + s[13] * dec) - rT10
    dy[IDX["S_IN"]] += (-p.Y_su * p.N_bac * r[5] + (p.N_aa - p.Y_aa * p.N_bac) * r[6]
                        - p.Y_fa * p.N_bac * r[7] - p.Y_c4 * p.N_bac * r[8] - p.Y_c4 * p.N_bac * r[9]
                        - p.Y_pro * p.N_bac * r[10] - p.Y_ac * p.N_bac * r[11] - p.Y_h2 * p.N_bac * r[12]
                        + (p.N_bac - p.N_xc) * dec
                        + (p.N_xc - p.f_xI_xc * p.N_I - p.f_sI_xc * p.N_I - p.f_pr_xc * p.N_aa) * r[1])
    dy[IDX["S_I"]] += p.f_sI_xc * r[1]
    dy[IDX["X_xc"]] += -r[1] + dec
    dy[IDX["X_ch"]] += p.f_ch_xc * r[1] - r[2]
    dy[IDX["X_pr"]] += p.f_pr_xc * r[1] - r[3]
    dy[IDX["X_li"]] += p.f_li_xc * r[1] - r[4]
    dy[IDX["X_su"]] += p.Y_su * r[5] - r[13]
    dy[IDX["X_aa"]] += p.Y_aa * r[6] - r[14]
    dy[IDX["X_fa"]] += p.Y_fa * r[7] - r[15]
    dy[IDX["X_c4"]] += p.Y_c4 * (r[8] + r[9]) - r[16]
    dy[IDX["X_pro"]] += p.Y_pro * r[10] - r[17]
    dy[IDX["X_ac"]] += p.Y_ac * r[11] - r[18]
    dy[IDX["X_h2"]] += p.Y_h2 * r[12] - r[19]
    dy[IDX["X_I"]] += p.f_xI_xc * r[1]
    # S_cat, S_an: inflow/outflow only (already set)
    vr = p.V_liq / p.V_gas
    dy[IDX["S_gas_h2"]] = -y[IDX["S_gas_h2"]] * q_gas / p.V_gas + rT8 * vr
    dy[IDX["S_gas_ch4"]] = -y[IDX["S_gas_ch4"]] * q_gas / p.V_gas + rT9 * vr
    dy[IDX["S_gas_co2"]] = -y[IDX["S_gas_co2"]] * q_gas / p.V_gas + rT10 * vr
    return dy


@dataclass
class SteadyStateResult:
    y: np.ndarray
    p: ADM1Params
    q_in: float
    y_in: np.ndarray
    info: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return dict(zip(STATE_NAMES, self.y))

    def outputs(self) -> dict:
        th = self.p.thermo()
        sp = speciation(self.y, self.p, th)
        R = rates(self.y, self.p, th, sp)
        q_gas = R["q_gas"]            # m3/d at P_atm and T_op (BSM2 reporting basis)
        q_head = R["q_gas_head"]      # m3/d at P_gas: the flow that carries the mass
        P_gas = R["P_gas"]
        # Normal m3 (0 degC, 1.01325 bar) of dry CH4: from COD flow, 64 kg COD/kmol, 22.414 Nm3/kmol
        ch4_Nm3_d = q_head * self.y[IDX["S_gas_ch4"]] / 64.0 * 22.414
        co2_Nm3_d = q_head * self.y[IDX["S_gas_co2"]] * 22.414
        vfa = sum(self.y[IDX[n]] for n in ["S_va", "S_bu", "S_pro", "S_ac"])
        return {
            "pH": sp["pH"], "S_nh3_kmolN_m3": sp["S_nh3"], "S_nh4_kmolN_m3": sp["S_nh4"],
            "S_hco3_kmolC_m3": sp["S_hco3"], "S_co2_kmolC_m3": sp["S_co2"],
            "VFA_total_kgCOD_m3": vfa,
            "q_gas_m3_d": q_gas, "q_gas_headspace_m3_d": q_head, "P_gas_bar": P_gas,
            "p_gas_h2_bar": R["p_h2"], "p_gas_ch4_bar": R["p_ch4"], "p_gas_co2_bar": R["p_co2"],
            "CH4_Nm3_d": ch4_Nm3_d, "CO2_Nm3_d": co2_Nm3_d,
            "CH4_frac_dry": ch4_Nm3_d / (ch4_Nm3_d + co2_Nm3_d),
            "inhibition": R["I"],
        }


def steady_state(y_in: np.ndarray, q_in: float, p: ADM1Params, y0: np.ndarray | None = None,
                 t_end: float | None = None, polish: bool = True) -> SteadyStateResult:
    """Integrate to (near) steady state with a stiff solver, then polish with fsolve."""
    th = p.thermo()
    s = carbon_coefficients(p)
    if y0 is None:
        y0 = default_initial_state(y_in)
    hrt = p.V_liq / q_in
    t_end = t_end or max(200.0, 15.0 * hrt)
    sol = solve_ivp(rhs, (0.0, t_end), y0, method="BDF", args=(p, y_in, q_in, th, s),
                    rtol=1e-8, atol=1e-12)
    if not sol.success:
        raise RuntimeError(f"integration failed: {sol.message}")
    y = sol.y[:, -1]
    info = {"t_end": t_end, "n_rhs": sol.nfev,
            "max_rel_rate_after_integration": float(np.max(np.abs(rhs(0, y, p, y_in, q_in, th, s)) / (np.abs(y) + 1e-12)))}
    if polish:
        y_pol, inf, ier, msg = fsolve(lambda z: rhs(0, z, p, y_in, q_in, th, s), y, full_output=True, xtol=1e-13)
        if ier == 1 and np.all(y_pol >= -1e-12):
            y = np.maximum(y_pol, 0.0)
            info["polished"] = True
        else:
            info["polished"] = False
            info["polish_msg"] = msg
    info["max_abs_rhs"] = float(np.max(np.abs(rhs(0, y, p, y_in, q_in, th, s))))
    return SteadyStateResult(y=y, p=p, q_in=q_in, y_in=y_in, info=info)


def default_initial_state(y_in: np.ndarray, inoculum: float = 1.0, alkalinity: float = 0.1) -> np.ndarray:
    """Generic INOCULATED start (like a digester seeded with active sludge).

    ADM1 has multiple steady states. Starting with little biomass and no buffer, the
    model (like a real digester) can sour: acids accumulate, pH drops to ~5 and
    methanogens wash out (observed in step 4a, first run). A seeded, buffered start
    selects the healthy branch. Values are generic, NOT tuned to any reference:
    every trophic group at `inoculum` kg COD/m3, inorganic C and N at `alkalinity`
    kmol/m3, VFAs and sugars at zero, cations/anions/inerts as in the influent.
    """
    y0 = np.zeros(len(STATE_NAMES))
    for n in ["S_I", "X_I", "S_cat", "S_an"]:
        y0[IDX[n]] = y_in[IDX[n]]
    for n in ["X_su", "X_aa", "X_fa", "X_c4", "X_pro", "X_ac", "X_h2"]:
        y0[IDX[n]] = inoculum
    y0[IDX["S_IC"]] = alkalinity
    y0[IDX["S_IN"]] = max(alkalinity, y_in[IDX["S_IN"]])
    y0[IDX["S_h2"]] = 1e-7
    y0[IDX["S_gas_ch4"]] = 1.0
    y0[IDX["S_gas_co2"]] = 0.01
    y0[IDX["S_gas_h2"]] = 1e-5
    return y0


def influent_vector(**kw) -> np.ndarray:
    """Build the 26-element liquid influent vector by state name (missing = 0)."""
    v = np.zeros(N_LIQ)
    for k, val in kw.items():
        v[IDX[k]] = val
    return v


# --------------------------------------------------------------------- balances
def cod_of(y: np.ndarray) -> float:
    """Liquid COD (kg COD/m3): all COD-based states."""
    names = ["S_su", "S_aa", "S_fa", "S_va", "S_bu", "S_pro", "S_ac", "S_h2", "S_ch4", "S_I",
             "X_xc", "X_ch", "X_pr", "X_li", "X_su", "X_aa", "X_fa", "X_c4", "X_pro", "X_ac", "X_h2", "X_I"]
    return float(sum(y[IDX[n]] for n in names))


def nitrogen_of(y: np.ndarray, p: ADM1Params) -> float:
    """Liquid N (kmol N/m3)."""
    bac = sum(y[IDX[n]] for n in ["X_su", "X_aa", "X_fa", "X_c4", "X_pro", "X_ac", "X_h2"])
    return float(y[IDX["S_IN"]] + p.N_aa * (y[IDX["S_aa"]] + y[IDX["X_pr"]]) + p.N_xc * y[IDX["X_xc"]]
                 + p.N_I * (y[IDX["S_I"]] + y[IDX["X_I"]]) + p.N_bac * bac)


def carbon_of(y: np.ndarray, p: ADM1Params) -> float:
    """Liquid C (kmol C/m3)."""
    c = {"S_su": p.C_su, "S_aa": p.C_aa, "S_fa": p.C_fa, "S_va": p.C_va, "S_bu": p.C_bu, "S_pro": p.C_pro,
         "S_ac": p.C_ac, "S_ch4": p.C_ch4, "S_I": p.C_sI, "X_xc": p.C_xc, "X_ch": p.C_ch, "X_pr": p.C_pr,
         "X_li": p.C_li, "X_I": p.C_xI}
    bac = sum(y[IDX[n]] for n in ["X_su", "X_aa", "X_fa", "X_c4", "X_pro", "X_ac", "X_h2"])
    return float(sum(y[IDX[n]] * v for n, v in c.items()) + y[IDX["S_IC"]] + p.C_bac * bac)


def balances(res: SteadyStateResult) -> dict:
    """Steady-state closure of COD, N and C: (in - out)/in, in %."""
    p, y, y_in, q = res.p, res.y, res.y_in, res.q_in
    yin_full = np.concatenate([y_in, np.zeros(3)])
    q_gas = res.outputs()["q_gas_headspace_m3_d"]
    cod_in = q * cod_of(yin_full)
    cod_out = q * cod_of(y) + q_gas * (y[IDX["S_gas_ch4"]] + y[IDX["S_gas_h2"]])
    n_in, n_out = q * nitrogen_of(yin_full, p), q * nitrogen_of(y, p)
    c_in = q * carbon_of(yin_full, p)
    # gas CH4 carbon counted with C_ch4 (0.0156, BSM2 value) for consistency with the
    # S_IC stoichiometry; 1/64 = 0.015625 would leave a 0.16 % rounding residual on CH4-C.
    c_out = q * carbon_of(y, p) + q_gas * (y[IDX["S_gas_ch4"]] * p.C_ch4 + y[IDX["S_gas_co2"]])
    return {"COD_in_kg_d": cod_in, "COD_out_kg_d": cod_out, "COD_closure_pct": (cod_in - cod_out) / cod_in * 100,
            "N_closure_pct": (n_in - n_out) / n_in * 100, "C_closure_pct": (c_in - c_out) / c_in * 100}
