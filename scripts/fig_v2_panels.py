#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIHC —— 图 1–6 的期刊规格绘制（调用 make_figures_v2 的样式与数据加载）。"""
from make_figures_v2 import *  # noqa: F401,F403
from matplotlib.ticker import NullLocator

RNG = np.random.default_rng(7)


def _sig_stars(p):
    return "***" if p < 1e-3 else "**" if p < 1e-2 else "*" if p < 0.05 else ""


# ===================== Figure 1 =====================
def fig1(D):
    res, uni, rs, expr = D["res"], D["uni"], D["rs"], D["expr"]
    fig = plt.figure(figsize=(DC, 7.8))   # R3-m13：热图 23 个基因名抬到 6.5 pt 后需加高
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1.0], hspace=0.60, wspace=0.48)

    # --- A: forest of the univariate-significant genes
    ax = fig.add_subplot(gs[0, 0]); ax.set_gid("panel_A")
    u = uni.dropna(subset=["HR"]).sort_values("p")
    m = len(u); u = u.copy()
    u["q"] = (u["p"] * m / (np.arange(m) + 1)).iloc[::-1].cummin().iloc[::-1]
    sig = u[u["p"] < 0.05].sort_values("HR")
    y = np.arange(len(sig))
    for i, (_, r) in enumerate(sig.iterrows()):
        col = RED if r["q"] < 0.05 else GREY
        ax.plot([r["HR_lo"], r["HR_hi"]], [i, i], color=col, lw=0.9, solid_capstyle="butt")
        ax.plot([r["HR"]], [i], "o", color=col, ms=2.6)
    ax.axvline(1.0, color="k", lw=0.6, ls="--")
    ax.set_yticks(y); ax.set_yticklabels(sig["gene"], fontsize=6.5)
    ax.set_xscale("log"); ax.set_xlabel("Hazard ratio per SD (95% CI)")
    # R3-m7：对数横轴只落 1 个主刻度（10⁰ → "1"），HR 点只能靠目测估读。
    # 改为显式给出可读的小数刻度，并关掉次刻度，避免回落成 6×10⁻¹ 形态。
    ax.set_xticks([0.8, 0.9, 1.0, 1.25, 1.5])
    ax.set_xticklabels(["0.8", "0.9", "1.0", "1.25", "1.5"])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_ylim(-0.8, len(sig) - 0.2)
    ax.set_title("Univariate Cox, the 23 MRGs with P < 0.05", loc="left", pad=3, fontweight="bold")
    ax.legend(handles=[Patch(color=RED, label="BH q < 0.05 (n = 5)"),
                       Patch(color=GREY, label="BH q ≥ 0.05 (n = 18)")],
              loc="lower right", frameon=False, fontsize=6.5)
    panel_letter(ax, "A")

    # --- B: risk score + survival status
    ax = fig.add_subplot(gs[0, 1]); ax.set_gid("panel_B")
    o = np.argsort(rs["scoreA"].values)
    s = rs["scoreA"].values[o]; T = rs["T"].values[o]; E = rs["E"].values[o]
    g = rs["groupA"].values[o]
    ax.fill_between(np.arange(len(s)), 0, s, where=(g == 0), color=BLUE, alpha=0.55, lw=0)
    ax.fill_between(np.arange(len(s)), 0, s, where=(g == 1), color=RED, alpha=0.55, lw=0)
    ax.plot(np.arange(len(s)), s, color="k", lw=0.6)
    ax.axhline(np.median(rs["scoreA"]), color="k", ls="--", lw=0.6)
    ax.set_ylabel("Model A risk score"); ax.set_xlabel("Patients ordered by risk score")
    ax.set_title("Model A risk score, median split", loc="left", pad=3, fontweight="bold")
    ax.set_xlim(0, len(s)); ax.set_xticks([])
    axin = ax.inset_axes([0, -0.30, 1, 0.22])
    axin.scatter(np.arange(len(s))[E == 1], np.ones((E == 1).sum()), s=0.6, color=RED, marker="|")
    axin.scatter(np.arange(len(s))[E == 0], np.zeros((E == 0).sum()), s=0.6, color=GREY, marker="|")
    axin.set_yticks([0, 1]); axin.set_yticklabels(["Alive", "Dead"], fontsize=6.5)
    axin.set_ylim(-0.6, 1.6); axin.set_xticks([])
    for sp in ("top", "right", "bottom"): axin.spines[sp].set_visible(False)
    panel_letter(ax, "B")

    # --- C: expression heatmap
    ax = fig.add_subplot(gs[1, 0]); ax.set_gid("panel_C")
    genesA = list(D["coefA"].sort_values("coef", ascending=False)["term"])
    hm = expr.reindex(rs.index)[genesA].T.values
    im = ax.imshow(hm, aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2,
                   extent=[0, hm.shape[1], 0, hm.shape[0]], interpolation="nearest")
    ax.set_yticks(np.arange(len(genesA)) + 0.5); ax.set_yticklabels(genesA, fontsize=6.5)
    ax.set_xticks([]); ax.set_xlabel("Patients ordered by risk score")
    ax.set_title("The 23 Model A genes", loc="left", pad=3, fontweight="bold")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.015)
    cb.set_label("Z-score", fontsize=6.5); cb.ax.tick_params(labelsize=6.5)
    panel_letter(ax, "C", dx=-0.20)

    # --- D: KM Model A
    ax = fig.add_subplot(gs[1, 1]); ax.set_gid("panel_D")
    times = np.array([0, 12, 24, 36, 48, 60])
    for gi, (col, name) in enumerate([(BLUE, "Low risk"), (RED, "High risk")]):
        mm = rs["groupA"].values == gi
        ts, ss = km_curve(rs["T"].values[mm], rs["E"].values[mm])
        ax.step(ts, ss, where="post", color=col, lw=1.0, label=name + f" (n = {mm.sum()})")
    ax.set_xlabel("Months"); ax.set_ylabel("Overall survival")
    # R3-m6：横轴原先画到 80 月，而 at-risk 表止于 60 月，末段曲线无 at-risk 支撑。
    # 统一截到 60 月，使横轴与 at-risk 表逐点对齐。
    ax.set_xlim(0, 60); ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, loc="upper right", fontsize=6.5)
    ax.set_title("Model A Kaplan–Meier, log-rank $P$ = " + p_fmt(res['modelA']['logrank_p']),
                 loc="left", pad=3, fontweight="bold")
    add_atrisk(fig, ax, rs["T"].values, rs["E"].values, rs["groupA"].values,
               ["Low", "High"], times)
    panel_letter(ax, "D")

    r = savefig(fig, "1")
    return r, dict(A=fig.axes[0], B=fig.axes[1], C=fig.axes[2], D=fig.axes[3])


