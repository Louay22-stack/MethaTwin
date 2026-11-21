"""
Phase 3, step 6a - Design of experiments: N coupled plant simulations (ADM1 -> DWSIM).

Latin hypercube (scipy.stats.qmc, seed 42) over 6 design/operating variables and 2 uncertain
kinetic parameters (log-uniform). Runs in parallel worker processes, each with its own DWSIM
engine; every result is appended to the CSV as soon as it is available, so the run can be
interrupted and resumed (finished sample ids are skipped).

Output: 03_data/processed/doe_simulations.csv  (one row per sample, inputs + outputs + status)
Run from the project root:  python 05_code/step6a_doe.py [N] [workers]
"""
from __future__ import annotations

import csv
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import qmc

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "03_data" / "processed" / "doe_simulations.csv"

# name: (low, high, scale)
SPACE = {
    "maize_share": (0.0, 0.15, "lin"),        # decree 2016-929 cap on main crops
    "cive_share": (0.05, 0.45, "lin"),        # slurry >= 40 % FM (wet digestion)
    "feed_t_d": (60.0, 160.0, "lin"),
    "hrt_d": (40.0, 110.0, "lin"),
    "water_per_kNm3": (100.0, 200.0, "lin"),  # step 5 optimum ~130
    "p_flash_bar": (2.0, 3.5, "lin"),
    "k_dis": (0.05, 0.5, "log"),              # calibrated 0.1 (Bulkowska 2015), BSM2 0.5
    "K_I_nh3": (0.0012, 0.0084, "log"),       # literature range (Bulkowska 2015 Tab. 5)
}

_DW = None


def design(n: int, seed: int = 42) -> list[dict]:
    u = qmc.LatinHypercube(d=len(SPACE), seed=seed).random(n)
    pts = []
    for i, row in enumerate(u):
        x = {"sample_id": i}
        for (k, (lo, hi, sc)), v in zip(SPACE.items(), row):
            x[k] = lo + v * (hi - lo) if sc == "lin" else float(np.exp(np.log(lo) + v * (np.log(hi) - np.log(lo))))
        pts.append(x)
    return pts


def _init():
    global _DW
    from dwsim_bridge import load_dwsim
    _DW = load_dwsim()


def _work(x: dict) -> dict:
    from methatwin.plant import simulate_plant
    sid = x.pop("sample_id")
    try:
        r = simulate_plant(x, _DW)
    except Exception as exc:  # never let one sample kill the pool
        r = {**x, "status": f"fatal: {str(exc)[:120]}"}
    r["sample_id"] = sid
    return {k: (float(v) if isinstance(v, (np.floating, np.bool_)) else v) for k, v in r.items()}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    pts = design(n)
    done = set()
    if OUT.exists():
        with OUT.open(newline="", encoding="utf-8") as f:
            done = {int(float(r["sample_id"])) for r in csv.DictReader(f)}
    todo = [p for p in pts if p["sample_id"] not in done]
    print(f"{len(done)} done, {len(todo)} to run with {workers} workers", flush=True)
    fields = None
    t0 = time.time()
    ctx = mp.get_context("spawn")
    with ctx.Pool(workers, initializer=_init) as pool:
        for i, r in enumerate(pool.imap_unordered(_work, todo, chunksize=1), 1):
            if fields is None:
                fields = ["sample_id", *SPACE, "status", "time_s", "V_liq_m3", "OLR_kgVS_m3_d", "VS_t_d",
                          "CH4_Nm3_h", "biogas_dry_Nm3_h", "y_CH4_dry", "pH", "VFA_gCOD_L", "free_NH3_mgN_L",
                          "TAN_gN_L", "CH4_yield_Nm3_tVS", "residual_Xc_kgCOD_m3", "adm1_COD_closure_pct",
                          "adm1_max_abs_rhs", "digester_stable", "upg_converged", "upg_iterations",
                          "water_m3_h", "biomethane_Nm3_h", "BM_CH4_pct", "BM_CO2_pct", "BM_O2_ppm",
                          "BM_HHV_kWh_Nm3", "BM_Wobbe", "CH4_slip_pct", "P_el_upg_kW", "spec_el_kWh_Nm3_raw",
                          "CO2_stream_Nm3_h", "CO2_stream_t_yr", "upg_mass_closure_pct", "upg_in_validity_window"]
                new = not OUT.exists()
                fh = OUT.open("a", newline="", encoding="utf-8")
                w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
                if new:
                    w.writeheader()
            w.writerow(r)
            fh.flush()
            if i % 25 == 0 or i == len(todo):
                el = time.time() - t0
                print(f"{i}/{len(todo)}  elapsed {el/60:.1f} min  eta {el/i*(len(todo)-i)/60:.1f} min", flush=True)
    if fields is not None:
        fh.close()


if __name__ == "__main__":
    main()
