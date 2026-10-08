#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIHC —— 外部验证：GSE76427（Illumina HumanHT-12 v4, GPL10558）

输入：
  /tmp/GSE76427_series_matrix.txt.gz
  /tmp/GPL10558.annot.gz
  数据/modelA_coef.csv、数据/modelB_coef.csv、数据/lihc_expr_z.csv（取训练集均值/SD）

产出：数据/external_GSE76427.csv、数据/external_summary.json
"""
import os, sys, gzip, json, math
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test
from sksurv.metrics import concordance_index_censored

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
MATRIX = "/tmp/GSE76427_series_matrix.txt.gz"
ANNOT = "/tmp/GPL10558.annot.gz"
SEED = 42


def cidx(t, e, s):
    return float(concordance_index_censored(np.asarray(e, bool), np.asarray(t, float),
                                            np.asarray(s, float))[0])


def km_median(t, e):
    if len(t) == 0:
        return float("nan")
    return float(KaplanMeierFitter().fit(np.asarray(t, float), np.asarray(e, bool)).median_survival_time_)


def bootstrap_c(score, t, e, B=2000, seed=SEED):
    rng = np.random.default_rng(seed); vals = []
    n = len(t)
    for _ in range(B):
        idx = rng.integers(0, n, n)
        try:
            vals.append(cidx(t[idx], e[idx], score[idx]))
        except Exception:
            pass
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def main():
    # ---------- 1. 解析 series matrix
    print("[1] 解析 GSE76427 series matrix")
    meta = {}
    chars = []
    table_start = None
    with gzip.open(MATRIX, "rt", errors="ignore") as f:
        for i, line in enumerate(f):
            if line.startswith("!series_matrix_table_begin"):
                table_start = i; break
            if line.startswith("!Sample_geo_accession"):
                meta["gsm"] = [x.strip('"') for x in line.rstrip("\n").split("\t")[1:]]
            if line.startswith("!Sample_title"):
                meta["title"] = [x.strip('"') for x in line.rstrip("\n").split("\t")[1:]]
            if line.startswith("!Sample_characteristics_ch1"):
                chars.append([x.strip('"') for x in line.rstrip("\n").split("\t")[1:]])
    n = len(meta["gsm"])
    rec = {k: {} for k in ["patient", "tissue", "event_os", "dur_os", "age", "sex",
                            "bclc", "tnm"]}
    def key_of(s):
        s = s.lower()
        if "patient id" in s: return "patient"
        if s.startswith("tissue"): return "tissue"
        if "event_os" in s: return "event_os"
        if "duryears_os" in s: return "dur_os"
        if "age (years)" in s: return "age"
        if "gender" in s: return "sex"
        if "bclc" in s: return "bclc"
        if "tnm_staging" in s: return "tnm"
        return None
    for row in chars:
        k = key_of(row[0])
        if not k:
            continue
        for j, v in enumerate(row):
            rec[k][j] = v.split(":", 1)[-1].strip()
    print(f"    样本 {n}，特征行 {len(chars)}")

    # ---------- 2. 表达矩阵
    print("[2] 读取表达矩阵")
    with gzip.open(MATRIX, "rt", errors="ignore") as f:
        for _ in range(table_start + 1):
            f.readline()
        header = f.readline().rstrip("\n").split("\t")
        header = [h.strip('"') for h in header]
        rows = []
        for line in f:
            if line.startswith("!series_matrix_table_end"):
                break
            parts = line.rstrip("\n").split("\t")
            rows.append(parts)
    probes = [r[0].strip('"') for r in rows]
    vals = np.array([[float(x) if x not in ("", "NA", "null") else np.nan for x in r[1:]]
                     for r in rows], dtype=float)
    expr = pd.DataFrame(vals, index=probes, columns=header[1:])
    print(f"    {expr.shape[0]} 探针 × {expr.shape[1]} 样本")

    # ---------- 3. 注释
    print("[3] 探针→基因")
    p2g = {}
    with gzip.open(ANNOT, "rt", errors="ignore") as f:
        hdr = None
        for line in f:
            if line.startswith("^") or line.startswith("!"):
                continue
            cols = line.rstrip("\n").split("\t")
            if cols[0].startswith("#"):
                continue
            if hdr is None:
                hdr = cols
                ix_id = hdr.index("ID"); ix_sym = hdr.index("Gene symbol")
                continue
            if len(cols) <= max(ix_id, ix_sym):
                continue
            sym = cols[ix_sym].strip()
            if sym and sym != "":
                p2g[cols[ix_id]] = sym.upper()

    # ---------- 4. 构建队列
    print("[4] 构建肿瘤队列")
    is_tumor = [rec["tissue"].get(j, "") .lower().startswith("primary") for j in range(expr.shape[1])]
    samples = [expr.columns[j] for j in range(expr.shape[1]) if is_tumor[j]]
    keep = [j for j in range(expr.shape[1]) if is_tumor[j]]
    sub = expr.iloc[:, keep]
    recs = []
    for pos, j in enumerate(keep):
        try:
            os_t = float(rec["dur_os"].get(j, "NA"))
            os_e = int(float(rec["event_os"].get(j, "NA")))
        except Exception:
            continue
        recs.append({"sample": expr.columns[j], "col": pos,
                     "T": os_t * 12.0, "E": os_e,
                     "age": float(rec["age"].get(j, "nan") or "nan"),
                     "sex": rec["sex"].get(j, ""),
                     "tnm": rec["tnm"].get(j, ""),
                     "bclc": rec["bclc"].get(j, "")})
    val = pd.DataFrame(recs)
    val = val[val["T"] > 0]
    print(f"    肿瘤样本 {sub.shape[1]}，有 OS 的 {val.shape[0]}，事件 {int(val['E'].sum())}")

    # ---------- 5. 基因表达（每基因取平均表达最高的探针）
    panel = [l.strip().upper() for l in open(os.path.join(HERE, "mrg_panel.txt")) if l.strip()]
    gene_rows = {}
    for p in sub.index:
        g = p2g.get(p)
        if g in panel:
            gene_rows.setdefault(g, []).append(p)
    gexpr = {}
    for g, ps in gene_rows.items():
        if len(ps) == 1:
            gexpr[g] = sub.loc[ps[0]].values
        else:
            means = np.nanmean(sub.loc[ps].values, axis=1)
            gexpr[g] = sub.loc[ps[np.nanargmax(means)]].values
    G = pd.DataFrame(gexpr, index=sub.columns).iloc[[r["col"] for r in recs]]
    print(f"    面板基因在 GSE76427 可得：{G.shape[1]}/{len(panel)}")

    # ---------- 6. 评分（队列内 z 化）
    Gz = (G - G.mean()) / G.std()
    coefB = pd.read_csv(os.path.join(DATA, "modelB_coef.csv"))
    coefA = pd.read_csv(os.path.join(DATA, "modelA_coef.csv"))
    out = {"n_tumor": int(val.shape[0]), "events": int(val["E"].sum()),
           "n_genes_available": int(G.shape[1])}
    print(f"[5] 评分")

    def score_from(coefdf):
        have = [g for g in coefdf["term"] if g in Gz.columns]
        missing = [g for g in coefdf["term"] if g not in Gz.columns]
        s = np.zeros(len(Gz))
        for g in have:
            c = float(coefdf.loc[coefdf["term"] == g, "coef"].values[0])
            s = s + c * Gz[g].values
        return s, have, missing

    for lab, cdf in [("ModelA", coefA), ("ModelB", coefB)]:
        s, have, missing = score_from(cdf)
        T = val["T"].values; E = val["E"].values
        c = cidx(T, E, s)
        lo, hi = bootstrap_c(s, T, E)
        med = np.median(s); grp = (s > med).astype(int)
        lr = logrank_test(T[grp == 1], T[grp == 0], E[grp == 1], E[grp == 0])
        cz = CoxPHFitter().fit(pd.DataFrame({"z": (s - s.mean()) / s.std(), "T": T, "E": E}),
                               duration_col="T", event_col="E")
        sz = cz.summary.loc["z"]
        out[lab] = {"genes_used": len(have), "genes_missing": missing,
                    "c_index": c, "c_index_CI": [lo, hi],
                    "HR_per_SD": float(sz["exp(coef)"]),
                    "HR_lo": float(sz["exp(coef) lower 95%"]),
                    "HR_hi": float(sz["exp(coef) upper 95%"]),
                    "p": float(sz["p"]),
                    "logrank_p": float(lr.p_value),
                    "median_OS_low": km_median(T[grp == 0], E[grp == 0]),
                    "median_OS_high": km_median(T[grp == 1], E[grp == 1]),
                    "n_high": int(grp.sum()), "n_low": int((1 - grp).sum())}
        print(f"    {lab}: 用 {len(have)} 基因, C={c:.4f} {out[lab]['c_index_CI']}, "
              f"HR/SD={out[lab]['HR_per_SD']:.3f} ({out[lab]['HR_lo']:.3f}-{out[lab]['HR_hi']:.3f}), "
              f"P={out[lab]['p']:.2e}, logrank={out[lab]['logrank_p']:.2e}, "
              f"中位OS {out[lab]['median_OS_low']:.1f} vs {out[lab]['median_OS_high']:.1f}")

    # 多因素（年龄、性别、TNM III/IV）
    print("[6] 多因素校正（年龄/性别/TNM III–IV）")
    sB, _, _ = score_from(coefB)
    d = val.copy(); d["z"] = (sB - sB.mean()) / sB.std()
    d["age_z"] = (pd.to_numeric(d["age"], errors="coerce") - pd.to_numeric(d["age"], errors="coerce").mean()) / pd.to_numeric(d["age"], errors="coerce").std()
    d["male"] = d["sex"].astype(str).str.contains("1").astype(int)
    d["adv"] = d["tnm"].astype(str).str.upper().str.contains("III|IV").astype(int)
    d2 = d.dropna(subset=["age_z"])
    cB2 = CoxPHFitter().fit(d2[["z", "age_z", "male", "adv", "T", "E"]], duration_col="T", event_col="E")
    s = cB2.summary
    out["adjusted_ModelB"] = {k: {"HR": float(s.loc[k, "exp(coef)"]),
                                  "lo": float(s.loc[k, "exp(coef) lower 95%"]),
                                  "hi": float(s.loc[k, "exp(coef) upper 95%"]),
                                  "p": float(s.loc[k, "p"])} for k in s.index}
    print(f"    Model B 校正后 score HR={out['adjusted_ModelB']['z']['HR']:.3f} "
          f"(P={out['adjusted_ModelB']['z']['p']:.2e}), n={d2.shape[0]}")
    for k in ["adv", "male", "age_z"]:
        print(f"      {k}: HR={out['adjusted_ModelB'][k]['HR']:.3f} P={out['adjusted_ModelB'][k]['p']:.3f}")

    # 保存逐患者
    save = val.copy()
    save["scoreA"] = score_from(coefA)[0]; save["scoreB"] = sB
    save.to_csv(os.path.join(DATA, "external_GSE76427.csv"), index=False)
    json.dump(out, open(os.path.join(DATA, "external_summary.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n===== 外部验证完成 =====")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
