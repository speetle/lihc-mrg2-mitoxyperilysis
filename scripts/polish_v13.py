#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
polish_v13.py —— SCI-writing-VIP §8 复用模式：句级润色（v1.2 -> v1.3）

机检依据（style_compare.py / count_connectors.py / anti_ai_check.py）：
  1. 平均句长 28.8 vs 真人 22.6（+6.2）；≥35 词长句占 32.4% vs 真人 10.3%
  2. 连接词种类 17 vs 真人 40（过渡手段单一）
  3. `because` 11/205 句 = 5.37/百句（真人最高词项 2.88/百句，D-36 上限 3.0）
  4. `but` 13 次（含句首 3 次），`however` 0 次 —— 真人语料 however 是第 2 高频连接词（2.49/百句）
  5. 句首 `And` 5 次 / `But` 3 次（D-36 框架层 ② 变更记录腔）
  6. D-19：让步连接词被通用转折词静默替代（although 仅 1 次、despite 0 次）
  7. anti_ai_check R5：`robust` 3 处语义未落地

规则：**一个数字都不许动**（数值/P 值/CI/文献编号/基因名/探针号）。
      每处替换必须唯一命中，否则整体失败退出（避免静默漏改）。
"""
import sys, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.2.md")
DST = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.3.md")

# (编号, 类别, old, new)
R = [

# ── A. 句首 And / But（D-36 框架层 ② 变更记录腔）────────────────────
("A1", "句首And", "And the panel was derived for a glioma analysis of the same concept and is applied here unchanged.",
 "The panel was derived for a glioma analysis of the same concept and is applied here unchanged."),

("A2", "句首And", "And three of the five corrected hits are redox rather than cell-cycle genes:",
 "Three of the five corrected hits are redox rather than cell-cycle genes:"),

("A3", "句首And", "And although no coefficient reversed direction relative to its univariate estimate, the ridge penalty shrank every one to the point that none was individually significant (all *P* > 0.21; Table 2), so the coefficients cannot be read as biological effect sizes.",
 "Although no coefficient reversed direction relative to its univariate estimate, the ridge penalty shrank every one to the point that none was individually significant (all *P* > 0.21; Table 2). The coefficients cannot be read as biological effect sizes."),

("A4", "句首And", "And **the two models remain indistinguishable even under the honest estimate**:",
 "**The two models remain indistinguishable even under the honest estimate**:"),

("A5", "句首And", "And the random-panel benchmark inverted. In GSE14520,",
 "The random-panel benchmark inverted too. In GSE14520,"),

("A6", "句首But", "But coherence is not transport, and the redox reading rests on a gene whose own selection stability is threshold-dependent.",
 "Coherence is not transport, however, and the redox reading rests on a gene whose own selection stability is threshold-dependent."),

("A7", "句首But", "But the same high-risk group is also enriched for CTNNB1 mutation, and CTNNB1-mutant HCC is conventionally the better-prognosis, immune-excluded subclass [8,36].",
 "The same high-risk group is also enriched for CTNNB1 mutation, however, and CTNNB1-mutant HCC is conventionally the better-prognosis, immune-excluded subclass [8,36]."),

("A8", "句首But", "But one of those two genes sits on the selection threshold and disappears under two of ten bootstrap seeds; the apparent discrimination carries about 0.10 C-index units of optimism; and in an independent cohort of 242 tumours",
 "One of those two genes sits on the selection threshold and disappears under two of ten bootstrap seeds. The apparent discrimination carries about 0.10 C-index units of optimism. And in an independent cohort of 242 tumours"),

# ── B. because 11 -> 4（保留语义必需处）────────────────────────────
("B1", "because", "Sorafenib [4], lenvatinib [5] and the atezolizumab–bevacizumab combination [6] have each extended survival in advanced disease, but the gain is measured in months and no molecular biomarker is used in routine practice to select between them.",
 "Sorafenib [4], lenvatinib [5] and the atezolizumab–bevacizumab combination [6] have each extended survival in advanced disease, by months rather than years. No molecular biomarker is used in routine practice to select between them."),

("B2", "because", "The therapeutic backbone is itself redox-active: sorafenib kills HCC cells in part by generating mitochondrial reactive oxygen species and by interfering with the unfolded-protein response, and resistance to it is accompanied by a shift in redox metabolism [9,10].",
 "The therapeutic backbone is itself redox-active. Sorafenib kills HCC cells in part by generating mitochondrial reactive oxygen species and by interfering with the unfolded-protein response, and resistance to it is accompanied by a shift in redox metabolism [9,10]."),

("B3", "because", "The results are given in full because the negative one is the informative one.",
 "The results are given in full: the negative one is the informative one."),

("B4", "because", "Tumour-versus-normal expression used the cBioPortal per-gene Z-score profile computed against reference normal liver samples; because the PanCancer Atlas LIHC cohort contains only primary solid tumours, no within-cohort normal comparison is possible and the reference-normal profile is used in its place.",
 "Tumour-versus-normal expression used the cBioPortal per-gene Z-score profile computed against reference normal liver samples. The PanCancer Atlas LIHC cohort contains only primary solid tumours, so no within-cohort normal comparison is possible and the reference-normal profile is used in its place."),

("B5", "because", "Because the PanCancer Atlas LIHC cohort contains only primary solid tumours, this is an external-reference comparison and is descriptive only.",
 "The PanCancer Atlas LIHC cohort contains only primary solid tumours, so this is an external-reference comparison and is descriptive only."),

("B6", "because", "which we omit because cell-line pharmacogenomic resources are not patient-matched to these cohorts and predicted IC₅₀ values from a fitted model are extrapolation rather than observation.",
 "which we omit: cell-line pharmacogenomic resources are not patient-matched to these cohorts, and predicted IC₅₀ values from a fitted model are extrapolation rather than observation."),

# ── C. therefore 8 -> 3 ─────────────────────────────────────────
("C1", "therefore", "A gene programme reporting on mitochondrial oxidative stress should therefore be informative in this tumour type.",
 "A gene programme reporting on mitochondrial oxidative stress should be informative in this tumour type."),

("C2", "therefore", "the concept therefore transfers from macrophages to bulk tumour transcriptomes, but the present work cannot claim priority for such a model.",
 "The concept therefore transfers from macrophages to bulk tumour transcriptomes; the present work cannot claim priority for such a model."),

("C3", "therefore", "We therefore designed this study around replication rather than discovery.",
 "We designed this study around replication rather than discovery."),

("C4", "therefore", "We therefore repeated the *entire* Model B procedure — LASSO path, 1-SE rule, 200-bootstrap stability selection at π ≥ 0.75 and the multivariable fit — inside each training fold of a 10-fold split, applied the resulting coefficients to the held-out fold, and did the same for the Model A pipeline so that the two are compared on equal terms.",
 "We repeated the *entire* Model B procedure inside each training fold of a 10-fold split — LASSO path, 1-SE rule, 200-bootstrap stability selection at π ≥ 0.75 and the multivariable fit — and applied the resulting coefficients to the held-out fold. The Model A pipeline was run the same way, so that the two are compared on equal terms."),

("C5", "therefore", "A pure LASSO-plus-1-SE rule therefore did not by itself produce a sparse model: the prognostic signal in this panel is diffuse and many weakly correlated genes carry interchangeable information.",
 "A pure LASSO-plus-1-SE rule did not by itself produce a sparse model: the prognostic signal in this panel is diffuse, and many weakly correlated genes carry interchangeable information."),

("C6", "therefore", "The result therefore does not hinge on the value 0.75 itself.",
 "The result does not hinge on the value 0.75 itself."),

("C7", "therefore", "The ordering of the two scores therefore inverted between discovery and validation, which is the signature of selection optimism rather than of a transferable biological signal (Figure 5B).",
 "The ordering of the two scores inverted between discovery and validation — the signature of selection optimism rather than of a transferable biological signal (Figure 5B)."),

# ── D. but -> however / although（D-19 让步语义不得被静默降级）──────
("D1", "让步", "The cell-cycle genes KIF15, ASF1B and MCM5 are present, but they are not the leading edge of the corrected list.",
 "The cell-cycle genes KIF15, ASF1B and MCM5 are present, although they are not the leading edge of the corrected list."),

("D2", "however", "Across 200 bootstrap resamples at the 1-SE α the median model contained 11 genes (interquartile range 8–14, full range 4–16), but the *identity* of the leading genes was reproducible at the top:",
 "Across 200 bootstrap resamples at the 1-SE α the median model contained 11 genes (interquartile range 8–14, full range 4–16). The *identity* of the leading genes, however, was reproducible at the top:"),

("D3", "让步", "The defensible statement is therefore narrower than the one this literature usually makes: **in the discovery cohort MRG-2 dominates the proliferation score in joint regression models, but its discrimination is statistically indistinguishable from that of a generic proliferation score.**",
 "The defensible statement is narrower than the one this literature usually makes: **in the discovery cohort MRG-2 dominates the proliferation score in joint regression models, although its discrimination is statistically indistinguishable from that of a generic proliferation score.**"),

("D4", "让步", "is consistent with the TP53-mutated compartment described below, but it remains a marker-mean proxy that is not corrected for tumour purity.",
 "is consistent with the TP53-mutated compartment described below, although it remains a marker-mean proxy that is not corrected for tumour purity."),

("D5", "however", "its π ranges from 0.690 to 0.805 and falls below the prespecified 0.75 in two seeds, at which point the \"two-gene signature\" is a one-gene signature, whereas KIF15 never fell below 0.875.",
 "its π ranges from 0.690 to 0.805 and falls below the prespecified 0.75 in two seeds, at which point the \"two-gene signature\" is a one-gene signature. KIF15, by contrast, never fell below 0.875."),

# ── E. 长句切分（≥35 词 -> 目标 <20%）────────────────────────────
("E1", "切分", "We derive a prognostic index from the full MRG panel in TCGA-LIHC, re-derive it with LASSO-Cox and bootstrap stability selection, and subject the compressed score to four questions in sequence: does it survive a *nested* estimate of optimism, in which the whole selection procedure is repeated inside every cross-validation fold; is the stability threshold reproducible under an independent bootstrap seed; does it beat random panels of the same size; and does it transport to an independent cohort with the coefficients frozen.",
 "We derive a prognostic index from the full MRG panel in TCGA-LIHC and re-derive it with LASSO-Cox and bootstrap stability selection. The compressed score then faces four questions in sequence: nested optimism, seed reproducibility of the stability threshold, a random-panel benchmark, and transport to an independent cohort with the coefficients frozen."),

("E2", "切分", "*GSE14520* (Roessler et al. [26]) is an Affymetrix HG-U133A/HG-U133A-2.0 cohort of resected HCC and the standard external validation resource for HCC prognostic signatures; from the series matrices (GPL571 and GPL3921) and the series clinical supplement we obtained 242 tumours, 96 deaths (39.7%) and a median follow-up of 57.0 months.",
 "*GSE14520* (Roessler et al. [26]) is an Affymetrix HG-U133A/HG-U133A-2.0 cohort of resected HCC and the standard external validation resource for HCC prognostic signatures. From the series matrices (GPL571 and GPL3921) and the series clinical supplement we obtained 242 tumours, 96 deaths (39.7%) and a median follow-up of 57.0 months."),

("E3", "切分", "Probe-to-gene mapping used each platform's annotation file; where a probe set carried several symbols the probe was indexed under every symbol, and where several probes mapped to one gene the probe with the highest mean expression was retained.",
 "Probe-to-gene mapping used each platform's annotation file. Where a probe set carried several symbols the probe was indexed under every symbol; where several probes mapped to one gene, the probe with the highest mean expression was retained."),

("E4", "切分", "No criterion in that screen measured the death phenotype itself — neither lysis, mitochondria–plasma-membrane contact, nor BAX/BAK1/BID dependence — so the selected genes are immune-plus-metabolic-stress responders in a macrophage system, not validated effectors of mitoxyperilysis.",
 "No criterion in that screen measured the death phenotype itself — neither lysis, mitochondria–plasma-membrane contact, nor BAX/BAK1/BID dependence. The selected genes are immune-plus-metabolic-stress responders in a macrophage system, not validated effectors of mitoxyperilysis."),

("E5", "切分", "Core effector genes of the pathway (SOD2, TXNRD1, BID, BAK1, RICTOR) are panel members and TXNRD1 and OSGIN2 entered the top univariate hits; this is an observation, not a claim that the score measures the pathway.",
 "Core effector genes of the pathway (SOD2, TXNRD1, BID, BAK1, RICTOR) are panel members, and TXNRD1 and OSGIN2 entered the top univariate hits. This is an observation, not a claim that the score measures the pathway."),

("E6", "切分", "Univariate Cox regression was applied to each of the 91 genes and genes with *P* < 0.05 were carried forward into a multivariable Cox model with an L2 ridge penalty (penalizer = 1.0) to control collinearity.",
 "Univariate Cox regression was applied to each of the 91 genes. Genes with *P* < 0.05 were carried forward into a multivariable Cox model with an L2 ridge penalty (penalizer = 1.0) to control collinearity."),

("E7", "切分", "Gene-wise Z-scores for all evaluable panel genes were retrieved for the identical patient set and re-standardised to zero mean and unit variance; the stored means and standard deviations fixed the transformation applied in the validation cohorts.",
 "Gene-wise Z-scores for all evaluable panel genes were retrieved for the identical patient set and re-standardised to zero mean and unit variance. The stored means and standard deviations fixed the transformation applied in the validation cohorts."),

("E8", "切分", "Genes with π ≥ 0.75 were carried into a multivariable Cox model and members not significant at *P* < 0.05 were removed; both the π ≥ 0.75 set and the final reduced set are reported so that the effect of the last step is visible.",
 "Genes with π ≥ 0.75 were carried into a multivariable Cox model, and members not significant at *P* < 0.05 were removed. Both the π ≥ 0.75 set and the final reduced set are reported so that the effect of the last step is visible."),

("E9", "切分", "with q = 16 and p = 91 it is E[V] ≤ 5.63 at π = 0.75, ≤ 7.03 at π = 0.70 and ≤ 4.69 at π = 0.80, all larger than the final model, so the threshold is a prespecified selection rule and not a false-discovery guarantee.",
 "with q = 16 and p = 91 it is E[V] ≤ 5.63 at π = 0.75, ≤ 7.03 at π = 0.70 and ≤ 4.69 at π = 0.80. All three exceed the final model size, so the threshold is a prespecified selection rule and not a false-discovery guarantee."),

("E10", "切分", "To ask whether a two-gene score does anything an arbitrary pair of panel genes would not, 3,000 random pairs were drawn from the evaluable panel without replacement, a two-gene Cox model was fitted in each cohort, and the apparent C-index of each pair was recorded; the observed MRG-2 value is reported as a percentile.",
 "To ask whether a two-gene score does anything an arbitrary pair of panel genes would not, 3,000 random pairs were drawn from the evaluable panel without replacement. A two-gene Cox model was fitted in each cohort and the apparent C-index of each pair recorded. The observed MRG-2 value is reported as a percentile."),

("E11", "切分", "Non-synonymous mutation calls for 16 recurrently altered HCC genes were retrieved from the same cBioPortal study, with gene symbols resolved from the Entrez identifiers carried by each record, and mutation frequencies compared between risk groups by Fisher's exact test.",
 "Non-synonymous mutation calls for 16 recurrently altered HCC genes were retrieved from the same cBioPortal study, with gene symbols resolved from the Entrez identifiers carried by each record. Mutation frequencies were compared between risk groups by Fisher's exact test."),

("E12", "切分", "Analyses were run in Python 3.13 (pandas, NumPy, SciPy, matplotlib, lifelines 0.30.3, scikit-survival 0.28.0), and every table and figure is reproducible from the deposited per-patient tables (Supplementary Tables S1–S13) together with the two public validation cohorts.",
 "Analyses were run in Python 3.13 (pandas, NumPy, SciPy, matplotlib, lifelines 0.30.3, scikit-survival 0.28.0). Every table and figure is reproducible from the deposited per-patient tables (Supplementary Tables S1–S13) together with the two public validation cohorts."),

("E13", "切分", "and CEP19 (q = 0.028) — with MBOAT7 at q = 0.051 on the boundary; the remaining 17 of the 23 carried q = 0.057–0.20.",
 "and CEP19 (q = 0.028) — with MBOAT7 at q = 0.051 on the boundary. The remaining 17 of the 23 carried q = 0.057–0.20."),

("E14", "切分", "with a further nine risk-associated genes at HR > 1.22 and five protective genes led by PPP1R10 (HR 0.794, *P* = 5.0×10⁻³); the full list is in Table 3 (Figure 1A).",
 "A further nine risk-associated genes had HR > 1.22, and five protective genes were led by PPP1R10 (HR 0.794, *P* = 5.0×10⁻³). The full list is in Table 3 (Figure 1A)."),

("E15", "切分", "High-risk patients had substantially worse OS (median 35.8 vs 80.7 months; HR 1.87 per SD, 95% CI 1.56–2.24; log-rank *P* = 1.9×10⁻⁶; Figure 1B–D), an apparent C-index of 0.684 (95% CI 0.625–0.733) and a mean time-dependent AUC of 0.733 (1/3/5-year 0.772 / 0.718 / 0.720; Figure 2A).",
 "High-risk patients had substantially worse OS (median 35.8 vs 80.7 months; HR 1.87 per SD, 95% CI 1.56–2.24; log-rank *P* = 1.9×10⁻⁶; Figure 1B–D). The apparent C-index was 0.684 (95% CI 0.625–0.733) and the mean time-dependent AUC 0.733 (1/3/5-year 0.772 / 0.718 / 0.720; Figure 2A)."),

("E16", "切分", "What the threshold does *not* provide is false-discovery control: the Meinshausen–Bühlmann bound is E[V] ≤ 5.63 at π = 0.75 (q = 16, p = 91), larger than the two-gene model it is supposed to protect (Section 2.4).",
 "What the threshold does *not* provide is false-discovery control: the Meinshausen–Bühlmann bound is E[V] ≤ 5.63 at π = 0.75 (q = 16, p = 91). That bound exceeds the two-gene model it is supposed to protect (Section 2.4)."),

("E17", "切分", "Both coefficients are significant and agree in direction with their univariate estimates; the two genes are only weakly correlated, so the coefficients can be interpreted individually; and the **EPV ratio is 64.5** (129 deaths, 2 terms) against 5.6 for Model A.",
 "Both coefficients are significant and agree in direction with their univariate estimates. The two genes are only weakly correlated, so the coefficients can be interpreted individually. The **EPV ratio is 64.5** (129 deaths, 2 terms) against 5.6 for Model A."),

("E18", "切分", "under two of the ten seeds its π falls to 0.690 and 0.735, and the π ≥ 0.75 set then contains KIF15 alone, so the \"two-gene\" score degenerates into a single-gene score. A score whose second member is decided by the bootstrap seed is not a stable two-gene signature, and we report it as a threshold-marginal rather than a robust member (Figure 5D; Supplementary Table S11).",
 "under two of the ten seeds its π falls to 0.690 and 0.735, the π ≥ 0.75 set then contains KIF15 alone, and the \"two-gene\" score degenerates into a single-gene score. A score whose second member is decided by the bootstrap seed is not a stable two-gene signature; we report it as a threshold-marginal rather than a stably selected member (Figure 5D; Supplementary Table S11)."),

("E19", "切分", "MRG-2 separated survival as well as the 23-gene model in the discovery data: median split gave 180 patients per group with median OS 80.7 vs 33.0 months (log-rank *P* = 6.3×10⁻⁶; Figure 3C), HR 1.66 per SD (95% CI 1.37–2.00; *P* = 1.2×10⁻⁷) and an apparent C-index of 0.677 (95% CI 0.623–0.728), statistically indistinguishable from Model A's 0.684",
 "MRG-2 separated survival as well as the 23-gene model in the discovery data. Median split gave 180 patients per group with median OS 80.7 vs 33.0 months (log-rank *P* = 6.3×10⁻⁶; Figure 3C) and HR 1.66 per SD (95% CI 1.37–2.00; *P* = 1.2×10⁻⁷). The apparent C-index was 0.677 (95% CI 0.623–0.728), statistically indistinguishable from Model A's 0.684"),

("E20", "切分", "In the discovery cohort MRG-2 is nonetheless exceptional among two-gene panels: against 3,000 random pairs from the same 91 genes",
 "In the discovery cohort MRG-2 is nonetheless exceptional among two-gene panels. Against 3,000 random pairs from the same 91 genes"),

("E21", "切分", "Unsurprising in part: KIF15 is a mitotic kinesin.",
 "KIF15 is a mitotic kinesin, so this is unsurprising in part."),

("E22", "切分", "In a joint model containing both scores, MRG-2 carried HR 1.60 per SD (95% CI 1.21–2.12; *P* = 6.4×10⁻⁴) while the proliferation score did not retain significance (HR 1.05, 95% CI 0.80–1.37; *P* = 0.73).",
 "In a joint model containing both scores, MRG-2 carried HR 1.60 per SD (95% CI 1.21–2.12; *P* = 6.4×10⁻⁴). The proliferation score did not retain significance (HR 1.05, 95% CI 0.80–1.37; *P* = 0.73)."),

("E23", "切分", "Its C-index confidence interval includes 0.5, its hazard ratio is not significant, and after adjustment for age, sex, TNM stage III–IV and platform the score is clearly null (HR 1.05, *P* = 0.63) while stage remains strongly prognostic (HR 3.04, *P* < 0.001).",
 "Its C-index confidence interval includes 0.5 and its hazard ratio is not significant. After adjustment for age, sex, TNM stage III–IV and platform the score is clearly null (HR 1.05, *P* = 0.63), while stage remains strongly prognostic (HR 3.04, *P* < 0.001)."),

("E24", "切分", "and **52.97% of them matched or beat MRG-2** — the observed score sits at the **47th percentile** of the null distribution, below its own mean, whereas in the discovery cohort it exceeded all 3,000 (Figure 5C).",
 "and **52.97% of them matched or beat MRG-2**. The observed score sits at the **47th percentile** of the null distribution, below its own mean; in the discovery cohort it exceeded all 3,000 (Figure 5C)."),

("E25", "切分", "The direction problem is not specific to the MRG panel: in the same 115 tumours,",
 "The direction problem is not specific to the MRG panel. In the same 115 tumours,"),

("E26", "切分", "**These subtypes were not separated by survival (log-rank *P* = 0.171)** and the silhouette is low in absolute terms, so we report the clustering as a negative result and make no claim for the labels:",
 "**These subtypes were not separated by survival (log-rank *P* = 0.171)**, and the silhouette is low in absolute terms. We report the clustering as a negative result and make no claim for the labels:"),

("E27", "切分", "The one robust finding — loss of NK-cell signal in high-risk tumours — is consistent",
 "The one firm finding — loss of NK-cell signal in high-risk tumours — is consistent"),

("E28", "切分", "The two-gene score was better in every respect that matters for a prognostic index in the discovery data: its coefficients are significant and directionally consistent with their univariate estimates, so they can be read; the EPV ratio rises from 5.6 to 64.5; it matches the full-panel model's discrimination with two parameters instead of 23; it does not absorb AJCC stage; and it beat all 3,000 random two-gene panels we drew.",
 "The two-gene score was better in every respect that matters for a prognostic index in the discovery data. Its coefficients are significant and directionally consistent with their univariate estimates, so they can be read. The EPV ratio rises from 5.6 to 64.5, the model matches the full-panel discrimination with two parameters instead of 23, it does not absorb AJCC stage, and it beat all 3,000 random two-gene panels we drew."),

("E29", "切分", "Fully nested cross-validation cut both models to about 0.58 and made them indistinguishable — not a failure of the compression argument, but a demonstration that the *apparent* superiority of both models over chance was largely selection optimism, and that a study reporting only apparent C-indices in this design is reporting an artefact.",
 "Fully nested cross-validation cut both models to about 0.58 and made them indistinguishable. That is not a failure of the compression argument; it is a demonstration that the *apparent* superiority of both models over chance was largely selection optimism, and that a study reporting only apparent C-indices in this design is reporting an artefact."),

("E30", "切分", "Repetition of the bootstrap under ten seeds then showed MAFG's stability to be a threshold artefact: its π ranges from 0.690 to 0.805",
 "Repetition of the bootstrap under ten seeds then showed MAFG's stability to be a threshold artefact. Its π ranges from 0.690 to 0.805"),

("E31", "切分", "the data support one robustly stable gene and one threshold-marginal gene.",
 "the data support one stably selected gene and one threshold-marginal gene."),

("E32", "切分", "and a position at the 47th percentile of 3,000 random two-gene panels, while a generic 20-gene proliferation score in the same cohort reached 0.596 and a log-rank *P* of 7.2×10⁻⁴.",
 "and a position at the 47th percentile of 3,000 random two-gene panels. A generic 20-gene proliferation score in the same cohort reached 0.596 and a log-rank *P* of 7.2×10⁻⁴."),

("E33", "切分", "One possibility is that the diffuse signal in the panel is genuinely distributed — the median bootstrap model contained 11 genes and the LASSO never produced a sparse solution on its own — so that a 19-gene ridge index captures more of it than any two genes can; on that reading the compression was an over-compression, and the lesson is not \"simpler is better\" but \"stability selection can compress past the point where the retained genes still carry the signal\".",
 "One possibility is that the diffuse signal in the panel is genuinely distributed: the median bootstrap model contained 11 genes and the LASSO never produced a sparse solution on its own. On that reading a 19-gene ridge index captures more of the signal than any two genes can, and the compression was an over-compression. The lesson is not \"simpler is better\" but \"stability selection can compress past the point where the retained genes still carry the signal\"."),

("E34", "切分", "we cannot separate those explanations.",
 "We cannot separate those explanations."),

("E35", "切分", "Fitted to the whole panel it is 23 genes at an events-per-variable ratio of 5.6 with no interpretable coefficient; refitted with stability selection it is two genes, KIF15 and MAFG, at a ratio of 64.5, with coefficients that are individually significant, and with the same discrimination as the 23-gene model under fully nested cross-validation.",
 "Fitted to the whole panel it is 23 genes at an events-per-variable ratio of 5.6 with no interpretable coefficient. Refitted with stability selection it is two genes, KIF15 and MAFG, at a ratio of 64.5, with coefficients that are individually significant and with the same discrimination as the 23-gene model under fully nested cross-validation."),

# ── F. 版本号 ───────────────────────────────────────────────────
("F1", "版本", "## Data provenance note (not for submission)",
 "## Data provenance note (not for submission)"),
]

def main():
    t = open(SRC, encoding="utf-8").read()
    fail, done = [], []
    for tag, cat, old, new in R:
        if old == new:
            continue
        c = t.count(old)
        if c != 1:
            fail.append(f"  ✗ {tag} [{cat}] 命中 {c} 次（须为 1）：{old[:70]}…")
            continue
        t = t.replace(old, new)
        done.append(f"  ✓ {tag} [{cat}]")
    if fail:
        print("❌ 有替换未按预期命中，未写出文件：")
        print("\n".join(fail))
        sys.exit(1)
    open(DST, "w", encoding="utf-8").write(t)
    print(f"✅ 共 {len(done)} 处替换全部唯一命中 → {os.path.basename(DST)}")
    for d in done:
        print(d)

if __name__ == "__main__":
    main()
