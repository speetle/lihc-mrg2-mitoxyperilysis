#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v1.6 收尾压缩：R1-M8 回填使正文升至 6,031 词（限 <6,000），本脚本做**纯散文压缩**。

原则（与 trim_v15h 一致）：
  * 每条 old 必须唯一命中；new 不得引入原本没有的数字；
  * 被删片段里出现的数字，必须在文档**他处仍出现**（对应 compress_gate 的判据 A）；
  * 不触碰任何结论、不触碰任何表格数值。
"""
import re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.6.md")
s = open(P, encoding="utf-8").read()

EDITS = [
# ---- T0：一致性必改（§4 Limitations 仍写 "about 0.10 units"）----
("so the apparent C-index of 0.677 retained about 0.10 units of optimism;",
 "so the apparent C-index of 0.677 retained 0.081 units of optimism;"),

# ---- T1：§2.6 收紧 ----
("The primary statistic is the **pooled out-of-fold C-index** — the ten held-out linear predictors "
 "concatenated and scored once over all 360 patients — because fold-wise C-indices have different event "
 "rates and their mean is biased. We repeated the whole nested procedure under **ten independent random "
 "splits** and report the mean and standard deviation of the pooled statistic (Supplementary Methods).",
 "The primary statistic is the **pooled out-of-fold C-index** — the ten held-out predictions "
 "concatenated and scored once — because fold-wise C-indices have different event rates and their mean "
 "is biased. The whole procedure was repeated under **ten independent random splits**; the mean and "
 "standard deviation across them are reported (Supplementary Methods)."),

# ---- T2：§3.3 EPV 段微删 ----
("One objection is that the ridge penalty, not the number of terms, produced those null coefficients; "
 "it is not so. Refitting the same 23 genes without penalty converges, leaves every coefficient small "
 "(largest |coefficient| 0.35, largest hazard ratio 1.33, no sign reversals, design condition number 6.0)",
 "One objection is that the penalty, not the number of terms, produced those null coefficients; it is "
 "not so. Refitting the same 23 genes without penalty converges, leaves every coefficient small "
 "(largest |coefficient| 0.35, largest hazard ratio 1.33, no sign reversals, condition number 6.0)"),

# ---- T3：§3.5 删去复述整句（该对比已由前两句完整给出）----
("ΔC = +0.034 (95% CI −0.012 to +0.076; *P* = 0.147); Model A does separate (ΔC = +0.041, 95% CI 0.002 to 0.080; *P* = 0.038). "
 "**In the discovery cohort MRG-2 therefore dominates the proliferation score in joint regression models, "
 "although its discrimination is statistically indistinguishable from that of a generic proliferation score.** "
 "Its only distinctive feature is",
 "ΔC = +0.034 (95% CI −0.012 to +0.076; *P* = 0.147); Model A does separate (ΔC = +0.041, 95% CI 0.002 to 0.080; *P* = 0.038). "
 "Its only distinctive feature is"),

# ---- T4：Introduction 机制段微删 ----
("Whether a gene programme defined in macrophages under acute stimulation is represented at all in a "
 "human epithelial tumour transcriptome is a separate and untested question, and we therefore treat the "
 "panel as an exploratory macrophage-derived stress-response index rather than as a readout of the pathway.",
 "Whether a gene programme defined in macrophages under acute stimulation is represented in a human "
 "epithelial tumour transcriptome is a separate and untested question, and we therefore treat the panel "
 "as an exploratory stress-response index rather than a readout of the pathway."),

# ---- T5：§2.4 微删 ----
("the last step (backward elimination at *P* < 0.05) means the reported coefficient *P* values are "
 "post-selection estimates rather than pre-specified tests.",
 "the last step (backward elimination at *P* < 0.05) makes the reported coefficient *P* values "
 "post-selection estimates rather than pre-specified tests."),

# ---- T6：§3.5 议题句微删 ----
("The result of this study is not that a mitoxyperilysis-related score predicts HCC survival. It is that "
 "**the same 91 genes, fitted two ways, produce a 23-gene index that is over-parameterised and a two-gene "
 "index that is not — that compression is free in the discovery data — and that the compressed score "
 "nevertheless fails to transport to an independent cohort, where it is no better than a random pair of "
 "panel genes or a generic proliferation score.**",
 "The result of this study is not that a mitoxyperilysis-related score predicts HCC survival. It is that "
 "**the same 91 genes, fitted two ways, produce an over-parameterised 23-gene index and a two-gene index "
 "that is not — compression is free in the discovery data — yet the compressed score still fails to "
 "transport to an independent cohort, where it is no better than a random pair of panel genes or a "
 "generic proliferation score.**"),

# ---- T7：Discussion「worked」段删去与 §3.3 重复的一句 ----
("With 23 coefficients on 129 deaths the EPV ratio was 5.6, half the conventional threshold [29,30], and "
 "no coefficient was individually significant, so the fitted weights carry no interpretable biology.",
 "With 23 coefficients on 129 deaths the EPV ratio was 5.6, half the conventional threshold [29,30], and "
 "no coefficient was individually significant."),

# ---- T8：Discussion 两点微删 ----
("yet the frozen score landed at the 47th percentile of the null externally, because resampling measures "
 "the stability of a choice within a dataset, not its validity outside one.",
 "yet the frozen score landed at the 47th percentile of the null externally: resampling measures the "
 "stability of a choice within a dataset, not its validity outside one."),

# ---- T9：Limitations 微删 ----
("a human bulk tumour target, neither retained gene a pathway executioner, and differing aetiology, "
 "follow-up structure and platform; we cannot separate those explanations.",
 "a human bulk tumour target, neither retained gene a pathway executioner, differing aetiology and "
 "platform; we cannot separate those explanations."),

("We likewise omit any drug-sensitivity analysis (GDSC/CTRP), since cell-line pharmacogenomic resources "
 "are not patient-matched to these cohorts and predicted IC₅₀ values are extrapolation rather than "
 "observation.",
 "We likewise omit any drug-sensitivity analysis (GDSC/CTRP): cell-line pharmacogenomic resources are "
 "not patient-matched to these cohorts, so predicted IC₅₀ values are extrapolation, not observation."),
]

W = lambda x: len([w for w in x.split() if re.search(r"[A-Za-z0-9]", w)])
body = lambda t: t.split("## 1. Introduction")[1].split("## Declarations")[0]
abst = lambda t: t.split("## Abstract")[1].split("**Keywords")[0]

# 有意替换的数字：新值必须能在一次实跑产物中找到出处；旧值的消失需在 compress_gate 中核销。
NEW_OK = {"0.081"}      # = nested_pooled.json 的 optimism.MRG2.diff（0.0811）
DROP_OK = {"0.10"}      # §4 的 "about 0.10 units of optimism" 被实测 0.081 取代

b0, a0 = W(body(s)), W(abst(s))
dropped = set()
for old, new in EDITS:
    n = s.count(old)
    assert n == 1, "命中 %d 次（应为 1）：\n%r" % (n, old[:100])
    d_old = set(re.findall(r"\d+(?:\.\d+)?", old))
    d_new = set(re.findall(r"\d+(?:\.\d+)?", new))
    surplus = d_new - d_old - NEW_OK
    assert not surplus, "引入了原本没有且未登记的数字：%s" % surplus
    dropped |= (d_old - d_new)

out = s
for old, new in EDITS:
    out = out.replace(old, new, 1)

# 被删数字必须在文档他处仍出现（DROP_OK 除外，那是有意替换）
missing = sorted(d for d in dropped if d not in out and d not in DROP_OK)
assert not missing, "以下数字在被删片段之外不再出现（会触发闸门判据 A）：%s" % missing
print("被删片段涉及的数字（均在他处保留）：", ", ".join(sorted(dropped - DROP_OK)) or "（无）")
print("有意替换、需闸门核销的数字：", ", ".join(sorted(d for d in dropped if d in DROP_OK)) or "（无）",
      "->", ", ".join(sorted(NEW_OK)))

b1, a1 = W(body(out)), W(abst(out))
print("正文 IMRaD : %d -> %d  (-%d)" % (b0, b1, b0 - b1))
print("摘要       : %d -> %d  (-%d)" % (a0, a1, a0 - a1))
assert b1 < 6000, "正文仍超限：%d" % b1
assert a1 < 300, "摘要仍超限：%d" % a1
open(P, "w", encoding="utf-8").write(out)
print("✅ 已落盘，两项均在限内（正文余量 %d 词）" % (6000 - b1))
