#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gse76427_prolif_control.py —— 补算 GSE76427 中增殖标志物的对照结果（可复现，落盘）

背景：正文 §3.7 引用了 GSE76427 中 MKI67 / TOP2A / CCNB1 的 HR，但该结果此前**没有任何落盘产物**，
      属可复现性缺口（Reviewer 3 的核心关切）。本脚本用与 external_GSE76427.py 完全相同的
      载入与探针映射逻辑重算，并写入 数据/revised/gse76427_prolif_control.json。

输入：/tmp/GSE76427_series_matrix.txt.gz、/tmp/GPL10558.annot.gz
输出：数据/revised/gse76427_prolif_control.json（+ 控制台表）
"""
import os, gzip, json
import numpy as np, pandas as pd
from lifelines import CoxPHFitter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
MATRIX = "/tmp/GSE76427_series_matrix.txt.gz"
ANNOT = "/tmp/GPL10558.annot.gz"

PROLIF = ["MKI67", "PCNA", "CCNB1", "CCNB2", "CDK1", "BUB1", "BUB1B", "AURKA", "AURKB",
          "TOP2A", "MCM2", "MCM3", "MCM4", "MCM6", "MCM7", "CDKN3", "RACGAP1", "ASPM",
          "CENPE", "TTK"]
FOCUS = ["MKI67", "TOP2A", "CCNB1"]


def load():
    meta, chars, ts = {}, [], None
    with gzip.open(MATRIX, "rt", errors="ignore") as f:
        for i, line in enumerate(f):
            if line.startswith("!series_matrix_table_begin"):
                ts = i; break
            if line.startswith("!Sample_geo_accession"):
                meta["gsm"] = [x.strip('"') for x in line.rstrip("\n").split("\t")[1:]]
            if line.startswith("!Sample_characteristics_ch1"):
                chars.append([x.strip('"') for x in line.rstrip("\n").split("\t")[1:]])

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
    rec = {}
    for row in chars:
        k = key_of(row[0])
        if not k: continue
        rec[k] = {j: v.split(":", 1)[-1].strip() for j, v in enumerate(row)}

    with gzip.open(MATRIX, "rt", errors="ignore") as f:
        for _ in range(ts + 1): f.readline()
        header = [h.strip('"') for h in f.readline().rstrip("\n").split("\t")]
        rows = []
        for line in f:
            if line.startswith("!series_matrix_table_end"): break
            rows.append(line.rstrip("\n").split("\t"))
    probes = [r[0].strip('"') for r in rows]
    vals = np.array([[float(x) if x not in ("", "NA", "null") else np.nan for x in r[1:]]
                     for r in rows], dtype=float)
    expr = pd.DataFrame(vals, index=probes, columns=header[1:])

    p2g = {}
    with gzip.open(ANNOT, "rt", errors="ignore") as f:
        hdr = None
        for line in f:
            if line.startswith("^") or line.startswith("!"): continue
            cols = line.rstrip("\n").split("\t")
            if cols[0].startswith("#"): continue
            if hdr is None:
                hdr = cols; ix_id = hdr.index("ID"); ix_sym = hdr.index("Gene symbol"); continue
            if len(cols) <= max(ix_id, ix_sym): continue
            sym = cols[ix_sym].strip()
            if sym: p2g[cols[ix_id]] = sym.upper()

    keep = [j for j in range(expr.shape[1])
            if rec.get("tissue", {}).get(j, "").lower().startswith("primary")]
    sub = expr.iloc[:, keep]
    recs = []
    for pos, j in enumerate(keep):
        try:
            t = float(rec["dur_os"].get(j, "NA")); e = int(float(rec["event_os"].get(j, "NA")))
        except Exception:
            continue
        if t > 0:
            recs.append({"col": pos, "T": t * 12.0, "E": e})
    val = pd.DataFrame(recs)

    gene_rows = {}
    for p in sub.index:
        g = p2g.get(p)
        if g in PROLIF: gene_rows.setdefault(g, []).append(p)
    gex = {}
    for g, ps in gene_rows.items():
        if len(ps) == 1:
            gex[g] = sub.loc[ps[0]].values
        else:
            means = np.nanmean(sub.loc[ps].values, axis=1)
            gex[g] = sub.loc[ps[np.nanargmax(means)]].values
    G = pd.DataFrame(gex, index=sub.columns).iloc[[r["col"] for r in recs]].reset_index(drop=True)
    return G, val.reset_index(drop=True)


def main():
    G, val = load()
    T, E = val["T"].values, val["E"].values
    print(f"GSE76427 肿瘤 {len(val)}，事件 {int(E.sum())}，增殖标志物可得 {G.shape[1]}/20")

    out = {"cohort": {"n": int(len(val)), "events": int(E.sum()),
                      "n_prolif_available": int(G.shape[1]),
                      "platform": "GPL10558", "endpoint": "OS (months)",
                      "note": "Each marker standardised within the cohort (Z-score); univariate Cox per marker."}}
    for g in FOCUS:
        if g not in G.columns:
            out[g] = {"available": False}; print(f"  {g}: 平台不可得"); continue
        z = (G[g].values - G[g].mean()) / G[g].std()
        cph = CoxPHFitter().fit(pd.DataFrame({"z": z, "T": T, "E": E}), "T", "E")
        s = cph.summary.loc["z"]
        out[g] = {"HR_per_SD": round(float(s["exp(coef)"]), 4),
                  "HR_lo": round(float(s["exp(coef) lower 95%"]), 4),
                  "HR_hi": round(float(s["exp(coef) upper 95%"]), 4),
                  "p": round(float(s["p"]), 4)}
        print(f"  {g}: HR {out[g]['HR_per_SD']:.2f} "
              f"(95% CI {out[g]['HR_lo']:.2f}–{out[g]['HR_hi']:.2f}), P = {out[g]['p']:.3f}")

    if G.shape[1] >= 5:
        zs = ((G - G.mean()) / G.std()).mean(axis=1)
        cph = CoxPHFitter().fit(pd.DataFrame({"z": zs.values, "T": T, "E": E}), "T", "E")
        s = cph.summary.loc["z"]
        out["20-gene proliferation score"] = {
            "genes_available": int(G.shape[1]),
            "HR_per_SD": round(float(s["exp(coef)"]), 4),
            "HR_lo": round(float(s["exp(coef) lower 95%"]), 4),
            "HR_hi": round(float(s["exp(coef) upper 95%"]), 4),
            "p": round(float(s["p"]), 4)}
        print("  20-gene proliferation score: HR %.2f (95%% CI %.2f–%.2f), P = %.3f"
              % (out["20-gene proliferation score"]["HR_per_SD"],
                 out["20-gene proliferation score"]["HR_lo"],
                 out["20-gene proliferation score"]["HR_hi"],
                 out["20-gene proliferation score"]["p"]))

    dst = os.path.join(DATA, "revised", "gse76427_prolif_control.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    json.dump(out, open(dst, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("已落盘:", dst)


if __name__ == "__main__":
    main()
