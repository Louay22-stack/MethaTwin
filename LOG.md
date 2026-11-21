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
