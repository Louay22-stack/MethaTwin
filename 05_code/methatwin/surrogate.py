"""
methatwin.surrogate - Batch prediction with the trained surrogates (step 6), including the
digester -> scrubber cascade and the physics feature. Same feature engineering as
05_code/step6b_surrogate.py.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_FILE = Path(__file__).resolve().parents[2] / "04_models_and_simulations" / "step6_surrogate" / "models" / "surrogates.joblib"


class Surrogate:
    def __init__(self, path: Path = MODEL_FILE):
        b = joblib.load(path)
        self.inputs, self.log_inputs, self.models = b["inputs"], set(b["log_inputs"]), b["models"]

    def _X(self, df: pd.DataFrame, upgrading: bool) -> np.ndarray:
        X = df[self.inputs].copy()
        for c in self.log_inputs:
            X[c] = np.log10(X[c])
        if upgrading:
            fsi = (1 - df.y_CH4_dry) * 1000.0 / df.water_per_kNm3 / df.p_flash_bar
            X = pd.concat([X, df[["y_CH4_dry", "biogas_dry_Nm3_h"]], fsi.rename("fsi")], axis=1)
        return X.to_numpy(float)

    def _reg(self, name: str, X: np.ndarray) -> np.ndarray:
        m = self.models[name]
        est, scale = m["model"]
        p = est.predict(X)
        if scale is not None:
            p = p * scale[1] + scale[0]
        return 10 ** p if m["log"] else p

    def _prob(self, name: str, X: np.ndarray) -> np.ndarray:
        return self.models[name]["model"][0].predict_proba(X)[:, 1]

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """df: the 8 inputs. Returns predicted outputs and feasibility probabilities."""
        df = df.reset_index(drop=True).copy()
        Xd = self._X(df, False)
        out = pd.DataFrame(index=df.index)
        for t in ["CH4_Nm3_h", "y_CH4_dry", "pH", "VFA_gCOD_L", "free_NH3_mgN_L"]:
            out[t] = self._reg(t, Xd)
        out["p_stable"] = self._prob("digester_stable", Xd)
        out["p_upg_valid"] = self._prob("upgrading_valid", Xd)
        tmp = df.assign(y_CH4_dry=out.y_CH4_dry, biogas_dry_Nm3_h=out.CH4_Nm3_h / out.y_CH4_dry)
        out["biogas_dry_Nm3_h"] = tmp.biogas_dry_Nm3_h
        Xu = self._X(tmp, True)
        for t in ["biomethane_Nm3_h", "BM_CO2_pct", "BM_O2_ppm", "CH4_slip_pct", "P_el_upg_kW"]:
            out[t] = self._reg(t, Xu)
        out["p_spec"] = self._prob("spec_ok", Xu)
        return out