# ===================== Figure 2 =====================
def fig2(D):
    res, mv, rs = D["res"], D["mv"], D["rs"]
    fig, axes = plt.subplots(1, 3, figsize=(DC, 2.7))
    fig.subplots_adjust(wspace=0.42)

    ax = axes[0]; ax.set_gid("panel_A")
    t, aA, aB = np.array(res["modelA"]["auc_times"]), np.array(res["modelA"]["auc"]), np.array(res["modelB"]["auc"])
    k = t <= 60
    ax.plot(t[k], aA[k], "o-", color=RED, ms=2.4, lw=0.9, label="Model A")
    ax.plot(t[k], aB[k], "s-", color=BLUE, ms=2.4, lw=0.9, label="MRG-2")
    ax.axhline(0.5, color=GREY, ls=":", lw=0.7)
    ax.set_xlabel("Months"); ax.set_ylabel("Time-dependent AUC")
    ax.set_ylim(0.5, 0.85); ax.set_xticks([12, 24, 36, 48, 60])
    ax.legend(frameon=False, loc="lower left", fontsize=6.5)
    ax.set_title("Time-dependent AUC (12–60 mo)", loc="left", pad=3, fontweight="bold")
    # ⚠️ 数值红线（2026-10-04 实测踩坑）：此处原写 "41"，与 Table 1 及
    #    Figure 1D 的 at-risk 表（11 + 29 = 40）矛盾。从 S3 逐患者数据复算：
    #    T ≥ 60 月者恰为 40（9 例死亡 + 31 例删失）。
    # ⚠️ 2026-10-04 先生指出 Figure2A 遮挡：该注记写在右下角 (0.98, 0.03)，
    #    与左下角图例 'MRG-2 (n = 180)' 的文字横向上咬在一起（实测互压 22%）。
    #    改为按"不压数据、不压图例"自动选位。
    place_text_clear(ax, "40 at risk at 60 mo",
                     [(0.98, 0.03, "right", "bottom"),
                      (0.98, 0.97, "right", "top"),
                      (0.03, 0.97, "left", "top")],
                     fontsize=6.5, color=GREY)
    panel_letter(ax, "A")

    ax = axes[1]; ax.set_gid("panel_B")
    pf = pd.read_csv(os.path.join(DATA, "prolif_expr_z.csv"), index_col=0)
    pf = pf.reindex(rs.index)
    if "pat" in pf.columns: pf = pf.drop(columns=["pat"])
    prolif = pf.mean(axis=1).values
    ax.scatter(prolif, rs["scoreA"].values, s=1.6, color=GREY, alpha=0.45, lw=0)
    z = np.polyfit(prolif, rs["scoreA"].values, 1)
    xs = np.linspace(prolif.min(), prolif.max(), 20)
    ax.plot(xs, np.polyval(z, xs), color=RED, lw=1.0)
    ax.set_xlabel("20-gene proliferation score"); ax.set_ylabel("Model A risk score")
    ax.set_title(f"Score vs proliferation (ρ = {res['prolif']['A']['spearman_rho']:.2f})",
                 loc="left", pad=3, fontweight="bold")
    panel_letter(ax, "B")

    ax = axes[2]; ax.set_gid("panel_C")
    # ⚠️ 字段口径（2026-10-04 实测踩坑）：multivariable.csv 的 model 列取值是
    #    "Model A" / "Model B"（不是 "adjusted_ModelB"），term 列是 score_z / age_z /
    #    sex_male / stage_III_IV / grade_G3_G4（不是 z / male / adv / gr）。
    #    旧筛选条件命中 0 行 → 森林图整个面板空白（但坐标轴照画，肉眼不易发现）。
    NAMEMAP = {"score_z": "MRG-2 (per SD)", "age_z": "Age (per SD)",
               "sex_male": "Male sex", "stage_III_IV": "Stage III–IV",
               "grade_G3_G4": "Grade G3–G4"}
    sub = mv[mv["model"] == "Model A"].copy()
    sub["label"] = sub["term"].map(NAMEMAP)
    sub = sub.dropna(subset=["label"]).sort_values("HR")
    assert len(sub) == 5, f"Figure2C 期望 5 个协变量，实际 {len(sub)} 个 —— 数据字段可能已变"
    yy = np.arange(len(sub))
    for i, (_, r) in enumerate(sub.iterrows()):
        col = RED if (r["lo"] > 1 or r["hi"] < 1) else GREY
        ax.plot([r["lo"], r["hi"]], [i, i], color=col, lw=0.9)
        ax.plot([r["HR"]], [i], "o", color=col, ms=2.6)
    ax.axvline(1, color="k", lw=0.6, ls="--")
    ax.set_yticks(yy); ax.set_yticklabels(list(sub["label"]), fontsize=6.5)
    ax.set_ylim(-0.7, len(sub) - 0.3)
    ax.set_xscale("log"); ax.set_xlabel("Hazard ratio (95% CI)")
    # R3-m3：森林图惯例刻度为 0.5/1/2，不写 6×10⁻¹ / 2×10⁰ 这类科学记数。
    ax.set_xticks([0.5, 0.75, 1.0, 1.5, 2.0, 3.0])
    ax.set_xticklabels(["0.5", "0.75", "1.0", "1.5", "2.0", "3.0"])
    ax.xaxis.set_minor_locator(NullLocator())
    # R1-m2：主口径改为完整病例 n=337（见 §2.7），标题随之更新。
    ax.set_title(f"Model A, multivariable (n = {int(sub['n'].iloc[0])})", loc="left", pad=3, fontweight="bold")
    panel_letter(ax, "C", dx=-0.30)

    # ⚠️ 2026-10-04 先生指出 Figure2C 遮挡：面板 C 的长刻度标签
    #    （'MRG-2 (per SD)' 等）横向伸进面板 B 达 23%。改为自适应间距。
    ensure_no_crossbleed(fig, list(axes), 0.42)

    r = savefig(fig, "2")
    return r, dict(A=axes[0], B=axes[1], C=axes[2])


