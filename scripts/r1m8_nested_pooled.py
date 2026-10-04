#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R1-M8 修复 —— 完全嵌套 CV 的正确统计量：pooled out-of-fold C-index + 多随机划分方差。

审稿人 R1 的第 8 条 Major 意见（原文）：
  「§3.3 'the nested value of 0.576, with a standard error of 0.032 over ten folds,
   sits only about 2.4 standard errors above chance' ...
   ①标准做法是把各折 held-out 预测拼起来算一个 pooled C-index；对折 C-index 直接
     取均值是有偏估计（各折事件率不同）。
   ②SD/√10 不是该估计量的标准误——K 折的折间 C-index 共享训练数据、且分折仅用
     单一随机划分（Bengio–Grandvalet 早已指出 CV 方差的这种估计偏低）。
   ③(0.576−0.5)/0.032 = 2.4 把折 C-index 当独立正态样本，单位数仅 10。」
  具体修改：①报告 pooled out-of-fold C-index 为主；②嵌套重复 ≥10 个随机划分，
  报折间/划分间方差；③对 optimism（约 0.10）给出 bootstrap CI；④删去或以恰当
  不确定性重写「2.4 个标准误高于随机」。

本脚本只做这一件事，不动任何其它分析：
  [0] 单划分（预设 seed=42）pooled out-of-fold C-index  —— 主统计量
  [1] NS=10 个独立随机划分下的 pooled 统计量（均值 / SD / 范围 / 分位）
  [2] optimism（apparent − pooled）的配对 bootstrap 95% CI（预设划分）
  [3] 折间 C-index 的分布（保留为次要信息，并给出折间 SD 与「折数修正」后的口径）

⚠️ 与既有一致性：划分 0 的折叠分配与 bootstrap 种子与 stats_hardening.py 的
   [2] 完全一致（outer seed=42，inner seed_boot=2026+k，nboot=100，seed_cv=42），
   因此划分 0 的「折 C-index 均值」必须复现沉积值 0.576，作为本脚本的自我一致性断言。

产出
  数据/revised/nested_pooled.json
  补充材料/Table_S10b_嵌套pooled与多划分.csv
