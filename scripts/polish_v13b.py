#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
polish_v13b.py —— 第二轮句级润色（v1.3 -> v1.3，就地）

第一轮复测后仍剩两项：
  · `because` 7 次 = 2.81/百句，顶词占比 16.7%（D-36 分布层上限 12%）
  · 连接词种类 18 vs 真人 40（过渡手段单一，属分布性单调）

本轮只做 6 处，目标：because -> 5（2.02/百句，占比 11.9%），
                     种类 18 -> 21。数值一律不动。
"""
import sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.3.md")

R = [
# because -> 冒号（真人语料含冒号句 19.5%，本稿 14.1%，有空间）
("G1", "because",
 "Ethics approval was not required because all data are de-identified and publicly available.",
 "Ethics approval was not required: all data are de-identified and publicly available."),

("G2", "because",
 "A GEPIA2-style cross-database comparison was rejected because it would mix differences in RNA source, library preparation and processing pipeline into the contrast.",
 "A GEPIA2-style cross-database comparison was rejected: it would mix differences in RNA source, library preparation and processing pipeline into the contrast."),

# because -> since（真人 has since 0.08/百句；同时切分 35 词长句）
("G3", "since",
 "C-index differences were tested by a *paired* bootstrap over patients (2,000 resamples) rather than by comparing independent intervals, because both scores are computed on the same patients.",
 "C-index differences were tested by a *paired* bootstrap over patients (2,000 resamples) rather than by comparing independent intervals, since both scores are computed on the same patients."),

# additionally -> in addition（新增种类），同时切分长句
("G4", "in addition",
 "Because a bootstrap threshold is seed-dependent, the 200-resample step was repeated under ten independent seeds, and the threshold was additionally varied over π = 0.60, 0.65, 0.70, 0.75, 0.80 and 0.85 at the primary seed.",
 "Because a bootstrap threshold is seed-dependent, the 200-resample step was repeated under ten independent seeds. In addition, the threshold was varied over π = 0.60, 0.65, 0.70, 0.75, 0.80 and 0.85 at the primary seed."),

# 新增 notably（真人 0.41/百句）
("G5", "notably",
 "Three of the five corrected hits are redox rather than cell-cycle genes:",
 "Notably, three of the five corrected hits are redox rather than cell-cycle genes:"),

# 新增 consequently（真人 0.08/百句）：承接前一句的因果，替代口语化 so
("G6", "consequently",
 "It ranked patients acceptably — median survival 80.7 versus 35.8 months — by distributing a shared signal across collinear terms, so compression was not an aesthetic preference.",
 "It ranked patients acceptably — median survival 80.7 versus 35.8 months — by distributing a shared signal across collinear terms; consequently, compression was not an aesthetic preference."),
]

def main():
    t = open(F, encoding="utf-8").read()
    fail = []
    for tag, cat, old, new in R:
        c = t.count(old)
        if c != 1:
            fail.append(f"  ✗ {tag} [{cat}] 命中 {c} 次（须为 1）：{old[:70]}…")
            continue
        t = t.replace(old, new)
        print(f"  ✓ {tag} [{cat}]")
    if fail:
        print("❌ 未写出：\n" + "\n".join(fail)); sys.exit(1)
    open(F, "w", encoding="utf-8").write(t)
    print(f"✅ 6 处替换全部唯一命中，已就地写回 {os.path.basename(F)}")

if __name__ == "__main__":
    main()
