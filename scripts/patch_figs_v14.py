#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_figs_v14.py —— 按盲审意见修补 fig_v2_panels.py（v1.3 图 → v1.4 图）

对应条目
--------
R3-m3  Figure 2C 对数横轴刻度标注不规范（6×10⁻¹ / 10⁰ / 2×10⁰）→ 改 0.5/0.75/1/1.5/2
R3-m7  Figure 1A 对数横轴仅 1 个刻度（10⁰）→ 补 0.8/0.9/1.0/1.25/1.5
R3-m6  Figure 1D / 3C / 5A 横轴画到 80 月，at-risk 表止于 60 月 → 横轴统一截到 60 月
R3-m4  Figure 5B / 5C 缺面板级图例 → 补面板图例
R1-m2  Figure 2C 标题 n=360 → 主口径 n=337

每处替换均断言唯一命中，命中不到即退出，不写出任何文件。
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "fig_v2_panels.py")

src = open(F, encoding="utf-8").read()
orig = src

R = []

# ---- R3-m7：Figure 1A 对数横轴补刻度
R.append((
    "R3-m7",
    '    ax.set_xscale("log"); ax.set_xlabel("Hazard ratio per SD (95% CI)")\n'
    '    ax.set_ylim(-0.8, len(sig) - 0.2)',
    '    ax.set_xscale("log"); ax.set_xlabel("Hazard ratio per SD (95% CI)")\n'
    '    # R3-m7：对数横轴只落 1 个主刻度（10⁰ → "1"），HR 点只能靠目测估读。\n'
    '    # 改为显式给出可读的小数刻度，并关掉次刻度，避免回落成 6×10⁻¹ 形态。\n'
    '    ax.set_xticks([0.8, 0.9, 1.0, 1.25, 1.5])\n'
    '    ax.set_xticklabels(["0.8", "0.9", "1.0", "1.25", "1.5"])\n'
    '    ax.xaxis.set_minor_locator(NullLocator())\n'
    '    ax.set_ylim(-0.8, len(sig) - 0.2)',
))

# ---- R3-m3 + R1-m2：Figure 2C 对数横轴刻度 + 标题 n
R.append((
    "R3-m3",
    '    ax.set_xscale("log"); ax.set_xlabel("Hazard ratio (95% CI)")\n'
    '    ax.set_title("Model A, multivariable (n = 360)", loc="left", pad=3, fontweight="bold")',
    '    ax.set_xscale("log"); ax.set_xlabel("Hazard ratio (95% CI)")\n'
    '    # R3-m3：森林图惯例刻度为 0.5/1/2，不写 6×10⁻¹ / 2×10⁰ 这类科学记数。\n'
    '    ax.set_xticks([0.5, 0.75, 1.0, 1.5, 2.0, 3.0])\n'
    '    ax.set_xticklabels(["0.5", "0.75", "1.0", "1.5", "2.0", "3.0"])\n'
    '    ax.xaxis.set_minor_locator(NullLocator())\n'
    '    # R1-m2：主口径改为完整病例 n=337（见 §2.7），标题随之更新。\n'
    '    ax.set_title(f"Model A, multivariable (n = {int(sub[\'n\'].iloc[0])})", '
    'loc="left", pad=3, fontweight="bold")',
))

# ---- R3-m6：三张 KM 图横轴截到 60 月，与 at-risk 表对齐
for tag, anchor in [
    ("R3-m6/fig1D",
     '    ax.set_title(f"Model A Kaplan–Meier, log-rank P = {res[\'modelA\'][\'logrank_p\']:.1e}",'),
    ("R3-m6/fig3C",
     '    ax.set_title(f"MRG-2 Kaplan–Meier, log-rank P = {res[\'modelB\'][\'logrank_p\']:.1e}",'),
]:
    R.append((
        tag,
        '    ax.set_xlim(0, 80); ax.set_ylim(0, 1.02)\n'
        '    ax.legend(frameon=False, loc="upper right", fontsize=5.5)\n'
        + anchor,
        '    # R3-m6：横轴原先画到 80 月，而 at-risk 表止于 60 月，末段曲线无 at-risk 支撑。\n'
        '    # 统一截到 60 月，使横轴与 at-risk 表逐点对齐。\n'
        '    ax.set_xlim(0, 60); ax.set_ylim(0, 1.02)\n'
        '    ax.legend(frameon=False, loc="upper right", fontsize=5.5)\n'
        + anchor,
    ))

