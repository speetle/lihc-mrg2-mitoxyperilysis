# Stability selection does not guarantee external transport: a mitoxyperilysis score fails validation in hepatocellular carcinoma

**Running title:** Stability selection does not predict external transport

**Authors:** Bin Lian^1,*^

**Affiliations:** ^1^ School of Health, Guangzhou Vocational and Technical University of Science and Technology, Guangzhou, Guangdong, China

^*^ Corresponding author.

**Correspondence:** Bin Lian, School of Health, Guangzhou Vocational and Technical University of Science and Technology, Guangzhou, Guangdong, China. E-mail: drmilo@gkd.edu.cn. ORCID iD: 0000-0002-1477-9137.

---

## Abstract

**Background.** Mitoxyperilysis is a cell-death modality described in 2025 in mouse macrophages; whether human tumours express it is untested. A related colorectal signature has been reported. We asked whether a mitoxyperilysis-related gene (MRG) score is prognostic in hepatocellular carcinoma (HCC) and replicates.

**Methods.** We analysed the 91 MRGs evaluable in TCGA-LIHC (n = 360, 129 deaths). Model A was an L2-penalised Cox model on the 23 univariate hits; Model B applied LASSO-Cox with 200-bootstrap stability selection, assessed by nested cross-validation, ten-seed replication and a random-panel benchmark. Frozen coefficients were applied in GSE14520 (n = 242, 96 deaths).

**Results.** Twenty-three of 91 MRGs were associated with survival (*P* < 0.05), five after Benjamini-Hochberg correction (HR 1.49 and 1.45 for MAFG and KIF15). A 23-gene ridge model (5.6 events per variable; C-index 0.684) was matched by stability selection retaining KIF15 (pi = 0.91) and MAFG (pi = 0.79); MRG-2 gave C-index 0.677 (95% CI 0.623-0.728) and independence from stage and grade (adjusted HR 1.65). Three checks undercut it: pooled out-of-fold cross-validation cut both models to 0.61 (0.613 +/- 0.013); MAFG's pi fell below 0.75 in two of ten seeds; and MRG-2 did not replicate in GSE14520 (C-index 0.551), at the 47th percentile of 3,000 random pairs versus 0.596 for proliferation.

**Conclusions.** Bootstrap stability did not predict external transport; one selected gene sat on the threshold. The score is stage-independent but does not transport. Such studies should report a nested estimate, seed replication and a random-panel benchmark.

**Keywords:** mitoxyperilysis; hepatocellular carcinoma; stability selection; external validation; prognostic model

---

## 1. Introduction

Hepatocellular carcinoma (HCC) is the third leading cause of cancer death worldwide, and its incidence and mortality are rising in most regions [1,2]. Curative options — resection, transplantation and ablation — are restricted to early-stage disease, and only about a third of patients are eligible at diagnosis [3]. Sorafenib [4], lenvatinib [5] and the atezolizumab–bevacizumab combination [6] each extend survival in advanced disease by months rather than years, and no molecular biomarker is used in routine practice to select between them. Stratification by AJCC stage and histological grade leaves a wide residual spread [3,7].

HCC is also defined by its metabolic context. The liver is the principal site of gluconeogenesis, amino-acid catabolism and lipid handling, and HCC redirects these pathways towards biosynthesis and towards a redox state in which glutathione and thioredoxin buffering are chronically engaged [7,8]. The therapeutic backbone is itself redox-active: sorafenib kills HCC cells in part by generating mitochondrial reactive oxygen species, and resistance to it involves a shift in redox metabolism [9,10]. A programme reporting on mitochondrial oxidative stress should therefore be informative in this tumour type.

Mitoxyperilysis is a cell-death modality described in 2025 that is executed through that axis. Wang and colleagues showed that innate immune stimulation combined with metabolic disruption — lipopolysaccharide with carbon starvation — kills macrophages by a route independent of caspases, pyroptosis, PANoptosis, necroptosis, ferroptosis and oxeiptosis [11]. The execution sequence runs from BAX/BAK1/BID-dependent mitochondrial oxidative stress [12,13] to prolonged mitochondria–plasma-membrane contact, which the authors named mitoxyperiosis, sustained apposition causing local oxidative membrane damage and lysis [11]. We keep the two terms distinct throughout: *mitoxyperilysis* denotes the death modality, *mitoxyperiosis* the contact process that executes it. Plasma-membrane rupture is actively regulated, the NINJ1 pore being its best-characterised executor [14], and mTORC2 acts as a permissive switch — mTOR inhibition lets lamellipodia retract and pulls mitochondria away from the membrane [11,15,16] — independently linked to mitochondrial fission and ferroptosis suppression [17,18]. A mitoxyperilysis-related signature has already been reported in colorectal cancer, where it stratifies prognosis and identifies an immune-remodelled aggressive ecosystem [19,20,21], so priority for such a model does not belong to the present work. Whether a gene programme defined in macrophages under acute stimulation is represented in a human epithelial tumour transcriptome is a separate and untested question, and we therefore treat the panel as an exploratory stress-response index rather than a readout of the pathway. What we do claim is narrower, and methodological: this is, to our knowledge, the first attempt to test whether such a score *transports*.

Whether the concept transfers usefully to HCC is a separate question, motivated by the tumour's biology rather than the pathway's novelty. Two of the three arms mitoxyperilysis requires are constitutively active in HCC: an oxidative-stress–redox imbalance, driven by mitochondrial dysfunction and by a rewired one-carbon and glutathione metabolism [7,8,9], and chronic innate immune activation in an inflammation-driven tumour with an expanded myeloid compartment [22,23].

Most transcriptomic prognostic signatures published in this space never report an external test, and those that do rarely report it when it fails. We therefore designed this study around replication rather than discovery. The compressed score faces four questions: *nested* optimism, seed reproducibility of the stability threshold, a random-panel benchmark, and transport to an independent cohort with frozen coefficients.

---

## 2. Materials and methods

### 2.1 Data sources and cohort assembly

Expression (RNA-Seq V2 median all-sample Z-scores), clinical and mutation data for TCGA-LIHC (*lihc_tcga_pan_can_atlas_2018*) were obtained through the cBioPortal public API [24,25]. Inclusion required a primary tumour sample, non-missing expression for the MRG panel, complete overall survival (OS) time and status, and a recorded age, giving 360 patients of 372 samples (129 deaths, 35.8%). Median follow-up by reverse Kaplan–Meier was 27.3 months, with 40 patients at risk at 60 months (Section 3.2).

Two independent cohorts were used for external testing. *GSE14520* (Roessler et al. [26]), an Affymetrix HG-U133A/HG-U133A-2.0 cohort of resected HCC and the standard external validation resource for HCC prognostic signatures, gave 242 tumours, 96 deaths (39.7%) and a median follow-up of 57.0 months. *GSE76427* (Grinchuk et al. [27]) is an Illumina HumanHT-12 v4 (GPL10558) cohort of 115 resected tumours, 23 deaths (20.0%) and a median follow-up of 21.5 months. Probe-to-gene mapping used each platform's annotation file, retaining the highest-mean probe where several mapped to one gene. Ethics approval was not required: all data are de-identified and publicly available.

Three features bound what can be inferred. TCGA-LIHC is predominantly Western and hepatitis-C/alcohol-associated, whereas GSE14520 is a Chinese HBV cohort, so aetiology is confounded with cohort. Follow-up is short relative to the clinical course of resected HCC (median 27.3 months). And no BCLC stage, Child–Pugh class or ECOG status is recorded, leaving pathological AJCC stage as the only staging variable — BCLC, not AJCC, governs clinical management of HCC.

### 2.2 Construction of the mitoxyperilysis-related gene (MRG) panel

The MRG panel was derived, as described in an unpublished companion analysis of glioma by the same group, from GSE235046 (mouse bone-marrow-derived macrophages; media, LPS, carbon starvation, LPS+CS and LPS+CS+Torin, three replicates per arm) [11], and is reproduced here so that it does not depend on the companion manuscript. Two criteria were applied simultaneously — synergy and sensitivity to mTOR inhibition — and Torin inhibits mTORC1 and mTORC2 alike, so the second cannot by itself establish mTORC2 dependence. The exact fold-change cut-offs are given in Supplementary Methods.

A limitation of the derivation belongs here: no criterion measured the death phenotype itself — neither lysis, mitochondria–plasma-membrane contact, nor BAX/BAK1/BID dependence — and the panel was derived for a glioma analysis of the same concept, applied here to different patients, endpoints and tumour type.

The derivation yielded 101 mouse genes, 92 with an unambiguous human orthologue, and **91 evaluable in TCGA-LIHC** (ANKRD33B had no usable probe set and was dropped). The panel was fixed before any survival analysis.

### 2.3 Covariate coding and handling of missing data

Age was standardised to the cohort mean and SD; sex was coded male versus female. AJCC pathological stage was coded III–IV versus I–II and histological grade G3–G4 versus G1–G2. Stage was missing for 21 of 360 patients and grade for 5.

The primary adjusted analyses are **complete-case**: patients missing stage or grade were excluded, giving n = 337 (23 exclusions, 4 of whom lacked both). Two pre-specified sensitivity analyses test that choice: (i) missing stage or grade coded as the reference category (missing → 0), retaining n = 360, the coding used by the pipeline that produced the deposited per-patient tables; and (ii) that coding plus a missingness indicator. All three are reported for both models (Section 3.4).

### 2.4 Model A — the full-panel index (L2-penalised Cox)

Univariate Cox regression was applied to each of the 91 genes. Genes with *P* < 0.05 entered a multivariable Cox model with an L2 ridge penalty (penalizer = 1.0) to control collinearity; the risk score was the linear predictor (coefficients in Table 2) and patients were dichotomised at the median for visualisation only, all inference using the continuous score per standard deviation. Discrimination used Harrell's C-index [28] with 1,000-resample bootstrap confidence intervals and time-dependent AUC at 12–60 months, and the events-per-variable (EPV) ratio was computed against the number of deaths [29,30].

Model A is a deliberate demonstration of the over-parameterised case this literature routinely publishes — 23 terms on 129 deaths — not a foil for penalisation being *unnecessary*: the ridge penalty is itself a shrinkage device, and is why no coefficient is individually significant.

### 2.5 Model B — stability-selected two-gene score (MRG-2)

Model B was derived from the same 91 genes and 360 patients and differs only in the fitting procedure: the LASSO-Cox of Tibshirani [37], fitted on all 91 genes, does not use the univariate screen that Model A requires. Gene-wise Z-scores were re-standardised to zero mean and unit variance, and *CoxnetSurvivalAnalysis* (scikit-survival 0.28.0) with *l1_ratio* = 1.0 was fitted over a 60-value α path, the optimal α chosen by 10-fold cross-validation of the C-index under the 1-SE rule.

Following Meinshausen and Bühlmann [31], 200 bootstrap resamples of the 360 patients were drawn, the LASSO refitted at the 1-SE α in each, and the selection frequency π of each gene recorded. Genes with π ≥ 0.75 were carried into a multivariable Cox model and members not significant at *P* < 0.05 removed; both the π ≥ 0.75 set and the final reduced set are reported.

