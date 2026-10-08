#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIHC —— 统计加固 v2（纯本地，不联网）

修正 v1 的两处口径错误：
  (1) Model B 的 LASSO 是在**全部 91 个基因**上跑的（不是先做单因素筛选）—— 与
      lihc_pipeline.py 一致；v1 误加了单因素筛选步骤。
  (2) 配对 bootstrap / 随机面板基准使用**正确的 MRG-2 分数**（KIF15+MAFG，C=0.6767）。

计算项
  [1] 复现性核对（全数据 Model B）→ 与沉积值对账
  [2] 完全嵌套 10 折 CV：Model B 流程 与 Model A 流程 各一遍
  [3] bootstrap 种子的可重复性（10 个独立种子）→ π 的稳健性
  [4] π 阈值敏感性 + Meinshausen–Bühlmann 上界
  [5] 配对 bootstrap C-index 差值（MRG-2 / Model A / 增殖评分）
  [6] 随机 2 基因面板基准（3000 次）
产出：数据/stats_hardening.json
"""
import os, json, math, time, warnings
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from sksurv.metrics import concordance_index_censored
from sksurv.linear_model import CoxnetSurvivalAnalysis
from sksurv.util import Surv

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
SEED = 42
ALPHAS = np.logspace(-1.2, -3.0, 60)
PI_THR = 0.75


def C(t, e, s):
    return float(concordance_index_censored(np.asarray(e, bool), np.asarray(t, float),
                                            np.asarray(s, float))[0])


def load():
    coh = pd.read_csv(os.path.join(DATA, "analysis_cohort.csv"), index_col=0)
    stab = pd.read_csv(os.path.join(DATA, "modelB_stability.csv"))
    genes = [g for g in stab["gene"] if g in coh.columns]
    df = coh.copy()
    df["T"] = df["OS_MONTHS"].astype(float)
    df["E"] = df["OS_EVENT"].astype(int)
    df = df[df["T"] > 0]
    prolif = pd.read_csv(os.path.join(DATA, "prolif_expr_z.csv"), index_col=0)
    pg = list(prolif.columns)
    pr = prolif.reindex(df.index)
    for c in pg:
        df["__P_" + c] = pr[c].values
    df["PROLIF"] = pr[pg].mean(axis=1).values
    return df, genes, pg


def lasso_path_cv(Xm, y, n_folds=10, seed=SEED):
    est = CoxnetSurvivalAnalysis(l1_ratio=1.0, alphas=ALPHAS.tolist(),
                                 fit_baseline_model=False).fit(Xm, y)
    rng = np.random.default_rng(seed)
    folds = np.array_split(rng.permutation(len(Xm)), n_folds)
    cv = []
    for a in est.alphas_:
        cs = []
        for f in folds:
            tr = np.setdiff1d(np.arange(len(Xm)), f)
            try:
                m = CoxnetSurvivalAnalysis(l1_ratio=1.0, alphas=[a]).fit(Xm[tr], y[tr])
                cs.append(C(_Tf[f], _Ef[f], Xm[f] @ m.coef_[:, 0]))
            except Exception:
                pass
        cv.append(np.mean(cs) if cs else np.nan)
    cv = np.array(cv)
    i_min = int(np.nanargmax(cv))
    se = np.nanstd(cv) / math.sqrt(n_folds)
    i_1se = int(np.where(cv >= cv[i_min] - se)[0][0])
    return est, cv, i_min, i_1se, float(est.alphas_[i_1se]), float(est.alphas_[i_min])


_Tf = None; _Ef = None


def modelB_on(Xz, T, E, nboot=200, seed_boot=2026, pi_thr=PI_THR, seed_cv=SEED, genes=None):
    """在给定数据上跑一遍 Model B（全部候选基因直接进 LASSO）。"""
    genes = list(Xz.columns) if genes is None else genes
    Xm = Xz[genes].values
    y = Surv.from_arrays(E.astype(bool), T.astype(float))
    est, cv, i_min, i_1se, a1se, amin = lasso_path_cv(Xm, y, seed=seed_cv)
    rr = np.random.default_rng(seed_boot)
    freq = {g: 0 for g in genes}; nsel = []
    for b in range(nboot):
        bs = rr.integers(0, len(Xm), len(Xm))
        try:
            m = CoxnetSurvivalAnalysis(l1_ratio=1.0, alphas=[a1se]).fit(Xm[bs], y[bs])
            sel = [g for g, c in zip(genes, m.coef_[:, 0]) if abs(c) > 1e-8]
            for g in sel:
                freq[g] += 1
            nsel.append(len(sel))
        except Exception:
            pass
    fr = {g: freq[g] / nboot for g in genes}
    stable = sorted([g for g in genes if fr[g] >= pi_thr], key=lambda g: -fr[g])
    cur, removed = list(stable), []
    while len(cur) > 1:
        dd = Xz[cur].copy(); dd["T"] = T; dd["E"] = E
        try:
            cph = CoxPHFitter().fit(dd, "T", "E")
        except Exception:
            break
        if (cph.summary["p"] >= 0.05).any() and len(cur) > 2:
            drop = cph.summary["p"].idxmax(); removed.append(drop)
            cur = [g for g in cur if g != drop]
        else:
            break
    res = {"pi": fr, "stable": stable, "final_genes": cur, "removed": removed,
           "alpha_1se": a1se, "alpha_min": amin, "nsel_median": int(np.median(nsel)) if nsel else None,
           "nsel_range": [int(min(nsel)), int(max(nsel))] if nsel else None,
           "nsel_iqr": [int(np.percentile(nsel, 25)), int(np.percentile(nsel, 75))] if nsel else None}
    if cur:
        dd = Xz[cur].copy(); dd["T"] = T; dd["E"] = E
        cph = CoxPHFitter().fit(dd, "T", "E")
        res["coef"] = {g: float(cph.params_[g]) for g in cur}
        res["coef_p"] = {g: float(cph.summary.loc[g, "p"]) for g in cur}
        res["c_index_apparent"] = C(T, E, cph.predict_log_partial_hazard(dd).values)
        res["score"] = cph.predict_log_partial_hazard(dd).values
    return res


def modelA_on(Xz, T, E, penalizer=1.0):
    """Model A：单因素筛选(P<0.05) → L2 岭多因素。"""
    ps = {}
    for g in Xz.columns:
        dd = pd.DataFrame({"x": Xz[g].values, "T": T, "E": E})
        try:
            ps[g] = float(CoxPHFitter().fit(dd, "T", "E").summary.loc["x", "p"])
        except Exception:
            ps[g] = 1.0
    hits = [g for g in Xz.columns if ps[g] < 0.05]
    if not hits:
        return {"hits": [], "c_index_apparent": None}
    dd = Xz[hits].copy(); dd["T"] = T; dd["E"] = E
    cph = CoxPHFitter(penalizer=penalizer).fit(dd, "T", "E")
    return {"hits": hits, "n_hits": len(hits),
            "c_index_apparent": C(T, E, cph.predict_log_partial_hazard(dd).values),
            "coef": {g: float(cph.params_[g]) for g in hits}}


def paired_bootstrap_cdiff(t, e, s1, s2, B=2000, seed=7):
    rng = np.random.default_rng(seed)
    n = len(t); d = []
    base = C(t, e, s1) - C(t, e, s2)
    for _ in range(B):
        idx = rng.integers(0, n, n)
        if e[idx].sum() < 5:
            continue
        d.append(C(t[idx], e[idx], s1[idx]) - C(t[idx], e[idx], s2[idx]))
    d = np.array(d)
    return {"diff": base, "lo": float(np.percentile(d, 2.5)), "hi": float(np.percentile(d, 97.5)),
            "p_two_sided": float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))),
            "B_used": int(len(d))}


def main():
    global _Tf, _Ef
    t0 = time.time(); out = {}
    df, genes, pg = load()
    T = df["T"].values.astype(float); E = df["E"].values.astype(int)
    _Tf, _Ef = T, E          # lasso_path_cv 内部计算 C-index 用
    X = df[genes]
    Xz = (X - X.mean()) / X.std()
    out["cohort"] = {"n": len(df), "events": int(E.sum()), "n_genes": len(genes),
                     "n_prolif": len(pg)}
    print(f"队列 n={len(df)} deaths={E.sum()} genes={len(genes)}")

    # ---------- [1] 全数据复现 ----------
    print("[1] 全数据 Model B 复现 ...")
    full = modelB_on(Xz, T, E, nboot=200, seed_boot=2026)
    out["full"] = {k: v for k, v in full.items() if k != "score"}
    out["full"]["stability_table"] = {g: round(v, 4) for g, v in
                                      sorted(full["pi"].items(), key=lambda kv: -kv[1])[:12]}
    print("    ∈π≥0.75:", full["stable"], "最终:", full["final_genes"],
          "C=%.4f" % full["c_index_apparent"], "(沉积值 0.6767)")

    # ---------- [3] 种子可重复性 ----------
    print("[3] bootstrap 种子可重复性（10 个独立种子）...")
    seeds = [2026, 2027, 1, 2, 3, 42, 100, 555, 777, 1234]
    rep = {}
    for sd in seeds:
        r = modelB_on(Xz, T, E, nboot=200, seed_boot=sd)
        rep[str(sd)] = {"KIF15": round(r["pi"]["KIF15"], 4), "MAFG": round(r["pi"]["MAFG"], 4),
                        "AKNA": round(r["pi"]["AKNA"], 4), "PPP1R10": round(r["pi"]["PPP1R10"], 4),
                        "stable_set": r["stable"], "nsel_median": r["nsel_median"]}
        print(f"    seed={sd:5d} KIF15={r['pi']['KIF15']:.3f} MAFG={r['pi']['MAFG']:.3f} "
              f"→ π≥0.75 = {r['stable']}")
    mk = [rep[str(s)]["MAFG"] for s in seeds]; kk = [rep[str(s)]["KIF15"] for s in seeds]
    out["seed_replication"] = {
        "per_seed": rep, "seeds": seeds,
        "KIF15": {"min": min(kk), "max": max(kk), "mean": float(np.mean(kk))},
        "MAFG": {"min": min(mk), "max": max(mk), "mean": float(np.mean(mk)),
                 "n_below_thr": int(sum(1 for v in mk if v < PI_THR)), "n_seeds": len(seeds)},
        "n_seeds_with_2gene": int(sum(1 for s in seeds if len(rep[str(s)]["stable_set"]) == 2)),
        "n_seeds_with_1gene": int(sum(1 for s in seeds if len(rep[str(s)]["stable_set"]) == 1)),
    }
    print("    KIF15 范围 %.3f–%.3f ；MAFG 范围 %.3f–%.3f（%d/%d 种子低于 0.75）"
          % (min(kk), max(kk), min(mk), max(mk),
             out["seed_replication"]["MAFG"]["n_below_thr"], len(seeds)))

    # ---------- [4] π 敏感性 + MB 上界 ----------
    sens = {}
    for thr in (0.60, 0.65, 0.70, 0.75, 0.80, 0.85):
        sens[f"{thr:.2f}"] = sorted([g for g in genes if full["pi"][g] >= thr],
                                    key=lambda g: -full["pi"][g])
    out["pi_sensitivity_seed2026"] = sens
    q = full["nsel_range"][1]; p = len(genes)
    out["mb_bound"] = {"E[V] <= q^2/((2*pi-1)*p)": True, "q_max": q, "q_median": full["nsel_median"],
                       "p": p,
                       "bounds": {f"{thr:.2f}": q * q / ((2 * thr - 1) * p)
                                  for thr in (0.70, 0.75, 0.80)}}
    print("    MB 上界 (q=%d,p=%d):" % (q, p),
          {k: round(v, 2) for k, v in out["mb_bound"]["bounds"].items()})

    # ---------- [2] 完全嵌套 10 折 CV ----------
    print("[2] 完全嵌套 10 折 CV ...")
    _Tf, _Ef = T, E
    rng = np.random.default_rng(SEED)
    folds = np.array_split(rng.permutation(len(df)), 10)
    nb_c, nb_g, na_c, na_k = [], [], [], []
    for k, f in enumerate(folds):
        tr = np.setdiff1d(np.arange(len(df)), f)
        Xtr, Xte = Xz.iloc[tr], Xz.iloc[f]
        _Tf, _Ef = T[tr], E[tr]
        try:
            r = modelB_on(Xtr, T[tr], E[tr], nboot=100, seed_boot=2026 + k)
            if r["final_genes"]:
                ste = Xte[r["final_genes"]].values @ np.array([r["coef"][g] for g in r["final_genes"]])
                nb_c.append(C(T[f], E[f], ste)); nb_g.append(r["final_genes"])
        except Exception as ex:
            nb_g.append(None)
        _Tf, _Ef = T[tr], E[tr]
        try:
            ra = modelA_on(Xtr, T[tr], E[tr])
            if ra.get("coef"):
                kk2 = list(ra["coef"])
                ste = Xte[kk2].values @ np.array([ra["coef"][g] for g in kk2])
                na_c.append(C(T[f], E[f], ste)); na_k.append(ra["n_hits"])
        except Exception:
            na_k.append(None)
        print(f"    fold{k+1}: B{'+' if nb_g[-1] else '-'}{len(nb_g[-1]) if nb_g[-1] else 0}基因 "
              f"C={nb_c[-1]:.3f} | A {na_k[-1]}基因 C={na_c[-1]:.3f}")
    _Tf, _Ef = T, E
    out["nested_cv"] = {
        "modelB": {"fold_C": [round(x, 4) for x in nb_c], "genes": nb_g,
                   "mean": float(np.mean(nb_c)) if nb_c else None,
                   "sd": float(np.std(nb_c)) if nb_c else None, "n_ok": len(nb_c)},
        "modelA": {"fold_C": [round(x, 4) for x in na_c], "n_hits": na_k,
                   "mean": float(np.mean(na_c)) if na_c else None,
                   "sd": float(np.std(na_c)) if na_c else None, "n_ok": len(na_c)},
    }
    print("    嵌套 B: %.4f ± %.4f ；嵌套 A: %.4f ± %.4f"
          % (np.mean(nb_c), np.std(nb_c), np.mean(na_c), np.std(na_c)))

    # ---------- [5] 配对 bootstrap ----------
    print("[5] 配对 bootstrap C-index 差值 ...")
    rs = pd.read_csv(os.path.join(DATA, "risk_scores.csv"), index_col=0)
    sA = rs["scoreA"].reindex(df.index).values
    cb = full["coef"]
    sB = Xz[list(cb)].values @ np.array([cb[g] for g in cb])
    sP = df["PROLIF"].values
    out["c_index_point"] = {"MRG2": C(T, E, sB), "ModelA": C(T, E, sA), "Prolif": C(T, E, sP)}
    out["paired_bootstrap"] = {
        "MRG2_minus_Prolif": paired_bootstrap_cdiff(T, E, sB, sP),
        "MRG2_minus_ModelA": paired_bootstrap_cdiff(T, E, sB, sA),
        "ModelA_minus_Prolif": paired_bootstrap_cdiff(T, E, sA, sP),
    }
    print("    ", {k: (round(v["diff"], 4), round(v["lo"], 4), round(v["hi"], 4), round(v["p_two_sided"], 4))
                   for k, v in out["paired_bootstrap"].items()})

    # ---------- [6] 随机面板基准 ----------
    print("[6] 随机 2 基因面板基准（3000 次）...")
    rr = np.random.default_rng(11); rnd = []; cols = list(Xz.columns)
    for b in range(3000):
        pair = [cols[i] for i in rr.choice(len(cols), 2, replace=False)]
        dd = Xz[pair].copy(); dd["T"] = T; dd["E"] = E
        try:
            cph = CoxPHFitter().fit(dd, "T", "E")
            rnd.append(C(T, E, cph.predict_log_partial_hazard(dd).values))
        except Exception:
            pass
    rnd = np.array(rnd); obs = out["c_index_point"]["MRG2"]
    out["random_panel"] = {"n_fitted": int(len(rnd)), "mean": float(rnd.mean()), "sd": float(rnd.std()),
                           "p95": float(np.percentile(rnd, 95)),
                           "pct_matching_or_beating": float((rnd >= obs).mean()),
                           "percentile_of_observed": float((rnd < obs).mean() * 100),
                           "observed_MRG2": obs}
    print("    随机 mean=%.4f sd=%.4f p95=%.4f；观测 %.4f 超过 %.1f%%"
          % (rnd.mean(), rnd.std(), np.percentile(rnd, 95), obs,
             out["random_panel"]["percentile_of_observed"]))

    out["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(DATA, "stats_hardening.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n写出 数据/stats_hardening.json  用时 %.1fs" % out["runtime_s"])


if __name__ == "__main__":
    main()
