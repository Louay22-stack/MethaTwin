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