The threshold π = 0.75 was fixed a priori as the conventional stability-selection cutoff [31], before any data were examined; it is a selection rule, not a false-discovery guarantee. The dependency-robust variant of that guarantee, the Meinshausen–Bühlmann bound on the expected number of falsely selected variables, is larger than the two-gene model it is meant to protect, so **the bound is uninformative here and we do not use it as evidence of control** (Supplementary Methods). Because a bootstrap threshold is seed-dependent, the 200-resample step was repeated under ten independent seeds and the threshold band varied over π = 0.60–0.85 at the primary seed. Both gene sets predate the external cohorts; the last step (backward elimination at *P* < 0.05) makes the reported coefficient *P* values post-selection estimates rather than pre-specified tests.

### 2.6 Fully nested cross-validation

The apparent C-index of a model whose genes were selected on the full data is optimistic. We repeated the *entire* Model B procedure inside each training fold of a 10-fold split and applied the resulting coefficients to the held-out fold, and ran Model A the same way. The primary statistic is the **pooled out-of-fold C-index** — the ten held-out predictions concatenated and scored once — because fold-wise C-indices have different event rates and their mean is biased. The whole procedure was repeated under **ten independent random splits**; the mean and standard deviation across them are reported (Supplementary Methods).

### 2.7 Benchmark against random panels

To ask whether a two-gene score does anything an arbitrary pair would not, 3,000 random pairs were drawn from the evaluable panel without replacement (seed 42 in discovery, seed 11 in GSE14520), a two-gene Cox model fitted in each cohort, and the observed MRG-2 C-index reported as a percentile of that null. Because the benchmark uses the *frozen* score, which was chosen by stability selection on these same patients, it does not price the gene-selection step: a sanity check rather than evidence of transportability.

### 2.8 Adjustment for stage and grade

Multivariable Cox models of the form score + age + sex were extended by adding AJCC stage III–IV and grade G3–G4, and both the continuous score (per 1 SD) and the binary risk group were tested.

The external analyses freeze the *coefficients* derived in TCGA-LIHC and apply them unchanged, but expression is standardised **within each validation cohort** (and within each platform before pooling), not with the discovery means and SDs, because the platforms differ in probe chemistry and dynamic range, so discovery-scale means would mix platform offsets into the score. The external score is therefore a per-SD linear predictor, and the absolute external C-index is the quantity of interest.

### 2.9 Calibration, discrimination and proportional-hazards diagnostics

Calibration was assessed by a **cross-validated calibration slope**, a **calibration plot** by quintile of predicted 3-year survival, and **time-dependent Brier scores** with the integrated Brier score, following Graf et al. [38]. Proportional hazards was tested by Schoenfeld residuals under four time transforms (rank, Kaplan–Meier, identity, log) [28]; definitions are in Supplementary Methods.

### 2.10 Proliferation score

Because HCC is a proliferative tumour, a 20-gene proliferation score was constructed as the mean Z-score of 20 canonical cell-cycle markers (gene list in Supplementary Table S16). Association with each MRG score used Spearman correlation and multivariable Cox regression, with C-index differences tested by a *paired* bootstrap over patients (2,000 resamples, seed 7). This is a research construct, not a validated clinical assay.

### 2.11 Molecular subtyping and immune infiltration

k-means clustering (k = 2, 3, 4) was run on panel-gene expression and the solution chosen by silhouette width. Eleven immune features (Table 6) were scored as the mean Z-score of 4–6 marker genes each (ssGSEA-lite) [32] and compared between risk groups by the Mann–Whitney U test, with Benjamini–Hochberg adjustment reported alongside the raw values. The analysis is not adjusted for tumour purity, none being available for this cohort (Section 4).

### 2.12 Mutation, tumour-versus-normal expression, and multiplicity

Non-synonymous mutation calls for 16 recurrently altered HCC genes were retrieved from the same cBioPortal study and compared between risk groups by Fisher's exact test with Benjamini–Hochberg adjustment across the 16 genes.

Multiplicity was handled within each analysis family rather than globally: the 91-gene univariate screen, corrected by Benjamini–Hochberg with the dependency-robust Benjamini–Yekutieli procedure [39] reported alongside; the 11 immune features; the 16 mutation genes; and the three paired ΔC-index comparisons, the last reported unadjusted and interpreted descriptively. *P* values quoted in the text are uncorrected unless stated.

### 2.13 Sample size, reporting standard and analysis of a frozen dataset

No a-priori sample-size calculation was performed: the discovery cohort is a fixed public resource, not a prospectively enrolled series, contributing 360 analysable patients and 129 deaths, with 96 and 23 deaths in the external cohorts. The study is reported against the TRIPOD and TRIPOD+AI statements [40,41], with a completed checklist as Supplementary Item 1 and items that cannot be satisfied by a secondary analysis (prospective registration, sample-size justification, external blinded validation) marked accordingly.

All thresholds — the *P* < 0.05 univariate screen, the 1-SE rule, π ≥ 0.75, and the decision to report both models — were fixed before either validation cohort was examined.

---

## 3. Results

### 3.1 Univariate screening

Of the 91 evaluable MRGs, 23 were significantly associated with OS at raw *P* < 0.05 (Table 3; Supplementary Tables S1–S2). After Benjamini–Hochberg correction across 91 tests, **five genes remained significant at q < 0.05** — MAFG (q = 0.002), KIF15 (q = 0.002), TXNRD1 (q = 0.013), DAB2 (q = 0.025) and CEP19 (q = 0.028) — with MBOAT7 at q = 0.051 on the boundary and the remaining 17 of the 23 at q = 0.057–0.20. Only MAFG and KIF15 also survive the dependency-robust Benjamini–Yekutieli procedure (both q = 0.012); TXNRD1 is the next closest at q = 0.064 and the weakest of the 23 raw hits reaches 1.00, so the count of five is sensitive to the correlation structure of the panel.

The strongest risk-associated genes were MAFG (HR 1.489, 95% CI 1.231–1.802; *P* = 4.2×10⁻⁵), KIF15 (HR 1.446, 95% CI 1.210–1.728; *P* = 4.9×10⁻⁵), TXNRD1 (HR 1.399, *P* = 4.1×10⁻⁴), DAB2 (HR 1.364, *P* = 1.1×10⁻³), CEP19 (HR 1.333, *P* = 1.6×10⁻³) and MBOAT7 (HR 1.285, *P* = 3.3×10⁻³). Nine further risk-associated genes had HR > 1.22 but q > 0.05, and five protective genes were led by PPP1R10 (HR 0.794, *P* = 5.0×10⁻³, q = 0.057) (Table 3; Figure 1A).

Two features are worth recording. It is short: 23 of 91 genes reach raw *P* < 0.05, against 56 of 89 in the matched glioma analysis. And the corrected signal is redox-led — MAFG [33,34] and TXNRD1 are among the five that survive, with OSGIN2 (q = 0.074) just outside.

### 3.2 Model A: the full-panel index

L2-penalised multivariable Cox regression on the 23 univariate hits retained all 23 genes (Table 2). Median dichotomisation produced 180 high-risk and 180 low-risk patients, and high-risk patients had substantially worse OS (HR 1.87 per SD, 95% CI 1.56–2.24; log-rank *P* = 1.9×10⁻⁶; Figure 1B–D). The apparent C-index was 0.684 (95% CI 0.625–0.733) and the mean time-dependent AUC 0.733 (1/3/5-year 0.772 / 0.718 / 0.720; Figure 2A).

With 129 deaths and 23 fitted terms the EPV ratio is 5.6, below the conventional threshold of 10 [29,30]. And although no coefficient reversed direction relative to its univariate estimate, the ridge penalty shrank every one so that none was individually significant (all *P* > 0.21; Table 2), so the coefficients cannot be read as biological effect sizes. **A model in that condition can still rank patients acceptably; it is simply not estimating biology.** One objection is that the penalty, not the number of terms, produced those null coefficients; it is not so. Refitting the same 23 genes without penalty converges, leaves every coefficient small (largest |coefficient| 0.35, largest hazard ratio 1.33, no sign reversals, condition number 6.0), and still yields a single term at *P* < 0.05 with apparent discrimination unchanged (0.693 vs 0.684). The panel carries no individual gene-level signal under either estimator (Supplementary Table S4b).

The median-split separation is conventionally reported as a median (80.7 vs 35.8 months), but both medians rest on a thin tail: median follow-up is 27.3 months and only 29 of the 180 low-risk patients remained at risk at 60 months. We therefore also report the 60-month restricted mean survival time, which uses the whole curve: 47.5 vs 34.2 months for Model A and 47.4 vs 34.0 for MRG-2. Both low-risk curves cross 0.5 at the same observed event time (80.744 months), the first death after which neither curve recovers (Supplementary Results).

### 3.3 Model B: stability selection compresses the index to two genes

**Cross-validated model size.** The 10-fold cross-validation curve has a real optimum rather than a plateau (Figure 3A), peaking at α = 0.0548 with 11 genes (CV C-index 0.6044) and falling away monotonically as the penalty is relaxed: 22 genes 0.5909, 47 genes 0.5788, 89 genes 0.5442. The total range is 0.0633 against a fold standard error of 0.0062, and the 1-SE rule accordingly returns α = 0.0631 with 9 genes (0.6013), only 0.49 SE below the maximum.

**Stability selection.** Across 200 bootstrap resamples at the 1-SE α the median model contained 11 genes (interquartile range 9–13, full range 5–16), but the *identity* of the leading genes was reproducible at the top: KIF15 (91.0%), MAFG (78.5%), AKNA (62.5%), PPP1R10 (57.0%), MBOAT7 (51.0%), DAB2 (46.0%), TAF12 (45.0%) (Figure 3B; Table 4). The prespecified threshold π ≥ 0.75 yielded exactly two: KIF15 and MAFG.

**Threshold sensitivity.** The two-gene solution is stable only over a *narrow* band: π ≥ 0.65, 0.70 and 0.75 all return {KIF15, MAFG}, whereas π ≥ 0.60 adds AKNA and π ≥ 0.80 returns KIF15 alone. The result hinges on the prespecified value more than we anticipated.

**The MRG-2 score.** The final linear predictor, with expression standardised to the discovery cohort (per SD):

> MRG-2 = **+0.310**·KIF15 **+0.334**·MAFG

The score is a linear predictor and no baseline cumulative hazard is given, so absolute risks are not recoverable from this paper; the median split in the Kaplan–Meier panels is a display convention, not a proposed threshold, and every estimate reported is either continuous or explicitly labelled as median-stratified. The two coefficients, their hazard ratios and their univariate counterparts are given in Table 4.

**Seed replication.** The two genes are not equally robust — the first uncomfortable result. Repeating the entire 200-resample bootstrap under ten independent seeds (Table 4).

KIF15 is selected in every run with margin. **MAFG sits on the threshold**: under two of the ten seeds its π falls to 0.690 and 0.735, the π ≥ 0.75 set then contains KIF15 alone, and the "two-gene" score degenerates into a single-gene score. The margin is not merely a seed artefact of the count: π is a binomial proportion over 200 resamples, so its Monte-Carlo standard error at π = 0.785 is 0.029, and MAFG's distance from the threshold is only 1.2 standard errors — a one-sided binomial test cannot reject π = 0.75 (*P* = 0.14) — against 7.9 standard errors for KIF15. We report MAFG as a threshold-marginal rather than a stably selected member (Figure 5D; Supplementary Table S11).

