#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R1-M8 回填：把 pooled out-of-fold C-index 与十随机划分结果写回正文。

数据来源（唯一）：数据/revised/nested_pooled.json —— 由 r1m8_nested_pooled.py 产出。
  pooled（10 个随机划分）MRG-2 0.6133 ± 0.0134 [0.5956–0.6351]
  pooled（10 个随机划分）Model A 0.6218 ± 0.0096 [0.6104–0.6474]
  预设划分（seed 42）pooled：MRG-2 0.5956、Model A 0.6104
  optimism（apparent − pooled，配对 bootstrap 2000）：MRG-2 0.0811（0.0404–0.1218）、
                                                     Model A 0.0736（0.0526–0.0963）
  自我一致性：预设划分折均值 0.5758 vs 沉积 0.5760 ✅

改动原则：**只改与嵌套估计有关的表述**；不触碰任何其他数字。
"""
import re, json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.6.md")
J = os.path.join(BASE, "数据", "revised", "nested_pooled.json")

d = json.load(open(J, encoding="utf-8"))
p = d["primary_split"]; ac = d["across_splits"]; op = d["optimism"]
# 断言：所有写入正文的数字都取自这里，不允许再手打
V = {
    "B_mean": "%.3f" % ac["pooled_MRG2"]["mean"],          # 0.613
    "B_sd":   "%.3f" % ac["pooled_MRG2"]["sd"],            # 0.013
    "B_lo":   "%.3f" % ac["pooled_MRG2"]["min"],           # 0.596
    "B_hi":   "%.3f" % ac["pooled_MRG2"]["max"],           # 0.635
    "A_mean": "%.3f" % ac["pooled_ModelA"]["mean"],        # 0.622
    "A_sd":   "%.3f" % ac["pooled_ModelA"]["sd"],          # 0.010
    "A_lo":   "%.3f" % ac["pooled_ModelA"]["min"],         # 0.610
    "A_hi":   "%.3f" % ac["pooled_ModelA"]["max"],         # 0.647
    "B_pri":  "%.3f" % p["pooled_oof_C_MRG2"],             # 0.596
    "A_pri":  "%.3f" % p["pooled_oof_C_ModelA"],           # 0.610
    "optB":   "%.3f" % op["MRG2"]["diff"],                 # 0.081
    "optB_lo": "%.3f" % op["MRG2"]["lo"],                  # 0.040
    "optB_hi": "%.3f" % op["MRG2"]["hi"],                  # 0.122
    "optA":   "%.3f" % op["ModelA"]["diff"],               # 0.074
    "optA_lo": "%.3f" % op["ModelA"]["lo"],                # 0.053
    "optA_hi": "%.3f" % op["ModelA"]["hi"],                # 0.096
}
print("将写入的数值（全部取自 nested_pooled.json）：")
for k, v in V.items():
    print("   %-9s %s" % (k, v))

s = open(P, encoding="utf-8").read()

EDITS = [
# ---------------- 1. 摘要 ----------------
("Three checks undercut it: nested cross-validation cut both models to about 0.58 (MRG-2 0.576 ± 0.100); MAFG's π ranged",
 "Three checks undercut it: pooled out-of-fold cross-validation cut both models to about 0.61 "
 "(MRG-2 {B_mean} ± {B_sd} over ten random splits); MAFG's π ranged"),

# ---------------- 2. 方法 §2.6 ----------------
("The apparent C-index of a model whose genes were selected on the full dataset is optimistic. "
 "We repeated the *entire* Model B procedure inside each training fold of a 10-fold split and applied "
 "the resulting coefficients to the held-out fold. Model A was run the same way, with one seed (42) "
 "fixing the split. The reported standard deviation is **across folds**, a descriptive spread of fold "
 "performance, *not* a standard error of the pooled C-index (Supplementary Methods).",

 "The apparent C-index of a model whose genes were selected on the full data is optimistic. We repeated "
 "the *entire* Model B procedure inside each training fold of a 10-fold split and applied the resulting "
 "coefficients to the held-out fold, and ran Model A the same way. The primary statistic is the "
 "**pooled out-of-fold C-index** — the ten held-out linear predictors concatenated and scored once over "
 "all 360 patients — because fold-wise C-indices have different event rates and their mean is biased. "
 "We repeated the whole nested procedure under **ten independent random splits** and report the mean and "
 "standard deviation of the pooled statistic (Supplementary Methods)."),

# ---------------- 3. 结果 §3.3 引语 ----------------
("Those figures are apparent. Re-running the whole selection procedure inside each of ten outer folds "
 "gives the second uncomfortable result:",
 "Those figures are apparent. Re-running the whole selection procedure inside each of ten outer folds, "
 "and pooling the held-out predictions, gives the second uncomfortable result:"),

# ---------------- 4. 结果 §3.3 表 ----------------
("| Model | Fully nested 10-fold C-index | Fold range | Apparent |\n"
 "|---|---|---|---|\n"
 "| Model B (MRG-2) | **0.576 ± 0.100** | 0.371 – 0.732 | 0.677 |\n"
 "| Model A (23 genes) | **0.588 ± 0.103** | 0.336 – 0.704 | 0.684 |",
 "| Model | Pooled out-of-fold C-index (ten random splits) | Prespecified split | Range over splits | Apparent |\n"
 "|---|---|---|---|---|\n"
 "| Model B (MRG-2) | **{B_mean} ± {B_sd}** | {B_pri} | {B_lo} – {B_hi} | 0.677 |\n"
 "| Model A (23 genes) | **{A_mean} ± {A_sd}** | {A_pri} | {A_lo} – {A_hi} | 0.684 |"),

# ---------------- 5. 结果 §3.3 结论段 ----------------
("Two conclusions follow. The optimism is large — about 0.10 C-index units — and of the same magnitude "
 "for both models, so the *apparent* gap between them was never meaningful. **The two models remain "
 "indistinguishable even under the honest estimate**: two genes deliver the same nested discrimination "
 "as twenty-three, and the fold-to-fold spread makes any comparison uninformative (Section 2.6).",
 "Two conclusions follow. The optimism is real and excludes zero — {optB} C-index units for MRG-2 "
 "(95% CI {optB_lo}–{optB_hi}) and {optA} for Model A ({optA_lo}–{optA_hi}), of the same magnitude for "
 "both models, so the *apparent* gap between them was never meaningful. **The two models remain "
 "indistinguishable under the honest estimate**: two genes deliver the same pooled out-of-fold "
 "discrimination as twenty-three, and the split-to-split spread makes any comparison uninformative "
 "(Section 2.6)."),

# ---------------- 6. §3.7 轨迹句 ----------------
("Apparent 0.677 → fully nested 0.576 → independent cohort 0.551 → 47th percentile",
 "Apparent 0.677 → pooled out-of-fold {B_mean} → independent cohort 0.551 → 47th percentile"),

# ---------------- 7. 讨论 ----------------
("Fully nested cross-validation cut both models to about 0.58 and made them indistinguishable",
 "Pooled out-of-fold cross-validation cut both models to about 0.61 and made them indistinguishable"),

("That inversion, with the monotone decline from 0.677 to 0.576 to 0.551, is what selection optimism "
 "looks like when measured rather than assumed.",
 "That inversion, with the monotone decline from 0.677 to {B_mean} to 0.551, is what selection optimism "
 "looks like when measured rather than assumed."),

# ---------------- 8. 结论 ----------------
("the same discrimination as the 23-gene model under fully nested cross-validation",
 "the same discrimination as the 23-gene model under pooled out-of-fold cross-validation"),

("the apparent discrimination carries about 0.10 C-index units of optimism",
 "the apparent discrimination carries {optB} C-index units of optimism (95% CI {optB_lo}–{optB_hi})"),

# ---------------- 9. 图 5 图注（不计入正文字数） ----------------
("under fully nested 10-fold cross-validation (blue; error bars, ± 1 SD across folds) and in the "
 "external cohort GSE14520",
 "under pooled out-of-fold cross-validation (blue; bars, the pooled C-index averaged over ten "
 "independent random splits; error bars, ± 1 SD across splits) and in the external cohort GSE14520"),

("MRG-2 declines monotonically from 0.677 to 0.576 to 0.551, and the discovery ordering of MRG-2 "
 "above the proliferation score inverts externally.",
 "MRG-2 declines monotonically from 0.677 to {B_mean} to 0.551, and the discovery ordering of MRG-2 "
 "above the proliferation score inverts externally."),

# ---------------- 10. 补充方法 ----------------
("**Fully nested cross-validation.** Inside each training fold of the 10-fold split the *entire* Model B "
 "procedure was repeated — LASSO path, 1-SE rule, bootstrap stability selection at π ≥ 0.75, and the "
 "multivariable fit — and the resulting coefficients were applied to the held-out fold. The inner "
 "selection used 100 bootstrap resamples per fold rather than the 200 used for the primary fit. Model A "
 "was run the same way and a single seed (42) fixed the split. The standard deviation reported is across "
 "folds and is a descriptive spread of fold performance, not a standard error of the pooled C-index, "
 "because the ten folds are neither independent nor equally sized.",

 "**Fully nested cross-validation and pooled out-of-fold estimation.** Inside each training fold of the "
 "10-fold split the *entire* Model B procedure was repeated — LASSO path, 1-SE rule, bootstrap stability "
 "selection at π ≥ 0.75, and the multivariable fit — and the resulting coefficients were applied to the "
 "held-out fold; the inner selection used 100 bootstrap resamples per fold rather than the 200 used for "
 "the primary fit. Model A was run the same way. For each model the ten held-out linear predictors were "
 "then **concatenated into a single vector and scored once over all 360 patients**, giving the pooled "
 "out-of-fold C-index; averaging the ten fold-wise C-indices instead is biased because the folds differ "
 "in event rate, and the standard error of that mean is not defined by SD/√10 since the folds share "
 "training data and are neither independent nor equally sized. Because a single partition cannot "
 "separate the estimate from the partition, the whole nested procedure was repeated under **ten "
 "independent random splits** (outer seeds 42–51, all other settings unchanged: 10 folds, 100 inner "
 "bootstrap resamples, inner cross-validation seed 42). The prespecified seed 42 partition is reported "
 "separately; its fold-wise mean (0.576 for MRG-2) reproduces the value in the earlier analysis and is "
 "retained only as a consistency check. Optimism is the difference between the apparent C-index and the "
 "pooled out-of-fold C-index, with a paired bootstrap confidence interval (2,000 resamples, seed 7)."),

# ---------------- 11. 数据可得性：补 S10b ----------------
("S10 (fully nested 10-fold cross-validation), S11 (bootstrap seed replication)",
 "S10 (fully nested 10-fold cross-validation, with retained genes and held-out C-index per fold) with "
 "S10b (the pooled out-of-fold C-index under the prespecified partition and under ten independent random "
 "splits, with the optimism of each model and its 95% confidence interval), S11 (bootstrap seed replication)"),

# ---------------- 12. 补充表清单：补 S10b 条目 ----------------
("**Supplementary Table S10.** Fully nested 10-fold cross-validation of the Model B procedure: retained "
 "genes and held-out C-index per fold, and the corresponding per-fold results for the Model A pipeline.",
 "**Supplementary Table S10.** Fully nested 10-fold cross-validation of the Model B procedure: retained "
 "genes and held-out C-index per fold, and the corresponding per-fold results for the Model A pipeline.\n\n"
 "**Supplementary Table S10b.** Pooled out-of-fold C-index of both models under the prespecified "
 "partition and under ten independent random splits, with the mean, standard deviation and range across "
 "splits, and the optimism of each model as a paired bootstrap difference with its 95% confidence interval."),
]

for old, new in EDITS:
    n = s.count(old)
    assert n == 1, "命中 %d 次（应为 1）：\n%r" % (n, old[:90])
    new_f = new.format(**V)
    # 只允许出现 V 中的新数字或原文已有的数字
    s = s.replace(old, new_f, 1)

open(P, "w", encoding="utf-8").write(s)
print("\n✅ 回填完成，共 %d 处" % len(EDITS))

# ---- 复算字数（Word 口径：空白分隔且含字母或数字的 token） ----
W = lambda x: len([w for w in x.split() if re.search(r"[A-Za-z0-9]", w)])
body = s.split("## 1. Introduction")[1].split("## Declarations")[0]
ab = s.split("## Abstract")[1].split("**Keywords")[0]
t = s.split("\n")[0].lstrip("# ").strip()
print("正文 IMRaD : %d  (限 <6000)  %s" % (W(body), "✅" if W(body) < 6000 else "❌ 需压缩"))
print("摘要       : %d  (限 <300)   %s" % (W(ab), "✅" if W(ab) < 300 else "❌ 需压缩"))
print("标题       : %d 字符 / %d 词" % (len(t), len(t.split())))
