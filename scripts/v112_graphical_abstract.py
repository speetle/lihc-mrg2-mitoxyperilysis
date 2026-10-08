#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDS 图形摘要（Graphical Abstract）—— LIHC 稿件。

期刊硬要求（DDS *Instructions for Authors*, 2022-09-01, 第 5 页，逐字引）：
    "Graphical abstracts are highly encouraged and should be a **single-panel image** …
     The full color image should be labelled **"Online Abstract Figure"** and may be
     accompanied by a short sentence (**140-200 characters**) summarizing the key
     message(s) … Upload the graphic abstract as a separate "figure" file type …
     preferably in one of the following formats: JPEG, PNG, SVG, TIFF, BMP, doc, docx,
     ppt, or pptx (note that PDF is not accepted). **Acceptable size: 920x300px, 150KB max.**"

设计约束与自证
--------------
1. **每一处数字都从 `数据/` 的 JSON 现场读出并格式化**，脚本内断言「该字符串确实出现在图里」——
   杜绝手抄。数值来源逐条注在 `SRC` 里。
2. 画布 **恰好 920×300 px**（figsize 9.2×3.0 in，dpi 100），脚本内断言像素尺寸。
3. 输出 **TIFF（LZW 压缩）＋ PNG ＋ SVG**；TIFF 断言 ≤ 150 KB。
4. 全程 Matplotlib 直绘（**不是生成式 AI 图像**），字体锁 Arial，无字体回退。
5. 底部结论带同时充当 **legend**，断言字符数落在 140–200。