# ---- R3-m6：Figure 5A 外部 KM
R.append((
    "R3-m6/fig5A",
    '    ax.set_xlim(0, 80); ax.set_ylim(0, 1.02)\n'
    '    ax.legend(frameon=False, loc="upper right", fontsize=5.5)\n'
    '    ax.set_title(f"GSE14520, MRG-2 (C = {ext[\'ModelB\'][\'c_index\']:.3f}, P = {ext[\'ModelB\'][\'p\']:.2f})",',
    '    # R3-m6：同 Figure 1D/3C，横轴截到 60 月与 at-risk 表对齐。\n'
    '    ax.set_xlim(0, 60); ax.set_ylim(0, 1.02)\n'
    '    ax.legend(frameon=False, loc="upper right", fontsize=5.5)\n'
    '    ax.set_title(f"GSE14520, MRG-2 (C = {ext[\'ModelB\'][\'c_index\']:.3f}, P = {ext[\'ModelB\'][\'p\']:.2f})",',
))

# ---- R3-m4：Figure 5B 补面板级图例
R.append((
    "R3-m4/fig5B",
    '    ax.set_ylabel("Harrell\'s C-index"); ax.set_ylim(0.5, 0.75)\n'
    '    ax.set_title("Discrimination across estimates", loc="left", pad=3, fontweight="bold")',
    '    ax.set_ylabel("Harrell\'s C-index"); ax.set_ylim(0.5, 0.75)\n'
    '    # R3-m4：补面板级图例，使面板脱离图注也能读懂四种估计来源。\n'
    '    ax.legend(handles=[Patch(color=GREY, label="Apparent"),\n'
    '                       Patch(color=BLUE, label="Nested 10-fold"),\n'
    '                       Patch(color=RED, label="External (GSE14520)"),\n'
    '                       Patch(color=ORANGE, label="Proliferation")],\n'
    '              loc="lower left", frameon=False, fontsize=5.0, ncol=1,\n'
    '              handlelength=1.0, handletextpad=0.4, borderpad=0.2,\n'
    '              labelspacing=0.25)\n'
    '    ax.set_title("Discrimination across estimates", loc="left", pad=3, fontweight="bold")',
))

# ---- R3-m4：Figure 5C 补面板级图例
R.append((
    "R3-m4/fig5C",
    '    ax.set_xlabel("C-index of a random two-gene panel"); ax.set_ylabel("Density")\n'
    '    ax.set_title("Null distribution, 3,000 random pairs", loc="left", pad=3, fontweight="bold")',
    '    ax.set_xlabel("C-index of a random two-gene panel"); ax.set_ylabel("Density")\n'
    '    # R3-m4：补面板级图例，区分两层零分布。\n'
    '    ax.legend(handles=[Patch(color=BLUE, label="TCGA-LIHC null"),\n'
    '                       Patch(color=RED, label="GSE14520 null")],\n'
    '              loc="upper left", frameon=False, fontsize=5.2,\n'
    '              handlelength=1.0, handletextpad=0.4, borderpad=0.2)\n'
    '    ax.set_title("Null distribution, 3,000 random pairs", loc="left", pad=3, fontweight="bold")',
))

for tag, old, new in R:
    n = src.count(old)
    if n != 1:
        sys.exit(f"❌ [{tag}] 命中 {n} 次（应为 1），未写出任何文件。\n--- 目标片段 ---\n{old}")
    src = src.replace(old, new)
    print(f"  ✅ [{tag}] 唯一命中")

# 需要的 import：NullLocator
if "NullLocator" not in orig.split("\n\n")[0]:
    anchor = "from matplotlib.ticker import"
    if anchor in src:
        line = [l for l in src.split("\n") if l.startswith(anchor)][0]
        if "NullLocator" not in line:
            newline = line.replace(anchor, anchor + " NullLocator,", 1)
            src = src.replace(line, newline, 1)
            print(f"  ✅ [import] 在既有 ticker import 行加入 NullLocator")
    else:
        # 插到第一段 import 之后
        idx = src.find("\n\n")
        src = src[:idx] + "\nfrom matplotlib.ticker import NullLocator" + src[idx:]
        print("  ✅ [import] 新增 NullLocator import 行")

shutil.copy2(F, F + ".bak_v13")
open(F, "w", encoding="utf-8").write(src)
print(f"  → 已写出 {os.path.basename(F)}（备份 .bak_v13）")
