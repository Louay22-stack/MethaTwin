"""
Phase 3, step 6d - Overfitting and cascade checks for the surrogates.

1. Generalisation gap: R2 on the training set vs 5-fold CV vs the held-out test set.
   Overfitting = a large train-test gap, not a high test score.
2. Honest cascade test: the upgrading surrogates were trained/tested with the TRUE digester
   outputs (biogas flow, CH4 fraction) as features. In use these come from the digester
   surrogates, whose errors propagate. Here the test-set features are rebuilt from the
   digester-surrogate predictions and the upgrading R2 is recomputed.

Reads  03_data/processed/doe_simulations.csv, 04_models_and_simulations/step6_surrogate/models
Writes 04_models_and_simulations/step6_surrogate/overfitting_check.csv
Run from the project root:  python 05_code/step6d_overfitting_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold, cross_val_predict, train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))
import step6b_surrogate as S  # noqa: E402  (same split, features and gate as training)

OUT = S.OUT


def main() -> None:
    bundle = joblib.load(OUT / "models" / "surrogates.joblib")
    M = bundle["models"]
    df = pd.read_csv(S.DATA)
    solved = df.copy()
    gate = (df.status == "ok") & (df.upg_mass_closure_pct.abs() <= 0.1)
    ok = df[gate].copy()
    rows = []
    for block_df, targets, upg in ((solved, S.DIGESTER_TARGETS, False), (ok, S.UPGRADING_TARGETS, True)):
        tr, te = train_test_split(block_df, test_size=0.2, random_state=S.SEED)
        Xtr, Xte = S.features(tr, upg), S.features(te, upg)
        for t, log in targets.items():
            m = M[t]
            f = (lambda y: np.log10(np.maximum(y, 1e-6))) if log else (lambda y: y)
            ytr, yte = f(tr[t].to_numpy(float)), f(te[t].to_numpy(float))
            r_train = r2_score(ytr, S.predict(m["model"], Xtr))
            r_test = r2_score(yte, S.predict(m["model"], Xte))
            # CV on the training set with the selected configuration (out-of-fold predictions)
            est, scale = m["model"]
            y_cv_target = (ytr - scale[0]) / scale[1] if scale is not None else ytr
            oof = cross_val_predict(est, Xtr, y_cv_target, cv=KFold(5, shuffle=True, random_state=S.SEED))
            oof = oof * scale[1] + scale[0] if scale is not None else oof
            rows.append({"target": t, "scale": "log10" if log else "linear", "model": m["name"],
                         "R2_train": r_train, "R2_cv": r2_score(ytr, oof), "R2_test": r_test,
                         "gap_train_minus_test": r_train - r_test})

    # Honest cascade: digester-surrogate predictions replace the true digester outputs
    _, te = train_test_split(ok, test_size=0.2, random_state=S.SEED)
    te_c = te.copy()
    Xd = S.features(te_c, False)
    y_ch4_pred = S.predict(M["y_CH4_dry"]["model"], Xd)
    ch4_pred = S.predict(M["CH4_Nm3_h"]["model"], Xd)
    te_c["y_CH4_dry"] = y_ch4_pred
    te_c["biogas_dry_Nm3_h"] = ch4_pred / y_ch4_pred
    Xc = S.features(te_c, True)
    for t, log in S.UPGRADING_TARGETS.items():
        f = (lambda y: np.log10(np.maximum(y, 1e-6))) if log else (lambda y: y)
        r = r2_score(f(te[t].to_numpy(float)), S.predict(M[t]["model"], Xc))
        for row in rows:
            if row["target"] == t:
                row["R2_test_cascaded"] = r
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "overfitting_check.csv", index=False)
    pd.set_option("display.width", 200)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