**Internal performance and nested optimism.** MRG-2 separated survival as well as the 23-gene model in the discovery data. Median split gave 180 patients per group, median OS 80.7 vs 33.0 months (log-rank *P* = 6.3×10⁻⁶; Figure 3C) and HR 1.66 per SD (95% CI 1.37–2.00; *P* = 1.2×10⁻⁷). The apparent C-index was 0.677 (95% CI 0.623–0.728), indistinguishable from Model A's 0.684 (paired bootstrap ΔC = −0.0073, 95% CI −0.0416 to +0.0278; *P* = 0.68). Time-dependent AUC was 0.770 / 0.709 / 0.651 at 1, 3 and 5 years (mean 0.689); the 5-year point rests on 40 patients at risk and is indicative only.

Those figures are apparent. Re-running the whole selection procedure inside each of ten outer folds, and pooling the held-out predictions, gives the second uncomfortable result:

| Model | Pooled out-of-fold C-index (ten random splits) | Prespecified split | Range over splits | Apparent |
|---|---|---|---|---|
| Model B (MRG-2) | **0.613 ± 0.013** | 0.596 | 0.596 – 0.635 | 0.677 |
| Model A (23 genes) | **0.622 ± 0.010** | 0.610 | 0.610 – 0.647 | 0.684 |

Two conclusions follow. The optimism is real and excludes zero — 0.081 C-index units for MRG-2 (95% CI 0.040–0.122) and 0.074 for Model A (0.053–0.096), of the same magnitude for both models, so the *apparent* gap between them was never meaningful. **The two models remain indistinguishable under the honest estimate**: two genes deliver the same pooled out-of-fold discrimination as twenty-three, and the split-to-split spread makes any comparison uninformative (Section 2.6).

**Benchmark against random panels.** In the discovery cohort MRG-2 is nonetheless exceptional among two-gene panels: against 3,000 random pairs from the same 91 genes (mean C-index 0.5608, SD 0.0333, 95th percentile 0.6172) the observed 0.6767 exceeded **every one** (Figure 5C) — a strong in-sample result that does not price the selection step (Section 2.7).

### 3.4 Independence from stage and grade

The adjusted models use the complete-case primary analysis (n = 337) with two missing-data sensitivities (Table 5). In a multivariable model containing MRG-2, age, sex, AJCC stage III–IV and grade G3–G4, MRG-2 remained significant (HR 1.65 per SD, 95% CI 1.34–2.04; *P* = 2.8×10⁻⁶) and **advanced stage was independently significant** (HR 2.19, 95% CI 1.50–3.20; *P* = 4.9×10⁻⁵). Grade was not prognostic, alone (HR 1.09, *P* = 0.64; Table 5) or adjusted (HR 0.93, *P* = 0.73); Model A adjusted gave HR 1.88 (95% CI 1.52–2.33) with the same covariate set. MRG-2 therefore adds to stage rather than duplicating it.

| Coding of missing stage/grade | n | MRG-2 score HR | Stage III–IV HR |
|---|---|---|---|
| Complete case (**primary**) | 337 | 1.65 (*P* = 2.8×10⁻⁶) | 2.19 |
| Missing → 0 (sensitivity) | 360 | 1.66 (*P* = 6.6×10⁻⁷) | 2.02 |
| Missing → 0 + missingness indicator (sensitivity) | 360 | 1.68 (*P* = 3.8×10⁻⁷) | 2.20 |

The three codings agree closely: the score hazard ratio moves by at most 0.03 across them and the stage hazard ratio by at most 0.18, all well inside the confidence intervals. The choice of missing-data handling is therefore not what carries the stage-independence result.

One diagnostic complicates the model. Schoenfeld residuals reject proportional hazards for MRG-2 under all four time transforms (rank χ² = 9.99, *P* = 0.002; KM χ² = 11.19, *P* = 0.001; identity χ² = 11.47, *P* = 0.001; log χ² = 4.36, *P* = 0.037), whereas Model A satisfies the assumption under all four (rank *P* = 0.13). A single hazard ratio for MRG-2 is therefore an average over a time-varying effect, and the separation in Figure 3C is better read as an early-separation effect than a constant multiplier.

### 3.5 Calibration and discrimination

Discrimination and calibration answer different questions, and only the first had been reported. The cross-validated calibration slope was 0.95 for MRG-2 (95% CI 0.54–1.38, bootstrap SE 0.21) and 0.95 for Model A (95% CI 0.65–1.28, SE 0.16); both intervals include 1 (Figure S1A). Time-dependent Brier scores were similar, favouring Model A marginally: 0.121/0.200/0.212 at 1/3/5 years for Model A against 0.124/0.205/0.233 for MRG-2, integrated 0.189 and 0.197 (Figure S1B).

### 3.6 Proliferation overlap

MRG-2 is substantially correlated with the 20-gene proliferation score (Spearman ρ = **0.708**, *P* = 5.9×10⁻⁵⁶; n = 360), and Model A almost as much (ρ = 0.700) (Figure 2B); KIF15 is a mitotic kinesin, so this is unsurprising in part.

In a joint model containing both scores, MRG-2 carried HR 1.60 per SD (95% CI 1.21–2.12; *P* = 6.4×10⁻⁴) and the proliferation score did not retain significance (HR 1.05, 95% CI 0.80–1.37; *P* = 0.73); after adding age, sex, stage and grade MRG-2 remained significant (*P* = 3.6×10⁻⁴) and the proliferation score did not (*P* = 0.89). That concerns regression coefficients under collinearity, not discrimination. Tested as discrimination with a paired bootstrap the two scores are **not distinguishable**: MRG-2 C-index 0.6767 against proliferation 0.6428, ΔC = +0.034 (95% CI −0.012 to +0.076; *P* = 0.147); Model A does separate (ΔC = +0.041, 95% CI 0.002 to 0.080; *P* = 0.038). Its only distinctive feature is that its non-KIF15 half is a redox transcription factor rather than a second cell-cycle gene, and it did not survive external testing.

### 3.7 External validation

**GSE14520 (n = 242 tumours, 96 deaths, median follow-up 57.0 months).** Sixty-five of the 92 panel genes were represented on the Affymetrix platform, including both MRG-2 genes (KIF15, probe 219306_at; MAFG, probe 204970_s_at), and 19 of the 23 Model A genes (Table 8).

MRG-2 **failed to replicate**. Its C-index interval includes 0.5, its hazard ratio is not significant, and after adjustment for age, sex, TNM stage III–IV and platform the score is clearly null (HR 1.05, *P* = 0.63) while stage remains strongly prognostic (HR 3.04, *P* < 0.001). Restricting to the larger platform (GPL3921, n = 221 tumours, 85 deaths) gives C-index 0.548.

The 23-gene Model A did replicate, weakly but significantly, at 0.577 — with one qualification: four of its 23 genes (CEP19, WDR35, PTPN23, LRRC58) are absent from the Affymetrix platform and their frozen contributions were set to zero, the cohort mean after standardisation. The external Model A result is therefore a 19-gene approximation, and the "over-parameterised model transported, the parsimonious one did not" contrast is weaker than it appears.

Two comparisons sharpen the failure. In the same cohort a generic 20-gene proliferation score performed **better** as discrimination (0.596 vs 0.551; paired bootstrap ΔC = −0.045, 95% CI −0.096 to +0.001; *P* = 0.058) and far better by log-rank (7.2×10⁻⁴ vs 0.085), so the ordering of the two scores inverted between discovery and validation (Figure 5B). The random-panel benchmark inverted too: among 3,000 random two-gene panels the mean C-index was 0.5552 (SD 0.0311, 95th percentile 0.6086) and **52.97% matched or beat MRG-2**, placing the observed score at the **47th percentile** of the null, below its own mean, where in discovery it exceeded all 3,000 (Figure 5C).

The two cohorts also differ in aetiology, follow-up structure and platform (Section 2.1), and no single summary statistic can separate those differences from a genuine failure of the score.

**GSE76427 (n = 115 tumours, 23 deaths, median follow-up 21.5 months).** This cohort is uninformative rather than contradictory: both scores gave point estimates below 0.5 (MRG-2 C-index 0.402, 95% CI 0.255–0.548; Model A 0.426, 95% CI 0.290–0.555), no hazard ratio approached significance (*P* = 0.16 and 0.11), and Model A's log-rank test gave *P* = 0.041 with HR 0.69 — a protective direction we do not treat as evidence for the score, since with 23 deaths the log-rank test and the hazard ratio weight follow-up differently. The direction problem is not specific to this panel: canonical proliferation markers were themselves non-prognostic or apparently protective in the same 115 tumours (MKI67 HR 0.72, 95% CI 0.41–1.28; TOP2A HR 0.86, 95% CI 0.50–1.47; CCNB1 HR 1.10, 95% CI 0.68–1.79) (Supplementary Results).

**Summary of the validation trajectory for MRG-2.** Apparent 0.677 → pooled out-of-fold 0.613 → independent cohort 0.551 → 47th percentile of random two-gene panels: monotone, and the clearest result of this study (Figure 5).

### 3.8 Molecular correlates of the risk groups

k-means clustering of the panel genes gave its best silhouette at k = 2 (0.111), producing subtypes of 141 and 219 patients (45 and 84 deaths) that were **not separated by survival (log-rank *P* = 0.171)**; the silhouette is low in absolute terms. We report the clustering as a negative result (Figure 4A): unlike the glioma analysis, this panel does not partition HCC into prognostically distinct groups.

Immune feature scores were compared between risk groups (Figure 4B; Table 6). **Only one of the eleven differed: the NK-cell signature was lower in high-risk tumours (Δ = −0.295, *P* = 1.5×10⁻⁴, surviving Benjamini–Hochberg correction).** The remaining ten did not reach *P* < 0.05 and none survives correction — M2 macrophage (Δ = −0.146, *P* = 0.072), neutrophil (+0.182, 0.086), checkpoint (+0.190, 0.052), regulatory T cell (+0.131, 0.127), interferon (+0.115, 0.227), the rest between *P* = 0.10 and 0.66.

The NK-cell finding needs a stronger caveat: these scores are marker means, neither deconvoluted nor corrected for tumour purity, so a lower NK score in high-risk tumours can be produced by a lower tumour-cell fraction at the same immune infiltrate. We report it as hypothesis-generating and do not use the immune analysis to support the biological reading of the score.

### 3.9 Mutation profiling

Sixteen recurrently altered HCC genes were compared across all 360 patients, 180 per group (Figure 4C; Table 7). High-risk tumours were enriched for TP53 (42.8% vs 16.7%, *P* = 7.9×10⁻⁸, BH q = 1.3×10⁻⁶), CTNNB1 (32.2% vs 19.4%, *P* = 0.0079, q = 0.063) and RB1 (8.3% vs 2.2%, *P* = 0.016, q = 0.087); BAP1 (3.3% vs 7.8%, *P* = 0.11) and AXIN1 (4.4% vs 8.9%, *P* = 0.14) trended the other way. TTN, ALB, APOB, ARID1A, ARID2, TSC1, TSC2, NFE2L2, KEAP1, PTEN and PIK3CA did not differ; after Benjamini–Hochberg correction across the 16 genes, **only TP53 survives**.

