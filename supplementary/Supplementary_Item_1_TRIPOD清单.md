# Supplementary Item 1 — TRIPOD and TRIPOD+AI checklist

**Manuscript.** Stability selection does not guarantee external transport: a mitoxyperilysis score fails validation in hepatocellular carcinoma.

**Reporting standard.** The study is reported against the TRIPOD statement (Collins et al., *Ann Intern Med* 2015) and the TRIPOD+AI statement (Collins et al., *BMJ* 2024) [40,41]. TRIPOD is designed for studies that **develop and/or validate a multivariable prediction model**; TRIPOD+AI extends it to models developed with machine-learning or other algorithmic methods. Neither statement anticipates a study whose *primary conclusion is a validation failure*, so several items are marked **"not applicable in the intended sense"** with the reason given.

**Status key.** ✔ reported · ◐ partially satisfiable · ✘ not satisfiable by a secondary analysis of public data (reason given) · n/a not applicable to this design.

| # | TRIPOD item | TRIPOD+AI extension | Where | Status |
|---|---|---|---|---|
| 1 | Title: identify as developing/validating a multivariable prediction model, the target population and the outcome | Same | Title | ✔ Title states the transport failure explicitly; the target population (HCC) and outcome (overall survival) are named |
| 2 | Abstract: structured summary of objectives, data sources, participants, model, performance, results, limitations | Same | Abstract | ✔ Structured; Conclusions lead with the methodological finding |
| 3a | Background and objectives: explain the rationale, reference existing models, state objectives | 3a adds: report whether the model is intended for clinical use | Introduction | ✔ Objectives stated; no clinical-use claim is made anywhere |
| 3b | — | TRIPOD+AI: describe the intended use and the target user | Section 1, Section 4 Ninth limitation | ✔ Explicit "cannot do" list; no target user is claimed |
| 4a | Source of data: describe the data source and eligibility | 4a adds: data provenance and any preprocessing | Section 2.1 | ✔ cBioPortal study ID, GEO accessions, platform IDs, inclusion criteria and the 360/372 flow are given |
| 4b | — | TRIPOD+AI: describe data quality checks and any data cleaning | Supplementary Methods | ✔ Probe-to-gene mapping rule (highest-mean probe) stated |
| 5a | Participants: describe eligibility, setting, recruitment dates | Same | Section 2.1 | ◐ Public retrospective cohorts; recruitment dates are those of the source studies (TCGA-LIHC, GSE14520, GSE76427) |
| 5b | — | TRIPOD+AI: describe how the data were split | Sections 2.6, 2.7 | ✔ 10-fold split, seed 42; frozen-coefficient external application |
| 6a | Outcome: define the outcome, its measurement and how it was determined | Same | Sections 2.1, 2.4 | ✔ Overall survival, time and status from the source clinical files |
| 6b | — | TRIPOD+AI: report the outcome definition used at each site | Section 2.1 | ◐ OS in TCGA-LIHC and both GEO cohorts; recurrence-free survival was not usable (Limitation Eighth) |
| 7a | Predictors: define all predictors and how they were measured | Same | Sections 2.2, 2.4, 2.5 | ✔ The 91-gene panel derivation is reproduced in full; coefficients in Tables 2 and 4 |
| 7b | — | TRIPOD+AI: report predictor measurement details and any transformation | Sections 2.4, 2.5, 2.8 | ✔ Within-cohort Z-standardisation; frozen coefficients |
| 8 | Sample size: explain how the sample size was arrived at | Same | Section 2.13 | ✘ No a-priori calculation: the discovery cohort is a fixed public resource. Stated explicitly, with the number of events given |
| 9 | Missing data: report how missing data were handled | 9 adds: describe any imputation method | Sections 2.3, 3.4 | ✔ Complete-case primary (n = 337) plus two pre-specified sensitivities (missing → 0; missing → 0 + indicator), all reported for both models |
| 10a | Statistical analysis: describe the model-building procedure | 10a adds: algorithm, hyperparameters, tuning method | Sections 2.4–2.7 | ✔ Ridge penalty 1.0; LASSO-Cox over a 60-value path with the 1-SE rule; stability selection at π ≥ 0.75 over 200 bootstraps |
| 10b | Statistical analysis: describe the model performance measures | Same | Sections 3.2, 3.5 | ✔ Harrell's C-index, time-dependent AUC, restricted mean survival time, calibration slope, calibration plot, time-dependent and integrated Brier scores |
| 10c | Statistical analysis: describe how the model was validated | Same | Sections 2.6, 2.7, 3.7 | ✔ Fully nested 10-fold cross-validation, ten-seed bootstrap replication, random-panel benchmark, two independent external cohorts |
| 10d | — | TRIPOD+AI: describe any calibration and any comparison with existing models | Sections 3.5, 3.6, 3.7 | ✔ Calibration and Brier scores for both models; a generic 20-gene proliferation score used as a benchmark in both cohorts |
| 11 | Risk groups: describe how risk groups were defined, if used | Same | Sections 2.4, 3.3 | ✔ Median split, used for display only; all inference on the continuous score |
| 12a | Development vs validation: specify which was done and give details of the model | Same | Sections 2.4, 2.5, 3.2, 3.3 | ✔ Both developed and externally validated; coefficients given for both models |
| 12b | — | TRIPOD+AI: report the model specification (equation, weights) | Section 3.3, Table 4 | ✔ MRG-2 = +0.310·KIF15 + 0.334·MAFG (per SD). No baseline cumulative hazard is given, so absolute risks are not recoverable — stated in the text |
| 13a | Development: describe participant flow and the number with and without the outcome | Same | Section 2.1 | ✔ 360 of 372; 129 deaths (35.8%) |
| 13b | Development: report the model's performance | 13b adds: uncertainty and optimism correction | Sections 3.2, 3.3, 3.5 | ✔ Apparent and fully nested estimates reported side by side; the ~0.10 C-index optimism is quantified |
| 14a | Development: describe how the model was built (full model, selection, tuning) | Same | Sections 2.4, 2.5 | ✔ Including the disclosure that backward elimination makes the reported coefficient P values post-selection estimates |
| 14b | Development: report the final model and its performance | Same | Sections 3.2, 3.3, Tables 2 and 4 | ✔ |
| 15a | Validation: describe the validation procedure | Same | Sections 2.6, 2.7, 3.7 | ✔ Frozen coefficients, within-cohort standardisation, both platforms reported |
| 15b | Validation: report the performance in the validation data | 15b adds: calibration in the validation data | Section 3.7 | ◐ Discrimination reported in both external cohorts; **calibration was not assessable externally** because no baseline hazard is published with the score — stated as a limitation |
| 16 | Limitations: discuss limitations and generalisability | Same | Limitations, Section 4 | ✔ Nine numbered limitations, including the aetiology/follow-up/platform confound and the threshold-marginal status of MAFG |
| 17 | Interpretation: give an overall interpretation, compare with related work | 17 adds: clinical usefulness and implications | Section 4, Conclusion | ✔ Interpretation is deliberately restricted to the methodological claim; priority for a related signature is conceded to a prior colorectal-cancer report [21] |
| 18 | Implications: discuss implications for clinical use and future research | Same | Section 4 Ninth limitation, Conclusion | ✔ Explicit "cannot do" list; the proposed remedy is a reporting template |
| 19 | Supplementary information: provide supplementary material | Same | Supplementary Items S1–S16, Item 1 | ✔ |
| 20 | Funding: report the source of funding | Same | Declarations | ✔ No specific funding |
| 21 | Conflicts of interest: declare competing interests | Same | Declarations | ✔ None declared |
| 22 | Data and code availability: state where the data and code can be obtained | Same | Declarations | ✔ Public accession IDs given; derived data supplied as S1–S16; the code bundle is described, with deposit in Zenodo under a DOI promised on acceptance |

