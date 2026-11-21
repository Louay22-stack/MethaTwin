<p><img src="05_code/dashboard/assets/logo.svg" alt="MethaTwin" width="300"/></p>


**MethaTwin** is a machine-learning-accelerated digital twin of an agricultural biomethane plant (~200 Nm³/h), from the digester to the gas grid. It is built from public data and open-source tools only.

1. **Feed characterisation:** cattle slurry, cover-crop (CIVE) silage and maize silage, from literature data.
2. **Digester:** the IWA ADM1 model in Python (BSM2 form), validated against the benchmark and a published lab digester.
3. **Upgrading:** a high-pressure water-scrubbing flowsheet in DWSIM, built and solved from Python, with biogenic-CO₂ recovery.
4. **Surrogates:** ML models (random forest, XGBoost, MLP) trained on 2,000 coupled simulations.
5. **Economics:** a techno-economic model anchored on the French regulator's (CRE) 2024 cost survey, with surrogate-based optimisation verified by full simulation, Monte Carlo and robustness analysis.

**Final report:** [`07_report/MethaTwin_Final_Report.pdf`](07_report/MethaTwin_Final_Report.pdf)

## Interactive dashboard

A Streamlit web app lets anyone test the digital twin without DWSIM: move sliders for the feed blend, plant size, scrubber settings, microbial kinetics and prices, and see biomethane output, gas quality against the grid specification, digester stability, cost per MWh and NPV update instantly. It runs on the ML surrogates (milliseconds per design).

| Tab | What it shows |
|---|---|
| Plant simulator | Verdict banner, KPI cards, digester health, gas quality vs spec, cost and CAPEX breakdown; full-simulation check for saved designs |
| Design explorer | One-input sweeps (cost, output, acids, CO₂) and a feed-rate × retention-time cost map |
| Risk analysis | Live Monte Carlo (500–5,000 samples) and tornado chart for the current design |
| Optimisation | Verified optimal designs, economies of scale, one-click loading into the simulator |
| Model validation | Benchmark, lab-data, market and surrogate checks |
| About | Method, limitations, report download |

```powershell
pip install -r requirements.txt
```

```powershell
streamlit run 05_code/dashboard/app.py
```

The dashboard needs the trained models; if `04_models_and_simulations/step6_surrogate/models/surrogates.joblib` is missing, run `python 05_code/step6b_surrogate.py` first. Code: `05_code/dashboard/` (`app.py` interface, `core.py` model layer, `theme.py` palette and styles, `assets/` logo).

## Key results

| Area | Result |
|---|---|
| ADM1 validation | 36/36 BSM2 values within 1 % (max error 1.8×10⁻⁵ %); COD, N and C balances closed to < 10⁻⁶ % |
| Lab-data check | CH₄ %, pH, propionate and biogas in the measured range; acetate over-predicted |
| Upgrading | CO₂ 0.46 %, CH₄ slip 0.43 %, 0.176 kWh/Nm³ raw gas, ~1,600 t/yr biogenic CO₂ at 99.2 % |
| Surrogates | Test R² 0.992–0.999, train–test gap ≤ 0.0044, ~2,300× faster than simulation (batch) |
| Economics | CRE median reproduced (129.3 vs 129.6 €/MWh after feed correction); verified optima 157 / 150 / 145 / 140 €/MWh at 150 / 200 / 250 / 300 Nm³/h; break-even ≈ 180 Nm³/h |
| Risk | Monte Carlo P50 166 €/MWh, P(NPV > 0) 13 %; slurry price is the main driver; robustness to ammonia inhibition costs +8.4 €/MWh |

## Folder structure

