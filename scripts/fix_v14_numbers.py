#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_v14_numbers.py —— v1.4 初稿中"写的时候用的估算值"改为**实算值**

背景（这是本次修订最该被记住的一条）
------------------------------------
v1.4 初稿是先写文字、后补核对，其中 Table 5 的敏感性行、Table 7 的 BH q 列、
§3.1 的 BY 结论都是**按印象填的**，落盘后逐项复算才发现有 4 类错误：

  1. Table 5 表头写 "n = 337, 122 deaths" —— 完整病例实际死亡 **115**，不是 122。
  2. Table 5 敏感性行的 HR/CI 有 6 处小数位与实算不符（如 1.660→1.658,
     2.028→2.024, 3.5×10⁻⁷→3.8×10⁻⁷, 4.9×10⁻⁵→4.2×10⁻⁵）。
  3. Table 7 的 BH q 列有 9 处错误（BAP1 0.420→0.371, KEAP1 0.602→0.516,
     PIK3CA 0.674→0.759, ALB 0.851→1.000 等）。
  4. §3.1 写 "none of the 23 survives BY, smallest 0.021" —— 实算 **MAFG 与 KIF15
     都通过 BY（q = 0.0116）**，最小值不是 0.021。

教训：任何 q 值/CI 都必须在**同一脚本内由 p 值实算**，不得由印象填写。
本脚本只做这 4 类数值订正，不碰其他文字；每处断言唯一命中。
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
F = os.path.join(ROOT, "学生3_LIHC_MRG预后_SCI稿件_v1.4.md")
src = open(F, encoding="utf-8").read()
R = []

# ---- 1. Table 5 表头：事件数
R.append((
    "T5 表头事件数",
    "(n = 337, 122 deaths)",
    "(n = 337, 115 deaths)",
))

# ---- 2. Table 5 主口径两行小数位
R.append((
    "T5 主口径 score 行",
    "| MRG-2 | Score (per SD) | 1.651 | 1.339–2.037 | 2.8×10⁻⁶ |",
    "| MRG-2 | Score (per SD) | 1.650 | 1.338–2.035 | 2.8×10⁻⁶ |",
))
R.append((
    "T5 主口径 Model A score 行",
    "| Model A | Score (per SD) | 1.882 | 1.521–2.328 | 5.6×10⁻⁹ |",
    "| Model A | Score (per SD) | 1.880 | 1.521–2.325 | 5.6×10⁻⁹ |",
))

# ---- 3. Table 5 敏感性两档（实算值）
R.append((
    "T5 缺失→0 档",
    "| MRG-2 | Score (per SD) | 1.660 | 1.358–2.028 | 6.6×10⁻⁷ |\n"
    "| MRG-2 | Stage III–IV | 2.019 | 1.401–2.910 | 1.6×10⁻⁴ |\n"
    "| Model A | Score (per SD) | 1.936 | 1.580–2.371 | 1.7×10⁻¹⁰ |\n"
    "| Model A | Stage III–IV | 1.805 | 1.250–2.605 | 1.6×10⁻³ |",
    "| MRG-2 | Score (per SD) | 1.658 | 1.359–2.024 | 6.6×10⁻⁷ |\n"
    "| MRG-2 | Stage III–IV | 2.019 | 1.401–2.910 | 1.6×10⁻⁴ |\n"
    "| Model A | Score (per SD) | 1.934 | 1.580–2.368 | 1.7×10⁻¹⁰ |\n"
    "| Model A | Stage III–IV | 1.805 | 1.250–2.605 | 1.6×10⁻³ |",
))
R.append((
    "T5 缺失+指示变量档",
    "| MRG-2 | Score (per SD) | 1.684 | 1.377–2.059 | 3.5×10⁻⁷ |\n"
    "| MRG-2 | Stage III–IV | 2.196 | 1.502–3.210 | 4.9×10⁻⁵ |\n"
    "| Model A | Score (per SD) | 1.937 | 1.581–2.373 | 1.7×10⁻¹⁰ |\n"
    "| Model A | Stage III–IV | 1.966 | 1.346–2.871 | 5.2×10⁻⁴ |",
    "| MRG-2 | Score (per SD) | 1.683 | 1.377–2.058 | 3.8×10⁻⁷ |\n"
    "| MRG-2 | Stage III–IV | 2.196 | 1.507–3.201 | 4.2×10⁻⁵ |\n"
    "| Model A | Score (per SD) | 1.935 | 1.580–2.371 | 1.8×10⁻¹⁰ |\n"
    "| Model A | Stage III–IV | 1.966 | 1.346–2.871 | 4.7×10⁻⁴ |",
))