# ===================== Figure 3 =====================
def fig3(D):
    res, stab, rs = D["res"], D["stab"], D["rs"]
    fig, axes = plt.subplots(1, 3, figsize=(DC, 2.9))
    fig.subplots_adjust(wspace=0.62)

    # --- A: 真实 CV 曲线（v1 缺此面板内容）
    axA = axes[0]; axA.set_gid("panel_A")
    txtA = None
    cvp = os.path.join(DATA, "lasso_cv_path.json")
    if os.path.exists(cvp):
        P = json.load(open(cvp))
        al = np.array(P["alphas"]); cv = np.array(P["cv"]); ng = np.array(P["n_genes"])
        axA.plot(al, cv, "-", color="k", lw=0.9)
        axA.axvline(P["alpha_1se"], color=RED, ls="--", lw=0.8)
        axA.axvline(P["alpha_min"], color=BLUE, ls=":", lw=0.8)
        axA.plot([P["alpha_1se"]], [P["cv_1se"]], "o", color=RED, ms=3)
        axA.plot([P["alpha_min"]], [P["cv_min"]], "o", color=BLUE, ms=3)
        axA.axhline(P["cv_min"] - P["se_cv"], color=GREY, ls="-", lw=0.6)
        axA.set_xscale("log")
        axA.set_xlabel("α (log scale)"); axA.set_ylabel("10-fold CV C-index")
        ax2 = axA.twinx()
        ax2.plot(al, ng, "-", color=ORANGE, lw=0.7, alpha=0.85)
        ax2.set_ylabel("Non-zero genes", color=ORANGE, fontsize=6.5)
        ax2.tick_params(axis="y", labelcolor=ORANGE, labelsize=6)
        ax2.set_ylim(0, ng.max() * 1.25)
        txtA = (f"1-SE: α={P['alpha_1se']:.4f} ({P['n_at_1se']} genes)\n"
                f"min: α={P['alpha_min']:.4f} ({P['n_at_min']} genes)\n"
                f"range {cv.min():.3f}–{cv.max():.3f} (SE {P['se_cv']:.4f})")
        # ⚠️ 2026-10-04 先生指出 Figure3A 遮挡：注记原本画在这里的左下角，
        #    而 CV 曲线在该处恰好穿过 —— 实测**文字框内有 26 个曲线顶点**。
        #    面板内没有足够大的空口袋（曲线呈 V 形横贯全图），
        #    且白底半透明框压数据属违规，故改为**轴外脚注**，见函数末尾。
    else:
        axA.text(0.5, 0.5, "lasso_cv_path.json 缺失", ha="center", va="center", fontsize=6.5)
    axA.set_title("LASSO-Cox cross-validation path", loc="left", pad=3, fontweight="bold")
    panel_letter(axA, "A", dx=-0.22)

    # --- B: stability selection
    axB = axes[1]; axB.set_gid("panel_B")
    top = stab.head(15).iloc[::-1]
    cols = [RED if f >= 0.75 else GREY for f in top["freq"]]
    axB.barh(np.arange(len(top)), top["freq"], color=cols, height=0.72)
    axB.axvline(0.75, color="k", ls="--", lw=0.8)
    axB.set_yticks(np.arange(len(top))); axB.set_yticklabels(top["gene"], fontsize=6.5)
    axB.set_xlabel("Selection frequency π (200 bootstrap fits)")
    axB.set_xlim(0, 1.0)
    axB.set_title("Stability selection (π ≥ 0.75)", loc="left", pad=3, fontweight="bold")
    panel_letter(axB, "B", dx=-0.30)

    # --- C: KM MRG-2
    axC = axes[2]; axC.set_gid("panel_C")
    times = np.array([0, 12, 24, 36, 48, 60])
    handlesC = []
    for gi, (col, name) in enumerate([(BLUE, "Low risk"), (RED, "High risk")]):
        mm = rs["groupB"].values == gi
        ts, ss = km_curve(rs["T"].values[mm], rs["E"].values[mm])
        ln, = axC.step(ts, ss, where="post", color=col, lw=1.0,
                       label=name + f" (n = {mm.sum()})")
        handlesC.append(ln)
    axC.set_xlabel("Months"); axC.set_ylabel("Overall survival")
    # R3-m6：横轴原先画到 80 月，而 at-risk 表止于 60 月，末段曲线无 at-risk 支撑。
    # 统一截到 60 月，使横轴与 at-risk 表逐点对齐。
    axC.set_xlim(0, 60); axC.set_ylim(0, 1.02)
    axC.set_title("MRG-2 Kaplan–Meier, log-rank $P$ = " + p_fmt(res['modelB']['logrank_p']),
                  loc="left", pad=3, fontweight="bold")

    # ---- 统一收口：① 自适应面板间距 ② 图例 ③ at-risk 表 ④ 轴外脚注
    #      ⚠️ 顺序不可换：at-risk 表与脚注都按**当时的** axes 位置锚定左边缘，
    #         若在它们之后再改 subplots_adjust，表会与面板错位。
    ensure_no_crossbleed(fig, list(axes), 0.62)
    place_legend_clear(axC, [("upper right", None), ("lower left", None),
                             ("center right", None)],
                       handles=handlesC, frameon=False, fontsize=6.5)
    add_atrisk(fig, axC, rs["T"].values, rs["E"].values, rs["groupB"].values,
               ["Low", "High"], times)
    if txtA:
        add_footnote(fig, axA, txtA.split("\n"), fs=6.5)
    panel_letter(axC, "C", dx=-0.28)

    r = savefig(fig, "3")
    return r, dict(A=axA, B=axB, C=axC)


