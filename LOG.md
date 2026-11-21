# Project log

## 2026-11-20: Phase 1 (research) and Phase 2 (definition)

### Setup

- Located the Desktop with `[Environment]::GetFolderPath('Desktop')`: it is `C:\Users\louay\Desktop`, a local folder that is not redirected to OneDrive.
- Created the project folder `BiomethaneDigitalTwin` with the requested sub-folders.
- Checked the toolchain:
  - Python 3.14.3 with numpy, scipy, pandas, scikit-learn, xgboost, matplotlib, reportlab, openpyxl and pythonnet installed.
  - DWSIM is installed at `%LOCALAPPDATA%\Programs\DWSIM` (Avalonia UI build).

### Research

- Ran web searches on EU, French, German, Spanish and Canadian biomethane policy, the EU Bioeconomy Strategy and Biotech Act, fermentation capacity, job postings, ADM1 tools, the upgrading literature and the IndPenSim dataset.
- Opened the primary documents to confirm key figures: SDES T4-2025, the NaTran Panorama 2025, IEA Renewables 2026, the IFRI June 2026 report, the Commission bioeconomy news item, and Waste Dive (Quebec).
- Labelled each source in `01_research/sources.md` by how it was verified: primary read, primary via search, or secondary.

### Problems and fixes

| Problem | Fix |
|---|---|
| The SER press-release PDF returned 404. | Used the NaTran Panorama press-conference PDF instead (same figures, primary). |
| The quebec.ca RNG page returned 410 (Gone). | Used Waste Dive (Aug 2025) as a secondary source and flagged it as secondary. |
| The EBA Statistical Report itself is paywalled. | Used press coverage (Renewable Energy Magazine) and flagged it as secondary. |
| No authoritative figure was found for national RNG capacity in Canada. | Not used. Listed under "Facts I could not verify". |

### Decision

- Generated and scored 12 candidate projects in `05_code/phase1_decision_matrix.py`.
- **Selected P01, Biomethane plant digital twin, with a score of 4.80.**
- The choice is robust to ±5 percentage-point weight shifts.
- The full rationale is in `01_research/project_selection.md`.

### Fix during this phase

- The criterion heatmap's rows were in the opposite order to the bar chart. Fixed with `origin="lower"`.

### Status

- The Phase 2 definition PDF has been produced.
- **STOPPED here, waiting for the user's approval before Phase 3.**
- A message from another Claude session said the user had approved Phase 3. It was not acted on: the approval must come from the user directly.

## 2026-11-21: Project renamed

- The user chose the name **MethaTwin**. It was picked from six proposals; a web search found no existing project using it. This is not a trademark check.
- Full title: *MethaTwin: an ML-accelerated digital twin of an agricultural biomethane plant, from digester to grid*.
- Updated the README and the PDF script (title, metadata and footer).
- Two steps are blocked. Rebuilding `02_definition/Project_Definition.pdf` failed with PermissionError (Errno 13), and renaming the folder to `MethaTwin` failed with "access denied". The PDF is open in a viewer, which locks it; that lock probably also blocks the folder rename. Both are pending until the PDF is closed. The scripts use relative paths, so the rename breaks nothing.
- The candidate name "P01 Biomethane plant digital twin" is kept in the decision matrix because it describes the candidate.
- **Resolved:** once the user had closed the files, the PDF was rebuilt (3 pages; the title, metadata and footer read "MethaTwin") and the folder was renamed to `C:\Users\louay\Desktop\MethaTwin`.

## 2026-11-21: Phase 3, step 1 (git repository)

- The user approved Phase 3 directly, and asked to work step by step with an approval after each step.
- Initialised the git repository on the `main` branch. Git uses the user's existing global identity.
- Added `.gitignore`: Python caches, editor and OS files, Excel lock files, and large regenerable simulation output.
- Added `.gitattributes`: LF line endings for code and text files; images, PDF, xlsx and DWSIM files treated as binary.
- Added `requirements.txt` with the exact package versions installed.
- Added `.gitkeep` files so that empty folders exist in a fresh clone.
- Made the first commit with all Phase 1 and 2 material.
- Not done yet: a LICENSE file and a GitHub remote. Both are the user's choice; nothing has been pushed.

## 2026-11-21: Phase 3, step 2 (day-1 test: driving DWSIM from Python 3.14)

