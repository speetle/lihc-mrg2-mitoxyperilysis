#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出图 5C 所需的随机面板空分布原始数组，并补沉积 GSE14520 面板表达矩阵。

背景：v1 的 Figure 5C 只有汇总统计（mean/sd/p95），没有原始数组，无法画真实分布；
      且 GSE14520 的表达矩阵当时未沉积，无法复算。本脚本补上这两件事——
      因此 Figure 5C 的空分布是**重新计算**的，不是拟合的正态曲线。

复现口径（与沉积结果严格一致）：
  - 发现队列：与 stats_hardening.py [6] 相同 —— analysis_cohort.csv、91 基因、
    Xz=(X-mean)/std、default_rng(11)、3000 次、CoxPHFitter(2 基因)、Harrell C。
  - GSE14520：与 external_GSE14520.py [8] 相同 —— 平台内 z 化后合并、
    65 个可得面板基因、default_rng(11)、3000 次。
脚本内对 mean/sd/p95 与已沉积 JSON 做断言，不一致即报错。

产出：
  数据/random_panel_TCGA.npy           发现队列 3000 个随机 2 基因面板的 C-index
  数据/random_panel_GSE14520.npy       GSE14520 队列 3000 个随机 2 基因面板的 C-index
  数据/external_GSE14520_expr_z.csv    GSE14520 面板基因的平台内 z 化表达矩阵（补沉积）
  数据/export_fig_arrays.json          一致性核对记录