| Folder | Contents |
|---|---|
| `01_research/` | Research notes, `sources.md` (every source with its URL and how it was verified), decision matrix (.csv and .xlsx with live formulas) |
| `02_definition/` | `Project_Definition.pdf` (3 pages, the approved plan) |
| `03_data/` | Raw literature data, processed data and the 2,000-run DoE; `DATA_ORIGIN.md` gives the origin of every file |
| `04_models_and_simulations/` | Outputs of each step (JSON/CSV) and DWSIM flowsheets (`.dwxmz`, open in the DWSIM GUI) |
| `05_code/` | The `methatwin` package and one script per step |
| `06_figures/` | All figures (fig01–fig07) |
| `07_report/` | Final report (PDF) |
| `LOG.md` | Dated log of every step, decision, problem and fix |

## Code

| Module | Purpose |
|---|---|
| `methatwin/feedstock.py` | Feed dataclass, ThOD, BMP-based fractionation, blending |
| `methatwin/adm1.py` | ADM1 (BSM2 form): parameters, pH solver, rates, steady state, balances |
| `methatwin/dwsim_thermo.py` | Henry's-law data, fitted Peng–Robinson kij, property package |
| `methatwin/upgrading.py` | Water-scrubbing flowsheet built and solved in DWSIM; KPIs and balances |
| `methatwin/plant.py` | Coupled plant: digester → stability screen → upgrading, with the data-quality gate |
| `methatwin/surrogate.py` | Loads and runs the cascaded surrogates |
| `methatwin/tea.py` | CAPEX, OPEX, LCOE and NPV |
| `dwsim_bridge.py` | Loads DWSIM (.NET 10) into Python through pythonnet / CoreCLR |
| `dashboard/` | Streamlit dashboard (interface, model layer, brand theme, logo) |

## Reproducing the work

**Requirements**
- Python 3.14. Install the packages with `pip install -r requirements.txt`.
- DWSIM 10.2 (Avalonia build, free) installed in `%LOCALAPPDATA%\Programs\DWSIM`. It is needed for step 2, step 5, the DoE, and every script that runs the full simulation (6d, 7a, 7b, 7c, 7e).
- Run every command from the project root.

**Run order** (outputs go to `04_models_and_simulations/`, figures to `06_figures/`):

| Stage | Scripts (in `05_code/`) | Note |
|---|---|---|
| Research | `phase1_decision_matrix.py` | Decision matrix and fig01 |
| Definition | `phase2_definition_pdf.py` | Definition PDF and fig02 |
| DWSIM check | `step2_dwsim_smoke_test.py` | Needs DWSIM |
| Feed | `step3_feedstock.py` | Also draws fig03 |
| Digester | `step4a_adm1_bsm2_validation.py`, `step4b_adm1_base_case.py`, `step4c_adm1_experimental_check.py`, `step4d_figures.py` | fig04 |
| Upgrading | `step5a_thermo_check.py`, `step5b_hpws_design.py`, `step5c_figures.py` | Needs DWSIM; fig05 |
| DoE | `step6a_doe.py [N] [workers]` | Default 2,000 runs on 3 processes, ~19 min; resumable |
| Surrogates | `step6b_surrogate.py`, `step6c_figures.py`, `step6d_overfitting_check.py` | Regenerates the trained models (66 MB, not in git); fig06 |
| TEA | `step7a_tea_base.py`, `step7b_optimise.py`, `step7c_uncertainty.py`, `step7e_robust.py`, `step7d_figures.py` | Needs DWSIM and the trained models; fig07 |
| Report | `phase4_report_pdf.py` | Reads the saved outputs and builds the PDF |

Example:

```powershell
python 05_code/step4a_adm1_bsm2_validation.py
```

Seeds are fixed (42), so the DoE and the ML split are reproducible. The optimisation uses differential evolution and the DWSIM solvers, so re-runs may differ slightly in the last digits. A full re-run on a clean machine has not been tested yet.

## Limitations (short)

The models are validated against a benchmark, a lab digester and hand calculations, not against full-scale plant data. The digester is solved at steady state. The fitted gas-solubility parameters are valid at 10–15 °C. Costs are top-down from CRE averages. Section 6 of the report gives the full list.

## Data policy

The project uses public data and published literature only. The machine-learning component is a surrogate of a mechanistic model trained on simulated data. No empirical plant data and no unpublished manuscript data are used.