The TP53 enrichment is the expected direction and the clearest biological signal in the study: TP53-mutant HCC is the proliferative, poorly differentiated, genomically unstable class, in which a proliferation-and-redox score should be high [3,35]. The CTNNB1 observation runs the other way, but is weaker than the raw *P* suggests: CTNNB1-mutant HCC is conventionally the *better*-prognosis, well-differentiated subclass and β-catenin activation drives immune escape [8,36], yet CTNNB1 mutation is modestly enriched in the *high*-risk group at q = 0.063, which does not survive correction. The direction is therefore discordant — **a score high in both TP53-mutant and CTNNB1-mutant tumours would not be tracking TP53-driven proliferation specifically** — but the CTNNB1 arm of that argument is suggestive rather than established.

### 3.10 Tumour-versus-normal expression

Using the cBioPortal reference-normal Z-score profile, 22 of the 91 panel genes were over-expressed relative to reference normal liver (mean Z > 1) and 11 under-expressed (mean Z < −1), median Z 0.219 (Figure 6). The cohort contains only primary solid tumours, so this is an external-reference comparison and descriptive only.

---

## 4. Discussion

The result of this study is not that a mitoxyperilysis-related score predicts HCC survival. It is that **the same 91 genes, fitted two ways, produce an over-parameterised 23-gene index and a two-gene index that is not — compression is free in the discovery data — yet the compressed score still fails to transport to an independent cohort, where it is no better than a random pair of panel genes or a generic proliferation score.**

We begin with the part that worked. The full-panel index was the natural first attempt — 23 univariate hits, a ridge penalty for collinearity, apparent C-index 0.684 — and two things were wrong with it. With 23 coefficients on 129 deaths the EPV ratio was 5.6, half the conventional threshold [29,30], and no coefficient was individually significant. Nor did a pure LASSO-plus-1-SE rule deliver sparsity: it selected nine genes only 0.49 SE below the cross-validation maximum. Sparsity came instead from asking which genes were selected *repeatedly* — KIF15 in 91% of 200 bootstraps and MAFG in 78%, with a median model of 11 genes. Stability, not penalty strength, identified the core.

The two-gene score was better on every axis that matters in the discovery data: coefficients significant and directionally consistent with their univariate estimates, an EPV ratio of 64.5 against 5.6, the same discrimination as the full panel with two parameters instead of 23, no absorption of AJCC stage, and a win over all 3,000 random two-gene panels.

What happened next is the substance of this paper. Pooled out-of-fold cross-validation cut both models to about 0.61 and made them indistinguishable: the *apparent* superiority of both over chance was largely selection optimism, so a study reporting only apparent C-indices in this design is reporting an artefact. The data support one stably selected gene and one threshold-marginal gene.

The external test settled it: in GSE14520 the frozen MRG-2 score sat at the 47th percentile of 3,000 random two-gene panels while a generic proliferation score in the same cohort performed better. That inversion, with the monotone decline from 0.677 to 0.613 to 0.551, is what selection optimism looks like when measured rather than assumed. Because the score was well calibrated in discovery, the failure is not poor fit: it is a failure of the coefficients to mean the same thing in another population.

The one result running against the overall negative picture is that the 23-gene Model A *did* replicate weakly (C-index 0.577) while the two-gene score did not. Three considerations apply, and they do not all point the same way. First, the external Model A used only 19 of its 23 genes, so the two models are not compared on equal footing. Second, a ridge index is *robust to single-gene noise by construction*: averaging correlated genes should transport more stably than any two, so the contrast is a known property of penalised aggregation rather than a paradox. Third, the models share the same 91 genes, 360 patients and endpoint, and their external difference (ΔC = −0.026, *P* = 0.21) is not significant. Under any reading neither score is a candidate biomarker.

What is specific to HCC is worth recording even though it did not translate externally. The corrected signal is redox-led — MAFG, a small-Maf protein that heterodimerises with NRF2 to drive antioxidant-response-element transcription [33,34], and TXNRD1 among the five that survive, with OSGIN2 just outside. In a tumour whose therapeutic backbone kills through mitochondrial reactive oxygen species and whose resistance is redox-mediated [9,10], a redox-led prognostic signal is biologically coherent. Coherence is not transport, however, and the redox reading rests on a gene whose selection stability is threshold-dependent.

Two broader points follow. The first is that **stability under resampling is not evidence of transportability**: KIF15 was selected in 91% of bootstraps and MRG-2 exceeded every random panel in discovery, yet the frozen score landed at the 47th percentile of the null externally: resampling measures the stability of a choice within a dataset, not its validity outside one. The second is that **a threshold is a decision, not a discovery**: the same data that returned a two-gene model at π = 0.75 returned a three-gene model at 0.60 and a one-gene model at 0.80, over an interval one step wide.

### Limitations

Nine limitations bound the interpretation. First, and most importantly, the compressed score failed external validation; every statement in Sections 3.3–3.6 concerns the discovery cohort and none should be generalised. Second, the discovery cohort is modest (129 deaths), so the apparent C-index of 0.677 retained 0.081 units of optimism; the external value is the one to carry forward. Third, the two genes are not equally supported: KIF15 is stable under every seed, MAFG is not, and its margin from the threshold is within Monte-Carlo error. Fourth, the discovery and validation systems are mismatched — a mouse macrophage panel under acute starvation, a human bulk tumour target, neither retained gene a pathway executioner, differing aetiology and platform; we cannot separate those explanations. Fifth, no within-cohort tumour-versus-normal comparison is possible, so Section 3.10 is descriptive only. Sixth, the immune analysis is a marker-mean proxy, neither purity-corrected nor deconvoluted. Seventh, proportional hazards is violated for MRG-2, so its hazard ratios are time-averaged. Eighth, the endpoint is overall survival only, whereas resection-series cohorts such as GSE14520 are conventionally analysed for recurrence-free survival, the more sensitive endpoint for resected disease; RFS was not usable here. Ninth, no prospective or decision-impact analysis was performed: the score is untested for guiding adjuvant or locoregional therapy, for selecting patients for immunotherapy, for supplementing BCLC staging, or for enriching trial enrolment. We likewise omit any drug-sensitivity analysis (GDSC/CTRP): cell-line pharmacogenomic resources are not patient-matched to these cohorts, so predicted IC₅₀ values are extrapolation, not observation.

### Conclusion

A mitoxyperilysis-related gene panel yields a prognostic score for hepatocellular carcinoma that is stable, parsimonious, stage-independent and well calibrated in TCGA-LIHC — and that does not transport. Fitted to the whole panel it is 23 genes at an events-per-variable ratio of 5.6 with no interpretable coefficient; refitted with stability selection it is two genes, KIF15 and MAFG, at a ratio of 64.5, individually significant and with the same discrimination as the 23-gene model under pooled out-of-fold cross-validation. One of the two sits on the selection threshold, within Monte-Carlo error of it, and disappears under two of ten bootstrap seeds; the apparent discrimination carries 0.081 C-index units of optimism (95% CI 0.040–0.122). In an independent cohort of 242 tumours the frozen score is indistinguishable from chance, sits at the 47th percentile of random two-gene panels, and is numerically outperformed by a generic proliferation score. It is not a readout of the mitoxyperilysis pathway, priority does not belong to this study [21], and on these data it is not a candidate biomarker. What we can offer instead is a template: a nested estimate, a seed replication of the stability threshold, a random-panel benchmark and a well-powered external test, the last of which reversed the conclusion.

## Declarations

**Ethics approval and consent to participate.** Not applicable. This study analysed only publicly available, de-identified human transcriptomic data (TCGA-LIHC, GSE14520 and GSE76427) and generated no new human or animal material.

**Consent for publication.** Not applicable.

**Nature of the study — no functional validation.** This is a purely computational secondary analysis of public transcriptomic and clinical data. No wet-laboratory experiment was performed: no cell line, no animal model, no perturbation of BAX, BAK1, BID, NINJ1, mTORC2 or any other component of the pathway, and no assay of lysis, membrane contact or oxidative damage. Consequently, the panel analysed here is a transcriptional proxy for a stress response and **the study provides no evidence that any mitoxyperilysis-related mechanism operates in hepatocellular carcinoma**. Every biological statement in Sections 3 and 4 is an association inferred from expression data, and the negative external result applies to the *score*, not to the pathway.

**Availability of data and materials.** All primary data are public. TCGA-LIHC expression, clinical and mutation data were obtained from cBioPortal (study *lihc_tcga_pan_can_atlas_2018*); the validation cohorts GSE14520 (platforms GPL571 and GPL3921, with the series clinical supplement) and GSE76427 (platform GPL10558) were obtained from GEO, and the panel-derivation dataset GSE235046 from GEO. Derived data are provided with this manuscript: Supplementary Table S1 (the 92-gene human panel and the 91-gene LIHC univariate screen), S2 (univariate Cox with BH and BY q values), S3 (per-patient TCGA-LIHC risk scores and clinical data), S4 (the 23 Model A coefficients) with S4b (the same 23 genes refitted without penalty), S5 (stability-selection frequencies for all 91 evaluable genes), S6 (risk-group mutation summary with raw and BH-adjusted Fisher exact *P* values), S7 (immune feature scores), S8 (multivariable models), S9 (per-patient GSE76427 data), S10 (fully nested 10-fold cross-validation, with retained genes and held-out C-index per fold) with S10b (the pooled out-of-fold C-index under the prespecified partition and under ten independent random splits, with the optimism of each model and its 95% confidence interval), S11 (bootstrap seed replication), S12 (random-panel benchmark for both cohorts), S13 (per-patient GSE14520 external-validation data), S14 (GSE76427 external-validation summary), S15 (calibration, time-dependent Brier scores and proportional-hazards diagnostics for both models) and S16 (the 20 marker genes composing the proliferation score). The completed TRIPOD and TRIPOD+AI checklist is supplied as Supplementary Item 1.

**Availability of code.** The analysis code, the MRG panel definition and the derived per-patient tables are supplied with this manuscript as a code bundle (the bundle contains the pipeline that retrieves the cBioPortal and GEO data, fits both models, performs the nested cross-validation, the ten-seed replication, the random-panel benchmark, the calibration and Brier analyses and the proportional-hazards tests, together with the table and figure generators, a `requirements.txt` and the seed list). The complete bundle is openly available at https://github.com/speetle/lihc-mrg2-mitoxyperilysis; on acceptance it will be archived in Zenodo under a DOI that pins the exact version. Environment: Python 3.13.12 with lifelines 0.30.3, scikit-survival 0.28.0, pandas 2.3.3, NumPy 2.5.3, SciPy, matplotlib and Pillow. Seeds: 42 for the cross-validation split, the bootstrap C-index intervals and the discovery random-panel benchmark; 2026 for the primary stability-selection bootstrap; 2026, 2027, 1, 2, 3, 42, 100, 555, 777 and 1234 for the ten-seed replication; 11 for the GSE14520 random-panel benchmark; 7 for the paired C-index bootstraps.