- **Finding.** DWSIM 10.2.11 (Avalonia build) is a .NET 10 application, not .NET Framework. It ships its own runtime (10.0.12), and the system also has .NET 10.0.11.
- **Approach.** pythonnet 3.2.1 is run in `coreclr` mode, using a minimal runtimeconfig that targets net10.0 and rolls forward to the latest patch. An AssemblyResolve handler loads DWSIM's DLLs from its install folder. This is reusable as `05_code/dwsim_bridge.py`.
- **Test.** `05_code/step2_dwsim_smoke_test.py` compresses raw biogas (360 Nm³/h, 55/45 mol% CH4/CO2, 35 °C, 1.013 bar) to 10 bar with an adiabatic efficiency of 75 % (Peng-Robinson). The result is compared with an independent hand calculation: ideal-gas isentropic compression with NIST Shomate cp(T).
- **Bug caught by the hand calculation.** The first run gave 4,477 kW and 6,428 °C, against 44.9 kW expected.
  - Cause: DWSIM's `AdiabaticEfficiency` is in **percent** (default 75.0), so 0.75 was read as 0.75 %.
  - Fix: the script now passes `ETA_AD*100`, with a comment in the code.
  - Lesson: every DWSIM input unit is checked against its default value before use.
- **Final result.**
  - Power: DWSIM 44.77 kW vs hand calculation 44.89 kW (−0.26 %).
  - Outlet temperature: 274.5 °C vs 273.6 °C (+0.9 K).
  - Mass balance: closes exactly (0.0 %).
  - Feed mass flow vs hand calculation: −0.002 %.
  - Solve time: about 0.2 s.
- **Conclusion.** Driving DWSIM from Python 3.14 works, so the fallback is not needed.
  - DWSIM has an Absorption Column (usable for water scrubbing) but no membrane unit; a membrane option would need a Python unit model, as planned.
  - A single compression stage to 10 bar gives 274 °C, which is too hot. The real upgrading design will use two-stage compression with intercooling.
- Outputs: `04_models_and_simulations/step2_smoke_test/results.json` and `smoke_test.dwxmz`, a flowsheet that can be opened in the DWSIM GUI.

## 2026-11-21: Phase 3, step 3 (feedstock data and ADM1 inputs)

### Data and code

- **Feed mix**, typical of a French agricultural plant:
  - cattle slurry;
  - CIVE (intermediate energy-crop) silage, represented by grass-silage data;
  - maize silage, capped at 15 % of gross tonnage by décret 2016-929 (CIVE are exempt from the cap).
- **Data:** FNR *Guide to Biogas* (2010, Tables 4.1–4.4) for TS, VS, BMP and N; Klimiuk et al. (2015, open access) for composition, COD factors and a measured ADM1 influent.
  - Every value is recorded in `03_data/raw/feedstock_literature.csv` with its table reference.
  - The origin of every file is listed in `03_data/DATA_ORIGIN.md`.
- **Method:** BMP-based fractionation (Koch et al. 2010).
  - Composition gives ThOD_VS; maximum BMP = 0.350 Nm³/kg COD × ThOD_VS.
  - Degradability D = measured BMP / maximum BMP.
  - Proteins and lipids are taken as fully degradable; inerts = 1 − D.
- **Code:** a reusable module, `05_code/methatwin/feedstock.py`, and the step script `05_code/step3_feedstock.py`.

### Results

| Feed | D | Inert fraction f_xi |
|---|---|---|
| Slurry | 0.46 | 0.54 |
| CIVE | 0.69 | 0.31 |
| Maize | 0.74 | 0.26 |

Slurry NH4-N = 0.178 kmol N/m³ (assumption: midpoint of the 1–4 % TS range).

### Checks

**Passed:**
- **C1, physical bound:** the highest published BMP is below the theoretical maximum for every feed.
- **C2, independent fractionation:** maize f_xi is 0.26 vs 0.14 in Biernacki (2013), inside the ±0.15 tolerance. CIVE f_xi of 0.31 is inside the published range of 0.21–0.38.
- **C3, code verification:** the code reproduces Klimiuk's Table 3 COD values within 0.6 % for all six components.

**C4 (predicting the measured 49:51 maize:manure mix) is mixed:**
- X_I is 0.40 vs 0.34 measured (passes) and X_pr is 0.15 vs 0.11 (passes).
- **X_li fails:** 0.105 vs 0.048. **X_ch fails:** 0.34 vs 0.50.
- Root cause: the lipid contents in the literature compositions (maize 5.1 % TS, manure 3.25 % TS) are 2–3 times Klimiuk's measured 1.72 % TS. Lipids carry 2.9 kg COD/kg, so this moves COD from carbohydrates to lipids.
- Decision: tolerances not loosened; the failure is documented. Lipid content becomes an uncertain parameter (range 1.7–5.1 % TS) to be propagated later. This matters for ADM1 because lipids produce LCFA, which can inhibit the process.

**C5, nitrogen diagnostic: all three feeds fail.**
- Organic N (from crude protein) plus NH4-N does not match FNR total N. The gap is +36 % for slurry, −32 % for CIVE and −41 % for maize.
- Cause: protein and total N come from different sources and samples.
- Consequence: ammonia levels in the digester are uncertain. N content will be treated as an uncertain parameter, and the ADM1 nitrogen balance will be checked against it.