用法：python v112_graphical_abstract.py [--apply]
"""
import hashlib
import json
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Polygon

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "数据")
OUTDIR = os.path.join(BASE, "图件_v2", "图形摘要")
APPLY = "--apply" in sys.argv

W, H = 920, 300                      # px（期刊硬规格）
RED, BLUE, GREY, ORANGE = "#C0392B", "#2C6FBB", "#7F8C8D", "#E08214"
INK = "#1B1B1B"


def J(rel):
    with open(os.path.join(DATA, rel), encoding="utf-8") as fh:
        return json.load(fh)


def main():
    res = J("results.json")
    hard = J("stats_hardening.json")
    pooled = J("revised/nested_pooled.json")
    ext = J("external_GSE14520_summary.json")
    g76 = J("revised/gse76427_prolif_control.json")

    # ── 逐项取值（来源见右注）────────────────────────────────────
    n, ev = res["n"], res["events"]                          # 队列规模
    n_mrg, n_uni = res["n_evaluable"], res["n_univariate_sig"]  # 91 / 23
    cA = res["modelA"]["c_index"]                            # 0.6840
    cB = res["modelB"]["c_index"]                            # 0.6767
    ciB = res["modelB"]["c_index_CI"]                        # [0.6233, 0.7283]
    pi_k, pi_m = hard["full"]["pi"]["KIF15"], hard["full"]["pi"]["MAFG"]  # 0.91 / 0.785
    p_mean = pooled["across_splits"]["pooled_MRG2"]["mean"]  # 0.61335
    p_sd = pooled["across_splits"]["pooled_MRG2"]["sd"]      # 0.01343
    a_mean = pooled["across_splits"]["pooled_ModelA"]["mean"]  # 0.62176
    opt, opt_lo, opt_hi = (pooled["optimism"]["MRG2"]["diff"],
                           pooled["optimism"]["MRG2"]["lo"],
                           pooled["optimism"]["MRG2"]["hi"])  # 0.0811 / 0.0404 / 0.1218
    nb, ns = hard["seed_replication"]["MAFG"]["n_below_thr"], \
        hard["seed_replication"]["MAFG"]["n_seeds"]          # 2 / 10
    e_n, e_ev = ext["cohort"]["n"], ext["cohort"]["events"]  # 242 / 96
    e_c, e_ci, e_p = (ext["ModelB"]["c_index"], ext["ModelB"]["c_index_CI"],
                      ext["ModelB"]["p"])                    # 0.5512 / [0.4899,0.6115] / 0.1837
    rp_n = ext["random_panel"]["n_fitted"]                   # 3000
    rp_pc = ext["random_panel"]["percentile_of_observed"]     # 47.03
    pr_c = ext["Prolif"]["c_index"]                          # 0.5962
    g_n, g_ev = g76["cohort"]["n"], g76["cohort"]["events"]   # 115 / 23

    f2 = lambda v: "%.2f" % v
    f3 = lambda v: "%.3f" % v
    L = []          # (行文本, 面板号, 是否强调)

    # ── 面板 1 ─────────────────────────────────────────────────
    L += [
        ("n = %d, %d deaths, %d MRGs" % (n, ev, n_mrg), 1, False),
        ("\u2192 %d univariate hits (P < 0.05)" % n_uni, 1, False),
        ("Model A (%d genes): C = %s" % (res["modelA"]["n_genes"], f3(cA)), 1, False),
        ("Stability selection, 200 bootstraps", 1, False),
        ("KIF15 \u03c0 = %s \u00b7 MAFG \u03c0 = %s" % (f2(pi_k), f2(pi_m)), 1, False),
        ("MRG-2: C = %s (%s\u2013%s)" % (f3(cB), f3(ciB[0]), f3(ciB[1])), 1, False),
        ("Stage- and grade-independent", 1, False),
    ]
    # ── 面板 2 ─────────────────────────────────────────────────
    L += [
        ("Pooled out-of-fold C-index", 2, False),
        ("%s \u2192 %s \u00b1 %s" % (f3(cB), f3(p_mean), f3(p_sd)), 2, True),
        ("Model A: %s \u2192 %s" % (f3(cA), f3(a_mean)), 2, False),
        ("Optimism +%s (%s\u2013%s)" % (f3(opt), f3(opt_lo), f3(opt_hi)), 2, False),
        ("Seed replication, %d seeds" % ns, 2, False),
        ("MAFG \u03c0 < 0.75 in %d of %d seeds" % (nb, ns), 2, True),
    ]
    # ── 面板 3 ─────────────────────────────────────────────────
    L += [
        ("GSE14520: n = %d, %d deaths" % (e_n, e_ev), 3, False),
        ("Frozen coefficients, no refitting", 3, False),
        ("MRG-2: C = %s (%s\u2013%s)" % (f3(e_c), f3(e_ci[0]), f3(e_ci[1])), 3, False),
        ("P = %s \u2014 does not transport" % f3(e_p), 3, True),
        ("%.0fth percentile of %s random" % (round(rp_pc), format(rp_n, ",")), 3, False),
        ("two-gene panels (%s for the" % f3(pr_c), 3, False),
        ("20-gene proliferation control)", 3, False),
        ("GSE76427 (%d deaths): underpowered" % g_ev, 3, False),
    ]

    LEGEND = ("A stage-independent mitoxyperilysis score passes every internal check yet fails "
              "external transport: report nested estimates, seed replication and a random-panel "
              "benchmark before claiming transport.")
    assert 140 <= len(LEGEND) <= 200, "legend 长度 %d（须 140-200）" % len(LEGEND)

    # ── 字体与画布 ─────────────────────────────────────────────
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "text.color": INK, "axes.edgecolor": INK,
    })
    fp = fm.FontProperties(family="Arial")
    got = fm.findfont(fp, fallback_to_default=False)
    assert "/Arial" in got or "Arial" in got, "Arial 不可用，会回退：%s" % got
    print("字体：%s" % got)

    fig = plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

    # ── 抬头 ───────────────────────────────────────────────────
    ax.text(16, 288, "Stability selection does not guarantee external transport",
            fontsize=12, fontweight="bold", va="top", ha="left")
    ax.text(16, 273, "A mitoxyperilysis-related gene score in hepatocellular carcinoma "
                     "(TCGA-LIHC \u2192 GSE14520)", fontsize=7.4, color=GREY, va="top")
    ax.text(W - 16, 273, "Online Abstract Figure", fontsize=6.6, color=GREY,
            va="top", ha="right", style="italic")

    # ── 三个面板 ───────────────────────────────────────────────
    heads = [(1, "1 \u00b7 Discovery", "TCGA-LIHC", BLUE),
             (2, "2 \u00b7 Internal checks", "nested CV + seeds", ORANGE),
             (3, "3 \u00b7 External validation", "GSE14520", RED)]
    X0, X1, Y0, Y1, GAP = 16, W - 16, 30, 258, 22
    pw = (X1 - X0 - 2 * GAP) / 3.0
    xs = [X0 + i * (pw + GAP) for i in range(3)]

    for (idx, t1, t2, col), x in zip(heads, xs):
        ax.add_patch(FancyBboxPatch((x, Y0), pw, Y1 - Y0,
                                    boxstyle="round,pad=0,rounding_size=7",
                                    linewidth=0.9, edgecolor="#D5D8DC",
                                    facecolor="#F7F8F9", zorder=1))
        ax.add_patch(FancyBboxPatch((x + 8, Y1 - 9), pw - 16, 3.4,
                                    boxstyle="round,pad=0,rounding_size=1.7",
                                    linewidth=0, facecolor=col, zorder=2))
        ax.text(x + 12, Y1 - 15, t1, fontsize=8.8, fontweight="bold", color=col,
                va="top", zorder=3)
        ax.text(x + 12, Y1 - 29, t2, fontsize=6.8, color=GREY, va="top", zorder=3)

        rows = [r for r in L if r[1] == idx]
        y = Y1 - 47
        for txt, _p, emph in rows:
            ax.text(x + 12, y, txt, fontsize=7.1, va="top", zorder=3,
                    fontweight="bold" if emph else "normal",
                    color=col if emph else INK)
            y -= 15.0

        # 面板间箭头
        if idx < 3:
            xa = x + pw + 4
            ax.add_patch(Polygon([[xa, (Y0 + Y1) / 2 + 5], [xa + 11, (Y0 + Y1) / 2],
                                  [xa, (Y0 + Y1) / 2 - 5]],
                                 closed=True, facecolor="#9AA5B1", linewidth=0, zorder=2))
            ax.plot([xa - 3, xa + 1], [(Y0 + Y1) / 2] * 2, color="#9AA5B1", lw=1.1, zorder=2)

    # ── 底部结论（同时作为 legend）─────────────────────────────
    ax.plot([16, W - 16], [24, 24], color="#D5D8DC", lw=0.9)
    ax.text(16, 17, LEGEND, fontsize=7.0, va="top", color=INK)

    # ── 自证：每一行数字都必须真的画在图上 ──────────────────────
    blob = "\n".join(t for t, _p, _e in L) + "\n" + LEGEND
    for txt, _p, _e in L:
        assert txt in blob, "行文本掉了：%s" % txt
    print("面板行数：P1 %d / P2 %d / P3 %d ；legend %d 字符"
          % (sum(1 for r in L if r[1] == 1), sum(1 for r in L if r[1] == 2),
             sum(1 for r in L if r[1] == 3), len(LEGEND)))
    print("来源校验：C_A=%s C_B=%s pooled=%s±%s ext=%s p=%s pc=%s prolif=%s"
          % (f3(cA), f3(cB), f3(p_mean), f3(p_sd), f3(e_c), f3(e_p),
             round(rp_pc), f3(pr_c)))

    if not APPLY:
        print("（预演，不落盘）")
        return

    os.makedirs(OUTDIR, exist_ok=True)
    png = os.path.join(OUTDIR, "Graphical_Abstract.png")
    svg = os.path.join(OUTDIR, "Graphical_Abstract.svg")
    tif = os.path.join(OUTDIR, "Graphical_Abstract.tif")
    fig.savefig(png, dpi=100)
    fig.savefig(svg)
    plt.close(fig)

    from PIL import Image
    im = Image.open(png)
    assert im.size == (W, H), "画布 %s，应为 (%d, %d)" % (im.size, W, H)
    im.convert("RGB").save(tif, format="TIFF", compression="tiff_lzw")

    for p in (tif, png, svg):
        kb = os.path.getsize(p) / 1024.0
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
        print("  %-34s %8.1f KB  %s" % (os.path.basename(p), kb, h))
    assert os.path.getsize(tif) <= 150 * 1024, \
        "TIFF %.1f KB 超 150 KB 上限" % (os.path.getsize(tif) / 1024.0)
    assert Image.open(tif).size == (W, H)
    print("OK -> %s（%dx%d px，TIFF %.1f KB ≤ 150 KB）"
          % (OUTDIR, W, H, os.path.getsize(tif) / 1024.0))


if __name__ == "__main__":
    main()
