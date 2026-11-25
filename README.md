<p><img src="05_code/dashboard/assets/wordmark.svg" alt="MethaTwin" width="300"/></p>


**MethaTwin** is a machine-learning-accelerated digital twin of an agricultural biomethane plant (~200 Nm³/h), from the digester to the gas grid. It is built from public data and open-source tools only.

1. **Feed characterisation:** cattle slurry, cover-crop (CIVE) silage and maize silage, from literature data.
2. **Digester:** the IWA ADM1 model in Python (BSM2 form), validated against the benchmark and a published lab digester.
3. **Upgrading:** a high-pressure water-scrubbing flowsheet in DWSIM, built and solved from Python, with biogenic-CO₂ recovery.
4. **Surrogates:** ML models (random forest, XGBoost, MLP) trained on 2,000 coupled simulations.
5. **Economics:** a techno-economic model anchored on the French regulator's (CRE) 2024 cost survey, with surrogate-based optimisation verified by full simulation, Monte Carlo and robustness analysis.

**Final report:** [`07_report/MethaTwin_Final_Report.pdf`](07_report/MethaTwin_Final_Report.pdf)

## Interactive application

MethaTwin ships as an interactive web application (Streamlit) that anyone can use without DWSIM. Its slogan: **See your plant work before it exists.** The app opens on a start page with a 3D "living mirror": the real plant stands on a dark glass disc and its twin is its amber reflection underneath; three questions (biology, gas, money) bring the matching part of the twin to life. Every page then opens with a plain-language verdict; figures, tables and charts open on click, and technical terms are explained on hover, focus or tap. The settings live on the Your plant page and apply to every page; all live values come from the ML surrogates (milliseconds per design), and checked designs also show their full-simulation results.

| Page | What it does |
|---|---|
| Start | Slogan, brand promise, 3D living mirror (drag to turn; Biology/Gas/Money light up the twin's microbes, gas flow and coins), the three questions, ways in |
| Your plant | Verdict and three answers (biology, gas, money) next to the settings (reference design, feed and tank, gas cleaning, microbes, market; save and reset); key figures, process diagram, operating limits, costs and JSON export open on click |
| Try changes | The setting that matters most for cost; one-setting curves and a two-setting map on click |
| What could go wrong | On-demand Monte Carlo: “pays in N of 10 futures”; key figures, cost range, main drivers and every future (CSV) on click |
| Designs | Where you are; checked designs (select a row to load it) and your own saved designs (load, delete, compare, CSV) |
| Why trust it | Score of the 16 checks; scorecard, every check, surrogate accuracy, lab and market checks, figures on click |
| How it works | One-sentence summary, four steps, report download; methods, glossary, limits on click |

```powershell
pip install -r requirements.txt
```

```powershell
streamlit run 05_code/dashboard/app.py
```

The application needs the trained models; if `04_models_and_simulations/step6_surrogate/models/surrogates.joblib` is missing, run `python 05_code/step6b_surrogate.py` first (the app shows this instruction instead of crashing).

Code: `05_code/dashboard/`: `app.py` (shell: top bar, navigation, current-design chip), `state.py` (session state, scenarios, cached evaluations), `core.py` (model layer: surrogates + TEA), `tokens.py` (design tokens: primitive → semantic → component), `theme.py` (brand marks, CSS built from the tokens, chart template), `ui.py` (components, icon set, status logic, process diagram), `views/` (one file per page), `assets/` (mark, app icon and wordmark SVGs, `core3d.html` three.js scene). The design system (MASTER.md, tokens as DTCG JSON and CSS, concept board) is in `design-system/methatwin/`.

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
| `dashboard/` | Interactive application (shell, state, model layer, tokens, theme, components, pages, brand assets) |

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

## Licence

The code is released under the [MIT License](LICENSE). The literature data and sources it builds on remain under their original terms; see `01_research/sources.md` and `03_data/DATA_ORIGIN.md`.