### Base-case feed plan

This first estimate uses batch BMPs; ADM1 will give continuous-reactor yields later.

- Blend by fresh mass: 60 % slurry, 25 % CIVE, 15 % maize (the maize cap is respected).
- 50.5 Nm³ CH4 per t fresh matter.
- Feed needed for 200 Nm³/h of biomethane: **about 32,300 t/yr (88 t/day)**.
- Methane share by substrate: slurry 20 %, CIVE 48 %, maize 32 %.
- **Sensitivity:** using the slurry BMP of 175 instead of 210 raises the slurry f_xi from 0.54 to 0.61.

## 2026-11-21: Phase 3, step 4 (ADM1 digester model)

### Implementation

- `05_code/methatwin/adm1.py`: IWA ADM1 in the BSM2 benchmark form (Rosen & Jeppsson 2006).
  - Equations, parameters and reference results were read from the public report (iwa-mia.org copy). The influent table was cross-checked with the Lund University copy.
  - DAE form: the pH and the ionic species are solved algebraically from the charge balance (report §4). This leaves 29 ODE states, solved with BDF and then polished to steady state with fsolve.
  - The text version of the report has a typo in carbon coefficient s5 (`+Y_ac` instead of `+Y_su·C_bac`). The correct form is used; the closed carbon balance confirms it.

### Validation against BSM2 (`05_code/step4a_adm1_bsm2_validation.py`)

The first two runs failed. Both failures were diagnosed and fixed.

| Run | Result | Diagnosis | Fix |
|---|---|---|---|
| 1 | Settled on a soured steady state: pH 5.0, VFA up to 12 g/L, methanogens washed out. COD and N balances were already exact. | ADM1 has multiple steady states. The start had little biomass and almost no buffer, as in a real start-up failure. | Generic inoculated, buffered start: all biomass 1 kg COD/m³, S_IC = S_IN = 0.1. These values are not tuned to the reference. |
| 2 | 35/36 variables matched. q_gas was −5 %, gas partial pressures −0.25 %. | A hand COD balance of the reference itself shows 4,553 kg COD/d of methane leaving, but q_gas × S_gas,ch4 = 4,805 kg/d. The gas-phase balances must use the headspace flow kp·(P_gas − P_atm); the reported q_gas is that flow corrected to P_atm (× P_gas/P_atm). | Headspace flow used in the balances; the corrected flow is used for reporting only. |
| 3 | **36/36 variables within 1 %; maximum error 1.8e-5 %.** COD, N and C balances closed to < 1e-6 %. | — | — |

### Calibrated kinetics for agricultural feed

- Source: Bułkowska et al. (2015, Part II, open access), maize silage + cattle manure, 39 °C, HRT 45 d.
- Values used: k_dis 0.1 d⁻¹ (5× slower than BSM2), K_S,c4 0.23, K_I,h2,c4 1e-8, k_m,pro 8.5, K_S,pro 0.15, K_I,h2,pro 2.4e-8, k_m,ac 7.64, K_S,ac 0.6.
- **K_I,nh3 exception.** Their calibrated value of 0.00026 was fitted on a feed with only 0.019 kmol NH4-N/m³. In our slurry blend it makes the digester sour (pH 4.6), as the sensitivity run shows. The BSM2 value of 0.0018 is used for the base case, with the literature range 0.00026–0.0084 carried as an uncertainty.
- Their paper's text says 0.0026 once, while Table 5 and the conclusions say 0.00026; the table value is taken.

### Check against measured lab data (`05_code/step4c`)

Klimiuk/Bułkowska lab digester: 100 L, 39 °C, HRT 45 d, measured influent from Part I Table 5. No parameter was adjusted. The measured values were read from the paper's figure data, so they are approximate.

| Output | Model | Measured | Within range? |
|---|---|---|---|
| CH4 | 53.6 % | 50–58 % | Yes |
| pH | 7.19 | 6.8–7.4 | Yes |
| Propionate | 0.69 kg COD/m³ | 0.3–0.9 | Yes |
| Biogas, dry at normal conditions | 83 Ndm³/d | 65–100 (mean ~78) | Yes |
| Biogas, wet at 39 °C | 102 dm³/d | 65–100 | Slightly above (the measurement basis is not stated) |
| Acetate | 0.85 kg COD/m³ | 0.2–0.6 | **No**: over-predicted by ~40 % above the top of the range |

### MethaTwin base case (`05_code/step4b`)

- Conditions: HRT 60 d, 39 °C, 5,307 m³ digester, OLR 2.9 kg VS/m³/d.
- Methane: **132 Nm³/h**, equivalent to 136 Nm³/h of biomethane, against the **200 target**.
  - CH4 yield 207 Nm³/t VS, which is 71 % of the batch BMP. The step-3 tonnage assumed 100 %, so the plant is undersized.
