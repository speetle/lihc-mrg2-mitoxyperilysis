#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学生3 LIHC —— 补充图 Figure S1（校准 + 时间依赖 Brier）的**正式生成脚本**。

为什么补这个脚本：
    此前 Figure S1 是在会话里内联生成的，交付目录中**没有对应的生成脚本**，
    与稿件「每个图都可由沉积代码复现」的声明不符（Reviewer 3 的口径）。
    本脚本把它固化，并顺带修两处：

  1. **面板字母缺失**：正文引用的是「Figure S1A / S1B」，但原图没有 (A)/(B)。
  2. **配色与 Figure 2A 相反**：Figure 2A 里 Model A = 红、MRG-2 = 蓝，
     而原 S1 把 MRG-2 画成红、Model A 画成蓝。同稿内同一对被比较的模型
     必须同色。此处按 Figure 2A 统一为 **Model A = RED / MRG-2 = BLUE**。

数据源：`数据/revised/calibration_v14.json`（由 `分析脚本/revise_stats_v14.py` 产出）。
输出：`图件_v2/补充图/FigureS1_calibration.{png,pdf,svg}`（600 dpi PNG + 矢量）。
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from make_figures_v2 import BASE, RED, BLUE, GREY, panel_letter  # noqa: E402

SRC = os.path.join(BASE, "数据", "revised", "calibration_v14.json")
OUT = os.path.join(BASE, "图件_v2", "补充图")
os.makedirs(OUT, exist_ok=True)

# ---- 同稿内配色统一（对齐 Figure 2A）----
COLOR = {"Model A": RED, "MRG-2": BLUE}


def main():
    with open(SRC, encoding="utf-8") as fh:
        cal = json.load(fh)

    for k in ("Model A", "MRG-2"):
        assert k in cal, f"calibration_v14.json 缺少 {k}"

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    fig.subplots_adjust(wspace=0.34)

    # ---------------- A: 校准（按预测 3 年生存的五分位）----------------
    ax = axes[0]
    ax.plot([0, 1], [0, 1], ls="--", lw=0.8, color="#444444", label="Ideal")
    for name in ("Model A", "MRG-2"):
        pts = cal[name]["calib_points"]
        xs = [p["pred_mean"] for p in pts]
        ys = [p["km_obs"] for p in pts]
        ax.plot(xs, ys, "o-", color=COLOR[name], ms=3.0, lw=1.0,
                label=f"{name} (slope {cal[name]['cv_calibration_slope']:.2f})")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Mean predicted 3-year OS")
    ax.set_ylabel("Kaplan–Meier observed 3-year OS")
    ax.set_title("Calibration (quintiles)", loc="left", pad=3, fontweight="bold")
    ax.legend(frameon=False, fontsize=6.5, loc="lower right")
    panel_letter(ax, "A", dx=-0.20)

    # ---------------- B: 时间依赖 Brier ----------------
    ax = axes[1]
    for name in ("Model A", "MRG-2"):
        t = np.asarray(cal[name]["times"])
        b = np.asarray(cal[name]["brier"])
        ax.plot(t, b, "o-", color=COLOR[name], ms=3.0, lw=1.0,
                label=f"{name} (IBS {cal[name]['ibs']:.3f})")
    ax.set_xlabel("Time (months)")
    ax.set_ylabel("IPCW Brier score")
    ax.set_title("Time-dependent Brier score", loc="left", pad=3, fontweight="bold")
    ax.legend(frameon=False, fontsize=6.5, loc="lower right")
    panel_letter(ax, "B", dx=-0.20)

    # ---------------- 数值红线断言（防图与表/正文漂移）----------------
    sA = cal["Model A"]["cv_calibration_slope"]
    sB = cal["MRG-2"]["cv_calibration_slope"]
    assert abs(round(sA, 2) - 0.95) < 1e-9, f"Model A 斜率与正文不符：{sA}"
    assert abs(round(sB, 2) - 0.95) < 1e-9, f"MRG-2 斜率与正文不符：{sB}"
    assert abs(round(cal["Model A"]["ibs"], 3) - 0.189) < 1e-9
    assert abs(round(cal["MRG-2"]["ibs"], 3) - 0.197) < 1e-9

    stem = os.path.join(OUT, "FigureS1_calibration")
    fig.savefig(stem + ".png", dpi=600, bbox_inches="tight",
                pad_inches=0.02, facecolor="white")
    fig.savefig(stem + ".pdf", bbox_inches="tight", pad_inches=0.02,
                facecolor="white")
    fig.savefig(stem + ".svg", bbox_inches="tight", pad_inches=0.02,
                facecolor="white")
    plt.close(fig)

    print(f"  Figure S1: 斜率 Model A {sA:.4f} / MRG-2 {sB:.4f}"
          f"  |  IBS {cal['Model A']['ibs']:.4f} / {cal['MRG-2']['ibs']:.4f}")
    print(f"  输出 -> {os.path.relpath(stem, BASE)}.{{png,pdf,svg}}")


if __name__ == "__main__":
    main()