"""
import os, sys, json, importlib.util
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines import KaplanMeierFitter
import warnings
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
FIG  = os.path.join(BASE, "图件_v2")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def cidx(t, e, s):
    from sksurv.metrics import concordance_index_censored
    return float(concordance_index_censored(np.asarray(e, bool), np.asarray(t, float),
                                            np.asarray(s, float))[0])


def main():
    sh = load_module(os.path.join(HERE, "stats_hardening.py"), "shmod")
    ex = load_module(os.path.join(HERE, "external_GSE14520.py"), "exmod")
    rec = {}

    # ============ [1] 发现队列：随机 2 基因面板 ============
    print("[1] 发现队列随机面板（复现 stats_hardening [6]，seed=11）")
    df, genes, pg = sh.load()
    T = df["T"].values.astype(float); E = df["E"].values.astype(int)
    X = df[genes]; Xz = (X - X.mean()) / X.std()
    cols = list(Xz.columns)
    rr = np.random.default_rng(11); rnd = []
    for _ in range(3000):
        pair = [cols[i] for i in rr.choice(len(cols), 2, replace=False)]
        dd = Xz[pair].copy(); dd["T"] = T; dd["E"] = E
        try:
            cph = CoxPHFitter().fit(dd, "T", "E")
            rnd.append(cidx(T, E, cph.predict_log_partial_hazard(dd).values))
        except Exception:
            pass
    rnd = np.array(rnd)
    np.save(os.path.join(DATA, "random_panel_TCGA.npy"), rnd)
    dep = json.load(open(os.path.join(DATA, "stats_hardening.json")))["random_panel"]
    got = dict(n=int(len(rnd)), mean=float(rnd.mean()), sd=float(rnd.std()),
               p95=float(np.percentile(rnd, 95)))
    print(f"    重算 n={got['n']} mean={got['mean']:.4f} sd={got['sd']:.4f} p95={got['p95']:.4f}")
    print(f"    沉积     n={dep['n_fitted']} mean={dep['mean']:.4f} sd={dep['sd']:.4f} p95={dep['p95']:.4f}")
    ok = (abs(got["mean"] - dep["mean"]) < 1e-9 and abs(got["sd"] - dep["sd"]) < 1e-9
          and abs(got["p95"] - dep["p95"]) < 1e-9)
    print("    一致性:", "✅ 完全一致" if ok else "❌ 不一致")
    rec["discovery"] = {"recomputed": got, "deposited": dep, "match": bool(ok)}

    # ============ [2] GSE14520：重建面板表达矩阵 ============
    print("[2] GSE14520：重建平台内 z 化面板矩阵（复现 external_GSE14520 [1]–[5]）")
    sup = pd.read_csv(ex.SUPPL, sep="\t")
    sup = sup[sup["Tissue Type"].astype(str).str.strip().str.lower() == "tumor"].copy()
    sup = sup.dropna(subset=["Survival months", "Survival status"])
    sup["T"] = pd.to_numeric(sup["Survival months"], errors="coerce")
    sup["E"] = pd.to_numeric(sup["Survival status"], errors="coerce")
    sup = sup.dropna(subset=["T", "E"]); sup = sup[sup["T"] > 0]

    frames = {}
    for plat, p in ex.MATS.items():
        if os.path.exists(p):
            frames[plat] = ex.read_matrix(p)
    p2g = ex.read_annot(ex.ANNOT)
    panel = [l.strip().upper() for l in open(os.path.join(HERE, "mrg_panel.txt")) if l.strip()]
    prolif = [g for g in pd.read_csv(os.path.join(DATA, "prolif_expr_z.csv"), nrows=1).columns if g != "pat"]

    def gene_series(m, sub, gs):
        cols = [g for g in sub["Affy_GSM"] if g in m.columns]
        sub2 = sub[sub["Affy_GSM"].isin(cols)].copy()
        mm = m[cols]; out = {}
        for g in gs:
            ps = [p for p in p2g.get(g, []) if p in mm.index]
            if not ps:
                continue
            out[g] = (mm.loc[ps[0]].values if len(ps) == 1
                      else mm.loc[ps[int(np.nanargmax(np.nanmean(mm.loc[ps].values, axis=1)))]].values)
        return pd.DataFrame(out, index=cols), sub2

    blocks = []
    for plat, m in frames.items():
        gsms = set(m.columns)
        sub = sup[sup["Affy_GSM"].isin(gsms)].copy()
        if not len(sub):
            continue
        gdf, sub2 = gene_series(m, sub, panel + prolif)
        gdf["__platform"] = plat
        idx = sub2.set_index("Affy_GSM")
        gdf["__T"] = idx.loc[gdf.index, "T"].values
        gdf["__E"] = idx.loc[gdf.index, "E"].values
        blocks.append(gdf)

    def z_within(b):
        b = b.copy()
        for g in panel + prolif:
            if g in b.columns:
                v = pd.to_numeric(b[g], errors="coerce")
                b[g] = (v - np.nanmean(v)) / np.nanstd(v)
        return b

    allb = pd.concat([z_within(b) for b in blocks], axis=0)
    allb = allb.dropna(subset=["__T", "__E"]); allb = allb[allb["__T"] > 0]
    avail = [g for g in panel if g in allb.columns]
    print(f"    合并 n={len(allb)} 死亡={int(allb['__E'].sum())} 面板可得 {len(avail)}/{len(panel)}")

    # 补沉积：面板基因的平台内 z 化表达矩阵
    keep = avail + ["__T", "__E", "__platform"]
    outdf = allb[keep].copy()
    outdf.index.name = "sample"
    outdf.to_csv(os.path.join(DATA, "external_GSE14520_expr_z.csv"))
    print(f"    ✅ 已补沉积 数据/external_GSE14520_expr_z.csv  shape={outdf.shape}")

    T2 = allb["__T"].values.astype(float); E2 = allb["__E"].values.astype(int)
    exs = json.load(open(os.path.join(DATA, "external_GSE14520_summary.json")))
    c1 = exs["cohort"]
    chk = (len(allb) == c1["n"] and int(E2.sum()) == c1["events"] and len(avail) == c1["n_panel_available"])
    print(f"    队列一致性: 重算 n={len(allb)}/死亡={int(E2.sum())}/面板={len(avail)} ; "
          f"沉积 n={c1['n']}/死亡={c1['events']}/面板={c1['n_panel_available']} -> "
          f"{'✅' if chk else '❌'}")

    # ============ [3] GSE14520：随机 2 基因面板 ============
    print("[3] GSE14520 随机面板（复现 external_GSE14520 [8]，seed=11）")
    cols2 = [g for g in avail]
    rr = np.random.default_rng(11); rnd2 = []
    for _ in range(3000):
        pair = [cols2[i] for i in rr.choice(len(cols2), 2, replace=False)]
        dd = pd.DataFrame({pair[0]: allb[pair[0]], pair[1]: allb[pair[1]], "T": T2, "E": E2})
        try:
            cph = CoxPHFitter().fit(dd, "T", "E")
            rnd2.append(cidx(T2, E2, cph.predict_log_partial_hazard(dd).values))
        except Exception:
            pass
    rnd2 = np.array(rnd2)
    np.save(os.path.join(DATA, "random_panel_GSE14520.npy"), rnd2)
    dep2 = exs["random_panel"]
    got2 = dict(n=int(len(rnd2)), mean=float(rnd2.mean()), sd=float(rnd2.std()),
                p95=float(np.percentile(rnd2, 95)),
                pct_matching_or_beating=float((rnd2 >= exs["ModelB"]["c_index"]).mean()),
                percentile_of_observed=float((rnd2 < exs["ModelB"]["c_index"]).mean() * 100))
    print(f"    重算 n={got2['n']} mean={got2['mean']:.4f} sd={got2['sd']:.4f} "
          f"p95={got2['p95']:.4f} 追平或超越={got2['pct_matching_or_beating']*100:.2f}%")
    print(f"    沉积 n={dep2['n_fitted']} mean={dep2['mean']:.4f} sd={dep2['sd']:.4f} "
          f"p95={dep2['p95']:.4f} 追平或超越={dep2['pct_matching_or_beating']*100:.2f}%")
    ok2 = (abs(got2["mean"] - dep2["mean"]) < 1e-9 and abs(got2["sd"] - dep2["sd"]) < 1e-9)
    print("    一致性:", "✅ 完全一致" if ok2 else "❌ 不一致")
    rec["gse14520"] = {"recomputed": got2, "deposited": dep2, "match": bool(ok2),
                       "cohort_rebuilt": {"n": int(len(allb)), "events": int(E2.sum()),
                                          "panel_available": len(avail), "match": bool(chk)}}

    json.dump(rec, open(os.path.join(DATA, "export_fig_arrays.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n完成 -> 数据/random_panel_TCGA.npy、数据/random_panel_GSE14520.npy、"
          "数据/external_GSE14520_expr_z.csv、数据/export_fig_arrays.json")
    if not (ok and ok2 and chk):
        raise SystemExit("⚠ 存在不一致，请检查后再出图")


if __name__ == "__main__":
    main()
