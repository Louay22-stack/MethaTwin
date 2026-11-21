"""
methatwin.feedstock - turn literature feedstock data into ADM1 inputs.

Method (BMP-based fractionation, after Koch et al. 2010 as used by Klimiuk et al. 2015)
-------------------------------------------------------------------------------------
1. Composition (crude protein, lipid, carbohydrate in % TS) -> theoretical oxygen demand
   of the volatile solids, ThOD_VS [kg COD / kg VS], using the ThOD of each class
   (protein 1.42, lipid 2.90, carbohydrate 1.19 kg O2/kg; Klimiuk et al. 2015, Table 2).
   The three classes are re-normalised to 100 % of VS (the analysed classes do not sum
   exactly to VS in the sources).
2. Maximum methane potential if ALL organic matter were converted:
       BMP_max = 0.350 Nm3 CH4/kg COD * ThOD_VS         (stoichiometry, 0 degC, 1 atm)
3. Apparent anaerobic degradability from the MEASURED BMP:
       D = BMP_measured / BMP_max
4. ADM1 fractions of the composite COD (Koch et al. 2010 convention):
       proteins and lipids are fully degradable,
       degradable carbohydrates = D - f_pr - f_li,
       inerts X_I = 1 - D.
   If D < f_pr + f_li the data are inconsistent and an error is raised.

Units: COD in kg, methane in Nm3 (0 degC, 1.01325 bar), feed in t fresh matter (FM).
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Theoretical oxygen demand of each organic class, kg O2 per kg (Klimiuk et al. 2015, Tab. 2)
THOD = {"protein": 1.42, "lipid": 2.90, "carbohydrate": 1.19, "lignin": 1.56}
# Nm3 CH4 per kg COD converted: 22.414 L/mol / 64 g O2 per mol CH4
CH4_PER_COD = 22.414 / 64.0  # = 0.3502
N_IN_PROTEIN = 1 / 6.25      # kg N per kg crude protein (Batstone et al. 2003 via Klimiuk)
M_N = 14.007                 # kg/kmol


@dataclass
class Feedstock:
    """One feedstock, with literature values (fractions, not %)."""
    name: str
    ts: float                 # kg TS / kg FM
    vs: float                 # kg VS / kg TS
    protein: float            # kg / kg TS
    lipid: float              # kg / kg TS
    carbohydrate: float       # kg / kg TS
    bmp: float                # Nm3 CH4 / t VS (measured)
    nh4_n: float = 0.0        # kg NH4-N / kg TS
    n_total: float | None = None  # kg N / kg TS (for the consistency diagnostic)
    density: float = 1.0      # t / m3
    meta: dict = field(default_factory=dict)

    # ---- derived quantities ------------------------------------------------
    @property
    def vs_per_t(self) -> float:
        """kg VS per t FM."""
        return 1000.0 * self.ts * self.vs

    def class_shares_of_vs(self) -> dict:
        """Mass shares of protein / lipid / carbohydrate, re-normalised to VS."""
        tot = self.protein + self.lipid + self.carbohydrate
        return {"protein": self.protein / tot, "lipid": self.lipid / tot,
                "carbohydrate": self.carbohydrate / tot}

    @property
    def thod_vs(self) -> float:
        """kg COD per kg VS."""
        s = self.class_shares_of_vs()
        return sum(s[k] * THOD[k] for k in s)

    @property
    def bmp_max(self) -> float:
        """Nm3 CH4 / t VS if all VS were converted to methane."""
        return 1000.0 * CH4_PER_COD * self.thod_vs

    @property
    def degradability(self) -> float:
        """Apparent COD degradability D = measured BMP / maximum BMP."""
        return self.bmp / self.bmp_max

    def cod_fractions(self) -> dict:
        """ADM1 fractions of the particulate composite (sum = 1)."""
        s = self.class_shares_of_vs()
        cod = {k: s[k] * THOD[k] / self.thod_vs for k in s}  # COD shares of each class
        d = self.degradability
        if d > 1.0:
            raise ValueError(f"{self.name}: measured BMP exceeds the theoretical maximum")
        f_pr, f_li = cod["protein"], cod["lipid"]
        f_ch = d - f_pr - f_li
        if f_ch < 0:
            raise ValueError(f"{self.name}: D={d:.2f} < f_pr+f_li; data inconsistent")
        return {"f_pr": f_pr, "f_li": f_li, "f_ch": f_ch, "f_xi": 1.0 - d}

    def adm1_inputs(self) -> dict:
        """ADM1 influent concentrations of this feed (per m3 of feed)."""
        cod_total = self.vs_per_t * self.thod_vs * self.density  # kg COD / m3
        f = self.cod_fractions()
        return {
            "X_pr": f["f_pr"] * cod_total, "X_li": f["f_li"] * cod_total,
            "X_ch": f["f_ch"] * cod_total, "X_I": f["f_xi"] * cod_total,
            "S_IN": 1000.0 * self.ts * self.nh4_n * self.density / M_N,  # kmol N/m3
            "COD_total": cod_total,
        }

    def nitrogen_check(self) -> dict | None:
        """Organic N (from crude protein) + NH4-N vs total N, all in kg N / t FM."""
        if self.n_total is None:
            return None
        n_org = 1000.0 * self.ts * self.protein * N_IN_PROTEIN
        n_nh4 = 1000.0 * self.ts * self.nh4_n
        n_tot = 1000.0 * self.ts * self.n_total
        return {"N_org": n_org, "N_NH4": n_nh4, "N_total_lit": n_tot,
                "closure_pct": (n_org + n_nh4 - n_tot) / n_tot * 100.0}


def mix(feeds: list[Feedstock], fm_shares: list[float]) -> dict:
    """Properties of a blend defined by fresh-mass shares (must sum to 1)."""
    if abs(sum(fm_shares) - 1.0) > 1e-9:
        raise ValueError("fresh-mass shares must sum to 1")
    vs = sum(w * f.vs_per_t for f, w in zip(feeds, fm_shares))           # kg VS/t FM
    cod = sum(w * f.vs_per_t * f.thod_vs for f, w in zip(feeds, fm_shares))
    ch4 = sum(w * f.vs_per_t * f.bmp / 1000.0 for f, w in zip(feeds, fm_shares))
    keys = ["X_pr", "X_li", "X_ch", "X_I", "S_IN", "COD_total"]
    adm1 = {k: sum(w * f.adm1_inputs()[k] for f, w in zip(feeds, fm_shares)) for k in keys}
    return {"VS_kg_per_t": vs, "COD_kg_per_t": cod, "CH4_Nm3_per_t": ch4,
            "COD_fractions": {k: adm1[k] / adm1["COD_total"] for k in ["X_pr", "X_li", "X_ch", "X_I"]},
            "adm1": adm1}
