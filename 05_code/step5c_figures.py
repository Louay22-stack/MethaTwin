"""
Phase 3, step 5c - Figure for the upgrading step:
 (a) simplified process flow diagram of the selected water-scrubbing design with key results,
 (b) product CO2 vs circulating water for three flash pressures (10 absorber stages),
 (c) total energy penalty (electricity + LHV of methane slip) for the same designs.

Reads  04_models_and_simulations/step5_upgrading/{design_sweep.csv, final_design.json}
Writes 06_figures/fig05_upgrading_hpws.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "04_models_and_simulations" / "step5_upgrading"
FIG = ROOT / "06_figures" / "fig05_upgrading_hpws.png"
INK, MUTED, LIGHT, BLUE = "#0b0b0b", "#52514e", "#cde2fb", "#2a78d6"
SERIES = {2.0: "#2a78d6", 2.5: "#eb6834", 3.5: "#1baf7a"}


def pfd(ax, f):
    k, dsg, s = f["kpi"], f["design"], f["streams"]
    ax.set_xlim(0, 100); ax.set_ylim(0, 40); ax.axis("off")

    def box(x, y, w, h, t, sub="", strong=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.8",
                                    fc=BLUE if strong else LIGHT, ec="none"))
        c = "white" if strong else INK
        ax.text(x + w / 2, y + h * 0.64, t, ha="center", va="center", fontsize=8, weight="bold", color=c)
        if sub:
            ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=6.6, color=c)

    def arr(x1, y1, x2, y2, label="", lx=None, ly=None, ha="center"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9, color=MUTED, lw=1))
        if label:
            ax.text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 + 1.0,
                    label, fontsize=6.5, ha=ha, color=INK)

    raw = dsg["raw_dry_Nm3_h"]
    box(0.5, 13, 11, 7, "Raw biogas", f"{raw:.0f} Nm3/h dry\n{100*dsg['y_ch4_dry']:.1f} % CH4, 39 degC")
    box(15, 13, 11, 7, "Chill + KO", "E-100 / V-100\n5 degC")
    box(30, 13, 13, 7, "2-stage compr.", f"K-101/K-102 to {dsg['P_abs_bar']:.0f} bar\nintercooled", strong=True)
    box(47, 11, 12, 11, "Absorber T-201", f"{dsg['n_abs_stages']} eq. stages\n{dsg['P_abs_bar']:.0f} bar, 10 degC\nwater {dsg['water_m3_h']:.0f} m3/h",
        strong=True)
    box(64, 27, 14, 7.5, "Biomethane", f"{k['biomethane_Nm3_h_dry']:.0f} Nm3/h, {k['CH4_pct_dry']:.1f} % CH4\nCO2 {k['CO2_pct_dry']:.2f} %, O2 {k['O2_ppm_dry']:.0f} ppm")
    box(64, 13, 13, 7, "Flash F-201", f"{dsg['P_flash_bar']:.1f} bar\nrecycle {k['recycle_Nm3_h']:.0f} Nm3/h")
    box(64, 1, 13, 7, "CO2 flash F-202", f"{dsg['P_co2_flash_bar']:.2f} bar")
    box(84, 1, 15.5, 7, "Biogenic CO2", f"{k['CO2_stream_Nm3_h']:.0f} Nm3/h, {k['CO2_stream_purity_pct_dry']:.1f} % dry\n~{k['CO2_stream_t_per_yr_at_8400h']:.0f} t/yr")
    box(84, 13, 15.5, 7, "Air stripper T-301", f"air {dsg['air_Nm3_per_m3_water']:.0f} Nm3/m3 water\nslip to off-gas")
    arr(11.5, 16.5, 15, 16.5); arr(26, 16.5, 30, 16.5); arr(43, 16.5, 47, 16.5)
    arr(53, 22.3, 64, 30.5)
    arr(59, 14, 64, 15.5, "rich water", 61.5, 12.6)
    ax.plot([64, 61.5, 61.5, 36.5], [18.5, 18.5, 24.5, 24.5], color=MUTED, lw=1)
    arr(36.5, 24.5, 36.5, 20.3)
    ax.text(49, 25.2, "CH4-rich flash gas recycled to K-102", fontsize=6.5, ha="center", color=INK)
    arr(70.5, 13, 70.5, 8)
    arr(77, 4.5, 84, 4.5)
    arr(77, 6.5, 84, 14)
    ax.plot([91.5, 91.5, 45.0, 45.0], [13, 10, 10, 21], color=MUTED, lw=1)
    arr(45.0, 21, 47, 21)
    ax.text(44, 9.4, "lean water: pump P-301 + chiller E-301,\nback to absorber top",
            fontsize=6.5, color=INK, ha="right")
    ax.text(0.5, 38.5, "(a) Selected high-pressure water-scrubbing design (DWSIM, solved from Python)",
            fontsize=10, ha="left")
    ax.text(0.5, 35.6, f"Electricity {k['P_el_total_kW']:.1f} kW = {k['specific_el_kWh_per_Nm3_raw']:.3f} kWh/Nm3 raw gas"
            f"   |   CH4 slip {k['CH4_slip_pct']:.2f} %   |   CH4 recovery {k['CH4_recovery_pct']:.2f} %",
            fontsize=7.5, ha="left", color=MUTED)


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    sw = pd.read_csv(D / "design_sweep.csv")
    f = json.loads((D / "final_design.json").read_text())
    fig = plt.figure(figsize=(11, 8.2))
    fig.patch.set_facecolor("#fcfcfb")
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.32, wspace=0.25)
    pfd(fig.add_subplot(gs[0, :]), f)

    ok = sw[(sw.converged == True) & (sw.n_abs_stages == 10)]
    b, c = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
    for pf, col in SERIES.items():
        dd = ok[ok.P_flash_bar == pf].sort_values("water_m3_h")
        b.semilogy(dd.water_m3_h, dd.CO2_pct_dry, "-o", color=col, lw=2, ms=6, mec="#fcfcfb", label=f"flash {pf} bar")
        c.plot(dd.water_m3_h, dd.energy_penalty_kW, "-o", color=col, lw=2, ms=6, mec="#fcfcfb", label=f"flash {pf} bar")
    b.axhline(2.5, color=INK, lw=1, ls="--")
    b.text(70.5, 2.7, "grid limit 2.5 %", fontsize=7.5, ha="right")
    sel = f["design"]
    b.plot(sel["water_m3_h"], f["kpi"]["CO2_pct_dry"], "s", ms=11, mfc="none", mec=INK, mew=1.5)
    c.plot(sel["water_m3_h"], f["kpi"]["energy_penalty_kW"], "s", ms=11, mfc="none", mec=INK, mew=1.5)
    c.text(sel["water_m3_h"], f["kpi"]["energy_penalty_kW"] + 9, "selected", fontsize=7.5, ha="center")
    b.set_title("(b) Product CO2 (10 absorber stages)", loc="left", fontsize=10)
    c.set_title("(c) Energy penalty = electricity + LHV of CH4 slip", loc="left", fontsize=10)
    b.set_ylabel("CO2 in biomethane (mol %, dry)", color=MUTED)
    c.set_ylabel("kW", color=MUTED)
    c.text(0.02, 0.97, "At 3.5 bar and >= 55 m3/h the rich water is\nunder-saturated: the flash releases no gas\n"
           "and dissolved CH4 is lost (slip 1-10 %).", transform=c.transAxes, fontsize=7, va="top", color=MUTED)
    for a in (b, c):
        a.set_xlabel("Circulating water (m3/h)", color=MUTED)
        for s_ in ("top", "right"):
            a.spines[s_].set_visible(False)
        a.tick_params(colors=MUTED)
        a.grid(True, color="#e6e5e0", lw=0.6)
        a.set_axisbelow(True)
        a.legend(frameon=False, fontsize=7.5, loc="lower left" if a is b else "center left")
    fig.savefig(FIG, dpi=200, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print("written", FIG)


if __name__ == "__main__":
    main()