# ===================== Figure 4 =====================
def fig4(D):
    res, pcs, label, imm, mut = D["res"], D["pcs"], D["label"], D["imm"], D["mut"]
    fig, axes = plt.subplots(1, 3, figsize=(DC, 3.0))
    fig.subplots_adjust(wspace=0.50)

    ax = axes[0]; ax.set_gid("panel_A")
    for lab, col, nm in [(0, BLUE, "Subtype 1"), (1, RED, "Subtype 2")]:
        m = label == lab
        ax.scatter(pcs[m, 0], pcs[m, 1], s=2.2, color=col, alpha=0.65, lw=0, label=f"{nm} (n = {m.sum()})")
    ax.set_xlabel(f"PC1 ({res['pca_evr'][0]*100:.1f}%)"); ax.set_ylabel(f"PC2 ({res['pca_evr'][1]*100:.1f}%)")
    ax.legend(frameon=False, loc="upper right", fontsize=6.5, markerscale=2.5)
    ax.set_title("k-means subtypes (k = 2)", loc="left", pad=3, fontweight="bold", fontsize=7)
    # ⚠️ 2026-10-04 先生指出 Figure4A 遮挡：silhouette 注记原写死在左下角，
    #    实测有散点落在文字框内。改为按"不压数据/不压图例"自动选位。
    place_text_clear(ax, f"silhouette {res['kmeans']['sil']['2']:.3f}",
                     [(0.03, 0.03, "left", "bottom"),
                      (0.03, 0.10, "left", "bottom"),
                      (0.98, 0.03, "right", "bottom"),
                      (0.98, 0.10, "right", "bottom"),
                      (0.03, 0.97, "left", "top")],
                     fontsize=6.5)
    panel_letter(ax, "A")

    ax = axes[1]; ax.set_gid("panel_B")
    NICE = {"CD8_T": "CD8+ T cells", "CD4_T": "CD4+ T cells", "Treg": "Regulatory T",
            "NK": "NK cells", "B_cell": "B cells", "M1_macro": "M1 macrophage",
            "M2_macro": "M2 macrophage", "DC": "Dendritic cells",
            "Neutrophil": "Neutrophils", "Checkpoint": "Checkpoints",
            "IFN_signature": "Interferon"}
    ii = imm.iloc[::-1].copy()
    yy = np.arange(len(ii))
    cols = [RED if p < 0.05 else GREY for p in ii["p"]]
    ax.barh(yy, ii["diff"], color=cols, height=0.7)
    ax.axvline(0, color="k", lw=0.6)
    ax.set_yticks(yy)
    ax.set_yticklabels([NICE.get(f, f) for f in ii["feature"]], fontsize=6.5)
    lo, hi = float(ii["diff"].min()), float(ii["diff"].max())
    ax.set_xlim(lo * 1.30, hi * 1.95)          # 右侧留白，避免注记压住条形
    ax.set_xlabel("Δ (high − low risk), mean Z")
    ax.set_title("Immune features", loc="left", pad=3, fontweight="bold", fontsize=7)
    # ⚠️ 2026-10-04 先生指出 Figure4B 遮挡：注记原写死在右下角，
    #    而最底一行（Interferon, Δ=+0.115）的条形一直伸到文字框里（实测被盖 6%）。
    place_text_clear(ax, "red, P < 0.05",
                     [(0.97, 0.97, "right", "top"),
                      (0.97, 0.03, "right", "bottom"),
                      (0.03, 0.97, "left", "top")],
                     fontsize=6.5, color=RED)
    panel_letter(ax, "B", dx=-0.34)

    ax = axes[2]; ax.set_gid("panel_C")
    mm = mut.sort_values("high_pct", ascending=True)
    yy = np.arange(len(mm)); h = 0.36
    ax.barh(yy + h / 2, mm["high_pct"], height=h, color=RED, label="High risk")
    ax.barh(yy - h / 2, mm["low_pct"], height=h, color=BLUE, label="Low risk")
    ax.set_yticks(yy); ax.set_yticklabels(mm["gene"], fontsize=6.5)
    ax.set_xlabel("Mutation frequency (%)")
    ax.legend(frameon=False, loc="lower right", fontsize=6.5)
    ax.set_title("Mutations by risk group", loc="left", pad=3, fontweight="bold", fontsize=7)
    panel_letter(ax, "C", dx=-0.34)

    # ⚠️ 2026-10-04 先生指出 Figure4B 遮挡的另一半：'M1 macrophage' /
    #    'M2 macrophage' 这两个长刻度标签横向伸进面板 A 达 11%。自适应间距。
    ensure_no_crossbleed(fig, list(axes), 0.50)

    r = savefig(fig, "4")
    return r, dict(A=axes[0], B=axes[1], C=axes[2])


