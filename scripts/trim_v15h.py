# -*- coding: utf-8 -*-
"""v1.5 收尾压缩：仅删散文，不触碰任何数字/编号。
闸门后置：compress_gate.py 必须仍通过（无唯一数值丢失、无凭空新增）。"""
import re, sys, os

P = "学生3_LIHC_MRG预后_SCI稿件_v1.6.md"
src = open(P, encoding="utf-8").read()

EDITS = [
 # ---- 摘要（-11）----
 ("were associated with overall survival at *P* < 0.05 and five after Benjamini–Hochberg correction",
  "were associated with overall survival at *P* < 0.05, five after Benjamini–Hochberg correction"),
 ("A 23-gene ridge model (5.6 events per variable, no significant coefficient; log-rank",
  "A 23-gene ridge model (5.6 events per variable; log-rank"),
 ("and MAFG (π = 0.79): MRG-2, at 64.5 events per variable, gave C-index 0.677",
  "and MAFG (π = 0.79); MRG-2 gave C-index 0.677"),
 ("(adjusted HR 1.65 per SD, *P* = 2.8×10⁻⁶)", "(adjusted HR 1.65, *P* = 2.8×10⁻⁶)"),
 # ---- 正文 ----
 ("shared across the two studies but applied here to different patients, endpoints and tumour type.",
  "applied here to different patients, endpoints and tumour type."),
 ("having independently been linked to mitochondrial fission",
  "independently linked to mitochondrial fission"),
 ("[28]. Full definitions are in Supplementary Methods.",
  "[28]; definitions are in Supplementary Methods."),
 ("Both gene sets were obtained before the external cohorts were opened;",
  "Both gene sets predate the external cohorts;"),
 ("does anything an arbitrary pair of panel genes would not,",
  "does anything an arbitrary pair would not,"),
 ("Two features of this list are worth recording.", "Two features are worth recording."),
 ("**A model in that condition can still rank patients acceptably; it is simply not estimating biology** — the whole of the case for compression.",
  "**A model in that condition can still rank patients acceptably; it is simply not estimating biology.**"),
 ("Two properties of Model A motivate everything that follows. With 129 deaths",
  "With 129 deaths"),
 ("simply the first death after which neither curve recovers",
  "the first death after which neither curve recovers"),
 ("The result does hinge on the prespecified value to a degree we did not anticipate.",
  "The result hinges on the prespecified value more than we anticipated."),
 ("makes any comparison uninformative rather than merely non-significant (Section 2.6).",
  "makes any comparison uninformative (Section 2.6)."),
 ("and Section 3.7 shows this did not survive external testing.",
  "and it did not survive external testing."),
 ("Two further comparisons sharpen the failure.", "Two comparisons sharpen the failure."),
 ("monotone, and the clearest single result of this study (Figure 5).",
  "monotone, and the clearest result of this study (Figure 5)."),
 ("Ninth, no prospective or decision-impact analysis was performed and no clinical utility is claimed:",
  "Ninth, no prospective or decision-impact analysis was performed:"),
 ("The full-panel index was the natural first attempt — 23 univariate hits, a ridge penalty for collinearity, an apparent C-index of 0.684 —",
  "The full-panel index was the natural first attempt — 23 univariate hits, a ridge penalty for collinearity, apparent C-index 0.684 —"),
]

W = lambda x: len([w for w in x.split() if re.search(r"[A-Za-z0-9]", w)])
def body(t):
    return t.split("## 1. Introduction")[1].split("## Declarations")[0]
def abstract(t):
    a = t.split("## Abstract")[1].split("**Keywords")[0]
    return a

# 断言：每条 old 唯一命中，且 old/new 的数字集合完全相同
dropped = set()
for old, new in EDITS:
    n = src.count(old)
    assert n == 1, f"命中 {n} 次（应为 1）：{old[:60]!r}"
    d_old, d_new = set(re.findall(r"\d", old)), set(re.findall(r"\d", new))
    assert d_new <= d_old, f"引入了原本没有的数字：{old[:50]!r} -> {new[:50]!r}"
    dropped |= (d_old - d_new)

b0, a0 = W(body(src)), W(abstract(src))
out = src
for old, new in EDITS:
    out = out.replace(old, new, 1)
b1, a1 = W(body(out)), W(abstract(out))

print(f"正文 IMRaD : {b0} -> {b1}   (-{b0-b1})")
print(f"摘要（纯散文）: {a0} -> {a1}   (-{a0-a1})")
assert b1 < 6000, f"正文仍超限：{b1}"
assert a1 < 300, f"摘要仍超限：{a1}"
# 被删数字必须在文中他处仍出现（对应闸门 A：无唯一数值丢失）
missing = [d for d in sorted(dropped) if d not in out]
assert not missing, f"以下数字在被删片段之外不再出现：{missing}"
print("被删片段涉及的数字（均在他处保留）:", "".join(sorted(dropped)))
open(P, "w", encoding="utf-8").write(out)
print("✅ 已落盘，且两项均在限内")
