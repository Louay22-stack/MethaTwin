# Project selection

The full table is in `decision_matrix.csv` and `decision_matrix.xlsx`. The .xlsx keeps live formulas, so a weight can be changed to test the ranking. The figure is `06_figures/fig01_decision_matrix.png`.

**Weights:** market relevance 25 %, recruiter impact 20 %, feasibility 20 %, skills fit 15 %, depth and novelty 10 %, demonstrable outputs 10 %.

| Rank | Project | Score |
|---|---|---|
| 1 | **P01 Biomethane plant digital twin + ML surrogate + TEA** | **4.80** |
| 2 | P02 Fed-batch fermentation soft sensor & fault detection (IndPenSim) | 4.20 |
| 3 | P03 Precision-fermentation protein TEA (BioSTEAM) | 4.10 |
| 4–5 | P05 Biogenic CO2 valorisation / P08 Bayesian fed-batch optimisation | 4.00 |

**Robustness check.** P01 stays first under every pairwise ±5 percentage-point weight shift (30 scenarios, computed in `05_code/phase1_decision_matrix.py`).

## Why P01 beats the runners-up

**Against P02 (IndPenSim soft sensor):**

- P02 has the best data (a real public, industrial-scale dataset [L9]).
- But it is mainly an ML exercise on a dataset already used in many soft-sensor papers, so novelty is low.
- It involves no process design, no mass and energy balance, no simulator and no economics. Those are the skills that appear in almost every process-engineering posting [J6–J8].
- P01 shows the same ML skills and adds DWSIM, balances and TEA. It also targets the sector with the most active policy targets in the candidate's home markets (France, Spain, Germany and Quebec [S2, S10–S12]).

**Against P03 (precision-fermentation TEA):**

- P03 is very topical [S9, S15].
- But reliable strain and process data are proprietary, so the results would rest almost entirely on assumptions.
- It also does not use the candidate's biogas background or DWSIM automation.
- P01 can be validated against published benchmarks: the BSM2 ADM1 reference [L2, L3], upgrading energy and slip ranges [L7, L8], and EU cost ranges [S6]. Validation against published values is what makes a portfolio piece credible.

## What makes P01 distinctive

- It uses one integrated chain: feed, then digestion (ADM1), then biogas, then upgrading (DWSIM, automated from Python), then grid-quality biomethane plus biogenic CO2, then economics.
- The ML is used where it adds real value. It replaces a slow mechanistic chain by a fast surrogate, so thousands of design and operating points can be optimised. That is a hybrid-modelling and digital-twin pattern, which is a theme that recurs in the postings [J4, J5, L6].
- The reference plant is sized from public statistics. France has 15.5 TWh/yr of capacity over 803 sites [S1], about 19 GWh/yr per site, which is roughly 200 Nm³/h of biomethane (see the definition PDF for the arithmetic). The case is therefore representative of the market a recruiter knows.

## Main risks, handled in the definition document

- ADM1 is a stiff ODE system.
- DWSIM (the Avalonia build) automation through pythonnet on Python 3.14 is untested.
- Feedstock characterisation data are uncertain.
- The project must stay separate from the user's unpublished manuscript (see `research_notes.md` §4).