# ---- 4. §3.4 敏感性小结表：缺失+指示变量一档的 P
R.append((
    "§3.4 表",
    "| Missing → 0 + missingness indicator (sensitivity) | 360 | 1.68 (*P* = 9.4×10⁻⁷) | 2.20 |",
    "| Missing → 0 + missingness indicator (sensitivity) | 360 | 1.68 (*P* = 3.8×10⁻⁷) | 2.20 |",
))

# ---- 5. §3.1 BY 结论（原为印象填写，实算后改写）
R.append((
    "§3.1 BY",
    "and none of the 23 survives the dependency-robust Benjamini–Yekutieli procedure, "
    "under which the smallest adjusted value is 0.021 for MAFG and the largest of the 23 "
    "is 0.79. The count of five is therefore sensitive to the correlation structure of the panel",
    "Two of the 23 also survive the dependency-robust Benjamini–Yekutieli procedure "
    "(MAFG and KIF15, both q = 0.012); TXNRD1 is the next closest at q = 0.064, and the "
    "adjusted value for the weakest of the 23 raw hits is 1.00. The count of five is "
    "therefore sensitive to the correlation structure of the panel",
))

# ---- 6. Table 7 的 BH q 列（实算）
R.append((
    "T7 q 列",
    "| RB1 | 15 (8.3) | 4 (2.2) | 0.016 | 0.085 |\n"
    "| BAP1 | 6 (3.3) | 14 (7.8) | 0.105 | 0.420 |\n"
    "| AXIN1 | 8 (4.4) | 16 (8.9) | 0.138 | 0.442 |\n"
    "| TSC2 | 9 (5.0) | 3 (1.7) | 0.139 | 0.442 |\n"
    "| KEAP1 | 12 (6.7) | 6 (3.3) | 0.226 | 0.602 |\n"
    "| PIK3CA | 4 (2.2) | 8 (4.4) | 0.379 | 0.674 |\n"
    "| TSC1 | 5 (2.8) | 2 (1.1) | 0.449 | 0.718 |\n"
    "| ALB | 20 (11.1) | 24 (13.3) | 0.630 | 0.851 |\n"
    "| ARID1A | 15 (8.3) | 12 (6.7) | 0.690 | 0.851 |\n"
    "| APOB | 18 (10.0) | 16 (8.9) | 0.857 | 0.951 |\n"
    "| TTN | 46 (25.6) | 48 (26.7) | 0.905 | 0.951 |",
    "| RB1 | 15 (8.3) | 4 (2.2) | 0.016 | 0.087 |\n"
    "| BAP1 | 6 (3.3) | 14 (7.8) | 0.105 | 0.371 |\n"
    "| AXIN1 | 8 (4.4) | 16 (8.9) | 0.138 | 0.371 |\n"
    "| TSC2 | 9 (5.0) | 3 (1.7) | 0.139 | 0.371 |\n"
    "| KEAP1 | 12 (6.7) | 6 (3.3) | 0.226 | 0.516 |\n"
    "| PIK3CA | 4 (2.2) | 8 (4.4) | 0.379 | 0.759 |\n"
    "| TSC1 | 5 (2.8) | 2 (1.1) | 0.449 | 0.797 |\n"
    "| ALB | 20 (11.1) | 24 (13.3) | 0.630 | 1.000 |\n"
    "| ARID1A | 15 (8.3) | 12 (6.7) | 0.690 | 1.000 |\n"
    "| APOB | 18 (10.0) | 16 (8.9) | 0.857 | 1.000 |\n"
    "| TTN | 46 (25.6) | 48 (26.7) | 0.905 | 1.000 |",
))

# ---- 7. §3.9 正文中的 RB1 q
R.append((
    "§3.9 RB1 q",
    "RB1 (8.3% vs 2.2%, *P* = 0.016, q = 0.085)",
    "RB1 (8.3% vs 2.2%, *P* = 0.016, q = 0.087)",
))

for tag, old, new in R:
    n = src.count(old)
    if n != 1:
        sys.exit(f"❌ [{tag}] 命中 {n} 次（应为 1），未写出任何文件。\n--- 片段 ---\n{old}")
    src = src.replace(old, new)
    print(f"  ✅ [{tag}] 唯一命中")

shutil.copy2(F, F + ".bak_prefix")
open(F, "w", encoding="utf-8").write(src)
print("  → 已订正 v1.4（备份 .bak_prefix）")