## Items not satisfiable by this design, and why

| Item | Why it cannot be satisfied |
|---|---|
| 8 — a-priori sample size | The cohorts are fixed public resources; no prospective enrolment occurred. The number of events is reported instead (129 / 96 / 23) and the resulting precision is discussed. |
| 5a — recruitment dates | Secondary analysis: the cohorts were assembled and reported by their originating studies. |
| 15b — external calibration | The score is published as a linear predictor without a baseline cumulative hazard, so absolute risk — and therefore calibration — is not recoverable in a new cohort. This is a property of the model as defined, not of the validation. |
| 4b/7b — prospective data-quality assurance | No primary data collection occurred; quality control is limited to probe mapping, platform annotation and the inclusion filters in Section 2.1. |

## TRIPOD+AI-specific items

| Item | Status |
|---|---|
| Intended use, target user and deployment context | ✔ No clinical deployment is proposed; the model is presented as a research construct |
| Whether the model is a regression or an ML method | ✔ Regression-based (penalised Cox, LASSO-Cox); no neural or tree-based component |
| Reproducibility: code, environment, random seeds | ✔ Environment pinned (Python 3.13.12, lifelines 0.30.3, scikit-survival 0.28.0, pandas 2.3.3, NumPy 2.5.3) and every seed listed in the Declarations |
| Whether any generative AI contributed to the model | ✘ None. AI use was confined to language editing and code refactoring, declared in the Declarations; no AI tool generated data or results |
| Human oversight of AI-assisted steps | ✔ Language edits were audited sentence by sentence against the previous draft; the change log is available on request |