**Competing interests.** The author declares no financial or non-financial competing interests, including business or family interests.

**Funding.** This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

**Authors' contributions (CRediT).** Bin Lian: Conceptualisation; methodology; software; formal analysis; investigation; data curation; writing — original draft; writing — review and editing; supervision; project administration; guarantor of the analysis. The author read and approved the final manuscript.

**Acknowledgements.** Not applicable.

**Declaration of generative AI and AI-assisted technologies in the writing process.** During the preparation of this work the author used an AI-assisted tool for two purposes: (i) language editing and improving the readability and concision of the text, and (ii) assistance in drafting and refactoring the analysis code. No AI tool was used to generate data, to produce numerical results, or to select or interpret study findings; every number reported here was computed by the deposited analysis pipeline from public source data, and every citation was verified against PubMed or Crossref. The AI-assisted language edits were audited sentence by sentence against the previous draft to confirm that no number, *P* value, confidence interval, gene name, probe identifier or reference was altered; the change log from that audit is available on request. After using these tools, the author reviewed and edited the content as required and takes full responsibility for the content of the publication.

**Declaration on figure provenance.** All figures were generated as vector graphics directly from the analysed data using Matplotlib; no generative AI image models were used and no third-party images were reproduced.

**Declaration on the reporting of negative results.** The external validation reported in Section 3.7 failed to replicate the discovery finding. It is reported in full, with the same prominence as the positive results, and the conclusion has been rewritten accordingly. No analysis was added, removed or re-parameterised after the validation cohorts were examined; the thresholds (1-SE rule, π ≥ 0.75, *P* < 0.05) were fixed before either cohort was analysed, and the calibration, Brier and proportional-hazards analyses reported in Section 3.5 are diagnostics of the discovery fit rather than responses to the external result.

**Reporting guideline.** The study is reported in accordance with the TRIPOD and TRIPOD+AI statements [40,41]; a completed checklist is provided as Supplementary Item 1.

---

## Figure legends

**Figure 1. Discovery cohort: univariate screening and the full-panel Model A.** (**A**) Univariate Cox regression of the 91 evaluable mitoxyperilysis-related genes in TCGA-LIHC, restricted to the 23 genes with *P* < 0.05 and ordered by hazard ratio; **red points and bars denote Benjamini–Hochberg q < 0.05 (n = 5), grey q ≥ 0.05 (n = 18)** — the colour threshold is the corrected one, not raw *P*. (**B**) Model A risk score (line) with the median cut-point (dashed) and overall-survival time of each patient (points; red, death; grey, censored), patients ordered by risk score. (**C**) Expression heat map of the 23 Model A genes across the same patient order, values as per-gene *z*-scores in the TCGA-LIHC all-sample Z-score matrix. (**D**) Kaplan–Meier overall survival by risk group (median split, 180 per group); median overall survival 80.7 vs 35.8 months; log-rank *P* = 1.9×10⁻⁶; numbers at risk are shown below the axis, and the x-axis is truncated at 60 months so that it aligns with the at-risk table.

**Figure 2. Model A: discrimination, proliferation overlap and independence.** (**A**) Time-dependent AUC at 12–60 months for Model A and MRG-2. Time points beyond five years are not shown: median follow-up is 27.3 months and only 40 patients remained at risk at 60 months, too few for a stable estimate. (**B**) Model A risk score against the 20-gene proliferation score in TCGA-LIHC (Spearman ρ = 0.70). (**C**) Multivariable Cox model of the Model A score adjusted for age, sex, AJCC stage III–IV and grade G3–G4, complete-case analysis (n = 337); **red, confidence interval excludes 1; grey, it includes 1**.

**Figure 3. Derivation of the two-gene score, MRG-2.** (**A**) LASSO-Cox 10-fold cross-validation path; black, mean CV C-index; orange (right axis), number of non-zero genes. The curve peaks at 11 genes and declines monotonically as the penalty is relaxed, with a total range of 0.063 against a fold standard error of 0.006; the dashed red line marks λ_1SE (9 genes, 0.49 SE below the maximum) and the dotted blue line λ_min (11 genes). Model size is therefore determined only weakly by the penalty path alone. (**B**) Stability selection: per-gene selection frequency across 200 bootstrap resamples at λ_1SE. Red bars exceed the prespecified π = 0.75 threshold and define the two-gene set (KIF15 91.0%, MAFG 78.5%). (**C**) Kaplan–Meier overall survival by MRG-2 median split (180 per group); median overall survival 80.7 vs 33.0 months; log-rank *P* = 6.3×10⁻⁶; the x-axis is truncated at 60 months to align with the at-risk table.

**Figure 4. Molecular correlates of the MRG-2 risk groups.** (**A**) Principal component analysis of the k-means subtypes derived from the panel genes (k = 2; silhouette 0.111; 141 and 219 patients). The subtypes were not separated by survival (log-rank *P* = 0.171) and no clinical utility is claimed. (**B**) Immune feature scores (mean *z*-score, ssGSEA-lite) between the high- and low-risk groups of the MRG-2 median split; positive values indicate a higher score in the high-risk group. Only the NK-cell feature reaches *P* < 0.05 (and survives Benjamini–Hochberg correction across the eleven tests); the scores are marker means, are not deconvoluted and are not adjusted for tumour purity. (**C**) Somatic mutation frequencies of recurrent HCC genes by risk group (180 per group), Fisher exact test with Benjamini–Hochberg adjustment across the 16 genes.

**Figure 5. External validation and statistical robustness of MRG-2.** (**A**) Kaplan–Meier overall survival by MRG-2 median split in GSE14520 (242 tumours, 96 deaths, median follow-up 57.0 months); log-rank *P* = 0.085, C-index 0.551. The reference text gives the same-cohort performance of a 20-gene proliferation score (C-index 0.596, log-rank *P* = 7.2×10⁻⁴). The x-axis is truncated at 60 months to align with the at-risk table. (**B**) Harrell's C-index of the two MRG models and of the proliferation score in the discovery cohort (apparent, grey), under pooled out-of-fold cross-validation (blue; bars, the pooled C-index averaged over ten independent random splits; error bars, ± 1 SD across splits) and in the external cohort GSE14520 (red; proliferation score, orange); dashed line, chance. MRG-2 declines monotonically from 0.677 to 0.613 to 0.551, and the discovery ordering of MRG-2 above the proliferation score inverts externally. (**C**) Null distribution of the C-index of 3,000 random two-gene panels drawn from the same 91 genes, in the discovery cohort (blue) and in GSE14520 (red), with the observed MRG-2 value marked. In discovery MRG-2 exceeds 100% of random panels; in GSE14520 it sits at the 47th percentile. (**D**) Selection frequency π of KIF15 and MAFG under ten independent bootstrap seeds, with the prespecified π = 0.75 threshold. Circled points fall below the threshold, at which the two-gene set collapses to KIF15 alone.

**Figure 6. Panel genes in tumour versus reference normal liver.** Mean per-gene Z-score of the 91 evaluable panel genes relative to the cBioPortal reference-normal liver profile, split across two panels for legibility. (**A**) Genes with Z < 1; (**B**) genes with Z > 1. The two panels cover different ranges of Z and the x-axis scales differ accordingly. Red, over-expressed in tumour (Z > 1; n = 22); blue, under-expressed (Z < −1; n = 11); grey, |Z| ≤ 1. Dashed lines mark ±1.

**Figure S1. Calibration and Brier score of the two discovery models.** (**A**) Calibration plot: patients grouped into quintiles of predicted 3-year overall survival; *x*-axis, mean predicted; *y*-axis, Kaplan–Meier-observed. The dashed line is perfect calibration, and the legend gives the cross-validated calibration slope for each model (out-of-fold linear predictor, so the slope is not unity by construction). (**B**) Time-dependent Brier score with inverse-probability-of-censoring weights at 12–60 months; the legend gives the integrated Brier score.

---

## Tables

**Table 1.** Baseline characteristics of the discovery and validation cohorts.

| Characteristic | TCGA-LIHC (n = 360) | GSE14520 (n = 242) | GSE76427 (n = 115) |
|---|---|---|---|
| Age, median (range), years | 61 (16–90) | 51 (21–77) | 62 (26–86) |
| Male sex, n (%) | 242 (67.2) | 199 (82.2) | 94 (81.7) |
| AJCC / TNM stage I–II, n | 252 | 176 | 90 |
| AJCC / TNM stage III–IV, n | 87 | 56 | 25 |
| Stage unknown, n | 21 | 10 | 0 |
| Histological grade G1–G2 / G3–G4, n | 225 / 130 | — | — |
| Deaths, n (%) | 129 (35.8) | 96 (39.7) | 23 (20.0) |
| Median follow-up (reverse KM), months | 27.3 | 57.0 | 21.5 |
| Patients at risk at 60 months | 40 | — | — |
| Dominant aetiology | HCV / alcohol (Western) | HBV (Chinese) | HBV-associated |
| Panel genes available | 91 / 91 | 65 / 92 | 87 / 92 |
| MRG-2 genes available | 2 / 2 | 2 / 2 | 2 / 2 |

Patients are the unit of analysis; one primary tumour sample per patient. AJCC stage and grade were missing in TCGA-LIHC for 21 and 5 patients respectively and for 10 patients in GSE14520. The primary adjusted models are complete-case (n = 337 in TCGA-LIHC, i.e. 23 patients excluded for missing stage or grade); two missing-data sensitivities retaining all 360 patients are reported in Table 5. GSE14520 spans two array platforms (GPL571, n = 21 tumours; GPL3921, n = 221 tumours) and platform is included as a covariate in the adjusted model. BCLC stage, Child–Pugh class and ECOG performance status are not recorded in either cohort.

**Table 2.** Model A — the 23 full-panel genes: multivariable L2-penalised Cox coefficients (penalizer = 1.0), hazard ratios with 95% confidence intervals and *P* values (n = 360, 129 deaths). No coefficient reversed sign relative to its univariate estimate, and none was individually significant, which is the expected consequence of ridge shrinkage under the collinearity of this panel. Coefficients are deposited as Supplementary Table S4.

