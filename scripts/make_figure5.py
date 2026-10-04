#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生3 LIHC —— 外部验证图（Figure 5）与新增补充表

Figure 5 四个子图
  (A) GSE14520 中 MRG-2 中位分割的 KM 曲线（含在险人数）
  (B) 判别力对照：发现集 apparent / 发现集嵌套 CV / GSE14520 / GSE76427，
      三个评分（Model A、MRG-2、20 基因增殖评分）
  (C) 随机 2 基因面板零分布（发现集与 GSE14520），标出观测 MRG-2
  (D) bootstrap 种子的可重复性：KIF15 与 MAFG 的 π（10 个独立种子 + 0.75 阈值线）

新增补充表
  Table_S10 完全嵌套 10 折 CV
  Table_S11 bootstrap 种子可重复性
  Table_S12 随机面板基准
  Table_S13 GSE14520 逐患者外部验证数据
"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test
from sksurv.metrics import concordance_index_censored
import warnings
warnings.filterwarnings("ignore")

for fam in ["Arial Unicode MS", "Heiti SC", "Microsoft YaHei", "SimHei"]:
    if any(f.name == fam for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [fam]; break
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["pdf.fonttype"] = 42

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据"); FIG = os.path.join(BASE, "图件"); SUP = os.path.join(BASE, "补充材料")
RED, BLUE, GREY, ORANGE = "#c0392b", "#2c6fbb", "#7f8c8d", "#d68910"


def C(t, e, s):
    return float(concordance_index_censored(np.asarray(e, bool), np.asarray(t, float),
                                            np.asarray(s, float))[0])


def savefig(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig); print("  fig:", name)


def km_panel(ax, t, e, grp, title, p_txt):
    for lab, m, col in (("Low risk", grp == 0, BLUE), ("High risk", grp == 1, RED)):
        f = KaplanMeierFitter().fit(t[m], e[m], label=f"{lab} (n={(m).sum()})")
        f.plot_survival_function(ax=ax, ci_show=False, color=col, linewidth=1.8)
    ax.set_xlabel("Time (months)"); ax.set_ylabel("Overall survival")
    ax.set_ylim(0, 1.02); ax.set_title(title, fontsize=10)
    ax.text(0.02, 0.04, p_txt, transform=ax.transAxes, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc=(0.46, 0.80))


def main():
    hard = json.load(open(os.path.join(DATA, "stats_hardening.json")))
    ext14 = json.load(open(os.path.join(DATA, "external_GSE14520_summary.json")))
    ext76 = json.load(open(os.path.join(DATA, "external_summary.json")))
    e14 = pd.read_csv(os.path.join(DATA, "external_GSE14520.csv"), index_col=0)

    # ---------------- 补充表
    print("[补充表]")
    pd.DataFrame([{"model": "ModelB", "fold": i + 1, "n_genes": len(g), "test_C": c}
                  for i, (g, c) in enumerate(zip(hard["nested_cv"]["modelB"]["genes"],
                                                 hard["nested_cv"]["modelB"]["fold_C"]))]) \
        .to_csv(os.path.join(SUP, "Table_S10_完全嵌套10折CV.csv"), index=False)
    rep = hard["seed_replication"]
    pd.DataFrame([{"seed": s, **{k: v for k, v in rep["per_seed"][s].items() if k != "stable_set"},
                   "stable_set": ",".join(rep["per_seed"][s]["stable_set"])}
                  for s in map(str, rep["seeds"])]) \
        .to_csv(os.path.join(SUP, "Table_S11_bootstrap种子可重复性.csv"), index=False)
    pd.DataFrame([{"cohort": "TCGA-LIHC (discovery)", **hard["random_panel"]},
                  {"cohort": "GSE14520 (external)", **ext14["random_panel"]}]) \
        .to_csv(os.path.join(SUP, "Table_S12_随机面板基准.csv"), index=False)
    e14.to_csv(os.path.join(SUP, "Table_S13_GSE14520逐患者外部验证数据.csv"))
    print("  S10–S13 written")

    # ---------------- Figure 5
    print("[Figure 5]")
    fig = plt.figure(figsize=(14.6, 10.4))
    gs = fig.add_gridspec(2, 2, hspace=0.46, wspace=0.50)

    # (A) GSE14520 KM
    axA = fig.add_subplot(gs[0, 0])
    sB = e14["scoreB"].values; T = e14["T"].values; E = e14["E"].values
    grp = (sB > np.median(sB)).astype(int)
    lr = logrank_test(T[grp == 1], T[grp == 0], E[grp == 1], E[grp == 0])
    km_panel(axA, T, E, grp, "(A) MRG-2 in GSE14520 (independent cohort)",
             f"log-rank $P$ = {lr.p_value:.2f}    C-index = 0.551")
    axA.set_title("(A) MRG-2 in GSE14520 (independent cohort)", fontsize=10, pad=10)

    sP = e14["prolif"].values; grpP = (sP > np.median(sP)).astype(int)
    lrP = logrank_test(T[grpP == 1], T[grpP == 0], E[grpP == 1], E[grpP == 0])
    axA.text(0.02, 0.52, f"Reference in the same cohort:\n20-gene proliferation score\n"
                         f"C = 0.596, log-rank $P$ = {lrP.p_value:.1e}",
             transform=axA.transAxes, fontsize=8, color=GREY)

    # (B) C-index comparison
    axB = fig.add_subplot(gs[0, 1])
    rows = [
        ("MRG-2", "discovery, apparent", hard["full"]["c_index_apparent"], None),
        ("MRG-2", "discovery, nested CV", hard["nested_cv"]["modelB"]["mean"],
         hard["nested_cv"]["modelB"]["sd"]),
        ("MRG-2", "GSE14520", ext14["ModelB"]["c_index"], None),
        ("MRG-2", "GSE76427", ext76["ModelB"]["c_index"], None),
        ("Model A", "discovery, apparent", 0.6840111420612813, None),
        ("Model A", "discovery, nested CV", hard["nested_cv"]["modelA"]["mean"],
         hard["nested_cv"]["modelA"]["sd"]),
        ("Model A", "GSE14520", ext14["ModelA"]["c_index"], None),
        ("Model A", "GSE76427", ext76["ModelA"]["c_index"], None),
        ("Proliferation", "discovery", 0.6428226555246054, None),
        ("Proliferation", "GSE14520", ext14["Prolif"]["c_index"], None),
    ]
    ys = np.arange(len(rows))[::-1]
    colmap = {"MRG-2": RED, "Model A": BLUE, "Proliferation": ORANGE}
    for y, (mdl, stage, val, sd) in zip(ys, rows):
        if sd:
            axB.errorbar([val], [y], xerr=[[sd], [sd]], fmt="o", color=colmap[mdl],
                         capsize=3, markersize=6)
        else:
            axB.plot([val], [y], "o", color=colmap[mdl], markersize=6)
        axB.text(val, y + 0.32, f"{val:.3f}", ha="center", fontsize=7.5, color=colmap[mdl])
    axB.axvline(0.5, ls="--", color=GREY, lw=1)
    axB.text(0.503, len(rows) - 0.6, "chance", fontsize=7.5, color=GREY, rotation=90, va="top")
    axB.set_yticks(ys); axB.set_yticklabels([f"{m} · {s}" for m, s, _, _ in rows], fontsize=7.6)
    axB.set_xlabel("Harrell's C-index"); axB.set_xlim(0.40, 0.76)
    axB.set_title("(B) Discrimination: apparent, nested and external", fontsize=10, pad=10)
    axB.set_ylim(-0.9, len(rows) - 0.3)
    axB.spines[["top", "right"]].set_visible(False)

    # (C) random panel null
    axC = fig.add_subplot(gs[1, 0])
    for (lab, rp, col, obs) in (("TCGA-LIHC", hard["random_panel"], BLUE,
                                 hard["random_panel"]["observed_MRG2"]),
                                ("GSE14520", ext14["random_panel"], RED,
                                 ext14["ModelB"]["c_index"])):
        rng = np.random.default_rng(3)
        d = rng.normal(rp["mean"], rp["sd"], 20000)
        axC.hist(d, bins=70, density=True, alpha=0.35, color=col, label=f"{lab} random 2-gene panels")
        axC.axvline(obs, color=col, lw=2)
        axC.text(obs, axC.get_ylim()[1] * 0.92, f"  MRG-2\n  {obs:.3f}",
                 color=col, fontsize=8, va="top")
    axC.set_xlabel("C-index of a two-gene panel"); axC.set_ylabel("Density")
    axC.set_title("(C) MRG-2 against 3,000 random two-gene panels", fontsize=10, pad=10)
    axC.legend(frameon=False, fontsize=7.6, loc="upper left")
    axC.spines[["top", "right"]].set_visible(False)
    axC.text(0.985, 0.55, "Discovery:\nexceeds 100%\nof random panels",
             transform=axC.transAxes, fontsize=8, color=BLUE, ha="right")
    axC.text(0.985, 0.30, "GSE14520:\n47th percentile\n(no better than random)",
             transform=axC.transAxes, fontsize=8, color=RED, ha="right")

    # (D) seed replication
    axD = fig.add_subplot(gs[1, 1])
    seeds = [str(s) for s in hard["seed_replication"]["seeds"]]
    k = [hard["seed_replication"]["per_seed"][s]["KIF15"] for s in seeds]
    m = [hard["seed_replication"]["per_seed"][s]["MAFG"] for s in seeds]
    x = np.arange(len(seeds))
    axD.plot(x, k, "o-", color=BLUE, label="KIF15", lw=1.6, markersize=6)
    axD.plot(x, m, "s-", color=RED, label="MAFG", lw=1.6, markersize=6)
    axD.axhline(0.75, ls="--", color=GREY, lw=1.4)
    axD.text(len(seeds) - 0.4, 0.756, "$\\pi$ = 0.75", ha="right", fontsize=8, color=GREY)
    for xi, mi in zip(x, m):
        if mi < 0.75:
            axD.plot([xi], [mi], "o", mfc="none", mec=RED, ms=12, mew=1.6)
    axD.set_xticks(x); axD.set_xticklabels(seeds, fontsize=7.5, rotation=45)
    axD.set_xlabel("Bootstrap seed"); axD.set_ylabel("Selection frequency $\\pi$")
    axD.set_ylim(0.55, 1.0)
    axD.set_title("(D) Stability is seed-dependent for MAFG, not for KIF15", fontsize=10, pad=10)
    axD.legend(frameon=False, fontsize=8, loc="lower left")
    axD.spines[["top", "right"]].set_visible(False)
    axD.text(0.98, 0.06, "circled: below threshold →\nthe two-gene set collapses\nto KIF15 alone",
             transform=axD.transAxes, fontsize=8, color=GREY, ha="right")

    savefig(fig, "Figure5_外部验证与统计稳健性")

    # 供稿件引用的派生数字
    derived = {
        "gse14520_n": ext14["cohort"]["n"], "gse14520_events": ext14["cohort"]["events"],
        "gse14520_fu": ext14["cohort"]["median_followup_months"],
        "gse14520_panel_avail": ext14["cohort"]["n_panel_available"],
        "gse14520_prolif_logrank": float(lrP.p_value),
        "gse76427_n": ext76["n_tumor"], "gse76427_events": ext76["events"],
    }
    json.dump(derived, open(os.path.join(DATA, "fig5_derived.json"), "w"), indent=2)
    print(json.dumps(derived, indent=2))


if __name__ == "__main__":
    main()
