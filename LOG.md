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