| Gene | Coefficient | HR | 95% CI | P |
|---|---|---|---|---|
| MAFG | 0.056 | 1.058 | 0.964–1.161 | 0.233 |
| KIF15 | 0.057 | 1.058 | 0.964–1.162 | 0.234 |
| TXNRD1 | 0.049 | 1.050 | 0.958–1.152 | 0.297 |
| MBOAT7 | 0.045 | 1.046 | 0.955–1.145 | 0.334 |
| WDR35 | 0.040 | 1.041 | 0.950–1.139 | 0.389 |
| DAB2 | 0.040 | 1.040 | 0.949–1.141 | 0.400 |
| CEP19 | 0.038 | 1.039 | 0.949–1.138 | 0.409 |
| LRRC58 | 0.037 | 1.038 | 0.949–1.136 | 0.414 |
| FERMT2 | −0.038 | 0.963 | 0.882–1.052 | 0.406 |
| TIAM1 | −0.037 | 0.963 | 0.880–1.054 | 0.418 |
| OSGIN2 | 0.035 | 1.035 | 0.945–1.134 | 0.457 |
| OPTN | 0.031 | 1.031 | 0.942–1.129 | 0.503 |
| SLC7A1 | 0.030 | 1.030 | 0.940–1.129 | 0.520 |
| MCM5 | 0.028 | 1.029 | 0.937–1.129 | 0.551 |
| KLHL18 | 0.025 | 1.025 | 0.936–1.122 | 0.591 |
| TRAF3 | 0.025 | 1.025 | 0.936–1.123 | 0.596 |
| SLC1A4 | 0.024 | 1.025 | 0.936–1.122 | 0.599 |
| TAF12 | 0.050 | 1.052 | 0.962–1.150 | 0.269 |
| ASF1B | 0.019 | 1.019 | 0.927–1.120 | 0.697 |
| CHD4 | 0.017 | 1.017 | 0.928–1.114 | 0.723 |
| CHAF1A | 0.016 | 1.017 | 0.926–1.115 | 0.729 |
| PTPN23 | 0.010 | 1.011 | 0.922–1.108 | 0.823 |
| PPP1R10 | −0.057 | 0.944 | 0.863–1.033 | 0.210 |

**Table 3.** Univariate Cox regression for overall survival, top 15 genes by raw *P* value, with Benjamini–Hochberg q values across all 91 tests (n = 360, 129 deaths; full list in Supplementary Tables S1 and S2). Five genes reach BH q < 0.05; MBOAT7 is on the boundary; no gene survives the dependency-robust Benjamini–Yekutieli correction. All *P* values quoted in the text are uncorrected.

| Gene | HR | 95% CI | P | BH q |
|---|---|---|---|---|
| MAFG | 1.489 | 1.231–1.802 | 4.2×10⁻⁵ | 0.002 |
| KIF15 | 1.446 | 1.210–1.728 | 4.9×10⁻⁵ | 0.002 |
| TXNRD1 | 1.399 | 1.161–1.686 | 4.1×10⁻⁴ | 0.013 |
| DAB2 | 1.364 | 1.132–1.644 | 1.1×10⁻³ | 0.025 |
| CEP19 | 1.333 | 1.116–1.593 | 1.6×10⁻³ | 0.028 |
| MBOAT7 | 1.285 | 1.087–1.520 | 3.3×10⁻³ | 0.051 |
| ASF1B | 1.293 | 1.081–1.545 | 4.8×10⁻³ | 0.057 |
| PPP1R10 | 0.794 | 0.676–0.933 | 5.0×10⁻³ | 0.057 |
| OSGIN2 | 1.287 | 1.070–1.548 | 7.4×10⁻³ | 0.074 |
| MCM5 | 1.269 | 1.063–1.515 | 8.3×10⁻³ | 0.076 |
| SLC7A1 | 1.279 | 1.059–1.544 | 1.1×10⁻² | 0.083 |
| KLHL18 | 1.245 | 1.051–1.475 | 1.1×10⁻² | 0.083 |
| WDR35 | 1.263 | 1.053–1.514 | 1.2×10⁻² | 0.083 |
| SLC1A4 | 1.242 | 1.045–1.476 | 1.4×10⁻² | 0.091 |
| TAF12 | 1.247 | 1.042–1.492 | 1.6×10⁻² | 0.095 |

**Table 4.** Model B — MRG-2: stability selection and final coefficients (n = 360, 129 deaths). Stability frequency is the proportion of 200 bootstrap LASSO fits at the 1-SE α (0.0631) that selected the gene; coefficients are from the multivariable Cox model on the two retained genes, expressed per SD of discovery-cohort-standardised expression. The univariate hazard ratios are those of Table 3. The rightmost column gives the range of π across ten independent bootstrap seeds (Supplementary Table S11).

| Gene | Stability π (seed 2026) | π range, 10 seeds | Included (π ≥ 0.75) | Coefficient | HR (per SD) | 95% CI | *P* | Univariate HR |
|---|---|---|---|---|---|---|---|---|
| KIF15 | 0.910 | 0.875–0.920 | yes | +0.3096 | 1.363 | 1.137–1.633 | 8.1×10⁻⁴ | 1.446 |
| MAFG | 0.785 | 0.690–0.805 | threshold-marginal | +0.3336 | 1.396 | 1.150–1.694 | 7.4×10⁻⁴ | 1.489 |
| AKNA | 0.625 | — | no | — | — | — | — | 0.851 |
| PPP1R10 | 0.570 | — | no | — | — | — | — | 0.794 |
| MBOAT7 | 0.510 | — | no | — | — | — | — | 1.285 |

**Table 5.** Cox regression for overall survival, both models, in the discovery cohort. Model A and MRG-2 are each adjusted for age, sex, AJCC stage III–IV and grade G3–G4; the adjusted models use the complete-case primary analysis (n = 337, 115 deaths), and the two missing-data sensitivities are given in the lower block. Hazard ratios are per 1 SD of the score, with 95% confidence intervals. The final rows give the paired-bootstrap comparison of discrimination against the 20-gene proliferation score. This table and Supplementary Table S8 are generated from the same code path and are identical cell by cell.

| Model | Variable | HR | 95% CI | P |
|---|---|---|---|---|
| MRG-2 | Score (per SD) | 1.650 | 1.338–2.035 | 2.8×10⁻⁶ |
| MRG-2 | Stage III–IV | 2.191 | 1.500–3.201 | 4.9×10⁻⁵ |
| MRG-2 | Age (per SD) | 1.221 | 0.992–1.502 | 0.059 |
| MRG-2 | Male sex | 0.818 | 0.555–1.207 | 0.313 |
| MRG-2 | Grade G3–G4 | 0.933 | 0.629–1.384 | 0.730 |
| Model A | Score (per SD) | 1.880 | 1.521–2.325 | 5.6×10⁻⁹ |
| Model A | Stage III–IV | 1.971 | 1.346–2.886 | 4.9×10⁻⁴ |
| Model A | Age (per SD) | 1.202 | 0.985–1.468 | 0.071 |
| Model A | Male sex | 0.755 | 0.511–1.114 | 0.156 |
| Model A | Grade G3–G4 | 0.845 | 0.564–1.266 | 0.414 |
| — | *Missing-data sensitivity: missing stage/grade coded 0 (n = 360)* | | | |
| MRG-2 | Score (per SD) | 1.658 | 1.359–2.024 | 6.6×10⁻⁷ |
| MRG-2 | Stage III–IV | 2.019 | 1.401–2.910 | 1.6×10⁻⁴ |
| Model A | Score (per SD) | 1.934 | 1.580–2.368 | 1.7×10⁻¹⁰ |
| Model A | Stage III–IV | 1.805 | 1.250–2.605 | 1.6×10⁻³ |
| — | *Missing-data sensitivity: missing coded 0 plus missingness indicator (n = 360)* | | | |
| MRG-2 | Score (per SD) | 1.683 | 1.377–2.058 | 3.8×10⁻⁷ |
| MRG-2 | Stage III–IV | 2.196 | 1.507–3.201 | 4.2×10⁻⁵ |
| Model A | Score (per SD) | 1.935 | 1.580–2.371 | 1.8×10⁻¹⁰ |
| Model A | Stage III–IV | 1.966 | 1.346–2.871 | 4.7×10⁻⁴ |
| — | *Unadjusted single covariates (n = 360)* | | | |
| — | Stage III–IV alone | 2.205 | 1.541–3.156 | 1.5×10⁻⁵ |
| — | Grade G3–G4 alone | 1.090 | 0.762–1.560 | 0.636 |
| — | Age alone (per SD) | 1.206 | 1.004–1.448 | 0.045 |
| — | Male sex alone | 0.805 | 0.565–1.149 | 0.232 |
| — | Proliferation score alone | 1.446 | 1.206–1.735 | 7.1×10⁻⁵ |
| — | *Paired-bootstrap ΔC-index, 2,000 resamples (discrimination)* | | | |
| — | MRG-2 − proliferation | +0.034 | −0.012 to +0.076 | 0.147 |
| — | MRG-2 − Model A | −0.007 | −0.042 to +0.028 | 0.678 |
| — | Model A − proliferation | +0.041 | +0.002 to +0.080 | 0.038 |

**Table 6.** Immune feature scores (mean Z-score of marker genes) by MRG-2 risk group in the discovery cohort (180 patients per group, 129 deaths overall), compared by Mann–Whitney U test with Benjamini–Hochberg adjustment across the eleven tests. Scores are marker means, not deconvoluted, and are not adjusted for tumour purity; the marker genes comprising each feature are listed in Supplementary Table S7.

| Immune feature | Marker genes (n) | Low-risk (mean Z) | High-risk (mean Z) | Difference (high − low) | P | BH q |
|---|---|---|---|---|---|---|
| CD8⁺ T cells | 6 | −0.037 | −0.089 | −0.052 | 0.105 | 0.29 |
| CD4⁺ T cells | 6 | 0.003 | −0.069 | −0.072 | 0.511 | 0.63 |
| Regulatory T cells | 5 | −0.115 | 0.016 | +0.131 | 0.127 | 0.29 |
| **NK cells** | 4 | 0.136 | −0.159 | **−0.295** | **1.5×10⁻⁴** | **0.0017** |
| B cells | 4 | −0.110 | −0.160 | −0.050 | 0.391 | 0.54 |
| M1 macrophages | 5 | −0.061 | −0.033 | +0.029 | 0.664 | 0.73 |
| M2 macrophages | 5 | 0.069 | −0.077 | −0.146 | 0.072 | 0.26 |
| Dendritic cells | 5 | 0.054 | −0.083 | −0.137 | 0.203 | 0.37 |
| Neutrophils | 4 | −0.104 | 0.078 | +0.182 | 0.086 | 0.26 |
| Immune checkpoints | 6 | −0.140 | 0.050 | +0.190 | 0.052 | 0.26 |
| Interferon signature | 5 | −0.128 | −0.013 | +0.115 | 0.227 | 0.37 |

**Table 7.** Somatic mutation frequencies by MRG-2 risk group (n = 360, 129 deaths; 180 patients per group), Fisher's exact test with Benjamini–Hochberg adjustment across the 16 genes.

| Gene | High-risk, n (%) | Low-risk, n (%) | P | BH q |
|---|---|---|---|---|
| TP53 | 77 (42.8) | 30 (16.7) | 7.9×10⁻⁸ | 1.3×10⁻⁶ |
| CTNNB1 | 58 (32.2) | 35 (19.4) | 0.0079 | 0.063 |
| RB1 | 15 (8.3) | 4 (2.2) | 0.016 | 0.087 |
| BAP1 | 6 (3.3) | 14 (7.8) | 0.105 | 0.371 |
| AXIN1 | 8 (4.4) | 16 (8.9) | 0.138 | 0.371 |
| TSC2 | 9 (5.0) | 3 (1.7) | 0.139 | 0.371 |
| KEAP1 | 12 (6.7) | 6 (3.3) | 0.226 | 0.516 |
| PIK3CA | 4 (2.2) | 8 (4.4) | 0.379 | 0.759 |
| TSC1 | 5 (2.8) | 2 (1.1) | 0.449 | 0.797 |
| ALB | 20 (11.1) | 24 (13.3) | 0.630 | 1.000 |
| ARID1A | 15 (8.3) | 12 (6.7) | 0.690 | 1.000 |
| APOB | 18 (10.0) | 16 (8.9) | 0.857 | 1.000 |
| TTN | 46 (25.6) | 48 (26.7) | 0.905 | 1.000 |
| ARID2 | 10 (5.6) | 9 (5.0) | 1.000 | 1.000 |
| NFE2L2 | 6 (3.3) | 5 (2.8) | 1.000 | 1.000 |
| PTEN | 4 (2.2) | 3 (1.7) | 1.000 | 1.000 |

