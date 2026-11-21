"""
Phase 3, step 6b - Machine-learning surrogates of the coupled plant model.

Data   : 03_data/processed/doe_simulations.csv (step 6a, Latin hypercube, 8 inputs).
Split  : 80 % train / 20 % test, random, seed 42. The test set is never used for tuning.
Tuning : 5-fold cross-validation on the training set (RandomizedSearchCV, small grids).
Models : Random Forest, XGBoost, MLP (StandardScaler + MLPRegressor) - best by CV RMSE.
Tasks  :
  classifiers - digester_stable (all solved samples); upgrading_valid (stable samples: scrubber
                converged and mass balance closed within 0.1 %); spec_ok = CO2 < 2.5 % (valid samples)
  regressors  - digester outputs (all solved samples) and upgrading outputs (upgraded samples).
  Strongly skewed positive targets (CO2 %, slip %) are learned as log10 and reported on the
  original scale too.
Outputs: 04_models_and_simulations/step6_surrogate/{metrics.csv, models/*.joblib, speed.json,
         importance.csv}
Run from the project root:  python 05_code/step6b_surrogate.py
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score,
                             roc_auc_score)
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier, XGBRegressor

warnings.filterwarnings("ignore", category=UserWarning)
ROOT = Path(__file__).resolve().parents[1]
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "03_data" / "processed" / "doe_simulations.csv"
OUT = ROOT / "04_models_and_simulations" / "step6_surrogate"
INPUTS = ["maize_share", "cive_share", "feed_t_d", "hrt_d", "water_per_kNm3", "p_flash_bar", "k_dis", "K_I_nh3"]
LOG_INPUTS = {"k_dis", "K_I_nh3"}          # sampled log-uniform -> give models the log
DIGESTER_TARGETS = {"CH4_Nm3_h": False, "y_CH4_dry": False, "pH": False, "VFA_gCOD_L": False,
                    "free_NH3_mgN_L": False}
UPGRADING_TARGETS = {"biomethane_Nm3_h": False, "BM_CO2_pct": True, "BM_O2_ppm": False,
                     "CH4_slip_pct": True, "P_el_upg_kW": False}
SEED = 42


UPG_EXTRA = ["y_CH4_dry", "biogas_dry_Nm3_h", "flash_saturation_index"]


def add_physics_features(df: pd.DataFrame) -> pd.DataFrame:
    """Physics-informed feature for the scrubber: CO2 loading of the water per bar of flash
    pressure, (1 - y_CH4) * 1000 / water_per_kNm3 / p_flash  [Nm3 CO2 per m3 water per bar].
    It decides whether the flash water is under-saturated (step 5: flash releases no gas)."""
    df = df.copy()
    df["flash_saturation_index"] = (1 - df.y_CH4_dry) * 1000.0 / df.water_per_kNm3 / df.p_flash_bar
    return df


def features(df: pd.DataFrame, upgrading: bool = False) -> np.ndarray:
    X = df[INPUTS].copy()
    for c in LOG_INPUTS:
        X[c] = np.log10(X[c])
    if upgrading:  # cascade: digester outputs (from the digester surrogate in use) + physics feature
        X = pd.concat([X, add_physics_features(df)[UPG_EXTRA]], axis=1)
    return X.to_numpy(float)


def regressors():
    return {
        "RandomForest": (RandomForestRegressor(random_state=SEED, n_jobs=-1),
                         {"n_estimators": [300, 600], "max_features": [0.5, 0.8, 1.0],
                          "min_samples_leaf": [1, 2, 4]}),
        "XGBoost": (XGBRegressor(random_state=SEED, n_jobs=4, tree_method="hist"),
                    {"n_estimators": [400, 800, 1200], "learning_rate": [0.03, 0.06, 0.1],
                     "max_depth": [3, 4, 6], "subsample": [0.8, 1.0], "colsample_bytree": [0.8, 1.0]}),
        "MLP": (make_pipeline(StandardScaler(), MLPRegressor(max_iter=3000, early_stopping=True,
                                                             random_state=SEED)),
                {"mlpregressor__hidden_layer_sizes": [(64, 64), (128, 64), (64, 64, 32)],
                 "mlpregressor__alpha": [1e-5, 1e-4, 1e-3],
                 "mlpregressor__learning_rate_init": [1e-3, 3e-3]}),
    }


def fit_best_regressor(X, y, n_iter=12):
    cv = KFold(5, shuffle=True, random_state=SEED)
    best, best_name, best_rmse, cv_scores = None, None, np.inf, {}
    for name, (est, grid) in regressors().items():
        ys = y
        if name == "MLP":  # scale target for the network
            mu, sd = y.mean(), y.std() or 1.0
            ys = (y - mu) / sd
        s = RandomizedSearchCV(est, grid, n_iter=n_iter, cv=cv, scoring="neg_root_mean_squared_error",
                               random_state=SEED, n_jobs=1 if name != "MLP" else 4)
        s.fit(X, ys)
        rmse = -s.best_score_ * (sd if name == "MLP" else 1.0)
        cv_scores[name] = rmse
        if rmse < best_rmse:
            best_rmse, best_name = rmse, name
            best = (s.best_estimator_, (mu, sd) if name == "MLP" else None)
    return best_name, best, cv_scores


def predict(model_tuple, X):
    est, scale = model_tuple
    p = est.predict(X)
    return p * scale[1] + scale[0] if scale is not None else p


def regression_block(df: pd.DataFrame, targets: dict, label: str, rows: list, models: dict):
    tr, te = train_test_split(df, test_size=0.2, random_state=SEED)
    upg = label == "upgrading"
    Xtr, Xte = features(tr, upg), features(te, upg)
    for t, log in targets.items():
        ytr = np.log10(np.maximum(tr[t].to_numpy(float), 1e-6)) if log else tr[t].to_numpy(float)
        yte_raw = te[t].to_numpy(float)
        name, mt, cvs = fit_best_regressor(Xtr, ytr)
        p = predict(mt, Xte)
        p_raw = 10 ** p if log else p
        row = {"block": label, "target": t, "log_target": log, "n_train": len(tr), "n_test": len(te),
               "best_model": name, **{f"cv_rmse_{k}": v for k, v in cvs.items()},
               "test_R2": r2_score(yte_raw, p_raw), "test_RMSE": mean_squared_error(yte_raw, p_raw) ** 0.5,
               "test_MAE": mean_absolute_error(yte_raw, p_raw), "test_range": float(np.ptp(yte_raw))}
        if log:
            row["test_R2_log"] = r2_score(np.log10(np.maximum(yte_raw, 1e-6)), p)
        rows.append(row)
        if hasattr(mt[0], "n_jobs"):
            mt[0].set_params(n_jobs=1)   # single-thread prediction (thread start-up dominates for 1 point)
        models[t] = {"model": mt, "log": log, "name": name, "upgrading_features": upg}
        print(f"  {t:18s} best={name:12s} test R2={row['test_R2']:.4f}"
              + (f" (log R2={row['test_R2_log']:.4f})" if log else ""), flush=True)
        if t in ("CH4_Nm3_h", "biomethane_Nm3_h", "BM_CO2_pct"):
            pd.DataFrame({"actual": yte_raw, "predicted": p_raw}).to_csv(OUT / f"parity_{t}.csv", index=False)
    return tr, te


def classifier(df: pd.DataFrame, target: str, rows: list, models: dict, upg: bool = False):
    tr, te = train_test_split(df, test_size=0.2, random_state=SEED, stratify=df[target])
    Xtr, Xte = features(tr, upg), features(te, upg)
    ytr, yte = tr[target].astype(int).to_numpy(), te[target].astype(int).to_numpy()
    cands = {"RandomForest": RandomForestClassifier(n_estimators=600, min_samples_leaf=2, random_state=SEED, n_jobs=-1),
             "XGBoost": XGBClassifier(n_estimators=600, learning_rate=0.05, max_depth=4, random_state=SEED, n_jobs=4),
             "MLP": make_pipeline(StandardScaler(), MLPClassifier((64, 64), max_iter=3000, early_stopping=True,
                                                                  random_state=SEED))}
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    scores = {k: cross_val_score(m, Xtr, ytr, cv=cv, scoring="roc_auc").mean() for k, m in cands.items()}
    best = max(scores, key=scores.get)
    m = cands[best].fit(Xtr, ytr)
    if hasattr(m, "n_jobs"):
        m.set_params(n_jobs=1)
    proba = m.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)
    rows.append({"block": "classifier", "target": target, "n_train": len(tr), "n_test": len(te),
                 "best_model": best, **{f"cv_auc_{k}": v for k, v in scores.items()},
                 "test_AUC": roc_auc_score(yte, proba), "test_accuracy": accuracy_score(yte, pred),
                 "test_F1": f1_score(yte, pred), "positive_rate": float(yte.mean())})
    models[target] = {"model": (m, None), "log": False, "name": best, "classifier": True, "upgrading_features": upg}
    print(f"  {target:18s} best={best:12s} test AUC={rows[-1]['test_AUC']:.4f} acc={rows[-1]['test_accuracy']:.4f}",
          flush=True)


def main() -> None:
    (OUT / "models").mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA)
    solved = df[df.status.isin(["ok", "digester_unstable", "upgrading_not_converged"])
                | df.status.str.startswith("upgrading_error")].copy()
    solved["digester_stable"] = solved.digester_stable.astype(float) > 0.5
    # Data-quality gate (applied here so the raw DoE file keeps every run for traceability):
    # an 'ok' scrubber run must close its mass balance within 0.1 % (117 runs failed this,
    # all at low flash pressure + high water flow, where DWSIM's column solver is loose).
    gate = (df.status == "ok") & (df.upg_mass_closure_pct.abs() <= 0.1)
    df.loc[(df.status == "ok") & ~gate, "status"] = "upgrading_balance_not_closed"
    solved.loc[df.loc[solved.index, "status"] == "upgrading_balance_not_closed", "status"] = "upgrading_balance_not_closed"
    ok = df[gate].copy()
    ok["spec_ok"] = ok.BM_CO2_pct < 2.5
    stable = solved[solved.digester_stable].copy()
    stable["upgrading_valid"] = df.loc[stable.index, "status"] == "ok"
    print(f"samples: {len(df)} total, {len(solved)} digester solved, {len(ok)} fully upgraded; "
          f"status counts (after quality gate): {df.status.value_counts().to_dict()}", flush=True)

    rows, models = [], {}
    print("Classifiers")
    classifier(solved, "digester_stable", rows, models)
    classifier(stable, "upgrading_valid", rows, models)   # where the scrubber simulation is reliable
    classifier(ok, "spec_ok", rows, models, upg=True)
    print("Digester regressors"); regression_block(solved, DIGESTER_TARGETS, "digester", rows, models)
    print("Upgrading regressors"); _, te = regression_block(ok, UPGRADING_TARGETS, "upgrading", rows, models)

    met = pd.DataFrame(rows)
    met.to_csv(OUT / "metrics.csv", index=False)
    joblib.dump({"inputs": INPUTS, "log_inputs": sorted(LOG_INPUTS), "upgrading_extra": UPG_EXTRA,
                 "models": models}, OUT / "models" / "surrogates.joblib")

    # Speed-up: one surrogate evaluation of all models vs one coupled simulation
    X1 = {False: features(te.iloc[[0]]), True: features(te.iloc[[0]], True)}
    t0 = time.perf_counter()
    for _ in range(200):
        for m in models.values():
            x1 = X1[m["upgrading_features"]]
            predict(m["model"], x1) if not m.get("classifier") else m["model"][0].predict_proba(x1)
    t_sur = (time.perf_counter() - t0) / 200
    XB = {False: features(te), True: features(te, True)}
    for m in models.values():  # batch prediction may use threads again
        if hasattr(m["model"][0], "n_jobs"):
            m["model"][0].set_params(n_jobs=-1)
    t0 = time.perf_counter()
    for m in models.values():
        xb = XB[m["upgrading_features"]]
        predict(m["model"], xb) if not m.get("classifier") else m["model"][0].predict_proba(xb)
    t_batch = (time.perf_counter() - t0) / len(te)
    t_sim = float(ok.time_s.mean())
    speed = {"mean_coupled_simulation_s": t_sim, "surrogate_single_point_all_models_s": t_sur,
             "surrogate_batch_per_point_s": t_batch, "speedup_single": t_sim / t_sur, "speedup_batch": t_sim / t_batch}
    (OUT / "speed.json").write_text(json.dumps(speed, indent=2), encoding="utf-8")
    print(json.dumps(speed, indent=1))

    # Permutation importance on the test set for two headline targets
    imp_rows = []
    for t, block_df in (("CH4_Nm3_h", solved), ("BM_CO2_pct", ok)):
        _, te_t = train_test_split(block_df, test_size=0.2, random_state=SEED)
        m = models[t]
        est = m["model"][0]
        y = np.log10(np.maximum(te_t[t].to_numpy(float), 1e-6)) if m["log"] else te_t[t].to_numpy(float)
        if m["model"][1] is not None:
            y = (y - m["model"][1][0]) / m["model"][1][1]
        pi = permutation_importance(est, features(te_t, m["upgrading_features"]), y, n_repeats=10,
                                    random_state=SEED, scoring="r2")
        names = INPUTS + (UPG_EXTRA if m["upgrading_features"] else [])
        for name, mu, sd in zip(names, pi.importances_mean, pi.importances_std):
            imp_rows.append({"target": t, "input": name, "importance_mean": mu, "importance_std": sd})
    pd.DataFrame(imp_rows).to_csv(OUT / "importance.csv", index=False)
    pd.set_option("display.width", 220, "display.max_columns", 30)
    print(met.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