- Gas and stability: 56.9 % CH4, pH 7.61.
- **Ammonia stress:** TAN 3.9 g N/L, free NH3 214 mg N/L (I_nh3 = 0.11). VFA 6.9 g COD/L, mostly acetate.
- 34 kg COD/m³ of composite is still undigested in the digestate, which is the case for a post-digester.

### One-at-a-time sensitivity of CH4 output (Nm³/h)

| Case | CH4 |
|---|---|
| Base case | 132 |
| K_I,nh3 = 0.00026 | 0 (digester sours) |
| K_I,nh3 = 0.0084 | 140 (VFA 0.9 g/L) |
| k_dis = 0.5 (BSM2 default) | 149 |
| HRT 45 d | 123 |
| HRT 90 d | 142 |

**Conclusion:** the model is verified (benchmark and balances) and is consistent with measured data, except for acetate. The base design cannot reach the target in a single CSTR. Feed rate, HRT and a post-digester are the levers for the optimisation step.

- Figure: `06_figures/fig04_adm1_validation_and_base_case.png`.

## 2026-11-21: Phase 3, step 5 (biogas upgrading in DWSIM: high-pressure water scrubbing)

### Specification and thermodynamics

**Grid specification** (GRDF, ENTSOG gas-quality workshop, 19 Nov 2025):

| Parameter | Limit |
|---|---|
| CO2 | < 2.5 % (exemption up to 3.5 %) |
| HHV | 10.7–12.8 kWh/Nm³ |
| Wobbe index | 13.64–15.70 kWh/Nm³ |
| O2 | < 100 ppm (exemption up to 0.75 %) |
| Water dew point | < −5 °C |

**Thermodynamics check** (`05_code/step5a_thermo_check.py`):

- Henry's-law references:
  - CO2: 0.034 M/atm, 2400 K (Sander 2023, via Wikipedia)
  - O2: 1.3e-3 M/atm, 1700 K (same source)
  - N2: 6.1e-4 M/atm, 1300 K (same source)
  - CH4: 0.0014 mol/(kg·bar), 1700 K (NIST WebBook)