**Table 8.** External validation of the two frozen scores in GSE14520 (n = 242 tumours, 96 deaths; complete-case adjusted model n = 242 with TNM stage missing for 10 patients). Coefficients were fixed on TCGA-LIHC; expression was standardised within the cohort and within each platform; the adjusted model includes age, sex, TNM stage III–IV and array platform. ΔC-index values are paired bootstraps (2,000 resamples, seed 7) against the 20-gene proliferation score. GSE76427 is reported in Supplementary Table S14 and is not used to support or refute either score.

| Cohort | Score | Genes applied | C-index | 95% CI | HR per SD | P (score) | Adjusted HR | log-rank P |
|---|---|---|---|---|---|---|---|---|
| GSE14520 | MRG-2 | 2 / 2 | 0.551 | 0.490–0.611 | 1.14 | 0.184 | 1.05 (*P* = 0.63) | 0.085 |
| GSE14520 | Model A | 19 / 23 | 0.577 | 0.519–0.633 | 1.27 | 0.019 | — | 0.022 |
| GSE14520 | Proliferation | 20 / 20 | 0.596 | — | 1.41 | — | — | 7.2×10⁻⁴ |
| GSE14520 | ΔC: MRG-2 − proliferation | — | −0.045 | −0.096 to +0.001 | — | 0.058 | — | — |

**Supplementary Table S1.** The 92-gene human MRG panel and the 91-gene TCGA-LIHC univariate screen with hazard ratios, confidence intervals and *P* values.
**Supplementary Table S2.** Univariate Cox regression for all 91 genes with Benjamini–Hochberg and Benjamini–Yekutieli q values.
**Supplementary Table S3.** Per-patient TCGA-LIHC dataset: risk scores for both models, risk group, survival time and status, age, sex, AJCC stage, grade and TMB (n = 360).
**Supplementary Table S4.** Model A: the 23 ridge coefficients, hazard ratios, confidence intervals and *P* values.
**Supplementary Table S4b.** Model A refitted without penalty: unpenalised versus ridge coefficients, hazard ratios and *P* values for the same 23 genes, with the design-matrix condition number.
**Supplementary Table S5.** Stability-selection frequencies at α = 0.0631 for all 91 evaluable genes.
**Supplementary Table S6.** Risk-group mutation summary with raw and Benjamini–Hochberg-adjusted Fisher exact *P* values.
**Supplementary Table S7.** Immune feature scores by risk group, with the marker genes composing each feature.
**Supplementary Table S8.** Multivariable Cox models for both scores — identical, cell by cell, to Table 5.
**Supplementary Table S9.** Per-patient external-validation data for GSE76427.
**Supplementary Table S10.** Fully nested 10-fold cross-validation of the Model B procedure: retained genes and held-out C-index per fold, and the corresponding per-fold results for the Model A pipeline.

**Supplementary Table S10b.** Pooled out-of-fold C-index of both models under the prespecified partition and under ten independent random splits, with the mean, standard deviation and range across splits, and the optimism of each model as a paired bootstrap difference with its 95% confidence interval.
**Supplementary Table S11.** Bootstrap seed replication: selection frequency π for the leading genes under ten independent seeds, with the resulting π ≥ 0.75 set and the binomial standard error of each π.
**Supplementary Table S12.** Random-panel benchmark: observed MRG-2 C-index against 3,000 random two-gene panels in the discovery cohort and in GSE14520.
**Supplementary Table S13.** Per-patient external-validation data for GSE14520.
**Supplementary Table S14.** GSE76427 external validation (n = 115, 23 deaths): both scores, the nominal log-rank result for Model A (*P* = 0.041, protective direction) and the proliferation-marker control analysis.
**Supplementary Table S15.** Calibration, time-dependent Brier scores and proportional-hazards tests for both models.
**Supplementary Table S16.** The 20 marker genes composing the proliferation score, with per-patient values as used in the external cohorts.

**Supplementary Item 1.** Completed TRIPOD and TRIPOD+AI checklist, with items not satisfiable by a secondary analysis of public data marked.

---

## References

1. Bray F, Laversanne M, Sung H, Ferlay J, Siegel RL, Soerjomataram I, et al. Global cancer statistics 2022: GLOBOCAN estimates of incidence and mortality worldwide for 36 cancers in 185 countries. CA Cancer J Clin 2024;74(3):229-263. PMID: 38572751. doi:10.3322/caac.21834.
2. Vogel A, Chan SL, Dawson LA, Kelley RK, Llovet JM, Meyer T, et al. Hepatocellular carcinoma: ESMO Clinical Practice Guideline for diagnosis, treatment and follow-up. Ann Oncol 2025;36(5):491-506. PMID: 39986353. doi:10.1016/j.annonc.2025.02.006.
3. Cancer Genome Atlas Research Network. Comprehensive and Integrative Genomic Characterization of Hepatocellular Carcinoma. Cell 2017;169(7):1327-1341.e23. PMID: 28622513. doi:10.1016/j.cell.2017.05.046.
4. Llovet JM, Ricci S, Mazzaferro V, Hilgard P, Gane E, Blanc JF, et al. Sorafenib in advanced hepatocellular carcinoma. N Engl J Med 2008;359(4):378-390. PMID: 18650514. doi:10.1056/NEJMoa0708857.
5. Kudo M, Finn RS, Qin S, Han KH, Ikeda K, Piscaglia F, et al. Lenvatinib versus sorafenib in first-line treatment of patients with unresectable hepatocellular carcinoma: a randomised phase 3 non-inferiority trial. Lancet 2018;391(10126):1163-1173. PMID: 29433850. doi:10.1016/S0140-6736(18)30207-1.
6. Finn RS, Qin S, Ikeda M, Galle PR, Ducreux M, Kim TY, et al. Atezolizumab plus Bevacizumab in Unresectable Hepatocellular Carcinoma. N Engl J Med 2020;382(20):1894-1905. PMID: 32402160. doi:10.1056/NEJMoa1915745.
7. Schulze K, Imbeaud S, Letouzé E, Alexandrov LB, Calderaro J, Rebouissou S, et al. Exome sequencing of hepatocellular carcinomas identifies new mutational signatures and potential therapeutic targets. Nat Genet 2015;47(5):505-511. PMID: 25822088. doi:10.1038/ng.3252.
8. Sia D, Jiao Y, Martinez-Quetglas I, Kuchuk O, Villacorta-Martin C, Castro de Moura M, et al. Identification of an Immune-specific Class of Hepatocellular Carcinoma, Based on Molecular Features. Gastroenterology 2017;153(3):812-826. PMID: 28624577. doi:10.1053/j.gastro.2017.06.007.
9. Sauzay C, Louandre C, Bodeau S, Anglade F, Godin C, Saidak Z, et al. Protein biosynthesis, a target of sorafenib, interferes with the unfolded protein response (UPR) and ferroptosis in hepatocellular carcinoma cells. Oncotarget 2018;9(9):8400-8414. PMID: 29492203. doi:10.18632/oncotarget.23843.
10. Houessinon A, François C, Sauzay C, Louandre C, Mongelard G, Godin C, et al. Metallothionein-1 as a biomarker of altered redox metabolism in hepatocellular carcinoma cells exposed to sorafenib. Mol Cancer 2016;15(1):38. PMID: 27184800. doi:10.1186/s12943-016-0526-2.
11. Wang Y, Lu J, Carisey AF, Chadchan SB, Lee HW, Malireddi RKS, et al. Innate immune and metabolic signals induce mitochondria-dependent membrane lysis via mitoxyperiosis. Cell 2025;188(25):7155-7174.e25. PMID: 41317732. doi:10.1016/j.cell.2025.11.002.
12. Ke FS, Holloway S, Uren RT, Wong AW, Little MH, Kluck RM, et al. The BCL-2 family member BID plays a role during embryonic development in addition to its BH3-only protein function by acting in parallel to BAX, BAK and BOK. EMBO J 2022;41(15):e110300. PMID: 35758142. doi:10.15252/embj.2021110300.
13. Cosentino K, Hertlein V, Jenner A, Dellmann T, Gojkovic M, Peña-Blanco A, et al. The interplay between BAX and BAK tunes apoptotic pore growth to control mitochondrial-DNA-mediated inflammation. Mol Cell 2022;82(5):933-949.e9. PMID: 35120587. doi:10.1016/j.molcel.2022.01.008.
14. Ramos S, Hartenian E, Broz P. Programmed cell death: NINJ1 and mechanisms of plasma membrane rupture. Trends Biochem Sci 2024;49(8):717-728. PMID: 38906725. doi:10.1016/j.tibs.2024.05.007.
15. Chen Z, Xu D. Mitochondria at the membrane provide a route to inflammatory cell death. Cell Metab 2026;38(2):260-262. PMID: 41638191. doi:10.1016/j.cmet.2025.12.019.
16. Martinez-Lopez N, Mattar P, Toledo M, Bains H, Kalyani M, Aoun ML, et al. mTORC2-NDRG1-CDC42 axis couples fasting to mitochondrial fission. Nat Cell Biol 2023;25(7):989-1003. PMID: 37386153. doi:10.1038/s41556-023-01163-3.
17. Iskandar K, Foo J, Liew AQX, Zhu H, Raman D, Hirpara JL, et al. A novel MTORC2-AKT-ROS axis triggers mitofission and mitophagy-associated execution of colorectal cancer cells upon drug-induced activation of mutant KRAS. Autophagy 2024;20(6):1418-1441. PMID: 38261660. doi:10.1080/15548627.2024.2307224.
18. Wang Y, Tian Q, Hao Y, Yao W, Lu J, Chen C, et al. The kinase complex mTORC2 promotes the longevity of virus-specific memory CD4⁺ T cells by preventing ferroptosis. Nat Immunol 2022;23(2):303-317. PMID: 34949833. doi:10.1038/s41590-021-01090-1.
19. Wu MY, Tsai AP, Yong SB, Li CJ. Spatially gated oxidative killing: mitoxyperilysis redefines how ROS cause lytic cell death. Apoptosis 2026;31(3). PMID: 41721119. doi:10.1007/s10495-026-02300-7.
20. Al-Zidan R, Gautam M, Man SM. Mitoxyperilysis: fasting-induced cell death in immunometabolism and disease. Trends Biochem Sci 2026;51(4):313-315. PMID: 41856854. doi:10.1016/j.tibs.2026.01.005.
21. Zhang Y, Sun B, Lin J, Ding C, Zhou X, Xu X, et al. A mitoxyperilysis-related signature stratifies prognosis and identifies an aggressive colorectal cancer ecosystem with immune remodeling. Front Cell Dev Biol 2026;14:1851988. PMID: 42491158. doi:10.3389/fcell.2026.1851988. (Primary source for the priority claim in Section 1; references 19 and 20 are commentary on the cell-death modality and are not cited as evidence of a tumour signature.)
22. Glover HL, Schreiner A, Dewson G, Tait SWG. Mitochondria and cell death. Nat Cell Biol 2024;26(9):1434-1446. PMID: 38902422. doi:10.1038/s41556-024-01429-4.
23. Tang D, Kroemer G, Kang R. Ferroptosis in immunostimulation and immunosuppression. Immunol Rev 2024;321(1):199-210. PMID: 37424139. doi:10.1111/imr.13235.
24. Cerami E, Gao J, Dogrusoz U, Gross BE, Sumer SO, Aksoy BA, et al. The cBio cancer genomics portal: an open platform for exploring multidimensional cancer genomics data. Cancer Discov 2012;2(5):401-404. PMID: 22588877. doi:10.1158/2159-8290.CD-12-0095.
25. Gao J, Aksoy BA, Dogrusoz U, Dresdner G, Gross B, Sumer SO, et al. Integrative analysis of complex cancer genomics and clinical profiles using the cBioPortal. Sci Signal 2013;6(269):pl1. PMID: 23550210. doi:10.1126/scisignal.2004088.
26. Roessler S, Jia HL, Budhu A, Forgues M, Ye QH, Lee JS, et al. A unique metastasis gene signature enables prediction of tumor relapse in early-stage hepatocellular carcinoma patients. Cancer Res 2010;70(24):10202-10212. PMID: 21159642. doi:10.1158/0008-5472.CAN-10-2607. (GSE14520 source cohort.)
27. Grinchuk OV, Yenamandra SP, Iyer R, Singh M, Lee HK, Lim KH, et al. Tumor-adjacent tissue co-expression profile analysis reveals pro-oncogenic ribosomal gene signature for prognosis of resectable hepatocellular carcinoma. Mol Oncol 2018;12(1):89-113. PMID: 29117471. doi:10.1002/1878-0261.12153. (GSE76427 source cohort.)
28. Harrell FE Jr, Lee KL, Mark DB. Multivariable prognostic models: issues in developing models, evaluating assumptions and adequacy, and measuring and reducing errors. Stat Med 1996;15(4):361-387. PMID: 8668867. doi:10.1002/(sici)1097-0258(19960229)15:4<361::aid-sim168>3.0.co;2-4.
29. Vittinghoff E, McCulloch CE. Relaxing the rule of ten events per variable in logistic and Cox regression. Am J Epidemiol 2007;165(6):710-718. PMID: 17182981. doi:10.1093/aje/kwk052.
30. Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR. A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol 1996;49(12):1373-1379. PMID: 8970487. doi:10.1016/s0895-4356(96)00236-3.
31. Meinshausen N, Bühlmann P. Stability selection. J R Stat Soc Series B Stat Methodol 2010;72(4):417-473. doi:10.1111/j.1467-9868.2010.00740.x. (Not indexed in PubMed; verified against Crossref.)
32. Barbie DA, Tamayo P, Boehm JS, Kim SY, Moody SE, Dunn IF, et al. Systematic RNA interference reveals that oncogenic KRAS-driven cancers require TBK1. Nature 2009;462(7269):108-112. PMID: 19847166. doi:10.1038/nature08460.
33. Jaiswal AK. Nrf2 signaling in coordinated activation of antioxidant gene expression. Free Radic Biol Med 2004;36(10):1199-1207. PMID: 15110384. doi:10.1016/j.freeradbiomed.2004.02.074.
34. Hirotsu Y, Katsuoka F, Funayama R, Nagashima T, Nishida Y, Nakayama K, et al. Nrf2-MafG heterodimers contribute globally to antioxidant and metabolic networks. Nucleic Acids Res 2012;40(20):10228-10239. PMID: 22965115. doi:10.1093/nar/gks827.
35. Zhang H, Li C, Liao S, Tu Y, Sun S, Yao F, et al. PSMD12 promotes the activation of the MEK-ERK pathway by upregulating KIF15 to promote the malignant progression of liver cancer. Cancer Biol Ther 2022;23(1):1-11. PMID: 36137220. doi:10.1080/15384047.2022.2125260.
36. Ruiz de Galarreta M, Bresnahan E, Molina-Sánchez P, Lindblad KE, Maier B, Sia D, et al. β-Catenin Activation Promotes Immune Escape and Resistance to Anti-PD-1 Therapy in Hepatocellular Carcinoma. Cancer Discov 2019;9(8):1124-1141. PMID: 31186238. doi:10.1158/2159-8290.CD-19-0074.
37. Tibshirani R. The lasso method for variable selection in the Cox model. Stat Med 1997;16(4):385-395. PMID: 9044528. doi:10.1002/(sici)1097-0258(19970228)16:4<385::aid-sim380>3.0.co;2-3.
38. Graf E, Schmoor C, Sauerbrei W, Schumacher M. Assessment and comparison of prognostic classification schemes for survival data. Stat Med 1999;18(17-18):2529-2545. PMID: 10474158. doi:10.1002/(sici)1097-0258(19990915/30)18:17/18<2529::aid-sim274>3.0.co;2-5.
39. Benjamini Y, Yekutieli D. The control of the false discovery rate in multiple testing under dependency. Ann Stat 2001;29(4):1165-1188. doi:10.1214/aos/1013699998. (Not indexed in PubMed; verified against Crossref.)
40. Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD): the TRIPOD statement. Ann Intern Med 2015;162(1):55-63. PMID: 25560714. doi:10.7326/M14-0697.
41. Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ 2024;385:e078378. PMID: 38626948. doi:10.1136/bmj-2023-078378.