# ===================== Figure 5 =====================
def fig5(D):
    res, hard, ext, ex14, rs = D["res"], D["hard"], D["ext"], D["ex14"], D["rs"]
    fig = plt.figure(figsize=(DC, 6.6))
    gs = fig.add_gridspec(2, 2, hspace=0.62, wspace=0.40)

    # --- A: external KM
    ax = fig.add_subplot(gs[0, 0]); ax.set_gid("panel_A")
    s = ex14["scoreB"].values; med = np.median(s); grp = (s > med).astype(int)
    times = np.array([0, 12, 24, 36, 48, 60])
    for gi, (col, name) in enumerate([(BLUE, "Low risk"), (RED, "High risk")]):
        mm = grp == gi
        ts, ss = km_curve(ex14["T"].values[mm], ex14["E"].values[mm])
        ax.step(ts, ss, where="post", color=col, lw=1.0, label=name + f" (n = {mm.sum()})")
    ax.set_xlabel("Months"); ax.set_ylabel("Overall survival")
    # R3-m6：同 Figure 1D/3C，横轴截到 60 月与 at-risk 表对齐。
    ax.set_xlim(0, 60); ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, loc="upper right", fontsize=6.5)
    ax.set_title(f"GSE14520, MRG-2 (C = {ext['ModelB']['c_index']:.3f}, P = {ext['ModelB']['p']:.2f})",
                 loc="left", pad=3, fontweight="bold")
    # ⚠️ add_atrisk 必须放在 set_xlabel 之后：它按 xlabel 的实际渲染位置定位，
    #    在空 xlabel 时调用会把表顶到横轴上，随后画出的 xlabel 又压上去（实测踩坑）。
    add_atrisk(fig, ax, ex14["T"].values, ex14["E"].values, grp,
               ["Low", "High"], times)
    panel_letter(ax, "A")

    # --- B: C-index across four estimates
    ax = fig.add_subplot(gs[0, 1]); ax.set_gid("panel_B")
    # R1-M8：嵌套柱改为 **pooled out-of-fold C-index 在 10 个独立随机划分上的均值 ± SD**。
    # 原图用的是「10 折各自 C-index 的均值 ± 折间 SD」——审稿人 R1-M8 指出对折值取均值有偏、
    # 折间 SD/√10 也不是该估计量的标准误。新口径与正文 §3.3 表、图注完全一致。
    _npj = os.path.join(DATA, "revised", "nested_pooled.json")
    if os.path.exists(_npj):
        acs = json.load(open(_npj, encoding="utf-8"))["across_splits"]
        nestA = (acs["pooled_ModelA"]["mean"], acs["pooled_ModelA"]["sd"])
        nestB = (acs["pooled_MRG2"]["mean"], acs["pooled_MRG2"]["sd"])
        nestlab = "Nested pooled\n(10 splits)"
    else:                                   # 兜底：旧口径（缺产物时不让整图崩掉）
        nb, na = hard["nested_cv"]["modelB"], hard["nested_cv"]["modelA"]
        nestA, nestB = (na["mean"], na["sd"]), (nb["mean"], nb["sd"])
        nestlab = "Nested\n10-fold"
        print("  [warn] 缺少 数据/revised/nested_pooled.json，Figure 5B 退回旧口径")
    # ---- 重排（R3-m13）：原先 7 根柱一字排开、每柱两行标签，在 ~2.8 in 宽的
    # 面板里横排放不下 —— 实测渲染成「Model AMRG-2Model A…」连读。
    # 改为**按估计来源分三组**（apparent / nested / external），组内 Model A 与
    # MRG-2 并排、以斜纹区分，再单列一根 proliferation 对照柱。四个 x 刻度即可。
    ciA = (ext["ModelA"]["c_index_CI"][1] - ext["ModelA"]["c_index_CI"][0]) / 3.92
    ciB = (ext["ModelB"]["c_index_CI"][1] - ext["ModelB"]["c_index_CI"][0]) / 3.92
    groups = [("Apparent", GREY,
               [(res["modelA"]["c_index"], None), (res["modelB"]["c_index"], None)]),
              (nestlab, BLUE, [nestA, nestB]),
              ("External\n(GSE14520)", RED,
               [(ext["ModelA"]["c_index"], ciA), (ext["ModelB"]["c_index"], ciB)])]
    for gi, (glab, col, vals) in enumerate(groups):
        for mi, (v, err) in enumerate(vals):
            x = gi + (mi - 0.5) * 0.40
            ax.bar(x, v - 0.5, bottom=0.5, color=col, width=0.34,
                   hatch=("" if mi == 0 else "///"),
                   edgecolor="#3A3A3A", linewidth=0.4,
                   yerr=(err if err else 0), capsize=1.6,
                   error_kw=dict(lw=0.7, ecolor="k"))
    XP = 3.15
    ax.bar(XP, ext["Prolif"]["c_index"] - 0.5, bottom=0.5, color=ORANGE, width=0.40)
    ax.axhline(0.5, color="k", ls="--", lw=0.7)
    ax.set_xticks([0, 1, 2, XP])
    # R1-M8：把 "Nested pooled (10 splits)" 压成两行短标签 —— 原写法在 2.79 in 宽的面板里
    # 与右邻 "External (GSE14520)" 的横向投影重叠 4%（figcheck 判据 C）。队列来源写进
    # 面板标题与图注，刻度只留最短的区分词。
    ax.set_xticklabels(["Apparent", "Nested\npooled", "External", "Proliferation"],
                       fontsize=6.5)
    ax.set_xlim(-0.55, XP + 0.55)
    ax.set_ylabel("Harrell's C-index"); ax.set_ylim(0.5, 0.78)
    # R3-m4：面板级图例 —— 来源已写进 x 刻度，此处只区分两个模型（斜纹）。
    ax.legend(handles=[Patch(facecolor="white", edgecolor="#3A3A3A",
                             label="Model A (23 genes)"),
                       Patch(facecolor="white", edgecolor="#3A3A3A", hatch="///",
                             label="MRG-2 (2 genes)")],
              loc="upper left", frameon=False, fontsize=6.5, ncol=1,
              handlelength=1.0, handletextpad=0.4, borderpad=0.2, labelspacing=0.25)
    ax.set_title("Discrimination across estimates", loc="left", pad=3, fontweight="bold")
    panel_letter(ax, "B", dx=-0.20)

    # --- C: random-panel null distributions
    ax = fig.add_subplot(gs[1, 0]); ax.set_gid("panel_C")
    b1 = np.load(os.path.join(DATA, "random_panel_TCGA.npy"))
    b2 = np.load(os.path.join(DATA, "random_panel_GSE14520.npy"))
    lo = min(b1.min(), b2.min()); hi = max(b1.max(), b2.max())
    bins = np.linspace(lo, hi, 46)
    ax.hist(b1, bins=bins, color=BLUE, alpha=0.55, lw=0, density=True)
    ax.hist(b2, bins=bins, color=RED, alpha=0.45, lw=0, density=True)
    ax.axvline(hard["random_panel"]["observed_MRG2"], color=BLUE, lw=1.2, ls="-")
    ax.axvline(ext["ModelB"]["c_index"], color=RED, lw=1.2, ls="-")
    # ⚠️ 2026-10-04 先生指出 Figure5C 遮挡：两条注记原用白底半透明框压在建图上方
    #    （GSE14520 那条实测被柱盖 38%），而白底框盖数据属违规。
    #    改为：① 先在顶端留出 55% 余量，② 注记与图例都按"不压数据"自动选位。
    ax.set_ylim(0, ax.get_ylim()[1] * 1.75)
    ax.set_xlabel("C-index of a random two-gene panel"); ax.set_ylabel("Density")
    # R3-m4：补面板级图例，区分两层零分布。
    place_legend_clear(ax, [("upper left", None), ("upper right", None)],
                       handles=[Patch(color=BLUE, label="TCGA-LIHC null"),
                                Patch(color=RED, label="GSE14520 null")],
                       frameon=False, fontsize=6.5,
                       handlelength=1.0, handletextpad=0.4, borderpad=0.2)
    # ⚠️ 注记右边缘必须与参照竖线**留出间隙**：竖线现按逐顶点加密采样，
    #    紧贴（Figure5C 原为 0.97 vs 线在 0.99）会被判为压线。
    place_text_clear(ax, "MRG-2 in TCGA\n(>100% of null)",
                     [(0.94, 0.97, "right", "top"),
                      (0.94, 0.72, "right", "top"),
                      (0.55, 0.97, "right", "top"),
                      (0.03, 0.97, "left", "top")],
                     fontsize=6.5, color=BLUE)
    place_text_clear(ax, "MRG-2 in GSE14520\n(47th percentile)",
                     [(0.35, 0.72, "right", "top"),
                      (0.35, 0.60, "right", "top"),
                      (0.94, 0.50, "right", "top"),
                      (0.35, 0.44, "right", "top")],
                     fontsize=6.5, color=RED)
    ax.set_title("Null distribution, 3,000 random pairs", loc="left", pad=3, fontweight="bold")
    panel_letter(ax, "C", dx=-0.22)

    # --- D: ten-seed π
    ax = fig.add_subplot(gs[1, 1]); ax.set_gid("panel_D")
    seeds = [str(s) for s in hard["seed_replication"]["seeds"]]
    kk = [hard["seed_replication"]["per_seed"][s]["KIF15"] for s in seeds]
    mk = [hard["seed_replication"]["per_seed"][s]["MAFG"] for s in seeds]
    xs = np.arange(len(seeds))
    ax.axhline(0.75, color="k", ls="--", lw=0.8)
    ax.plot(xs, kk, "o-", color=BLUE, ms=3, lw=0.8, label="KIF15")
    ax.plot(xs, mk, "s-", color=RED, ms=3, lw=0.8, label="MAFG")
    for i, v in enumerate(mk):
        if v < 0.75:
            ax.plot([i], [v], "o", mfc="none", mec=RED, ms=7, mew=1.0)
    ax.set_xticks(xs); ax.set_xticklabels(seeds, fontsize=6.5, rotation=60)
    ax.set_xlabel("Bootstrap seed"); ax.set_ylabel("Selection frequency π")
    ax.set_ylim(0.6, 1.0)
    ax.legend(frameon=False, loc="lower right", fontsize=6.5, ncol=2)
    # R3-m13：注记原为两行，右半段与右下角图例横向相撞（实测重叠）。
    # 只留一行短注记；"two-gene set collapses to KIF15" 的完整解释已在图注中。
    ax.text(0.02, 0.03, "circled: π < 0.75",
            transform=ax.transAxes, fontsize=6.5, va="bottom")
    ax.set_title("Stability under ten independent seeds", loc="left", pad=3, fontweight="bold")
    panel_letter(ax, "D", dx=-0.20)

    r = savefig(fig, "5")
    return r, {k: v for k, v in zip("ABCD", fig.axes)}


