"""
Phase 3, step 7d - Figure for techno-economics and optimisation:
 (a) LCOE of confirmed optimal designs vs plant size, with the CRE benchmark (median, IQR) and tariff
 (b) 200 Nm3/h designs: naive scale-up, nominal optimum, robust design (all full-simulation results)
 (c) Monte Carlo distribution of LCOE at the nominal optimum (surrogates, 10,000 samples)
 (d) tornado: one-at-a-time swing of LCOE at the nominal optimum
Writes 06_figures/fig07_tea_optimisation.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "04_models_and_simulations" / "step7_tea"
FIG = ROOT / "06_figures" / "fig07_tea_optimisation.png"
MUTED, INK, BLUE, LIGHT, ORANGE, AQUA = "#52514e", "#0b0b0b", "#2a78d6", "#cde2fb", "#eb6834", "#1baf7a"


def style(a):
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.tick_params(colors=MUTED)
    a.grid(True, color="#e6e5e0", lw=0.6)
    a.set_axisbelow(True)


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    opt = json.loads((D / "optimisation.json").read_text())
    unc = json.loads((D / "uncertainty.json").read_text())
    rob = json.loads((D / "robust_design.json").read_text())
    mc = pd.read_csv(D / "montecarlo.csv")
    tor = pd.read_csv(D / "tornado.csv")
    fig, ax = plt.subplots(2, 2, figsize=(11.5, 8.4))
    fig.patch.set_facecolor("#fcfcfb")

    # (a) LCOE vs size
    a = ax[0, 0]
    pts = sorted((v["final"]["simulation"]["bm_net_Nm3_h"], v["final"]["simulation"]["LCOE_EUR_MWh"])
                 for v in opt.values() if v["final"])
    a.axhspan(111.7, 146.0, color=LIGHT, lw=0, label="CRE 2024 interquartile range")
    a.axhline(129.6, color=BLUE, lw=1, ls=":", label="CRE median 129.6")
    a.axhline(152.8, color=INK, lw=1, ls="--", label="avg tariff 152.8 (BI 2023)")
    a.plot(*zip(*pts), "-o", color=ORANGE, lw=2, ms=7, mec="#fcfcfb", label="MethaTwin optimum (verified)")
    for x, y in pts:
        a.text(x, y + 1.4, f"{y:.0f}", ha="center", fontsize=8)
    a.set_xlabel("biomethane injected (Nm3/h)", color=MUTED); a.set_ylabel("LCOE (EUR/MWh HHV)", color=MUTED)
    a.set_title("(a) Economies of scale (full simulation of each optimum)", loc="left", fontsize=9.5)
    a.set_ylim(105, 165)
    a.legend(frameon=False, fontsize=7.2, loc="lower left")
    style(a)

    # (b) 200 Nm3/h designs
    a = ax[0, 1]
    c = unc["comparison_200"]
    rows = [("Naive scale-up\n(base design)", c["naive_scaled_base"]["simulation"], c["naive_scaled_base"]["design"]),
            ("Nominal optimum", c["optimum"]["simulation"], c["optimum"]["design"]),
            ("Robust optimum\n(K_I,NH3 >= 0.0016)", rob["final"]["simulation"], rob["final"]["design"])]
    cols = ["#9ec5f4", BLUE, AQUA]
    for i, ((lab, s, dsg), col) in enumerate(zip(rows, cols)):
        a.bar(i, s["LCOE_EUR_MWh"], color=col, width=0.6)
        a.text(i, s["LCOE_EUR_MWh"] + 1, f"{s['LCOE_EUR_MWh']:.1f}", ha="center", fontsize=8.5)
        a.text(i, 60, f"VFA {s['VFA_gCOD_L']:.1f} g/L\nHRT {dsg['hrt_d']:.0f} d\nCIVE {100*dsg['cive_share']:.0f} %\n"
                      f"feed {dsg['feed_t_d']:.0f} t/d\nNPV {s['NPV_EUR']/1e6:+.2f} MEUR",
               ha="center", va="bottom", fontsize=7.2, color="white" if i else INK)
    a.set_xticks(range(3), [r[0] for r in rows], fontsize=8)
    a.set_ylim(50, 175); a.set_ylabel("LCOE (EUR/MWh)", color=MUTED)
    a.set_title("(b) 200 Nm3/h: flat optimum; robustness costs +8.4 EUR/MWh", loc="left", fontsize=9.5)
    style(a)

    # (c) Monte Carlo
    a = ax[1, 0]
    st = mc[mc.p_stable >= 0.5]
    a.hist(st.LCOE_EUR_MWh, bins=60, color=BLUE, alpha=0.85)
    m = unc["montecarlo"]["LCOE_stable"]
    for k, ls in (("P10", ":"), ("P50", "-"), ("P90", ":")):
        a.axvline(m[k], color=INK, lw=1, ls=ls)
        a.text(m[k], a.get_ylim()[1] * 0.96, f" {k} {m[k]:.0f}", fontsize=7.5, va="top")
    a.axvspan(111, 169, color=LIGHT, alpha=0.5, lw=0)
    a.text(112, a.get_ylim()[1] * 0.6, "tariff range\n111-169", fontsize=7.2, color=MUTED)
    mu = unc["montecarlo"]
    a.set_title(f"(c) Monte Carlo, 10,000 samples: P(NPV>0) = {100*mu['P_NPV_positive_stable']:.0f} %, "
                f"{100*mu['share_predicted_unstable']:.0f} % unstable", loc="left", fontsize=9.5)
    a.set_xlabel("LCOE (EUR/MWh), stable samples", color=MUTED); a.set_ylabel("count", color=MUTED)
    style(a)

    # (d) tornado
    a = ax[1, 1]
    t = tor.sort_values("swing")
    base = unc["tornado_nominal_LCOE"]
    for i, r in enumerate(t.itertuples()):
        lo, hi = min(r.LCOE_low, r.LCOE_high), max(r.LCOE_low, r.LCOE_high)
        a.barh(i, hi - lo, left=lo, color=BLUE, height=0.6)
    a.axvline(base, color=INK, lw=1)
    a.set_xlim(min(t.LCOE_low.min(), t.LCOE_high.min()) - 3, max(t.LCOE_low.max(), t.LCOE_high.max()) + 3)
    a.set_yticks(range(len(t)), t.input, fontsize=7.6)
    a.set_xlabel(f"LCOE (EUR/MWh); line = nominal {base:.0f} (surrogate)", color=MUTED)
    a.set_title("(d) What drives the cost (one at a time)", loc="left", fontsize=9.5)
    style(a)

    fig.tight_layout()
    fig.savefig(FIG, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("written", FIG)


if __name__ == "__main__":
    main()
