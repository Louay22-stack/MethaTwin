"""
methatwin.upgrading - High-pressure water scrubbing (HPWS) biogas upgrading in DWSIM,
built and solved entirely from Python.

Flowsheet (tags as in the report):
  RAW biogas (wet, 39 degC) -> E-100 chiller (5 degC) -> V-100 knock-out (condensate)
  -> K-101 compressor (to P_FLASH) -> E-101 intercooler (30 degC) -> MIX-101 (+ flash-gas recycle REC)
  -> K-102 compressor (to P_ABS) -> E-102 aftercooler (T_GAS_ABS) -> T-201 absorber (gas to bottom)
  T-201 top  : BM, biomethane (water-saturated; drying not modelled, see notes)
  T-201 bottom: RICH water -> V-201 valve (P_FLASH) -> F-201 flash: gas = REC (recycled), liquid
              -> V-202 valve (1.05 bar) -> F-202 "CO2 flash": gas = CO2-rich biogenic CO2 stream
              -> T-301 air stripper (1.013 bar, AIR from K-301 blower) : top OFFGAS, bottom LEAN
              -> P-301 pump (P_ABS) -> E-301 chiller (T_WATER) -> WRET, returned to T-201 as WIN
Tear streams (closed in Python by successive substitution): REC and WIN.
Water make-up is added to WIN so that the circulating water flow stays at its set point.

Thermodynamics: Peng-Robinson with gas-water kij fitted to Henry's law (methatwin.dwsim_thermo),
valid 10-15 degC for the water-contacting units (checked in the results).
Units inside DWSIM are SI (K, Pa, mol/s, kW).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from .dwsim_thermo import create_pr_package

COMPOUNDS = ["Methane", "Carbon dioxide", "Water", "Nitrogen", "Oxygen"]
NM3_PER_MOL = 22.414e-3          # Nm3/mol at 0 degC, 1.01325 bar
HHV_CH4 = 11.06                  # kWh/Nm3 (0/0 degC basis), used for PCS/Wobbe check
M = {"Methane": 16.043, "Carbon dioxide": 44.010, "Water": 18.015, "Nitrogen": 28.014, "Oxygen": 31.999}


@dataclass
class UpgradingDesign:
    raw_dry_Nm3_h: float = 345.0      # dry raw biogas (design capacity)
    y_ch4_dry: float = 0.569          # from ADM1 base case
    T_raw_C: float = 39.0
    P_raw_bar: float = 1.02
    T_chill_C: float = 5.0            # gas pre-drying
    P_flash_bar: float = 3.5          # intermediate pressure = flash pressure
    P_abs_bar: float = 9.0
    T_inter_C: float = 30.0
    T_gas_abs_C: float = 15.0
    T_water_C: float = 10.0
    water_m3_h: float = 40.0          # circulating water
    n_abs_stages: int = 6             # equilibrium stages, absorber
    n_str_stages: int = 4             # equilibrium stages, stripper
    air_Nm3_per_m3_water: float = 8.0
    P_co2_flash_bar: float = 1.05
    eta_comp_pct: float = 75.0        # isentropic efficiency, gas compressors and blower
    eta_pump_pct: float = 75.0
    blower_dp_bar: float = 0.10
    T_air_C: float = 15.0
    cop_chiller: float = 3.0          # assumption (see notes); converts cold duty to electricity
    tear_tol: float = 1e-5
    max_iter: int = 120
    relax: float = 0.5                # under-relaxation of the gas-recycle tear (1 = none)


@dataclass
class UpgradingResult:
    design: dict
    converged: bool
    iterations: int
    kpi: dict = field(default_factory=dict)
    balances: dict = field(default_factory=dict)
    streams: dict = field(default_factory=dict)
    units: dict = field(default_factory=dict)


def _sat_water_bar(T_C: float) -> float:
    """Water vapour pressure (Antoine, 1-100 degC; mmHg constants 8.07131/1730.63/233.426)."""
    return 10 ** (8.07131 - 1730.63 / (233.426 + T_C)) / 750.062


class HPWSFlowsheet:
    def __init__(self, dw, design: UpgradingDesign, kij: dict | None = None):
        self.dw, self.d = dw, design
        self.interf = dw.Automation3()
        self.sim = self.interf.CreateFlowsheet()
        for c in COMPOUNDS:
            self.sim.AddCompound(c)
        create_pr_package(self.sim, kij)
        self.o = {}
        self._build()

    # ------------------------------------------------------------------ helpers
    def _add(self, kind: str, tag: str, x=0, y=0):
        obj = self.sim.AddObject(getattr(self.dw.ObjectType, kind), x, y, tag).GetAsObject()
        self.o[tag] = obj
        return obj

    def _ms(self, tag, x=0, y=0):
        return self._add("MaterialStream", tag, x, y)

    def _es(self, tag, x=0, y=0):
        return self._add("EnergyStream", tag, x, y)

    def _link(self, a, b, pa=-1, pb=-1):
        self.sim.ConnectObjects(self.o[a].GraphicObject, self.o[b].GraphicObject, pa, pb)

    def _set_stream(self, tag, comp: dict, T_K: float, P_Pa: float, mol_s: float):
        s = self.o[tag]
        z = np.array([comp.get(c, 0.0) for c in COMPOUNDS], dtype=float)
        z = z / z.sum()
        s.SetOverallComposition(self.dw.System.Array[float](list(z)))
        s.SetTemperature(T_K)
        s.SetPressure(P_Pa)
        s.SetMolarFlow(max(mol_s, 1e-9))

    def comp(self, tag) -> dict:
        s = self.o[tag]
        return {c: s.Phases[0].Compounds[c].MoleFraction for c in COMPOUNDS}

    def flow(self, tag) -> float:
        return self.o[tag].GetMolarFlow()

    # ------------------------------------------------------------------ build
    def _build(self):
        d = self.d
        from DWSIM.UnitOperations.UnitOperations import Compressor, Cooler, Pump, Valve  # type: ignore
        for t in ["RAW", "S2", "COND1", "S3", "S4", "S5", "REC", "S6", "S7", "S8", "WIN", "BM", "RICH",
                  "S10", "LIQ2", "S11", "CO2G", "LIQ3", "AIR0", "AIR", "OFFGAS", "LEAN", "S12", "WRET"]:
            self._ms(t)
        for t in ["Q-E100", "W-K101", "Q-E101", "W-K102", "Q-E102", "W-P301", "Q-E301", "W-K301"]:
            self._es(t)

        def cooler(tag, inl, out, q, T_C):
            u = self._add("Cooler", tag)
            self._link(inl, tag); self._link(tag, out); self._link(tag, q)
            u.CalcMode = Cooler.CalculationMode.OutletTemperature
            u.OutletTemperature = T_C + 273.15
            u.DeltaP = 0.0
            return u

        def compressor(tag, inl, out, w, P_bar):
            u = self._add("Compressor", tag)
            self._link(inl, tag); self._link(tag, out); self._link(w, tag)
            u.CalcMode = Compressor.CalculationMode.OutletPressure
            u.POut = P_bar * 1e5
            u.AdiabaticEfficiency = d.eta_comp_pct      # DWSIM expects percent (step 2 finding)
            return u

        def valve(tag, inl, out, P_bar):
            u = self._add("Valve", tag)
            self._link(inl, tag); self._link(tag, out)
            u.CalcMode = Valve.CalculationMode.OutletPressure
            u.OutletPressure = P_bar * 1e5
            return u

        def vessel(tag, inl, vap, liq):
            u = self._add("Vessel", tag)
            self._link(inl, tag, -1, 0)
            self._link(tag, vap, 0, 0)
            self._link(tag, liq, 1, 0)
            return u

        cooler("E-100", "RAW", "S2", "Q-E100", d.T_chill_C)
        vessel("V-100", "S2", "S3", "COND1")
        compressor("K-101", "S3", "S4", "W-K101", d.P_flash_bar)
        cooler("E-101", "S4", "S5", "Q-E101", d.T_inter_C)
        mix = self._add("NodeIn", "MIX-101")
        self._link("S5", "MIX-101", -1, 0); self._link("REC", "MIX-101", -1, 1); self._link("MIX-101", "S6")
        compressor("K-102", "S6", "S7", "W-K102", d.P_abs_bar)
        cooler("E-102", "S7", "S8", "Q-E102", d.T_gas_abs_C)

        abs_ = self._add("AbsorptionColumn", "T-201")
        abs_.SetNumberOfStages(d.n_abs_stages)
        abs_.SetTopPressure(d.P_abs_bar * 1e5)
        abs_.SetBottomStagePressure(d.P_abs_bar * 1e5)
        abs_.ConnectFeed(self.o["WIN"], 0)
        abs_.ConnectFeed(self.o["S8"], d.n_abs_stages - 1)
        abs_.ConnectTopProduct(self.o["BM"])
        abs_.ConnectBottoms(self.o["RICH"])

        valve("V-201", "RICH", "S10", d.P_flash_bar)
        # F-201 vapour goes to a separate stream (REC_OUT); REC is the tear copy fed to MIX-101
        self._ms("REC_OUT")
        vessel("F-201", "S10", "REC_OUT", "LIQ2")
        valve("V-202", "LIQ2", "S11", d.P_co2_flash_bar)
        vessel("F-202", "S11", "CO2G", "LIQ3")

        compressor("K-301", "AIR0", "AIR", "W-K301", 1.01325 + d.blower_dp_bar)
        strp = self._add("AbsorptionColumn", "T-301")
        strp.SetNumberOfStages(d.n_str_stages)
        strp.SetTopPressure(1.01325e5)
        strp.SetBottomStagePressure((1.01325 + d.blower_dp_bar) * 1e5)
        strp.ConnectFeed(self.o["LIQ3"], 0)
        strp.ConnectFeed(self.o["AIR"], d.n_str_stages - 1)
        strp.ConnectTopProduct(self.o["OFFGAS"])
        strp.ConnectBottoms(self.o["LEAN"])

        p = self._add("Pump", "P-301")
        self._link("LEAN", "P-301"); self._link("P-301", "S12"); self._link("W-P301", "P-301")
        p.CalcMode = Pump.CalculationMode.OutletPressure
        p.Pout = d.P_abs_bar * 1e5
        p.Eficiencia = d.eta_pump_pct
        cooler("E-301", "S12", "WRET", "Q-E301", d.T_water_C)

        # ---- fixed feeds
        y_w = _sat_water_bar(d.T_raw_C) / d.P_raw_bar
        dry_mol_s = d.raw_dry_Nm3_h / 3600.0 / NM3_PER_MOL
        self._set_stream("RAW", {"Methane": d.y_ch4_dry * (1 - y_w), "Carbon dioxide": (1 - d.y_ch4_dry) * (1 - y_w),
                                 "Water": y_w}, d.T_raw_C + 273.15, d.P_raw_bar * 1e5, dry_mol_s / (1 - y_w))
        air_mol_s = d.air_Nm3_per_m3_water * d.water_m3_h / 3600.0 / NM3_PER_MOL
        self._set_stream("AIR0", {"Nitrogen": 0.79, "Oxygen": 0.21}, d.T_air_C + 273.15, 1.01325e5, air_mol_s)
        # m3/h -> kg/h (x 999.7 kg/m3 at 10 degC) -> g/h (x 1000) -> mol/h (/ 18.015) -> mol/s
        # (a missing x1000 here gave 1/1000 of the water in the first run; caught by inspecting flows)
        self.water_mol_s = d.water_m3_h * 999.7 * 1000.0 / 18.015 / 3600.0
        # ---- initial tear guesses
        self._set_stream("REC", {"Methane": 0.5, "Carbon dioxide": 0.5}, d.T_inter_C + 273.15,
                         d.P_flash_bar * 1e5, 0.01 * dry_mol_s)
        self._set_stream("WIN", {"Water": 1.0}, d.T_water_C + 273.15, d.P_abs_bar * 1e5, self.water_mol_s)

    # ------------------------------------------------------------------ solve
    def solve(self) -> UpgradingResult:
        d = self.d
        converged, it, hist = False, 0, []
        for it in range(1, d.max_iter + 1):
            errs = self.interf.CalculateFlowsheet2(self.sim)
            if errs is not None and len(list(errs)) > 0:
                msgs = [str(e)[:300] for e in errs]
                raise RuntimeError(f"DWSIM errors at iteration {it}: {msgs}")
            # new tear values
            rec_new = (self.comp("REC_OUT"), self.o["REC_OUT"].GetTemperature(), self.flow("REC_OUT"))
            wret_c, wret_f = self.comp("WRET"), self.flow("WRET")
            water_in_wret = wret_c["Water"] * wret_f
            makeup = max(self.water_mol_s - water_in_wret, 0.0)
            win_flow = wret_f + makeup
            win_comp = {c: (wret_c[c] * wret_f + (makeup if c == "Water" else 0.0)) / win_flow for c in COMPOUNDS}
            # convergence measures, normalised by plant inflows (the recycle can legitimately be ~0
            # when the flash water is under-saturated, so relative-to-itself tests never converge)
            raw = self.flow("RAW")
            d_rec = abs(rec_new[2] - self.flow("REC")) / raw
            co2_raw = self.comp("RAW")["Carbon dioxide"] * raw
            d_win = abs(win_comp["Carbon dioxide"] * win_flow
                        - self.comp("WIN")["Carbon dioxide"] * self.flow("WIN")) / co2_raw
            hist.append((d_rec, d_win))
            self.makeup_mol_s = makeup
            if it > 2 and d_rec < d.tear_tol and d_win < d.tear_tol:
                converged = True
                break
            # damped update of the gas recycle (plain substitution oscillates at high water flow)
            f_old = self.flow("REC")
            c_old = self.comp("REC")
            f_rec = d.relax * rec_new[2] + (1 - d.relax) * f_old
            if f_rec > 1e-12:
                c_rec = {c: (d.relax * rec_new[0][c] * rec_new[2] + (1 - d.relax) * c_old[c] * f_old) / f_rec
                         for c in COMPOUNDS}
            else:  # flash produced no gas (under-saturated water): keep composition, zero flow
                c_rec = c_old
            self._set_stream("REC", c_rec, rec_new[1], d.P_flash_bar * 1e5, f_rec)
            self._set_stream("WIN", win_comp, d.T_water_C + 273.15, d.P_abs_bar * 1e5, win_flow)
        self.history = hist
        return self._results(converged, it)

    # ------------------------------------------------------------------ results
    def _results(self, converged: bool, iterations: int) -> UpgradingResult:
        d, o = self.d, self.o
        # Physical sanity check: DWSIM's column solver can return an all-liquid "solution"
        # (all biogas dissolved) without raising an error; CH4 solubility makes this impossible.
        if self.flow("BM") < 0.05 * self.flow("RAW"):
            raise RuntimeError("absorber solver returned no top product (non-physical solution)")
        ch4 = lambda t: self.comp(t)["Methane"] * self.flow(t)
        co2 = lambda t: self.comp(t)["Carbon dioxide"] * self.flow(t)
        bm = self.comp("BM")
        dry = 1.0 - bm["Water"]
        bm_dry = {c: bm[c] / dry for c in COMPOUNDS if c != "Water"}
        bm_dry_Nm3_h = self.flow("BM") * dry * NM3_PER_MOL * 3600
        mw_dry = sum(bm_dry[c] * M[c] for c in bm_dry)
        hhv = bm_dry["Methane"] * HHV_CH4
        wobbe = hhv / np.sqrt(mw_dry / 28.96)
        ch4_in = ch4("RAW")
        ch4_out_bm = ch4("BM")
        slip_off = ch4("OFFGAS") + ch4("CO2G") + ch4("COND1")
        # electricity: compressors, pump, blower (kW) + chillers via COP
        w = {k: o[k].DeltaQ for k in ["K-101", "K-102", "K-301", "P-301"]}
        q_cold = {k: o[k].DeltaQ for k in ["E-100", "E-301"]}       # sub-ambient cooling (chillers)
        q_cw = {k: o[k].DeltaQ for k in ["E-101", "E-102"]}         # cooling-water/air coolers
        p_el = sum(w.values()) + sum(q_cold.values()) / d.cop_chiller
        raw_Nm3_h = d.raw_dry_Nm3_h
        kpi = {
            "biomethane_Nm3_h_dry": bm_dry_Nm3_h, "CH4_pct_dry": 100 * bm_dry["Methane"],
            "CO2_pct_dry": 100 * bm_dry["Carbon dioxide"], "O2_ppm_dry": 1e6 * bm_dry["Oxygen"],
            "N2_pct_dry": 100 * bm_dry["Nitrogen"], "H2O_ppm_wet_before_dryer": 1e6 * bm["Water"],
            "HHV_kWh_Nm3": hhv, "Wobbe_kWh_Nm3": wobbe,
            "CH4_recovery_pct": 100 * ch4_out_bm / ch4_in, "CH4_slip_pct": 100 * slip_off / ch4_in,
            "CO2_stream_Nm3_h": self.flow("CO2G") * NM3_PER_MOL * 3600,
            "CO2_stream_purity_pct_dry": 100 * self.comp("CO2G")["Carbon dioxide"] / (1 - self.comp("CO2G")["Water"]),
            "CO2_captured_in_CO2_stream_pct": 100 * co2("CO2G") / co2("RAW"),
            "CO2_stream_t_per_yr_at_8400h": co2("CO2G") * 44.01e-3 * 3600 * 8400 / 1000,
            "power_kW": w, "cold_duty_kW": q_cold, "cooling_water_duty_kW": q_cw, "P_el_total_kW": p_el,
            "specific_el_kWh_per_Nm3_raw": p_el / raw_Nm3_h,
            "specific_el_kWh_per_Nm3_biomethane": p_el / bm_dry_Nm3_h,
            "recycle_Nm3_h": self.flow("REC") * NM3_PER_MOL * 3600,
            "makeup_water_kg_h": self.makeup_mol_s * 18.015 * 3.6,
            "T_absorber_bottom_C": o["RICH"].GetTemperature() - 273.15,
            "T_stripper_bottom_C": o["LEAN"].GetTemperature() - 273.15,
            "T_absorber_top_C": o["BM"].GetTemperature() - 273.15,
        }
        kpi["energy_penalty_kW"] = p_el + slip_off * NM3_PER_MOL * 3600 * 9.97   # + lost CH4 (LHV)
        kpi["water_units_in_validity_window"] = all(10.0 - 0.5 <= kpi[k] <= 15.0 + 0.5 for k in
                                                    ["T_absorber_bottom_C", "T_stripper_bottom_C", "T_absorber_top_C"])
        res = UpgradingResult(design=asdict(d), converged=converged, iterations=iterations, kpi=kpi)
        res.balances = self.balances()
        res.streams = {t: {"mol_s": self.flow(t), "T_C": o[t].GetTemperature() - 273.15,
                           "P_bar": o[t].GetPressure() / 1e5, "y": self.comp(t)}
                       for t in ["RAW", "COND1", "S8", "REC", "BM", "RICH", "CO2G", "OFFGAS", "LEAN", "WIN", "AIR"]}
        res.units = {"tear_history": self.history}
        return res

    def balances(self) -> dict:
        """Overall mass, component and energy balances of the converged flowsheet."""
        o = self.o
        ins = ["RAW", "AIR0"]
        outs = ["COND1", "BM", "CO2G", "OFFGAS"]
        mk = self.makeup_mol_s
        mass = lambda t: o[t].GetMassFlow()  # kg/s
        m_in = sum(mass(t) for t in ins) + mk * 18.015e-3
        m_out = sum(mass(t) for t in outs)
        # the water loop is closed by make-up; the residual from the last tear step is included
        loop_res = mass("WIN") - mass("WRET") - mk * 18.015e-3
        comp_bal = {}
        for c in ["Methane", "Carbon dioxide", "Nitrogen", "Oxygen"]:
            n_in = sum(self.comp(t)[c] * self.flow(t) for t in ins)
            n_out = sum(self.comp(t)[c] * self.flow(t) for t in outs)
            loop = self.comp("WIN")[c] * self.flow("WIN") - self.comp("WRET")[c] * self.flow("WRET")
            comp_bal[c] = 100 * (n_in + loop - n_out) / max(n_in, 1e-12)
        # energy (kW): enthalpy flows + work - heat removed
        H = lambda t: o[t].Phases[0].Properties.enthalpy * o[t].GetMassFlow()   # kJ/kg * kg/s = kW
        h_in = sum(H(t) for t in ins) + H("WIN") - H("WRET")
        h_out = sum(H(t) for t in outs)
        w_in = sum(o[k].DeltaQ for k in ["K-101", "K-102", "K-301", "P-301"])
        q_out = sum(o[k].DeltaQ for k in ["E-100", "E-101", "E-102", "E-301"])
        # make-up water enters as liquid at T_water (enthalpy approximated by WIN specific enthalpy)
        h_mk = o["WIN"].Phases[0].Properties.enthalpy * mk * 18.015e-3
        e_res = h_in + h_mk + w_in - q_out - h_out
        return {"mass_closure_pct": 100 * (m_in + loop_res - m_out) / m_in,
                "component_closure_pct": comp_bal,
                "energy_residual_kW": e_res,
                "energy_closure_pct_of_work_plus_heat": 100 * e_res / (w_in + q_out)}
