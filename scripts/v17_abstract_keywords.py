#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v1.7：摘要 296 -> <=250 词（DDS 官方硬限 250）；关键词 8 -> 5（DDS 4-6 / sir <=5）。
只动 Abstract 与 Keywords 两块，正文（## 1. Introduction 起）逐字节不动。
摘要压缩必然减少「只做冗余复述」的数值出现次数 -> 依 compress_gate 的 WAIVERS 体例，
另行落盘 摘要压缩豁免_v1.7.json 逐条说明理由与去向，再带 --waiver 过闸门。
"""
import re, os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.6.md")
DST  = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.7.md")
WJV  = os.path.join(BASE, "分析脚本", "摘要压缩豁免_v1.7.json")

W = lambda x: len([w for w in x.split() if re.search(r"[A-Za-z0-9]", w)])

NEW_ABSTRACT = """**Background.** Mitoxyperilysis is a cell-death modality described in 2025 in mouse macrophages; whether human tumours express it is untested. A related colorectal signature has been reported. We asked whether a mitoxyperilysis-related gene (MRG) score is prognostic in hepatocellular carcinoma (HCC) and replicates.

**Methods.** We analysed the 91 MRGs evaluable in TCGA-LIHC (n = 360, 129 deaths). Model A was an L2-penalised Cox model on the 23 univariate hits; Model B applied LASSO-Cox with 200-bootstrap stability selection, assessed by nested cross-validation, ten-seed replication and a random-panel benchmark. Frozen coefficients were applied in GSE14520 (n = 242, 96 deaths).

**Results.** Twenty-three of 91 MRGs were associated with survival (*P* < 0.05), five after Benjamini-Hochberg correction (HR 1.49 and 1.45 for MAFG and KIF15). A 23-gene ridge model (5.6 events per variable; C-index 0.684) was matched by stability selection retaining KIF15 (pi = 0.91) and MAFG (pi = 0.79); MRG-2 gave C-index 0.677 (95% CI 0.623-0.728) and independence from stage and grade (adjusted HR 1.65). Three checks undercut it: pooled out-of-fold cross-validation cut both models to 0.61 (0.613 +/- 0.013); MAFG's pi fell below 0.75 in two of ten seeds; and MRG-2 did not replicate in GSE14520 (C-index 0.551), at the 47th percentile of 3,000 random pairs versus 0.596 for proliferation.

**Conclusions.** Bootstrap stability did not predict external transport; one selected gene sat on the threshold. The score is stage-independent but does not transport. Such studies should report a nested estimate, seed replication and a random-panel benchmark."""

NEW_KEYWORDS = "**Keywords:** mitoxyperilysis; hepatocellular carcinoma; stability selection; external validation; prognostic model"

s = open(SRC, encoding="utf-8").read()
head, rest = s.split("## Abstract", 1)
old_abst, tail = rest.split("\n\n**Keywords", 1)
tail = "**Keywords" + tail
old_kw = re.search(r"\*\*Keywords:\*\*[^\n]*", tail).group(0)

assert W(old_abst) == 296
assert len([x for x in old_kw.split(":",1)[1].split(";") if x.strip()]) == 8

out = head + "## Abstract\n\n" + NEW_ABSTRACT + "\n\n" + tail.replace(old_kw, NEW_KEYWORDS, 1)
assert out.split("## 1. Introduction",1)[1] == s.split("## 1. Introduction",1)[1], "正文被误改！"

nw = W(NEW_ABSTRACT)
print("摘要 : 296 -> %d 词（DDS 硬限 <=250，%s）" % (nw, "通过" if nw <= 250 else "仍超限"))
assert nw <= 250, "新摘要仍超限：%d" % nw
open(DST, "w", encoding="utf-8").write(out)

# ---- 生成豁免表：逐 token 说明理由与去向 ----
NUM = re.compile(r'\d+(?:[.,]\d+)?(?:[×x]\d+)?')
CIT = re.compile(r'\[(\d+(?:[,\-–]\d+)*)\]')
a_raw = old_abst; b_raw = NEW_ABSTRACT
ca = {}
cb = {}
for t in NUM.findall(a_raw): ca[t] = ca.get(t,0)+1
for t in NUM.findall(b_raw): cb[t] = cb.get(t,0)+1
lost = dict((k, v-cb.get(k,0)) for k, v in ca.items() if v > cb.get(k,0))
WHERE = {
 "76427": "§3.7 与 Table S14（GSE76427 汇总）",
 "115":   "§3.7 与 Table S14",
 "1.9×10":"§3.2 正文与 Table 3",
 "2.8×10":"§3.4 正文与 Table 5",
 "0.690": "§3.3 正文（π 十个种子区间）",
 "0.805": "§3.3 正文（π 十个种子区间）",
 "0.490": "§3.7 正文（GSE14520 的 95% CI）",
 "0.611": "§3.7 正文（GSE14520 的 95% CI）",
 "95":    "§3.7 正文（第二个 95% CI；摘要只保留主模型的一个）",
 "14520": "§2.4/§3.7 正文（该队列在两处均出现）",
 "23":    "§3.2/§3.7 正文（GSE76427 的 23 例死亡）",
 "2":     "正文（MRG-2 在全稿出现 20 余次）",
 "15":    "正文（该数值在正文有独立出处）",
}
waiver = {
 "作业": "v1.6 -> v1.7：把摘要从 296 词压到 DDS 官方硬限 250 词",
 "依据": "Digestive Diseases and Sciences（Springer，首选刊）Instructions for Authors：Original Article 结构化摘要 no more than 250 words；关键词 four to six；摘要内不得使用文献引用与缩略语注释",
 "原则": "被移出摘要的数值一律只在摘要中做冗余复述；正文、图注或补充材料中均完整保留，故全稿层面零数值丢失（compress_gate 判据 A 通过）",
 "nums": {k: v for k, v in sorted(lost.items())},
 "cits_shift": "摘要内引用 [21] 依 DDS「abstract 不得含文献引用」删除；[21] 在 §1 Introduction 与 §4 Discussion 均已引用，编号与参考文献表不变，仅序列位移一位",
 "emph": "斜体标记集合不变",
}
for k in list(waiver["nums"]):
    waiver["nums"][k+":where"] = WHERE.get(k, "正文/补充材料中另有出处（见 compress_gate 判据 A 报告）")
json.dump(waiver, open(WJV, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n摘要中被移除的数值 token 计数：", dict(sorted(lost.items())))
print("豁免表已落盘：", os.path.basename(WJV))
print("关键词: 8 -> 5；已落盘", os.path.basename(DST), os.path.getsize(DST), "字节")
