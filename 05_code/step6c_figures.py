"""
Phase 3, step 6c - Figure for the surrogate step: held-out test parity plots for three
headline outputs and permutation importance of the inputs.

Reads  04_models_and_simulations/step6_surrogate/{parity_*.csv, metrics.csv, importance.csv, speed.json}
Writes 06_figures/fig06_surrogate_test_performance.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "04_models_and_simulations" / "step6_surrogate"
FIG = ROOT / "06_figures" / "fig06_surrogate_test_performance.png"
MUTED = "#52514e"
ABBR = {"RandomForest": "RF", "XGBoost": "XGB", "MLP": "MLP"}
LABEL = {"maize_share": "maize share", "cive_share": "CIVE share", "feed_t_d": "feed rate",
         "hrt_d": "HRT", "water_per_kNm3": "scrubber water", "p_flash_bar": "flash pressure",
         "k_dis": "k_dis (uncertain)", "K_I_nh3": "K_I,NH3 (uncertain)",
         "y_CH4_dry": "biogas CH4 fraction*", "biogas_dry_Nm3_h": "biogas flow*",
         "flash_saturation_index": "flash saturation index*"}


def style(a):
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.tick_params(colors=MUTED)
    a.grid(True, color="#e6e5e0", lw=0.6)
    a.set_axisbelow(True)


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    met = pd.read_csv(D / "metrics.csv").set_index("target")
    imp = pd.read_csv(D / "importance.csv")
    speed = json.loads((D / "speed.json").read_text())
    fig, ax = plt.subplots(2, 3, figsize=(12, 7.6))
    fig.patch.set_facecolor("#fcfcfb")
    panels = [("CH4_Nm3_h", "Digester methane (Nm3/h)", False),
              ("biomethane_Nm3_h", "Biomethane to grid (Nm3/h)", False),
              ("BM_CO2_pct", "CO2 in biomethane (mol %)", True)]
    for a, (t, title, log) in zip(ax[0], panels):
        p = pd.read_csv(D / f"parity_{t}.csv")
        a.scatter(p.actual, p.predicted, s=10, color="#2a78d6", alpha=0.6, lw=0)
        lo, hi = (p[["actual", "predicted"]].clip(lower=1e-3).min().min(), p[["actual", "predicted"]].max().max())
        a.plot([lo, hi], [lo, hi], color=MUTED, lw=1)
        if log:
            a.set_xscale("log"); a.set_yscale("log")
            a.axhline(2.5, color="#0b0b0b", lw=0.8, ls="--"); a.axvline(2.5, color="#0b0b0b", lw=0.8, ls="--")
        r = met.loc[t]
        extra = f"\nR2 (log10) = {r['test_R2_log']:.3f}" if log and not pd.isna(r.get("test_R2_log")) else ""
        a.set_title(f"{title}\n{r['best_model']}, test R2 = {r['test_R2']:.3f}{extra}", loc="left", fontsize=9.5)
        a.set_xlabel("coupled simulation (test set)", color=MUTED)
        a.set_ylabel("surrogate prediction", color=MUTED)
        style(a)

    for a, t, title in ((ax[1, 0], "CH4_Nm3_h", "Input importance: digester methane"),
                        (ax[1, 1], "BM_CO2_pct", "Input importance: CO2 in biomethane")):
        d = imp[imp.target == t].sort_values("importance_mean")
        a.barh([LABEL[i] for i in d.input], d.importance_mean, xerr=d.importance_std, color="#2a78d6",
               height=0.6, error_kw=dict(ecolor=MUTED, lw=1))
        a.set_xlabel("drop in test R2 when the input is shuffled", color=MUTED)
        a.set_title(title, loc="left", fontsize=9.5)
        style(a)
    ax[1, 1].text(0.98, 0.02, "* cascade / physics features", transform=ax[1, 1].transAxes, ha="right",
                  fontsize=7, color=MUTED)

    a = ax[1, 2]
    a.axis("off")
    cl = met[met.block == "classifier"]
    reg = met[met.block != "classifier"]
    lines = ["Held-out test set (20 %)", "never used for tuning", "RF random forest, XGB XGBoost,", "MLP neural network", ""]
    for t, r in reg.iterrows():
        lines.append(f"{t:<17s}{ABBR[r['best_model']]:<5s} R2 {r['test_R2']:.3f}")
    lines.append("")
    for t, r in cl.iterrows():
        lines.append(f"{t:<17s}{ABBR[r['best_model']]:<5s} AUC {r['test_AUC']:.3f}")
    lines += ["", f"Simulation:  {speed['mean_coupled_simulation_s']:.1f} s/point",
              f"Surrogates:  {speed['surrogate_batch_per_point_s']*1e3:.2f} ms/point",
              f"Speed-up:    ~{speed['speedup_batch']:,.0f}x (batch)"]
    a.text(0, 1, "\n".join(lines), va="top", family="DejaVu Sans Mono", fontsize=7.6)
    fig.tight_layout()
    fig.savefig(FIG, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("written", FIG)


if __name__ == "__main__":
    main()