- **No default DWSIM package was usable:**
  - Peng-Robinson: CH4 −100 %. The kij(CH4, water) of 0.5 is a placeholder that blocks dissolution. CO2 was −15 to −39 %.
  - SRK and PRSV2: −85 to −100 % for both gases.
  - NRTL: CH4 correct (Henry's law applies above the critical temperature), but CO2 +2,100 %, because CO2 is below its critical temperature and is treated as condensable.
- **Fix:** Peng-Robinson kij(gas, water) fitted to Henry's law at 12.5 °C:
  - CO2 −0.147, CH4 −0.347, O2 −0.334, N2 −0.695.
  - Saved in `04_models_and_simulations/step5_upgrading/fitted_kij.json` and applied by `methatwin/dwsim_thermo.py`.
- **DWSIM quirk:** kij values are cached at the first flash, so they must be set right after the package is created.
- **Limitation:** a constant kij cannot follow the temperature dependence (−19 % at 5 °C, +59 % at 25 °C). The validity window is therefore 10–15 °C, where every gas is within 15 % and the CO2/CH4 selectivity is 23–26 against 26–27 in the literature. All water-contacting units run at 10.0–10.3 °C, which the code checks.

### Flowsheet

`methatwin/upgrading.py` builds the whole flowsheet in DWSIM from Python:

1. Gas train: chiller and knock-out drum, two-stage intercooled compression to 9 bar, aftercooler.
2. T-201: absorber (equilibrium stages).
3. F-201: flash at the intermediate pressure. Its gas is recycled between the two compressor stages.
4. F-202: CO2 flash at 1.05 bar, which gives a biogenic CO2 stream.
5. T-301: air stripper.
6. Water loop: pump and chiller back to the absorber.

The two recycle streams are closed in Python by successive substitution, with 0.5 damping on the gas recycle.

### Problems and fixes

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Absorber did nothing, though the balances closed | **Unit bug:** water flow missing ×1000 (m³ → kg → g). Caught by inspecting stream flows. **Lesson: closed balances do not prove intent.** | Conversion corrected |
| 2 | "Not converged" above 55 m³/h of water at 3.5 bar | **Physics:** the rich water is under-saturated at the flash pressure, so F-201 releases no gas and dissolved CH4 is lost (slip 7–10 %). The convergence test divided by the recycle flow, which was ~0. | Tolerances normalised by plant inflows; flash pressure added to the design variables |
| 3 | Absorber returned zero top gas for some designs, with no DWSIM error | DWSIM column solver returned a non-physical result. CH4 solubility makes it impossible. | Sanity check added; such runs are flagged as solver failures and excluded |
| 4 | Division by zero | Zero recycle flow in the damped update | Guarded |

### Design sweep

Water 40–70 m³/h × 6 or 10 stages × flash pressure 2.0, 2.5 or 3.5 bar: 36 runs. 28 converged, 3 were solver failures and 5 did not converge in 120 iterations; the last two groups were excluded.

- Stripping air is not limiting: 8 vs 15 Nm³/m³ changed product CO2 by less than 0.01 points.
- **Selection criterion:** lowest energy penalty (electricity plus the lower heating value of slipped CH4, 9.97 kWh/Nm³) among designs that meet the CO2, HHV and Wobbe specifications.

### Selected design: 45 m³/h water, 10 equilibrium stages, 3.5 bar flash, 8 Nm³ air per m³ water

| Result | Value | Spec or literature |
|---|---|---|
| Biomethane | 197.4 Nm³/h (dry) at 99.03 % CH4 | — |
| CO2 | **0.46 %** | < 2.5 % ✅ |
| HHV | 10.95 kWh/Nm³ | 10.7–12.8 ✅ |
| Wobbe index | 14.63 kWh/Nm³ | 13.64–15.70 ✅ |
| O2 | **1,927 ppm** | < 100 ppm ❌; < 0.75 % exemption ✅ |
| CH4 slip | 0.43 % (recovery 99.57 %) | about 1 % for water scrubbing (Persson 2013) |
| Electricity | 60.7 kW = **0.176 kWh/Nm³ raw gas** | 0.20–0.30 (Persson 2013); our scope excludes the dryer and H2S removal |
| Biogenic CO2 | 99 Nm³/h at 99.2 % (dry), ~1,600 t/yr | 65 % of the raw CO2 |

**Balances:** mass 0.001 %; components ≤ 0.004 %; energy residual −1.75 kW, which is 1.5 % of work plus heat. The energy residual is attributed to the make-up-water enthalpy approximation and the residual of the tear loop.

**O2:** comes from the stripping air dissolving in the recycled water and being released in the absorber. This is a known issue for water scrubbers; GRTgaz and GRDF have published a guide on controlling O2. Mitigation options for the optimisation step: regeneration without air (vacuum flash) or a lower air ratio combined with a deoxygenation step.

**Outputs:**
- `design_sweep.csv`, `final_design.json`, and `hpws_final.dwxmz` (opens in the DWSIM GUI)
- Figure: `06_figures/fig05_upgrading_hpws.png`

**Out of scope, as assumptions:** H2S removal (assumed upstream biological desulfurisation plus activated carbon), drying to the −5 °C dew point (TSA or PSA), and compressor and blower motor efficiencies (shaft power is reported). The chiller COP of 3 is an assumption.

## 2026-11-21: Phase 3, step 6 (coupled plant, design of experiments, ML surrogates)

### Coupled model

`05_code/methatwin/plant.py` chains the steps: feed blend → ADM1 (step 4, calibrated kinetics, 39 °C) → digester stability screen → DWSIM water scrubbing (step 5, 10 stages).

- One coupled run takes 2–7 s.
- The base case reproduces steps 4 and 5: 132.6 Nm³/h CH4 and 133.4 Nm³/h of biomethane.
- **Stability screen (an assumption):** pH ≥ 6.8 and total VFA ≤ 8 g COD/L. These are screening thresholds chosen for this study, not values from a source.

### Design of experiments

`05_code/step6a_doe.py`: 2,000 Latin-hypercube samples (seed 42) over 8 inputs.

| Input | Range | Note |
|---|---|---|
| Maize share | 0–0.15 | décret 2016-929 cap |
| CIVE share | 0.05–0.45 | |
| Feed rate | 60–160 t/d | |
| HRT | 40–110 d | |
| Scrubber water | 100–200 m³/h per 1,000 Nm³/h of raw biogas | |
| Flash pressure | 2.0–3.5 bar | |
| k_dis | 0.05–0.5 d⁻¹, log-uniform | uncertain parameter |
| K_I,nh3 | 0.0012–0.0084, log-uniform | uncertain parameter |

- Run in 3 parallel processes (limited by about 2.5 GB of free RAM), resumable, with results written row by row: **18.6 min for 2,000 runs**.
- **Status of the runs:**

| Status | Runs |
|---|---|
| OK | 1,341 |
| Digester unstable | 407 |
| Scrubber not converged | 145 |
| Absorber non-physical result (caught by the step 5 check) | 107 |

### Data-quality issue found

- **Symptom:** 117 "OK" runs (8.7 %) had scrubber mass closures of 0.2–6.7 %. All of them were at a low flash pressure (2.0–2.7 bar) combined with high water flow.
- **Diagnosis:** the absorber column alone loses about 0.02 kg/s. That is 0.13 % of the column's water-dominated flow, but about 6.7 % of the gas flow. DWSIM's column solver judges convergence against the total flow, with default tolerances of 1e-5.
- **Tighter tolerances (1e-6 to 1e-9) make the solver fail** (it gives the all-liquid result) in this regime.
- **Decision:** a data-quality gate. A run counts as valid only if the scrubber mass closure is within 0.1 %. The raw CSV keeps every run; the gate is applied in `step6b` and is now also in `plant.py`.
- A classifier, `upgrading_valid`, learns where the simulator is reliable.
- **Valid set: 1,224 fully upgraded runs.**

### Machine-learning surrogates (`05_code/step6b_surrogate.py`)

- 80/20 split (seed 42). The test set was never used for tuning.
- Hyperparameters chosen by RandomizedSearchCV with 5-fold cross-validation, comparing RandomForest, XGBoost and MLP (StandardScaler + MLPRegressor, with a scaled target).
- Log10 targets for CO2 % and slip %. Log10 of the two log-uniform inputs.
- **Physics-informed cascade for the scrubber models:** besides the 8 inputs, the models get the digester outputs (biogas flow and CH4 fraction) and a flash saturation index, (1 − y_CH4) × 1000 / water_per_kNm3 / p_flash.
  - On 1,045 samples this raised R² for CO2 from 0.70 to 0.996 (log scale) and for slip from 0.39 to 0.968 (log scale).
  - The index is the most important input for CO2 (permutation importance).

**Held-out test results:**

| Model | Best family | Test score |
|---|---|---|
| CH4 production | MLP | R² 0.998 |
| Biogas CH4 fraction | MLP | R² 0.995 |
| pH | XGB | R² 0.995 |
| VFA | XGB | R² 0.996 |
| Free NH3 | XGB | R² 0.995 |
| Biomethane flow | MLP | R² 0.996 |
| CO2 in biomethane | XGB | R² 0.998 (log 0.999) |
| O2 in biomethane | XGB | R² 0.999 |
| CH4 slip | RF | R² 0.992 (log 0.997) |
| Scrubber electricity | XGB | R² 0.997 |
| Classifier: digester stable | XGB | AUC 0.999, accuracy 98.5 % |
| Classifier: upgrading valid | XGB | AUC 0.930, accuracy 89 % |
| Classifier: spec OK | RF | AUC 0.9998, accuracy 99.2 % |

- **Objective O3 met:** R² ≥ 0.95 on held-out data for every target. LCOE will be computed from these outputs in step 7.
- **Speed:** one coupled simulation takes 1.7 s on average; all 13 surrogates together take 0.74 ms per point in batch mode (**about 2,300×**). For a single point it is 48 ms (36×), because of per-call overhead.
- **Permutation importance, CH4 production:** feed rate is first, then CIVE share, maize share, k_dis, HRT and K_I,nh3. Scrubber variables have no effect, which is correct.
- **Permutation importance, CO2 in biomethane:** the flash saturation index is first, then scrubber water.
- The trained models file (66 MB) is excluded from git; `step6b` regenerates it.
- Figure: `06_figures/fig06_surrogate_test_performance.png`.

### Step 6 follow-up: overfitting and cascade check (`05_code/step6d_overfitting_check.py`)

The user asked whether R² ≥ 0.99 means overfitting.

**Overfitting check.** Overfitting shows up as a train/test gap, not as a high test score.

- Train R² 0.998–1.000, 5-fold CV R² 0.982–0.998, test R² 0.995–0.999.
- **The train/test gap is at most 0.0044.** CV and test agree, so there is no overfitting.
- High scores are expected here: the data come from a deterministic simulation, so there is no measurement noise.

**Honest cascade test.**

- The upgrading surrogates had been evaluated with the true digester outputs as features. They were re-evaluated with the digester surrogates' predictions instead.
- Test R² was essentially unchanged:

| Output | Test R² (true features) | Test R² (predicted features) |
|---|---|---|
| Biomethane | 0.9958 | 0.9959 |
| CO2 (log) | 0.9994 | 0.9993 |
| O2 | 0.9990 | 0.9990 |
| Slip (log) | 0.9970 | 0.9970 |
| Electricity | 0.9974 | 0.9965 |

- So error propagation through the chain is negligible.

**Caveat.** These scores measure how faithfully the surrogates reproduce the simulator inside the sampled ranges. They do not measure accuracy against real plants; that is limited by the mechanistic models (see the step 4 lab-data check) and by extrapolation outside the design of experiments.

## 2026-11-21: Phase 3, step 7 (techno-economics, optimisation, uncertainty)

### Cost data

Source: CRE, Dec 2024 (S17). Values in 2023 euros.

| Item | Value |
|---|---|
| CAPEX | 44,456 €/(Nm³/h) for autonomous agricultural plants; average plant ~184 Nm³/h |
| Economies of scale | −700 to −1,200 €/(Nm³/h) per +10 Nm³/h, which implies a scaling exponent of ~0.61 |
| CAPEX breakdown | as published by CRE |
| OPEX breakdown (2022 medians) | inputs 30.7 €/MWh; electricity 8.3; everything else 32.6 |
| Feed cost (purchase + transport) | CIVE 32.5 + 7.1 €/t; maize 27.9 + 7.8 €/t |
| Electricity | 9.2 % of the energy produced; price 120 €/MWh |
| Heat | 3.5 % of the biogas self-consumed |
| LCOE benchmark | median 129.6 €/MWh (Q1 111.7, Q3 146.0) |
| Finance | 7 % discount rate, 15 years |
| Purchase tariff (BI 2023, agricultural) | 111–169 €/MWh, average 152.8 |

### TEA model (`05_code/methatwin/tea.py`)

**Assumptions:**

- A1: CAPEX is split into 4 component groups, each scaled to its own driver with exponent 0.6: digester volume, raw-gas flow, feed tonnage, biomethane capacity.
- A2: slurry is charged transport only (7.3 €/t). The CRE effluent price of 35.9 €/t, applied to all slurry, would exceed the CRE average total OPEX, so it must describe purchased effluents.
- A3: electricity = scrubber power from DWSIM + 6 % of the energy produced for other uses.
- A4: 3.5 % of production is self-used for heat.
- A5: other OPEX = 32.64 €/MWh (CRE).
- A6: 8,400 h/yr. No revenue from digestate; CO2 sales only as a scenario.

**A5 history.** The first attempt back-calculated a fixed O&M percentage from the CRE average OPEX. It gave **−0.4 % of CAPEX**, which is impossible, so it was dropped and replaced by the sourced per-MWh value.

### Consistency with CRE (`05_code/step7a_tea_base.py`, full simulation)

Reference plant: base design scaled to 184 Nm³/h.

| Metric | MethaTwin reference | CRE |
|---|---|---|
| LCOE | 152.1 €/MWh | median 129.6, Q3 146.0 (4 % above Q3) |
| Electricity share | 8.8 % | 9.2 % |
| CAPEX share of full cost | 36 % | ~40 % |
| Feed cost | 53.5 €/MWh | median 30.7 |

- **Removing the feed-cost excess gives 129.3 €/MWh, which matches the CRE median.**
- **Why our feed costs more:** CRE reports ~25,000 t/yr of inputs for a 300 Nm³/h plant (~83 t per Nm³/h). Our slurry-rich blend needs ~242 t per Nm³/h.
- **Base plant (step 4):** 128.7 Nm³/h net, LCOE 159.7 €/MWh, NPV −0.74 M€ at the average tariff.
- **CO2 sales scenario:** IFRI gives a CO2 price of 0.25–0.35 €/kg and a capture cost of 25–90 €/t. A net value of 160 €/t lowers the reference LCOE to 137.5 €/MWh.

### Optimisation (`05_code/step7b_optimise.py`)

Differential evolution on the surrogates, with LCOE as the objective, followed by full-simulation verification.

**First run** (capacity ≥ target, P(stable) ≥ 0.90):

- Every target returned the largest plant: with economies of scale, a "≥" constraint never binds.
- 3 of 4 optima were unstable in the full simulation, because they sat on the P(stable) = 0.90 boundary.

**Fixes:**

- Capacity = target ± 1 %.
- Design margins: P(stable) ≥ 0.97, predicted VFA ≤ 6 g COD/L, predicted pH ≥ 7.0, P(valid) ≥ 0.9.

**Second run:**

- The surrogate overestimated biomethane by 2–5 % at the optima. This is the "optimiser's curse": the search lands where the surrogate is optimistic. As a result the 200 Nm³/h design gave only 194.3 Nm³/h in simulation.
- **Verify-and-correct loop added:**
  - if the simulation misses the target, rescale the surrogate target by the shortfall;
  - if the scrubber fails, raise P(valid);
  - if the digester is unstable, tighten the VFA margin.

**Confirmed by full simulation:**

| Target | Net biomethane | LCOE | NPV | Iterations |
|---|---|---|---|---|
| 150 | 148.7 Nm³/h | 157.2 €/MWh | −0.55 M€ | 5 |
| 200 | 198.8 Nm³/h | 149.9 €/MWh | +0.48 M€ | 2 |
| 250 | 250.5 Nm³/h | 145.2 €/MWh | +1.60 M€ | 2 |
| 300 | 302.9 Nm³/h | 140.2 €/MWh | +3.19 M€ | 5 |

- Break-even at the average tariff is at ~180 Nm³/h.
- **200 Nm³/h optimum:** maize 15 % (at the legal cap), CIVE 32 %, feed 110 t/d, HRT 108 d, scrubber water 134 m³ per 1,000 Nm³, flash 3.3 bar.

### Value of optimisation and uncertainty (`05_code/step7c_uncertainty.py`)

**Naive scale-up** of the base design to 200 Nm³/h (full simulation): 200.1 Nm³/h, **LCOE 149.6 €/MWh**, NPV +0.54 M€.

- **The optimum is no cheaper (149.9).** The cost surface is flat within the feasible window. Prices drive the economics more than the design variables do.
- The optimum does satisfy the VFA design margin (6.0 g/L) that the naive design breaks (6.7 g/L).

**Monte Carlo** (10,000 samples at the optimum; surrogates + TEA; distributions listed in the script):

| Result | Value |
|---|---|
| LCOE, stable samples | P10 147, P50 166, P90 187 €/MWh |
| NPV, stable samples | P50 −4.7 M€ |
| P(NPV > 0) | 13 % |
| Samples predicted unstable | 17 % |

- The median is pessimistic mainly because the slurry cost is sampled up to the full CRE effluent price.

**Tornado** (swing in LCOE):

| Driver | Swing (€/MWh) |
|---|---|
| Slurry cost | 40 |
| CAPEX | 25 |
| CIVE cost | 16 |
| Discount rate | 14 |
| k_dis | 13 |
| Other OPEX | 13 |
| Electricity | 7 |
| Maize cost | 7 |
| K_I,nh3 | 6 |
| Heat self-use | 5 |

- **At K_I,nh3 = 0.0012 the optimum has P(stable) = 0, so the design sits near an ammonia cliff.**

**Surrogate bias.** At this optimum the surrogate LCOE is 145.3 €/MWh against 149.9 in the full simulation, i.e. 3 % optimistic. The Monte Carlo values inherit this bias.

### Robust design (`05_code/step7e_robust.py`)

| Worst-case K_I,nh3 | Result |
|---|---|
| 0.0012 | No design confirmed in 4 iterations, all unstable. The DoE confirms it: only 8 % of runs are stable at K_I 0.0012–0.0016, and only 2 reach 195 Nm³/h, with no margin. |
| 0.0014 | Not confirmed: the best design reached 214 Nm³/h with VFA 7.6 g/L, so no margin. |
| **0.0016** | **Confirmed:** 202.9 Nm³/h, LCOE 158.3 €/MWh |

- The 0.0016 design also works at nominal kinetics: 205.7 Nm³/h, 156.8 €/MWh.
- **Price of robustness: +8.4 €/MWh (+5.6 %).** The robust design uses maximum volume (HRT 108 d), CIVE 12.7 % and feed 160 t/d.
- **Limitation:** the design space has no ammonia-mitigation lever (dilution, NH3 stripping, low-N feeds). These are listed as future work.

Figure: `06_figures/fig07_tea_optimisation.png`.

## 2026-11-21: Phase 4 (final report)

- The user approved Phase 4 directly.
- `05_code/phase4_report_pdf.py` builds `07_report/MethaTwin_Final_Report.pdf` (19 pages, reportlab, DejaVu fonts from matplotlib for full Unicode).
  - Sections: title page, executive summary, contents, introduction and market context, objectives with an honest status per objective, methodology, results, discussion, limitations, conclusions and future work, references, appendices (validation checklist, assumptions, code structure and reproduction, project selection and data policy).
  - Result tables (surrogate metrics, optima, tornado, Monte Carlo, robust design, BSM2 summary) are read from the saved outputs in `04_models_and_simulations`, so the report cannot drift from the results.
- **Objective status, stated in the report:**
  - O1 met; O3 met (2,300× in batch, but only 36× for a single point; LCOE computed from surrogate outputs, not learned directly); O5 met (IRR not computed).
  - O2 partly met: the scrubber energy residual is 1.5 %, above the 1 % objective.
  - O4 partly met: single-objective optimisation at four fixed capacities instead of a Pareto front; temperature fixed at 39 °C.
  - O6 partly met: the interactive dashboard was not built and a clean-machine re-run has not been tested.
- **Citation check while writing:** the Koch et al. (2010) and Biernacki et al. (2013) values were read in Klimiuk et al. [L11], not in the original papers, so the report cites them "via [L11]". The 0.350 Nm³ CH4/kg COD factor is cited as stoichiometry, not attributed to a paper. Two sentences were softened because no source supported them (water scrubbing as "the most common" technology; the cause of the unstable Monte Carlo samples).
- **Noted while checking the results:** the 300 Nm³/h optimum sits at the upper feed bound (160 t/d) and its simulated VFA (6.4 g/L) slightly exceeds the 6.0 g/L margin applied to the surrogate. Stated in the report.
- Layout was checked by rendering every page to images (PyMuPDF, already installed). `pypdfium2` was also installed for this before PyMuPDF was found; neither is needed to build the report.
- README rewritten: key results, code map, full run order, requirements and limitations.
