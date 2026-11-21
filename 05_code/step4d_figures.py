"""
Phase 3, step 4d - Figure for the ADM1 step: (a) BSM2 benchmark parity plot,
(b) base-case methane output and one-at-a-time sensitivities.

Reads  04_models_and_simulations/step4_adm1/{bsm2_validation.csv, base_case_results.json,
       base_case_sensitivity.json}
Writes 06_figures/fig04_adm1_validation_and_base_case.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "04_models_and_simulations" / "step4_adm1"
FIG = ROOT / "06_figures" / "fig04_adm1_validation_and_base_case.png"


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    val = pd.read_csv(D / "bsm2_validation.csv")
    base = json.loads((D / "base_case_results.json").read_text())
    sens = json.loads((D / "base_case_sensitivity.json").read_text())

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1, 1.25]})
    fig.patch.set_facecolor("#fcfcfb")

    v = val[val.reference > 0]
    a1.loglog(v.reference, v.model, "o", ms=6, color="#2a78d6", mec="#fcfcfb", mew=1.2)
    lim = [v.reference.min() / 3, v.reference.max() * 3]
    a1.plot(lim, lim, color="#52514e", lw=1)
    a1.set_xlim(lim); a1.set_ylim(lim)
    a1.set_xlabel("BSM2 reference value (Rosen & Jeppsson 2006)", color="#52514e")
    a1.set_ylabel("MethaTwin ADM1", color="#52514e")
    a1.set_title(f"(a) Benchmark: {int(val['pass'].sum())}/{len(val)} variables within 1 %"
                 f"\n     max error {val.rel_err_pct.abs().max():.1e} %", loc="left", fontsize=10)
    a1.text(0.97, 0.05, "35 states, pH and gas outputs\nspanning 10 orders of magnitude",
            transform=a1.transAxes, ha="right", va="bottom", fontsize=8, color="#52514e")

    labels = ["Base case\n(HRT 60 d, K_I,NH3 0.0018)"] + [k.replace(" (", "\n(") for k in sens]
    vals = [base["CH4_Nm3_h"]] + [s.get("CH4_Nm3_h", np.nan) for s in sens.values()]
    order = np.argsort(vals)
    y = np.arange(len(vals))
    colors = ["#2a78d6" if i == 0 else "#9ec5f4" for i in order]
    a2.barh(y, np.array(vals)[order], color=colors, height=0.6)
    for yi, i in zip(y, order):
        txt = f"{vals[i]:.0f}" if vals[i] > 0 else "0  (digester sours, pH 4.6)"
        a2.text(max(vals[i], 0) + 3, yi, txt, va="center", fontsize=8)
    a2.axvline(200 * 0.97, color="#0b0b0b", lw=1, ls="--")
    a2.text(200 * 0.97 - 3, 0.0, "target\n194 Nm3/h CH4\n= 200 Nm3/h\nbiomethane", fontsize=7.5,
            va="center", ha="right")
    a2.set_yticks(y, [labels[i] for i in order], fontsize=7.5)
    a2.set_xlim(0, 260)
    a2.set_xlabel("Methane produced (Nm3 CH4/h)", color="#52514e")
    a2.set_title("(b) Base-case digester and one-at-a-time sensitivities", loc="left", fontsize=10)

    for a in (a1, a2):
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        a.tick_params(colors="#52514e")
        a.grid(True, color="#e6e5e0", linewidth=0.6, which="major")
        a.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("written", FIG)


if __name__ == "__main__":
    main()
