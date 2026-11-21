# MethaTwin

**MethaTwin** is a machine-learning-accelerated digital twin of an agricultural biomethane plant. It follows the gas from the digester to the grid. The chain has five parts:

1. **Digestion:** an ADM1 co-digestion model in Python.
2. **Upgrading:** a DWSIM biogas-upgrading flowsheet, automated from Python.
3. **Products:** recovery of the biogenic CO2.
4. **Surrogate:** a machine-learning model trained on the simulations, used for fast optimisation.
5. **Economics:** a techno-economic analysis with uncertainty.

> **Status (2026-11-20):** Phases 1 and 2 are done (research, project selection and definition). Phase 3 (execution) waits for approval.

## Folder structure

| Folder | Contents |
|---|---|
| `01_research/` | Research notes, `sources.md` (every source with its URL and how it was verified), and the decision matrix (.csv, plus .xlsx with live formulas) |
| `02_definition/` | `Project_Definition.pdf` (3 pages) |
| `03_data/` | Raw and processed data, with the origin of every file (Phase 3) |
| `04_models_and_simulations/` | ADM1 model and DWSIM flowsheets (Phase 3) |
| `05_code/` | All scripts |
| `06_figures/` | Figures |
| `07_report/` | Final report (Phase 4) |
| `LOG.md` | Dated log of work, decisions, problems and fixes |

## Reproducing the work done so far

Run these from the project root with Python 3.14. Install the packages first with `pip install -r requirements.txt`.

```powershell
python 05_code/phase1_decision_matrix.py
```

```powershell
python 05_code/phase2_definition_pdf.py
```

## Data policy

The project uses public data and published literature only. The machine-learning component is a surrogate of a mechanistic model trained on simulated data. No empirical plant data and no unpublished manuscript data are used.