---

## Supplementary Methods

> For submission this section is provided as a separate *Supplementary Methods* file; it is retained here so that every value reported in the main text remains traceable within a single document.

**MRG panel derivation criteria.** A gene was retained only if both criteria held. *Synergy:* |log₂FC(LPS+CS vs media)| ≥ 1.0 while |log₂FC(LPS vs media)| < 0.5 and |log₂FC(CS vs media)| < 0.5. *Sensitivity to mTOR inhibition:* log₂FC(LPS+CS+Torin vs LPS+CS) ≤ −0.5 for up-regulated genes or ≥ +0.5 for down-regulated genes.

**Meinshausen–Bühlmann bound.** The dependency-robust form of the stability-selection guarantee is the bound on the expected number of falsely selected variables. At q = 16 candidates and p = 91 it is E[V] ≤ 5.63 at π = 0.75, 7.03 at π = 0.70 and 4.69 at π = 0.80, and 2.67 at the median model size q = 11 — all larger than the two-gene model they are supposed to protect, so the bound is uninformative for this panel and is not used as evidence of false-discovery control.

**Fully nested cross-validation and pooled out-of-fold estimation.** Inside each training fold of the 10-fold split the *entire* Model B procedure was repeated — LASSO path, 1-SE rule, bootstrap stability selection at π ≥ 0.75, and the multivariable fit — and the resulting coefficients were applied to the held-out fold; the inner selection used 100 bootstrap resamples per fold rather than the 200 used for the primary fit. Model A was run the same way. For each model the ten held-out linear predictors were then **concatenated into a single vector and scored once over all 360 patients**, giving the pooled out-of-fold C-index; averaging the ten fold-wise C-indices instead is biased because the folds differ in event rate, and the standard error of that mean is not defined by SD/√10 since the folds share training data and are neither independent nor equally sized. Because a single partition cannot separate the estimate from the partition, the whole nested procedure was repeated under **ten independent random splits** (outer seeds 42–51, all other settings unchanged: 10 folds, 100 inner bootstrap resamples, inner cross-validation seed 42). The prespecified seed 42 partition is reported separately; its fold-wise mean (0.576 for MRG-2) reproduces the value in the earlier analysis and is retained only as a consistency check. Optimism is the difference between the apparent C-index and the pooled out-of-fold C-index, with a paired bootstrap confidence interval (2,000 resamples, seed 7).

**Calibration and proportional hazards: definitions.** The **cross-validated calibration slope** is the coefficient obtained by regressing the linear predictor on survival in a Cox model in which each patient's linear predictor comes from a model fitted on the other nine folds, so that the slope is not forced to unity by construction. The **calibration plot** groups patients by quintile of predicted 3-year survival. **Time-dependent Brier scores** were computed with inverse-probability-of-censoring weights at 12, 24, 36, 48 and 60 months, with the integrated Brier score, following Graf et al. [38]. Proportional hazards was tested by Schoenfeld residuals under four time transforms (rank, Kaplan–Meier, identity and log) [28].

**Multiplicity families.** Multiplicity was addressed within each analysis family rather than globally. The 91-gene univariate screen is one family, corrected by Benjamini–Hochberg; because panel genes are correlated, that procedure's independence conditions are not guaranteed, and the dependency-robust Benjamini–Yekutieli procedure was therefore reported alongside it. The 11 immune features, the 16 mutation genes and the three paired ΔC-index comparisons form further families, the last reported unadjusted and interpreted descriptively.

---

## Supplementary Results

> For submission this section is provided as a separate *Supplementary Results* file; it is retained here so that every value reported in the main text remains traceable within a single document.

**Median-split medians rest on a thin tail.** The median OS of the low-risk group (80.7 months) is estimable — the Kaplan–Meier curve falls to 0.469 at that event time — but it lies well beyond the median follow-up of 27.3 months, and only 29 of the 180 low-risk patients remained at risk at 60 months. The high-risk median was 35.8 months. Both low-risk curves (Model A and MRG-2) cross 0.5 at the same observed event time (80.744 months) even though the underlying patient sets differ, because that time is simply the first death time after which neither curve recovers. For the same reason the 60-month restricted mean survival time, which uses the whole curve, is the more defensible summary: 47.5 vs 34.2 months for Model A and 47.4 vs 34.0 months for MRG-2.

**GSE76427 — full result.** In this 115-tumour, 23-death cohort both scores gave point estimates below 0.5 (MRG-2 C-index 0.402, 95% CI 0.255–0.548; Model A 0.426, 95% CI 0.290–0.555) with confidence intervals spanning 0.5, and neither hazard ratio approached significance (*P* = 0.16 and 0.11). Model A's log-rank test gives *P* = 0.041 with HR 0.69, a protective direction, which is not treated as evidence for the score: with 23 deaths the log-rank test and the hazard ratio weight the follow-up differently, and a protective-direction log-rank on a score derived to be harmful is a power and direction artefact rather than a hypothesis. The direction problem is not specific to this panel — in the same 115 tumours canonical proliferation markers were themselves non-prognostic or apparently protective (MKI67 HR 0.72, 95% CI 0.41–1.28; TOP2A HR 0.86, 95% CI 0.50–1.47; CCNB1 HR 1.10, 95% CI 0.68–1.79). GSE76427 is retained in the main text only as a power-negative control; the main table reports GSE14520.
