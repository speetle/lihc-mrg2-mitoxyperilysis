#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学生3 LIHC —— 补充材料表 + 主图生成（全部取自真实分析输出）"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
for fam in ["Arial Unicode MS", "Heiti SC", "Microsoft YaHei", "SimHei"]:
    if any(f.name == fam for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [fam]; break
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["pdf.fonttype"] = 42

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
FIG = os.path.join(BASE, "图件")
SUP = os.path.join(BASE, "补充材料")
os.makedirs(FIG, exist_ok=True); os.makedirs(SUP, exist_ok=True)
RED, BLUE, GREY = "#c0392b", "#2c6fbb", "#7f8c8d"


def savefig(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  fig:", name)


def main():
    res = json.load(open(os.path.join(DATA, "results.json")))
    uni = pd.read_csv(os.path.join(DATA, "univariate_cox.csv"))
    coefA = pd.read_csv(os.path.join(DATA, "modelA_coef.csv"))
    coefB = pd.read_csv(os.path.join(DATA, "modelB_coef.csv"))
    stab = pd.read_csv(os.path.join(DATA, "modelB_stability.csv"))
    rs = pd.read_csv(os.path.join(DATA, "risk_scores.csv"), index_col=0)
    mv = pd.read_csv(os.path.join(DATA, "multivariable.csv"))
    imm = pd.read_csv(os.path.join(DATA, "immune_infiltration.csv"))
    mut = pd.read_csv(os.path.join(DATA, "mutations.csv"))
    expr = pd.read_csv(os.path.join(DATA, "lihc_expr_z.csv"), index_col=0)
    label = np.load(os.path.join(DATA, "kmeans_labels.npy"))
    pcs = np.load(os.path.join(DATA, "pcs.npy"))
    panel = [l.strip().upper() for l in open(os.path.join(HERE, "mrg_panel.txt")) if l.strip()]

    # ---------------- 补充表
    print("[补充表]")
    s1 = uni.merge(pd.DataFrame({"gene": panel}), how="right", on="gene")
    s1["evaluable"] = s1["HR"].notna()
    s1.to_csv(os.path.join(SUP, "Table_S1_MRG面板与LIHC单因素结果.csv"), index=False)
    # BH q
    u = uni.sort_values("p").copy()
    m = len(u); u["BH_q"] = (u["p"] * m / (np.arange(m) + 1)).iloc[::-1].cummin().iloc[::-1]
    u.to_csv(os.path.join(SUP, "Table_S2_单因素Cox含BH校正.csv"), index=False)
    rs.to_csv(os.path.join(SUP, "Table_S3_TCGA_LIHC逐患者数据.csv"))
    coefA.to_csv(os.path.join(SUP, "Table_S4_ModelA_23基因系数.csv"), index=False)
    stab.to_csv(os.path.join(SUP, "Table_S5_稳定性选择频率.csv"), index=False)
    mut.to_csv(os.path.join(SUP, "Table_S6_突变频率.csv"), index=False)
    imm.to_csv(os.path.join(SUP, "Table_S7_免疫浸润.csv"), index=False)
    mv.to_csv(os.path.join(SUP, "Table_S8_多因素校正.csv"), index=False)
    if os.path.exists(os.path.join(DATA, "external_GSE76427.csv")):
        pd.read_csv(os.path.join(DATA, "external_GSE76427.csv")).to_csv(
            os.path.join(SUP, "Table_S9_GSE76427外部验证逐患者.csv"), index=False)
    print("  done")

    # ---------------- Fig 1: 单因素森林 + 风险三联 + KM（Model A）
    fig = plt.figure(figsize=(13, 10))
    ax = fig.add_subplot(2, 2, 1)
    u2 = u.iloc[::-1]
    sig = u2["p"] < 0.05
    ax.errorbar(u2.loc[sig, "HR"], np.arange(len(u2))[sig.values],
                xerr=[u2.loc[sig, "HR"] - u2.loc[sig, "HR_lo"],
                      u2.loc[sig, "HR_hi"] - u2.loc[sig, "HR"]],
                fmt="o", ms=3, color=RED, lw=0.8, label="P < 0.05")
    ns = ~sig
    ax.errorbar(u2.loc[ns, "HR"], np.arange(len(u2))[ns.values],
                xerr=[u2.loc[ns, "HR"] - u2.loc[ns, "HR_lo"],
                      u2.loc[ns, "HR_hi"] - u2.loc[ns, "HR"]],
                fmt="o", ms=3, color=GREY, lw=0.8, label="P ≥ 0.05")
    ax.axvline(1, color="k", lw=0.6, ls="--")
    ax.set_xscale("log"); ax.set_xlabel("Hazard ratio (95% CI)"); ax.set_ylabel("MRG (ordered by P)")
    ax.set_title(f"A  Univariate Cox, {len(u2)} evaluable MRGs", loc="left", fontsize=10)
    ax.legend(fontsize=7, frameon=False)
    yt = list(range(len(u2)))
    shown = [i for i in yt if i % 5 == 0]
    ax.set_yticks(shown); ax.set_yticklabels([u2["gene"].iloc[i] for i in shown], fontsize=6)

    ax2 = fig.add_subplot(2, 2, 2)
    order = np.argsort(rs["scoreA"].values)
    ax2.plot(rs["scoreA"].values[order], color=BLUE, lw=1)
    ax2.axhline(np.median(rs["scoreA"]), color="k", ls="--", lw=0.6)
    ax2.set_ylabel("Model A risk score"); ax2.set_title("B  Risk score distribution", loc="left", fontsize=10)
    ax3 = ax2.twinx()
    ax3.scatter(np.arange(len(order)), rs["T"].values[order], s=2,
                c=np.where(rs["E"].values[order] == 1, RED, GREY))
    ax3.set_ylabel("Overall survival (months)"); ax3.set_xlabel("Patients ordered by risk score")

    ax4 = fig.add_subplot(2, 2, 3)
    top = list(u.head(23)["gene"])
    hm = expr[top].iloc[order].T
    im = ax4.imshow(hm.values, aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2)
    ax4.set_yticks(range(len(top))); ax4.set_yticklabels(top, fontsize=6)
    ax4.set_xlabel("Patients ordered by risk score")
    ax4.set_title("C  Expression of the 23 Model A genes", loc="left", fontsize=10)
    plt.colorbar(im, ax=ax4, fraction=0.03, label="z")

    ax5 = fig.add_subplot(2, 2, 4)
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test
    for g, col, name in [(0, BLUE, "Low risk"), (1, RED, "High risk")]:
        m = rs["groupA"].values == g
        k = KaplanMeierFitter().fit(rs["T"].values[m], rs["E"].values[m], label=name)
        k.plot_survival_function(ax=ax5, ci_show=False, color=col)
    lr = logrank_test(rs["T"][rs["groupA"] == 1], rs["T"][rs["groupA"] == 0],
                      rs["E"][rs["groupA"] == 1], rs["E"][rs["groupA"] == 0])
    ax5.set_title(f"D  Model A Kaplan–Meier (log-rank P = {lr.p_value:.2e})", loc="left", fontsize=10)
    ax5.set_xlabel("Months"); ax5.set_ylabel("Overall survival")
    fig.suptitle("Figure 1  Discovery cohort: univariate screening and the full-panel Model A", y=1.00)
    savefig(fig, "Figure1_ModelA_建模")

    # ---------------- Fig 2: 时间依赖 AUC + 增殖相关 + 校正森林
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    times = np.array(res["modelA"]["auc_times"])
    keep = times <= 60
    axes[0].plot(times[keep], np.array(res["modelA"]["auc"])[keep], "o-", color=BLUE, ms=3, label="Model A")
    axes[0].plot(times[keep], np.array(res["modelB"]["auc"])[keep], "s--", color=RED, ms=3, label="Model B")
    axes[0].axhline(0.5, color="k", lw=0.6, ls=":")
    axes[0].set_xlabel("Months"); axes[0].set_ylabel("Time-dependent AUC")
    axes[0].set_title("A  Time-dependent AUC (12–60 mo)", loc="left", fontsize=10); axes[0].legend(fontsize=8, frameon=False)

    prolif = pd.read_csv(os.path.join(DATA, "prolif_expr_z.csv"), index_col=0)
    pg = [g for g in ["MKI67", "PCNA", "CCNB1", "CCNB2", "CDK1", "BUB1", "BUB1B", "AURKA",
                      "AURKB", "TOP2A", "MCM2", "MCM3", "MCM4", "MCM6", "MCM7", "CDKN3",
                      "RACGAP1", "ASPM", "CENPE", "TTK"] if g in prolif.columns]
    common = [p for p in rs.index if p in prolif.index]
    ps = prolif.loc[common, pg].mean(1).values
    sa = pd.Series(rs["scoreA"].values, index=rs.index).loc[common].values
    axes[1].scatter(ps, sa, s=6, alpha=0.5, color=BLUE)
    axes[1].set_xlabel("20-gene proliferation score (mean z)")
    axes[1].set_ylabel("Model A risk score")
    rho = res["prolif"]["A"]["spearman_rho"]
    axes[1].set_title(f"B  Score vs proliferation (Spearman ρ = {rho:.2f})", loc="left", fontsize=10)

    sub = mv[mv.model == "Model A"]
    ax = axes[2]
    names = {"score_z": "MRG score (per SD)", "age_z": "Age (per SD)", "sex_male": "Male sex",
             "stage_III_IV": "Stage III–IV", "grade_G3_G4": "Grade G3–G4"}
    ys = np.arange(len(sub))[::-1]
    for yy, (_, r_ow) in zip(ys, sub.iterrows()):
        c = RED if r_ow["p"] < 0.05 else GREY
        ax.errorbar([r_ow["HR"]], [yy],
                    xerr=[[r_ow["HR"] - r_ow["lo"]], [r_ow["hi"] - r_ow["HR"]]],
                    fmt="o", color=c, ms=5, lw=1.2, capsize=3)
    ax.axvline(1, color="k", ls="--", lw=0.6); ax.set_xscale("log")
    ax.set_yticks(ys); ax.set_yticklabels([names.get(t, t) for t in sub["term"]], fontsize=8)
    ax.set_xlabel("Adjusted HR (95% CI)")
    ax.set_title("C  Multivariable adjustment (n = 360)", loc="left", fontsize=10)
    fig.suptitle("Figure 2  Model A: discrimination, proliferation overlap and independence")
    savefig(fig, "Figure2_ModelA_表现与独立性")

    # ---------------- Fig 3: LASSO CV + 稳定性 + MRG-2 KM
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    a1 = res["lasso"]["alpha_1se"]; amin = res["lasso"]["alpha_min"]
    axes[0].axvline(a1, color=RED, ls="--", lw=1)
    axes[0].axvline(amin, color=BLUE, ls=":", lw=1)
    axes[0].text(a1, 0.905, f" α_1SE = {a1:.4f}\n ({res['lasso']['n_at_1se']} genes)",
                 color=RED, fontsize=8, ha="right")
    axes[0].text(amin, 0.805, f" α_min = {amin:.4f}\n ({res['lasso']['n_at_min']} genes)",
                 color=BLUE, fontsize=8, ha="left")
    axes[0].plot([a1], [res["lasso"]["cv_at_1se"]], "o", color=RED)
    axes[0].plot([amin], [res["lasso"]["cv_at_min"]], "o", color=BLUE)
    axes[0].set_xscale("log"); axes[0].set_xlabel("log₁₀ α"); axes[0].set_ylabel("10-fold CV C-index")
    axes[0].set_title("A  LASSO-Cox cross-validation path", loc="left", fontsize=10)

    keys = [g for g in ["KIF15", "MAFG", "AKNA", "PPP1R10", "MBOAT7", "DAB2", "TAF12", "CEP19",
                        "TXNRD1", "WDR35", "PDGFA", "TIAM1", "TRAF3", "FERMT2", "SLC7A1"]] \
        if False else list(stab.head(15)["gene"])
    fr = list(stab.head(15)["freq"])
    cols = [RED if f >= 0.75 else GREY for f in fr]
    axes[1].barh(np.arange(len(keys))[::-1], fr, color=cols)
    axes[1].axvline(0.75, color="k", ls="--", lw=0.8)
    axes[1].set_yticks(np.arange(len(keys))[::-1]); axes[1].set_yticklabels(keys, fontsize=8)
    axes[1].set_xlabel("Selection frequency π (200 bootstrap fits)")
    axes[1].set_title("B  Stability selection (π ≥ 0.75)", loc="left", fontsize=10)

    for g, col, name in [(0, BLUE, "Low risk"), (1, RED, "High risk")]:
        m = rs["groupB"].values == g
        k = KaplanMeierFitter().fit(rs["T"].values[m], rs["E"].values[m], label=name)
        k.plot_survival_function(ax=axes[2], ci_show=False, color=col)
    lr = logrank_test(rs["T"][rs["groupB"] == 1], rs["T"][rs["groupB"] == 0],
                      rs["E"][rs["groupB"] == 1], rs["E"][rs["groupB"] == 0])
    axes[2].set_title(f"C  MRG-2 (KIF15+MAFG) KM, log-rank P = {lr.p_value:.2e}", loc="left", fontsize=10)
    axes[2].set_xlabel("Months"); axes[2].set_ylabel("Overall survival")
    fig.suptitle("Figure 3  Derivation of the two-gene score (MRG-2)")
    savefig(fig, "Figure3_MRG2_推导")

    # ---------------- Fig 4: PCA + 免疫 + 突变
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    axes[0].scatter(pcs[:, 0], pcs[:, 1], c=[BLUE if x == 0 else RED for x in label], s=8, alpha=0.7)
    axes[0].set_xlabel(f"PC1 ({res['pca_evr'][0]*100:.1f}%)"); axes[0].set_ylabel(f"PC2 ({res['pca_evr'][1]*100:.1f}%)")
    axes[0].set_title(f"A  k-means subtypes (k={res['kmeans']['best_k']}, "
                      f"silhouette {res['kmeans']['sil'][str(res['kmeans']['best_k'])]})",
                      loc="left", fontsize=10)
    ii = imm.iloc[::-1]
    cols = [RED if d > 0 else BLUE for d in ii["diff"]]
    axes[1].barh(np.arange(len(ii)), ii["diff"], color=cols)
    axes[1].axvline(0, color="k", lw=0.6)
    axes[1].set_yticks(np.arange(len(ii))); axes[1].set_yticklabels(ii["feature"], fontsize=8)
    axes[1].set_xlabel("High-risk − low-risk (mean z)")
    axes[1].set_title("B  Immune features (Mann–Whitney)", loc="left", fontsize=10)
    mm = mut.sort_values("high_pct", ascending=False).head(12).iloc[::-1]
    ys = np.arange(len(mm))
    axes[2].barh(ys + 0.2, mm["high_pct"], height=0.4, color=RED, label="High risk")
    axes[2].barh(ys - 0.2, mm["low_pct"], height=0.4, color=BLUE, label="Low risk")
    axes[2].set_yticks(ys); axes[2].set_yticklabels(mm["gene"], fontsize=8)
    axes[2].set_xlabel("Mutation frequency (%)"); axes[2].legend(fontsize=8, frameon=False)
    axes[2].set_title("C  Recurrent mutations by risk group", loc="left", fontsize=10)
    fig.suptitle("Figure 4  Molecular correlates of the MRG-2 risk groups")
    savefig(fig, "Figure4_分子相关")

    # ---------------- Fig 5: 外部验证
    if os.path.exists(os.path.join(DATA, "external_summary.json")) and \
       os.path.exists(os.path.join(DATA, "external_GSE76427.csv")):
        ext = json.load(open(os.path.join(DATA, "external_summary.json")))
        ev = pd.read_csv(os.path.join(DATA, "external_GSE76427.csv"))
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
        med = np.median(ev["scoreB"]); grp = (ev["scoreB"] > med).astype(int)
        for g, col, name in [(0, BLUE, "Low risk"), (1, RED, "High risk")]:
            m = grp == g
            k = KaplanMeierFitter().fit(ev["T"].values[m], ev["E"].values[m], label=name)
            k.plot_survival_function(ax=axes[0], ci_show=False, color=col)
        lr = logrank_test(ev["T"][grp == 1], ev["T"][grp == 0], ev["E"][grp == 1], ev["E"][grp == 0])
        axes[0].set_title(f"A  GSE76427 MRG-2 KM, log-rank P = {lr.p_value:.2e}", loc="left", fontsize=10)
        axes[0].set_xlabel("Months"); axes[0].set_ylabel("Overall survival")
        labs = ["Model A\n(23 genes)", "Model B\n(MRG-2)"]
        vals = [ext["ModelA"]["c_index"], ext["ModelB"]["c_index"]]
        lo = [ext["ModelA"]["c_index_CI"][0], ext["ModelB"]["c_index_CI"][0]]
        hi = [ext["ModelA"]["c_index_CI"][1], ext["ModelB"]["c_index_CI"][1]]
        axes[1].errorbar([0, 1], vals, yerr=[np.array(vals) - np.array(lo), np.array(hi) - np.array(vals)],
                         fmt="o", ms=7, color=RED, capsize=4)
        axes[1].axhline(0.5, color="k", ls=":", lw=0.8)
        axes[1].set_xticks([0, 1]); axes[1].set_xticklabels(labs)
        axes[1].set_ylabel("External C-index (GSE76427)")
        axes[1].set_title("B  External discrimination", loc="left", fontsize=10)
        fig.suptitle("Figure 5  External validation in GSE76427")
        savefig(fig, "Figure5_外部验证")

    # ---------------- Fig 6: 肿瘤 vs 正常 (ref-normal z)
    if os.path.exists(os.path.join(DATA, "tumor_vs_normal.csv")):
        rn = pd.read_csv(os.path.join(DATA, "tumor_vs_normal.csv"), index_col=0).iloc[:, 0].sort_values()
        fig, ax = plt.subplots(figsize=(7, 9))
        cols = [RED if v > 0 else BLUE for v in rn.values]
        ax.barh(np.arange(len(rn)), rn.values, color=cols, height=0.85)
        ax.axvline(0, color="k", lw=0.6)
        ax.axvline(1, color=GREY, ls="--", lw=0.7); ax.axvline(-1, color=GREY, ls="--", lw=0.7)
        ax.set_yticks(np.arange(len(rn))); ax.set_yticklabels(rn.index, fontsize=5)
        ax.set_xlabel("Mean z-score relative to normal liver (cBioPortal ref-normal profile)")
        ax.set_title("Figure 6  Panel genes in tumour vs reference normal liver", loc="left", fontsize=10)
        savefig(fig, "Figure6_肿瘤vs正常")

    print("\n全部图表完成。")


if __name__ == "__main__":
    main()
