#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v1.6 -> v1.7 盲审逐条回复表：只更新「摘要词数 / 关键词数」这类台账数字，并追加第四轮说明。
评审意见与处置结论一字未动。"""
import os, re
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "历史版本_v1.0", "第四轮_v1.7", "逐条回复表_v1.6.md")
DST = os.path.join(BASE, "盲审", "逐条回复表_v1.7.md")

EDITS = [
 ("摘要现 **296 词**（纯散文，Word 口径；为 6,000/300 双限留出余量）",
  "摘要现 **238 词**（纯散文，Word 口径；对齐首选刊 DDS 的 `no more than 250 words` 硬限，余量 12 词）"),
 ("摘要 **296 词**，主句落在", "摘要 **238 词**，主句落在"),
 ("| 摘要（纯散文） | < 300 词 | **296** | ✅ |",
  "| 摘要（纯散文） | ≤ 250 词（DDS Original Article） | **238** | ✅ |\n"
  "| 关键词 | 4–6 个（DDS）／≤ 5 个（sir 规则） | **5** | ✅ |"),
 ("摘要 296（余量 4 词）", "摘要 238（余量 12 词）"),
]

TAIL = """

---

## 附：第四轮修订说明（v1.6 → v1.7）——本轮只做了一件事

**本轮唯一的改动，是补齐两条此前三轮审核都漏检的投稿硬限。正文（`## 1. Introduction` 起）逐字节未动。**

| 项 | 改前（v1.6） | 改后（v1.7） | 依据 |
|---|---|---|---|
| 摘要 | **296 词** | **238 词**（−58） | DDS *Instructions for Authors*：Original Article 结构化摘要 `no more than 250 words` |
| 关键词 | **8 个** | **5 个** | DDS `four to six keywords`；同时满足 sir 的「关键词 ≤5」硬规则 |

### 为什么会在第四轮才被发现

前三轮审核（全文逻辑审核、SCI-writing-VIP 润色、三位审稿人盲审）都只检查**稿内一致性**，
没有一条判据去**联网核对目标刊的投稿硬限**。摘要 296 词是照「< 300」这条自设口径写定的，
关键词 8 个从未与任何一条规则比对。这与学生 2（KIRC）那篇「摘要 1424 词」属同一类漏检：
**自设口径 ≠ 期刊口径**。已作为本轮的技术教训记入交付说明。

### 摘要压缩的代价与处置

摘要压到 250 词，必然要移出若干**只在摘要里做冗余复述**的数值与一处摘要内引文。
处置口径（逐条留痕于 `分析脚本/摘要压缩豁免_v1.7.json`，13 条）：

1. 被移出的数值（GSE76427 的 n 与 23 例死亡、两个 `×10⁻⁶`、三个 π 区间端点、第二个 95% CI 等）
   **正文、图注或补充材料中均完整保留**，全稿层面**零数值丢失** —— `compress_gate.py` 判据 A 通过。
2. 摘要内引文 `[21]` 依 DDS「abstract 不得使用文献引用」删除；该文献在 §1 与 §4 均已引用，
   **编号与参考文献表完全不变**（`ref_audit_v15.py`：41 条双源核验，问题 0）。
3. 为让上述豁免**可审计而非绕开闸门**，`数值指纹.py` 新增 `--waiver <json>` 入口，
   逐条打印被豁免的 token 及其去向；不带 `--waiver` 时行为与原来完全一致（严格模式）。
4. 关键词删到 5 个时移除了 `KIF15`——该基因符号在摘要与正文 §3.1/§3.3 均出现，检索不受影响。

### 尚未处理（须 sir 拍板）

DDS 另有两条本轮**未动**的规范，因为它们涉及标题本身，属于 sir 的决策范围：

- DDS 明文 `Do not use abbreviations in titles`，而现题名末词为 `HCC`。
  改成 `hepatocellular carcinoma` 后题名将达 121 字符（不计空格），**超出 DDS 的 120 字符上限 1 个**，
  需要同时微调题面（例如把 `mitoxyperilysis-related` 缩短为 `mitoxyperilysis`，可降至 113 字符）。
- 其余候选刊（CTO 3000 词/6 项、Biochemical Genetics、HBPD INT）的篇幅与结构要求见《择刊测评报告》。
"""

s = open(SRC, encoding="utf-8").read()
for old, new in EDITS:
    n = s.count(old)
    assert n == 1, "命中 %d 次（应为 1）：%r" % (n, old[:60])
    s = s.replace(old, new, 1)
# 断言必须放在追加「历史对照」段之前 —— 该段本来就含 296->238 的对照
for bad in ["**296 词**", "| **296** |", "摘要 296", "< 300 词"]:
    assert bad not in s, "仍有残留台账 %r" % bad
s = s.rstrip() + TAIL
assert "**238 词**" in s
open(DST, "w", encoding="utf-8").write(s)
print("已落盘 盲审/逐条回复表_v1.7.md  %d 字节" % os.path.getsize(DST))