"""
import os, sys, json, time, math
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
SUPP = os.path.join(BASE, "补充材料")
sys.path.insert(0, HERE)

import stats_hardening as SH          # 复用 load / modelB_on / modelA_on / C / paired_bootstrap_cdiff

SEED = 42
NFOLD = 10
NBOOT = 100          # 与沉积的完全嵌套口径一致
NS = 10              # 独立随机划分重复数（审稿人要求 ≥10）
DEPOSITED_MEAN_B = 0.576   # stats_hardening.json 的 nested_cv.modelB.mean


def one_split(Xz, T, E, outer_seed):
    """跑一个完全嵌套 10 折划分，返回逐患者 held-out 预测与辅助信息。"""
    n = len(Xz)
    rng = np.random.default_rng(outer_seed)
    folds = np.array_split(rng.permutation(n), NFOLD)

    sB = np.full(n, np.nan)          # Model B（MRG 流水线）held-out 线性预测
    sA = np.full(n, np.nan)          # Model A（单因素→L2 岭）held-out 线性预测
    foldB, foldA, genesB, hitsA = [], [], [], []

    for k, f in enumerate(folds):
        tr = np.setdiff1d(np.arange(n), f)
        Xtr, Xte = Xz.iloc[tr], Xz.iloc[f]
        SH._Tf, SH._Ef = T[tr], E[tr]        # lasso_path_cv 内部用全局 _Tf/_Ef

        # ---- Model B：整条 MRG 流水线（LASSO-CV → 1SE → 200/100-bootstrap 稳定性 → 后向消除）
        try:
            r = SH.modelB_on(Xtr, T[tr], E[tr], nboot=NBOOT,
                             seed_boot=2026 + 1000 * (outer_seed - SEED) + k,
                             seed_cv=SEED)
            g = r["final_genes"]
            genesB.append(g)
            if g:
                co = np.array([r["coef"][x] for x in g])
                sc = Xte[g].values @ co
                sB[f] = sc
                foldB.append(SH.C(T[f], E[f], sc))
            else:
                foldB.append(None)
        except Exception as ex:                        # noqa: BLE001
            genesB.append(None); foldB.append(None)
            print("      [warn] fold%d ModelB: %s" % (k + 1, ex))

        # ---- Model A：单因素 P<0.05 → L2 岭
        try:
            ra = SH.modelA_on(Xtr, T[tr], E[tr])
            if ra.get("coef"):
                kk = list(ra["coef"])
                co = np.array([ra["coef"][x] for x in kk])
                sc = Xte[kk].values @ co
                sA[f] = sc
                foldA.append(SH.C(T[f], E[f], sc)); hitsA.append(ra["n_hits"])
            else:
                foldA.append(None); hitsA.append(0)
        except Exception as ex:                        # noqa: BLE001
            foldA.append(None); hitsA.append(None)
            print("      [warn] fold%d ModelA: %s" % (k + 1, ex))

        print("      split(outer=%d) fold%2d: B%s C=%s | A %s基因 C=%s"
              % (outer_seed, k + 1,
                 ("+" + str(len(genesB[-1]))) if genesB[-1] else "-",
                 ("%.3f" % foldB[-1]) if foldB[-1] is not None else "  -  ",
                 hitsA[-1],
                 ("%.3f" % foldA[-1]) if foldA[-1] is not None else "  -  "))

    SH._Tf, SH._Ef = T, E

    def pooled(s):
        ok = np.isfinite(s)
        if ok.sum() < 10 or E[ok].sum() < 5:
            return None
        return float(SH.C(T[ok], E[ok], s[ok]))

    return {"outer_seed": outer_seed,
            "pooled_B": pooled(sB), "pooled_A": pooled(sA),
            "fold_B": [None if x is None else round(float(x), 4) for x in foldB],
            "fold_A": [None if x is None else round(float(x), 4) for x in foldA],
            "mean_fold_B": float(np.mean([x for x in foldB if x is not None])) if any(x is not None for x in foldB) else None,
            "mean_fold_A": float(np.mean([x for x in foldA if x is not None])) if any(x is not None for x in foldA) else None,
            "genes_B": genesB, "hits_A": hitsA,
            "oof_B": sB, "oof_A": sA}


def main():
    t0 = time.time()
    df, genes, pg = SH.load()
    T = df["T"].values.astype(float)
    E = df["E"].values.astype(int)
    X = df[genes]
    Xz = (X - X.mean()) / X.std()
    SH._Tf, SH._Ef = T, E
    n = len(df)
    print("队列 n=%d 死亡=%d 基因=%d" % (n, E.sum(), len(genes)))

    # ---------- [1] 全数据 apparent 与系数（用于 optimism） ----------
    print("[1] 全数据 apparent 复现 ...")
    full = SH.modelB_on(Xz, T, E, nboot=200, seed_boot=2026)
    cb = full["coef"]
    app_B = full["c_index_apparent"]
    sB_app = Xz[list(cb)].values @ np.array([cb[g] for g in cb])
    rs = pd.read_csv(os.path.join(DATA, "risk_scores.csv"), index_col=0)
    sA_app = rs["scoreA"].reindex(df.index).values
    app_A = SH.C(T, E, sA_app)
    print("    apparent: MRG-2 %.4f | Model A %.4f (沉积 0.6767 / 0.6840)"
          % (app_B, app_A))

    # ---------- [2] NS 个独立随机划分 ----------
    print("[2] %d 个独立随机划分（每划分 %d 折完全嵌套，nboot=%d）..." % (NS, NFOLD, NBOOT))
    splits = []
    for s in range(NS):
        outer = SEED + s
        print("  --- 划分 %d/%d (outer_seed=%d) ---" % (s + 1, NS, outer))
        r = one_split(Xz, T, E, outer)
        print("    pooled: B %s | A %s   (折均值 B %.4f)"
              % (("%.4f" % r["pooled_B"]) if r["pooled_B"] else "NA",
                 ("%.4f" % r["pooled_A"]) if r["pooled_A"] else "NA",
                 r["mean_fold_B"] if r["mean_fold_B"] else float("nan")))
        splits.append(r)

    pB = [r["pooled_B"] for r in splits if r["pooled_B"] is not None]
    pA = [r["pooled_A"] for r in splits if r["pooled_A"] is not None]
    mB = [r["mean_fold_B"] for r in splits if r["mean_fold_B"] is not None]
    mA = [r["mean_fold_A"] for r in splits if r["mean_fold_A"] is not None]

    # ---------- [3] 自我一致性：划分 0 的折均值须复现沉积值 ----------
    s0 = splits[0]
    assert s0["outer_seed"] == SEED
    got = s0["mean_fold_B"]
    print("\n[3] 自我一致性：划分0 折均值 %.4f vs 沉积 %.4f" % (got, DEPOSITED_MEAN_B))
    assert abs(got - DEPOSITED_MEAN_B) < 0.002, \
        "划分 0 未能复现沉积的折均值 %.4f（得到 %.4f）—— 流水线已漂移，勿据此改稿" % (DEPOSITED_MEAN_B, got)

    # ---------- [4] optimism 的配对 bootstrap CI（预设划分） ----------
    print("[4] optimism 配对 bootstrap ...")
    opt_B = SH.paired_bootstrap_cdiff(T, E, sB_app, s0["oof_B"], B=2000, seed=7)
    opt_A = SH.paired_bootstrap_cdiff(T, E, sA_app, s0["oof_A"], B=2000, seed=7)
    opt_B["apparent"] = app_B; opt_B["pooled"] = s0["pooled_B"]
    opt_A["apparent"] = app_A; opt_A["pooled"] = s0["pooled_A"]

    out = {
        "note": "R1-M8 修复：pooled out-of-fold C-index 为主统计量 + 多随机划分方差",
        "design": {"n": n, "events": int(E.sum()), "n_genes": len(genes),
                   "fold": NFOLD, "inner_nboot": NBOOT, "n_random_splits": NS,
                   "outer_seeds": [r["outer_seed"] for r in splits]},
        "apparent": {"MRG2": app_B, "ModelA": app_A},
        "primary_split": {                                  # 预设划分（seed=42）——与沉积口径同划分
            "outer_seed": s0["outer_seed"],
            "pooled_oof_C_MRG2": s0["pooled_B"],
            "pooled_oof_C_ModelA": s0["pooled_A"],
            "mean_of_fold_C_MRG2": s0["mean_fold_B"],
            "mean_of_fold_C_ModelA": s0["mean_fold_A"],
            "fold_C_MRG2": s0["fold_B"], "fold_C_ModelA": s0["fold_A"],
            "sd_of_fold_C_MRG2": float(np.std([x for x in s0["fold_B"] if x is not None])),
            "sd_of_fold_C_ModelA": float(np.std([x for x in s0["fold_A"] if x is not None])),
            "fold_genes_MRG2": s0["genes_B"], "fold_hits_ModelA": s0["hits_A"],
        },
        "random_splits": [{k: v for k, v in r.items() if not k.startswith("oof")} for r in splits],
        "across_splits": {
            "pooled_MRG2": {"mean": float(np.mean(pB)), "sd": float(np.std(pB)),
                            "min": float(min(pB)), "max": float(max(pB)),
                            "median": float(np.median(pB)), "n": len(pB),
                            "values": [round(x, 4) for x in pB]},
            "pooled_ModelA": {"mean": float(np.mean(pA)), "sd": float(np.std(pA)),
                              "min": float(min(pA)), "max": float(max(pA)),
                              "median": float(np.median(pA)), "n": len(pA),
                              "values": [round(x, 4) for x in pA]},
            "mean_of_fold_MRG2": {"mean": float(np.mean(mB)), "sd": float(np.std(mB)),
                                  "min": float(min(mB)), "max": float(max(mB))},
            "mean_of_fold_ModelA": {"mean": float(np.mean(mA)), "sd": float(np.std(mA)),
                                    "min": float(min(mA)), "max": float(max(mA))},
        },
        "optimism": {"MRG2": opt_B, "ModelA": opt_A},
        "runtime_s": round(time.time() - t0, 1),
    }

    os.makedirs(os.path.join(DATA, "revised"), exist_ok=True)
    jp = os.path.join(DATA, "revised", "nested_pooled.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # ---------- 补充表 S10b ----------
    rows = []
    for i, r in enumerate(splits):
        rows.append({"划分": "预设 seed=42" if i == 0 else "额外划分 %d" % i,
                     "outer_seed": r["outer_seed"],
                     "pooled_oof_C_MRG2": _r(r["pooled_B"]),
                     "pooled_oof_C_ModelA": _r(r["pooled_A"]),
                     "折C均值_MRG2": _r(r["mean_fold_B"]),
                     "折C均值_ModelA": _r(r["mean_fold_A"]),
                     "折C_SD_MRG2": _r(float(np.std([x for x in r["fold_B"] if x is not None]))),
                     "折C_SD_ModelA": _r(float(np.std([x for x in r["fold_A"] if x is not None]))),
                     "MRG2折内基因集": ";".join("+".join(g) if g else "空" for g in r["genes_B"])})
    rows.append({"划分": "★ 汇总（%d 个随机划分）" % len(pB), "outer_seed": "",
                 "pooled_oof_C_MRG2": "均值 %s (SD %s, %s–%s)" % (
                     _r(np.mean(pB)), _r(np.std(pB)), _r(min(pB)), _r(max(pB))),
                 "pooled_oof_C_ModelA": "均值 %s (SD %s, %s–%s)" % (
                     _r(np.mean(pA)), _r(np.std(pA)), _r(min(pA)), _r(max(pA))),
                 "折C均值_MRG2": "均值 %s (SD %s)" % (_r(np.mean(mB)), _r(np.std(mB))),
                 "折C均值_ModelA": "均值 %s (SD %s)" % (_r(np.mean(mA)), _r(np.std(mA))),
                 "折C_SD_MRG2": "", "折C_SD_ModelA": "", "MRG2折内基因集": ""})
    csv = os.path.join(SUPP, "Table_S10b_嵌套pooled与多划分.csv")
    pd.DataFrame(rows).to_csv(csv, index=False, encoding="utf-8-sig")
    open(os.path.join(SUPP, "Table_S10b_说明.md"), "w", encoding="utf-8").write(
        "# Table S10b 说明\n\n"
        "**用途**：R1-M8。原稿以「10 折 C-index 的均值 ± SD/√10」报告完全嵌套表现，"
        "并把 0.576 描述为「约 2.4 个标准误高于随机」。本表以标准口径替换之：\n\n"
        "- **主统计量 = pooled out-of-fold C-index**：把十折 held-out 线性预测拼成一条向量，"
        "对全部 %d 例患者算**一个** C-index（各折事件率不同时，对折值取均值是有偏的）。\n"
        "- **%d 个独立随机划分**：对折分配用 %d 个不同种子重复整条嵌套流程，"
        "报划分间均值与 SD，替代「SD/√10」。\n"
        "- 划分 0 的折分配与内部 bootstrap 种子与原稿完全一致，其折内 C-index 均值复现沉积的 0.576，"
        "作为本表的自我一致性校验。\n" % (n, NS, NS))

    print("\npooled（%d 个划分）MRG-2: %.4f ± %.4f  [%.4f–%.4f]"
          % (len(pB), np.mean(pB), np.std(pB), min(pB), max(pB)))
    print("pooled（%d 个划分）Model A: %.4f ± %.4f  [%.4f–%.4f]"
          % (len(pA), np.mean(pA), np.std(pA), min(pA), max(pA)))
    print("折均值（原口径，%d 个划分）MRG-2: %.4f ± %.4f" % (len(mB), np.mean(mB), np.std(mB)))
    print("optimism MRG-2: apparent %.4f − pooled %.4f = %.4f (95%%CI %.4f–%.4f)"
          % (app_B, s0["pooled_B"], opt_B["diff"], opt_B["lo"], opt_B["hi"]))
    print("\n写出 %s\n     %s\n用时 %.1fs" % (os.path.relpath(jp, BASE), os.path.relpath(csv, BASE), out["runtime_s"]))


def _r(x):
    return None if x is None else round(float(x), 4)


if __name__ == "__main__":
    main()
