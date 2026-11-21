"""
Phase 3, step 3 - Feedstock characterisation and ADM1 inputs, with validation checks.

Reads   03_data/raw/feedstock_literature.csv
Writes  03_data/processed/feedstock_adm1.csv
        03_data/processed/feedstock_checks.csv
        03_data/processed/base_case_feed_plan.json
        06_figures/fig03_feedstock_characterisation.png

Run from the project root:  python 05_code/step3_feedstock.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from methatwin.feedstock import CH4_PER_COD, THOD, Feedstock, mix  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "03_data" / "raw" / "feedstock_literature.csv"
PROC = ROOT / "03_data" / "processed"
FIG = ROOT / "06_figures" / "fig03_feedstock_characterisation.png"

# Reference plant (definition PDF, section 4): ~200 Nm3/h biomethane, 8,400 h/yr.
BIOMETHANE_NM3H = 200.0
Y_CH4_BIOMETHANE = 0.97      # assumed grid-quality CH4 content (refined in upgrading step)
HOURS = 8400.0
BASE_FM_SHARES = {"cattle_slurry": 0.60, "cive_silage": 0.25, "maize_silage": 0.15}
MAIZE_CAP = 0.15             # main-crop cap, share of gross tonnage (decree 2016-929, R1)


def lit(df: pd.DataFrame, feed: str, par: str, col: str = "value") -> float:
    v = df.loc[(df.feedstock == feed) & (df.parameter == par), col]
    if v.empty or pd.isna(v.iloc[0]):
        raise KeyError(f"{feed}/{par}/{col} missing")
    return float(v.iloc[0])


def build_feeds(df: pd.DataFrame, slurry_bmp: float | None = None) -> dict[str, Feedstock]:
    """Base-case feedstock objects (literature averages; % converted to fractions)."""
    slurry = Feedstock(
        "cattle_slurry", ts=lit(df, "cattle_slurry", "TS") / 100, vs=lit(df, "cattle_slurry", "VS") / 100,
        protein=lit(df, "cattle_slurry", "protein") / 100, lipid=lit(df, "cattle_slurry", "lipid") / 100,
        carbohydrate=lit(df, "cattle_slurry", "carbohydrate") / 100,
        bmp=slurry_bmp or lit(df, "cattle_slurry", "BMP_VS"),
        # Assumption 2 (DATA_ORIGIN.md): NH4-N = midpoint of the 1-4 % TS range
        nh4_n=0.5 * (lit(df, "cattle_slurry", "NH4_N", "low") + lit(df, "cattle_slurry", "NH4_N", "high")) / 100,
        n_total=lit(df, "cattle_slurry", "N_total") / 100)
    maize = Feedstock(
        "maize_silage", ts=lit(df, "maize_silage", "TS") / 100, vs=lit(df, "maize_silage", "VS") / 100,
        protein=lit(df, "maize_silage", "protein") / 100, lipid=lit(df, "maize_silage", "lipid") / 100,
        carbohydrate=lit(df, "maize_silage", "carbohydrate") / 100, bmp=lit(df, "maize_silage", "BMP_VS"),
        n_total=lit(df, "maize_silage", "N_total") / 100)
    # Assumption 1: CIVE represented by grass-silage data
    cive = Feedstock(
        "cive_silage", ts=lit(df, "grass_silage", "TS") / 100, vs=lit(df, "grass_silage", "VS") / 100,
        protein=lit(df, "grass_silage", "protein") / 100, lipid=lit(df, "grass_silage", "lipid") / 100,
        carbohydrate=lit(df, "grass_silage", "carbohydrate") / 100, bmp=lit(df, "grass_silage", "BMP_VS"),
        n_total=lit(df, "grass_silage", "N_total") / 100)
    return {f.name: f for f in (slurry, cive, maize)}


def feed_table(feeds: dict[str, Feedstock]) -> pd.DataFrame:
    rows = []
    for f in feeds.values():
        fr, a = f.cod_fractions(), f.adm1_inputs()
        rows.append({
            "feedstock": f.name, "TS_pct_FM": 100 * f.ts, "VS_pct_TS": 100 * f.vs,
            "VS_kg_per_t_FM": f.vs_per_t, "ThOD_kgCOD_per_kgVS": f.thod_vs,
            "BMP_measured_Nm3_per_tVS": f.bmp, "BMP_max_Nm3_per_tVS": f.bmp_max,
            "degradability_D": f.degradability, **fr,
            "X_pr_kgCOD_m3": a["X_pr"], "X_li_kgCOD_m3": a["X_li"], "X_ch_kgCOD_m3": a["X_ch"],
            "X_I_kgCOD_m3": a["X_I"], "S_IN_kmolN_m3": a["S_IN"], "COD_total_kg_m3": a["COD_total"],
            "CH4_Nm3_per_t_FM": f.vs_per_t * f.bmp / 1000.0,
        })
    return pd.DataFrame(rows)


def run_checks(df: pd.DataFrame, feeds: dict[str, Feedstock]) -> pd.DataFrame:
    checks = []

    def add(cid, desc, value, reference, passed, note=""):
        checks.append({"check": cid, "description": desc, "value": value,
                       "reference": reference, "pass": passed, "note": note})

    # C1 - physical upper bound: measured BMP (incl. top of range) <= theoretical maximum
    lit_name = {"cattle_slurry": "cattle_slurry", "cive_silage": "grass_silage", "maize_silage": "maize_silage"}
    for f in feeds.values():
        hi = lit(df, lit_name[f.name], "BMP_VS", "high")
        add("C1", f"{f.name}: highest published BMP <= theoretical max (Nm3/t VS)",
            round(hi, 1), round(f.bmp_max, 1), hi <= f.bmp_max,
            f"D at top of range = {hi / f.bmp_max:.2f}")

    # C2 - BMP-derived inert fraction vs independent fractionation (Klimiuk Tab. 4)
    m = feeds["maize_silage"].cod_fractions()["f_xi"]
    add("C2", "maize: f_xi from BMP vs Biernacki 2013 fractionation", round(m, 3), 0.14,
        abs(m - 0.14) <= 0.15, "tolerance +/-0.15 (different samples and methods)")
    g = feeds["cive_silage"].cod_fractions()["f_xi"]
    lo, hi = 0.21, 0.379
    add("C2", "CIVE/grass: f_xi from BMP within published range (Biernacki 2013 - Koch 2010)",
        round(g, 3), f"{lo}-{hi}", lo <= g <= hi)

    # C3 - reproduce Klimiuk Table 3: % TS * TS * ThOD -> kg COD/m3
    ts = lit(df, "mix_klimiuk", "TS")  # g/kg = kg/m3 at density 1
    pairs = [("protein", "protein"), ("lipid", "lipid"), ("starch", "carbohydrate"),
             ("cellulose", "carbohydrate"), ("hemicellulose", "carbohydrate"), ("lignin", "lignin")]
    for comp, cls in pairs:
        calc = lit(df, "mix_klimiuk", comp) / 100 * ts * THOD[cls]
        ref = lit(df, "mix_klimiuk", f"COD_{comp}")
        err = (calc - ref) / ref * 100
        add("C3", f"Klimiuk Tab.3 {comp} COD (kg COD/m3)", round(calc, 2), ref, abs(err) <= 1.0,
            f"error {err:+.2f} %")

    # C4 - predict Klimiuk's 49:51 (VS) maize:manure mixture and compare with measurement
    s, mz = feeds["cattle_slurry"], feeds["maize_silage"]
    w_mz, w_s = 0.49 / mz.vs_per_t, 0.51 / s.vs_per_t        # VS shares -> FM shares
    res = mix([mz, s], [w_mz / (w_mz + w_s), w_s / (w_mz + w_s)])["COD_fractions"]
    meas = {"X_pr": 0.111, "X_li": 0.048, "X_ch": 0.500, "X_I": 0.341}
    for k, tol in [("X_I", 0.10), ("X_pr", 0.05), ("X_li", 0.05), ("X_ch", 0.10)]:
        add("C4", f"49:51 maize:manure mix, fraction {k} (predicted vs measured)",
            round(res[k], 3), meas[k], abs(res[k] - meas[k]) <= tol, f"tolerance +/-{tol}")

    # C5 - nitrogen consistency (diagnostic, not pass/fail on the model)
    for f in feeds.values():
        n = f.nitrogen_check()
        add("C5", f"{f.name}: organic N + NH4-N vs total N (kg N/t FM)",
            round(n["N_org"] + n["N_NH4"], 2), round(n["N_total_lit"], 2),
            abs(n["closure_pct"]) <= 25, f"closure {n['closure_pct']:+.0f} % (diagnostic)")
    return pd.DataFrame(checks)


def base_case_plan(feeds: dict[str, Feedstock]) -> dict:
    names = list(BASE_FM_SHARES)
    blend = mix([feeds[n] for n in names], [BASE_FM_SHARES[n] for n in names])
    ch4_needed = BIOMETHANE_NM3H * Y_CH4_BIOMETHANE * HOURS            # Nm3 CH4/yr
    feed_t_yr = ch4_needed / blend["CH4_Nm3_per_t"]
    return {
        "basis": {"biomethane_Nm3_h": BIOMETHANE_NM3H, "y_CH4": Y_CH4_BIOMETHANE, "hours_per_yr": HOURS,
                  "note": "CH4 from measured BMP (batch, complete); continuous digester yield comes from ADM1 later"},
        "fm_shares": BASE_FM_SHARES,
        "maize_cap_respected": BASE_FM_SHARES["maize_silage"] <= MAIZE_CAP,
        "blend_VS_kg_per_t": blend["VS_kg_per_t"], "blend_CH4_Nm3_per_t": blend["CH4_Nm3_per_t"],
        "blend_COD_fractions": blend["COD_fractions"],
        "CH4_needed_Nm3_yr": ch4_needed, "feed_t_per_yr": feed_t_yr, "feed_t_per_day": feed_t_yr / 365,
        "feed_by_substrate_t_per_yr": {n: feed_t_yr * BASE_FM_SHARES[n] for n in names},
        "methane_share_by_substrate": {
            n: BASE_FM_SHARES[n] * feeds[n].vs_per_t * feeds[n].bmp / 1000 / blend["CH4_Nm3_per_t"]
            for n in names},
    }


def plot(tab: pd.DataFrame, df: pd.DataFrame, path: Path) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    labels = {"cattle_slurry": "Cattle slurry", "cive_silage": "CIVE silage\n(grass-silage data)",
              "maize_silage": "Maize silage"}
    lit_name = {"cattle_slurry": "cattle_slurry", "cive_silage": "grass_silage", "maize_silage": "maize_silage"}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.2))
    fig.patch.set_facecolor("#fcfcfb")
    x = np.arange(len(tab))
    parts = [("f_pr", "Proteins", "#2a78d6"), ("f_li", "Lipids", "#eb6834"),
             ("f_ch", "Degradable carbohydrates", "#1baf7a"), ("f_xi", "Inerts (non-degradable)", "#a8a79f")]
    bottom = np.zeros(len(tab))
    for col, lab, colr in parts:
        v = tab[col].to_numpy()
        a1.bar(x, v, 0.55, bottom=bottom, color=colr, label=lab, edgecolor="#fcfcfb", linewidth=1.5)
        for i, (b, h) in enumerate(zip(bottom, v)):
            if h > 0.06:
                a1.text(i, b + h / 2, f"{h:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if colr != "#a8a79f" else "#0b0b0b")
        bottom += v
    a1.set_xticks(x, [labels[n] for n in tab.feedstock])
    a1.set_ylabel("Share of feed COD (kg COD/kg COD)", color="#52514e")
    a1.set_title("ADM1 COD fractions (BMP-based)", loc="left", fontsize=10)
    a1.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2)
    a1.set_ylim(0, 1.0)

    w = 0.34
    meas = tab.BMP_measured_Nm3_per_tVS.to_numpy()
    lo = np.array([lit(df, lit_name[n], "BMP_VS", "low") for n in tab.feedstock])
    hi = np.array([lit(df, lit_name[n], "BMP_VS", "high") for n in tab.feedstock])
    a2.bar(x - w / 2, tab.BMP_max_Nm3_per_tVS, w, color="#cde2fb", label="Theoretical maximum (all COD to CH4)")
    a2.bar(x + w / 2, meas, w, color="#2a78d6", label="Published BMP (FNR 2010), bar = range")
    a2.errorbar(x + w / 2, meas, yerr=[meas - lo, hi - meas], fmt="none", ecolor="#0b0b0b", capsize=3, lw=1)
    for i, d in enumerate(tab.degradability_D):
        a2.text(i + w / 2, hi[i] + 12, f"D={d:.2f}", ha="center", fontsize=8)
    a2.set_xticks(x, [labels[n] for n in tab.feedstock])
    a2.set_ylabel("Nm3 CH4 per t VS", color="#52514e")
    a2.set_title("Methane potential: measured vs theoretical", loc="left", fontsize=10)
    a2.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=1)
    a2.set_ylim(0, 520)
    for a in (a1, a2):
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        a.tick_params(colors="#52514e")
        a.yaxis.grid(True, color="#e6e5e0", linewidth=0.6)
        a.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(RAW)
    feeds = build_feeds(df)
    tab = feed_table(feeds)
    checks = run_checks(df, feeds)
    plan = base_case_plan(feeds)

    # Sensitivity: slurry BMP 175 (computed from D1 per-FM averages) instead of 210
    alt = build_feeds(df, slurry_bmp=175.0)["cattle_slurry"]
    plan["sensitivity_slurry_BMP_175"] = {"f_xi": alt.cod_fractions()["f_xi"],
                                          "CH4_Nm3_per_t_FM": alt.vs_per_t * alt.bmp / 1000}

    PROC.mkdir(parents=True, exist_ok=True)
    tab.to_csv(PROC / "feedstock_adm1.csv", index=False, float_format="%.4g")
    checks.to_csv(PROC / "feedstock_checks.csv", index=False)
    (PROC / "base_case_feed_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    plot(tab, df, FIG)

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print(tab[["feedstock", "VS_kg_per_t_FM", "ThOD_kgCOD_per_kgVS", "BMP_measured_Nm3_per_tVS",
               "BMP_max_Nm3_per_tVS", "degradability_D", "f_pr", "f_li", "f_ch", "f_xi",
               "S_IN_kmolN_m3", "CH4_Nm3_per_t_FM"]].round(3).to_string(index=False))
    print()
    print(checks[["check", "description", "value", "reference", "pass", "note"]].to_string(index=False))
    print()
    print(json.dumps({k: plan[k] for k in ["blend_VS_kg_per_t", "blend_CH4_Nm3_per_t", "feed_t_per_yr",
                                           "feed_t_per_day", "feed_by_substrate_t_per_yr",
                                           "methane_share_by_substrate", "maize_cap_respected",
                                           "sensitivity_slurry_BMP_175"]}, indent=1))
    print(f"\nCH4 per kg COD used: {CH4_PER_COD:.4f} Nm3")


if __name__ == "__main__":
    main()