# ===================== Figure 6 =====================
def fig6(D):
    tvn = D["tvn"]
    v = pd.to_numeric(tvn.iloc[:, 0], errors="coerce").dropna().sort_values()
    fig, axes = plt.subplots(1, 2, figsize=(DC, 6.8))
    fig.subplots_adjust(wspace=0.55)
    n = len(v); half = int(np.ceil(n / 2))
    for pi, (ax, chunk) in enumerate(zip(axes, [v.iloc[:half], v.iloc[half:]])):
        ax.set_gid(f"panel_{'AB'[pi]}")
        cols = [RED if x > 1 else (BLUE if x < -1 else GREY) for x in chunk.values]
        yy = np.arange(len(chunk))
        ax.barh(yy, chunk.values, color=cols, height=0.75)
        ax.set_yticks(yy); ax.set_yticklabels(chunk.index, fontsize=6.5)
        ax.axvline(0, color="k", lw=0.6)
        ax.axvline(1, color="k", ls="--", lw=0.6); ax.axvline(-1, color="k", ls="--", lw=0.6)
        ax.set_xlabel("Mean Z vs reference normal liver")
        ax.set_ylim(-0.8, len(chunk) - 0.2)
        panel_letter(ax, "AB"[pi], dx=-0.20)
    # ⚠️ 2026-10-04 先生指出 Figure6A 遮挡：图例原固定在右上角且 frameon=False，
    #    而顶部若干行（CALCRL/ZBTB8A/BRWD3…）的正向条形正好穿过图例文字，
    #    实测被盖 7%。面板下半部各行的条形**全为负向**（FERMT2/ADAMTS2/TIAM1…），
    #    右半区天然为空 → 改为按"不压数据"自动选位，优先右下角。
    legend_clear_with_xheadroom(
        axes[0],
        [Patch(color=RED, label="Z > 1 (n = 22)"),
         Patch(color=BLUE, label="Z < −1 (n = 11)"),
         Patch(color=GREY, label="|Z| ≤ 1")],
        ["lower right", "upper right"],
        frameon=False, fontsize=6.5)
    # 两个面板共用横轴范围，避免 A 为放图例而单独加宽后左右面板刻度不一致。
    axes[1].set_xlim(*axes[0].get_xlim())
    axes[0].set_title("Panel genes in tumour vs reference normal liver",
                      loc="left", pad=3, fontweight="bold")
    r = savefig(fig, "6")
    return r, dict(A=axes[0], B=axes[1])


def main():
    print("字体:", FONT)
    D = load()
    report = {}
    for fn, name in [(fig1, "1"), (fig2, "2"), (fig3, "3"), (fig4, "4"), (fig5, "5"), (fig6, "6")]:
        try:
            r, axmap = fn(D)
            report[name] = {"png_px": r[:2], "aspect": round(r[2], 3),
                            "panels_expected": sorted(axmap)}
        except Exception as e:
            import traceback
            print(f"  ❌ Figure{name} 失败: {e}")
            traceback.print_exc()
            report[name] = {"error": str(e)}
    json.dump(report, open(os.path.join(DATA, "fig_v2_report.json"), "w"), indent=2)
    print("\n汇总:", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
