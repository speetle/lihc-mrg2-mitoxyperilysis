#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生3 LIHC —— 外部验证：GSE14520（Roessler 等，HCC 切除队列）

选它的理由：GSE76427 只有 23 个死亡事件，对 2 基因乃至 23 基因的评分都严重欠功效
（点估计 C≈0.40 但 95% CI 0.26–0.55 含 0.5；连 MKI67/TOP2A 等公认增殖预后标志物
都呈 HR<1，说明是该队列的端点问题，不是 MRG 特有）。GSE14520 有 242 例肿瘤、
96 个死亡事件、中位随访 51.6 个月，是 HCC 预后签名的标准外部验证集。

输入
  /tmp/GSE14520_suppl.txt.gz                 临床（含 Survival months/status）
  /tmp/GSE14520_GPL571.txt.gz                子系列矩阵（HG-U133A）
  /tmp/GSE14520_GPL3921.txt.gz               子系列矩阵（HG-U133A 2.0）
  /tmp/GPL3921.annot.gz                      探针→基因（两平台共用探针集命名空间）
  数据/modelA_coef.csv, 数据/modelB_coef.csv  冻结系数
  分析脚本/mrg_panel.txt                      MRG 面板
  数据/prolif_expr_z.csv                     取 20 个增殖基因名

产出：数据/external_GSE14520.csv、数据/external_GSE14520_summary.json
"""
import os, re, gzip, json
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test
from sksurv.metrics import concordance_index_censored
import warnings
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
SUPPL = "/tmp/GSE14520_suppl.txt.gz"
MATS = {"GPL571": "/tmp/GSE14520_GPL571.txt.gz", "GPL3921": "/tmp/GSE14520_GPL3921.txt.gz"}
ANNOT = "/tmp/GPL3921.annot.gz"
SEED = 42


def cidx(t, e, s):
    return float(concordance_index_censored(np.asarray(e, bool), np.asarray(t, float),
                                            np.asarray(s, float))[0])


def boot_c(s, t, e, B=2000, seed=SEED):
    rng = np.random.default_rng(seed); v = []; n = len(t)
    for _ in range(B):
        i = rng.integers(0, n, n)
        try:
            v.append(cidx(t[i], e[i], s[i]))
        except Exception:
            pass
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def km_med(t, e):
    try:
        return float(KaplanMeierFitter().fit(t, e).median_survival_time_)
    except Exception:
        return float("nan")


def read_matrix(path):
    """返回 probe×GSM 的 DataFrame。注意：enumerate 跳出时文件指针已在表头行。"""
    with gzip.open(path, "rt", errors="ignore") as f:
        for l in f:
            if l.startswith("!series_matrix_table_begin"):
                break
        header = [h.strip('"') for h in f.readline().rstrip("\n").split("\t")]
        rows = []
        for l in f:
            if l.startswith("!series_matrix_table_end"):
                break
            rows.append(l.rstrip("\n").split("\t"))
    probes = [r[0].strip('"') for r in rows]
    vals = np.array([[float(x) if x not in ("", "NA", "null") else np.nan for x in r[1:]]
                     for r in rows], dtype=float)
    return pd.DataFrame(vals, index=probes, columns=header[1:])


def read_annot(path):
    """探针 → 基因符号。

    Affymetrix 老平台（HG-U133A/2.0）的 Gene symbol 列大量使用多基因写法，例如
    KIF15 写作 'NPVF///KIF15'、MAFG 写作 'LOC644132///MAFG'。因此必须把 '///'
    分隔的**每一个**符号都索引进来；只取第一段会系统性丢失本文最关键的两个基因。
    """
    p2g = {}
    with gzip.open(path, "rt", errors="ignore") as f:
        hdr = None
        for l in f:
            if l.startswith(("^", "!", "#")):
                continue
            c = l.rstrip("\n").split("\t")
            if hdr is None:
                hdr = c
                if "ID" not in hdr or "Gene symbol" not in hdr:
                    raise RuntimeError("注释表头异常: %s" % hdr[:6])
                ix_id, ix_sym = hdr.index("ID"), hdr.index("Gene symbol")
                continue
            if len(c) <= max(ix_id, ix_sym):
                continue
            raw = c[ix_sym].strip()
            if not raw or raw == "---":
                continue
            for s in re.split(r"/{2,}", raw):
                s = s.strip().upper()
                if s and s != "---":
                    p2g.setdefault(s, []).append(c[ix_id].strip('"'))
    return p2g


def main():
    print("[1] 临床补充表")
    sup = pd.read_csv(SUPPL, sep="\t")
    sup = sup[sup["Tissue Type"].astype(str).str.strip().str.lower() == "tumor"].copy()
    sup = sup.dropna(subset=["Survival months", "Survival status"])
    sup["T"] = pd.to_numeric(sup["Survival months"], errors="coerce")
    sup["E"] = pd.to_numeric(sup["Survival status"], errors="coerce")
    sup = sup.dropna(subset=["T", "E"])
    sup = sup[sup["T"] > 0]
    print(f"    肿瘤且有生存：{len(sup)}  死亡：{int(sup['E'].sum())}  "
          f"随访中位：{sup['T'].median():.1f} 月")

    print("[2] 两个平台矩阵")
    frames = {}
    for plat, p in MATS.items():
        if not os.path.exists(p):
            print(f"    {plat}: 文件缺失，跳过"); continue
        m = read_matrix(p)
        frames[plat] = m
        print(f"    {plat}: {m.shape[0]} 探针 × {m.shape[1]} 样本")

    print("[3] 探针→基因")
    p2g = read_annot(ANNOT)
    print(f"    注释条目 {len(p2g)}")

    panel = [l.strip().upper() for l in open(os.path.join(HERE, "mrg_panel.txt")) if l.strip()]
    prolif = list(pd.read_csv(os.path.join(DATA, "prolif_expr_z.csv"), nrows=1).columns)
    prolif = [g for g in prolif if g != "pat"]

    print("[4] 组装每个平台的肿瘤亚矩阵")
    per_plat = {}
    for plat, m in frames.items():
        gsms = set(m.columns)
        sub = sup[sup["Affy_GSM"].isin(gsms)].copy()
        if len(sub) == 0:
            print(f"    {plat}: 无匹配样本"); continue
        sub["platform"] = plat
        per_plat[plat] = (m, sub)
        print(f"    {plat}: 匹配到 {len(sub)} 例肿瘤（死亡 {int(sub['E'].sum())}）")

    def gene_series(m, sub, genes):
        """从矩阵 m 抽出 sub 的样本、按基因取平均表达最高的探针。

        p2g 现在是 symbol → [probes]，直接用 p2g[g] 取候选探针。
        """
        cols = [g for g in sub["Affy_GSM"] if g in m.columns]
        sub2 = sub[sub["Affy_GSM"].isin(cols)].copy()
        mm = m[cols]
        out = {}
        for g in genes:
            ps = [p for p in p2g.get(g, []) if p in mm.index]
            if not ps:
                continue
            if len(ps) == 1:
                out[g] = mm.loc[ps[0]].values
            else:
                mns = np.nanmean(mm.loc[ps].values, axis=1)
                out[g] = mm.loc[ps[int(np.nanargmax(mns))]].values
        return pd.DataFrame(out, index=cols), sub2

    # 逐平台抽基因，再纵向拼接（每平台内部各自 z 化，再合并）
    blocks, metas, plat_blocks = [], [], []
    for plat, (m, sub) in per_plat.items():
        gdf, sub2 = gene_series(m, sub, panel + prolif)
        gdf["__platform"] = plat
        gdf["__T"] = sub2.set_index("Affy_GSM").loc[gdf.index, "T"].values
        gdf["__E"] = sub2.set_index("Affy_GSM").loc[gdf.index, "E"].values
        for c in ("Age", "Gender", "TNM staging", "BCLC staging"):
            if c in sub2.columns:
                gdf["__" + c] = sub2.set_index("Affy_GSM").loc[gdf.index, c].values
        blocks.append(gdf)
        plat_blocks.append((plat, gdf))

    # 平台内 z 化（每平台用自己的均值/SD，消除平台尺度差）
    def z_within(b):
        b = b.copy()
        for g in panel + prolif:
            if g in b.columns:
                v = pd.to_numeric(b[g], errors="coerce")
                b[g] = (v - np.nanmean(v)) / np.nanstd(v)
        return b

    zb = [z_within(b) for b in blocks]
    allb = pd.concat(zb, axis=0)
    allb = allb.dropna(subset=["__T", "__E"])
    allb = allb[allb["__T"] > 0]
    avail = [g for g in panel if g in allb.columns]
    print(f"[5] 合并队列 n={len(allb)}  面板可得 {len(avail)}/{len(panel)}")

    coefB = pd.read_csv(os.path.join(DATA, "modelB_coef.csv"))
    coefA = pd.read_csv(os.path.join(DATA, "modelA_coef.csv"))

    def score_of(cdf, frame):
        have = [g for g in cdf["term"] if g in frame.columns]
        s = np.zeros(len(frame))
        for g in have:
            s += float(cdf.loc[cdf["term"] == g, "coef"].values[0]) * frame[g].fillna(0).values
        return s, have

    T = allb["__T"].values.astype(float); E = allb["__E"].values.astype(int)
    out = {"cohort": {"n": int(len(allb)), "events": int(E.sum()),
                      "median_followup_months": float(KaplanMeierFitter().fit(T, 1 - E).median_survival_time_),
                      "platforms": {k: int(v[1].shape[0]) for k, v in per_plat.items()},
                      "n_panel_available": len(avail),
                      "n_panel_total": len(panel)}}
    print("    队列：", out["cohort"])

    print("[6] 评分与判别力")
    for lab, cdf in (("ModelA", coefA), ("ModelB", coefB)):
        s, have = score_of(cdf, allb)
        Z = (s - s.mean()) / s.std()
        c = cidx(T, E, s); lo, hi = boot_c(s, T, E)
        med = np.median(s); grp = (s > med).astype(int)
        lr = logrank_test(T[grp == 1], T[grp == 0], E[grp == 1], E[grp == 0])
        cz = CoxPHFitter().fit(pd.DataFrame({"z": Z, "T": T, "E": E}), "T", "E")
        sz = cz.summary.loc["z"]
        out[lab] = {"genes_used": len(have), "genes_missing": [g for g in cdf["term"] if g not in allb.columns],
                    "c_index": c, "c_index_CI": [lo, hi],
                    "HR_per_SD": float(sz["exp(coef)"]),
                    "HR_lo": float(sz["exp(coef) lower 95%"]),
                    "HR_hi": float(sz["exp(coef) upper 95%"]), "p": float(sz["p"]),
                    "logrank_p": float(lr.p_value),
                    "median_OS_low": km_med(T[grp == 0], E[grp == 0]),
                    "median_OS_high": km_med(T[grp == 1], E[grp == 1]),
                    "n_high": int(grp.sum()), "n_low": int((1 - grp).sum())}
        print(f"    {lab}: {len(have)} 基因 C={c:.4f} ({lo:.3f}-{hi:.3f}) HR/SD={sz['exp(coef)']:.3f} "
              f"P={sz['p']:.2e} logrank={lr.p_value:.2e} 中位 {out[lab]['median_OS_low']:.1f} vs "
              f"{out[lab]['median_OS_high']:.1f}")
        if lab == "ModelB":
            sB = s

    # 增殖评分（同队列内）
    pf = [g for g in prolif if g in allb.columns]
    sP = allb[pf].mean(axis=1).values
    out["Prolif"] = {"genes_used": len(pf), "c_index": cidx(T, E, sP)}
    czP = CoxPHFitter().fit(pd.DataFrame({"z": (sP - sP.mean()) / sP.std(), "T": T, "E": E}), "T", "E")
    out["Prolif"]["HR_per_SD"] = float(czP.summary.loc["z", "exp(coef)"])
    print(f"    增殖评分({len(pf)}基因): C={out['Prolif']['c_index']:.4f} "
          f"HR/SD={out['Prolif']['HR_per_SD']:.3f}")

    print("[7] 多因素校正（年龄/性别/TNM III-IV/平台）")
    d = pd.DataFrame({"z": (sB - sB.mean()) / sB.std(), "T": T, "E": E})
    d["age"] = pd.to_numeric(allb.get("__Age"), errors="coerce").values
    g = allb.get("__Gender")
    d["male"] = (g.astype(str).str.upper().str[0] == "M").astype(int).values if g is not None else 0
    tnm = allb.get("__TNM staging")
    d["adv"] = tnm.astype(str).str.upper().str.replace("STAGE", "").str.strip().str.startswith(("III", "IV")).astype(int).values if tnm is not None else 0
    d["plat"] = (allb["__platform"] == "GPL3921").astype(int).values
    d["age_z"] = (d["age"] - d["age"].mean()) / d["age"].std()
    d2 = d.dropna(subset=["age_z"])
    c = CoxPHFitter().fit(d2[["z", "age_z", "male", "adv", "plat", "T", "E"]], "T", "E")
    out["adjusted"] = {k: {"HR": float(c.summary.loc[k, "exp(coef)"]),
                           "lo": float(c.summary.loc[k, "exp(coef) lower 95%"]),
                           "hi": float(c.summary.loc[k, "exp(coef) upper 95%"]),
                           "p": float(c.summary.loc[k, "p"])} for k in c.summary.index}
    out["adjusted_n"] = int(d2.shape[0])
    print(f"    n={d2.shape[0]}  score HR={out['adjusted']['z']['HR']:.3f} (P={out['adjusted']['z']['p']:.2e})")
    for k in ("adv", "plat", "age_z", "male"):
        print(f"      {k}: HR={out['adjusted'][k]['HR']:.3f} P={out['adjusted'][k]['p']:.3f}")

    # 配对 bootstrap：三个评分两两比较（本队列功效足够，这才是决定性的检验）
    print("[7b] 配对 bootstrap C-index 差值")
    def pbc(s1, s2, B=2000, seed=7):
        rng = np.random.default_rng(seed); v = []; n = len(T)
        base = cidx(T, E, s1) - cidx(T, E, s2)
        for _ in range(B):
            i = rng.integers(0, n, n)
            if E[i].sum() < 5:
                continue
            v.append(cidx(T[i], E[i], s1[i]) - cidx(T[i], E[i], s2[i]))
        v = np.array(v)
        return {"diff": base, "lo": float(np.percentile(v, 2.5)), "hi": float(np.percentile(v, 97.5)),
                "p_two_sided": float(min(1.0, 2 * min((v <= 0).mean(), (v >= 0).mean())))}
    sA_ = score_of(coefA, allb)[0]
    out["paired_bootstrap"] = {
        "ModelB_minus_Prolif": pbc(sB, sP),
        "ModelB_minus_ModelA": pbc(sB, sA_),
        "ModelA_minus_Prolif": pbc(sA_, sP),
    }
    for k, v in out["paired_bootstrap"].items():
        print(f"    {k}: ΔC={v['diff']:+.4f} (95% CI {v['lo']:+.4f}~{v['hi']:+.4f}) P={v['p_two_sided']:.3f}")

    # 逐平台敏感性
    out["per_platform"] = {}
    for plat, gd in plat_blocks:
        if plat not in frames:
            continue
        b = z_within(gd)
        if len(b) < 30:
            print(f"    [{plat}] n={len(b)} 太小，跳过"); continue
        s2, have2 = score_of(coefB, b)
        if len(have2) < 2:
            continue
        cc = cidx(b["__T"].values, b["__E"].values.astype(int), s2)
        out["per_platform"][plat] = {"n": int(len(b)), "events": int(b["__E"].sum()),
                                     "c_index_ModelB": cc, "genes_used": len(have2)}
        print(f"    [{plat}] n={len(b)} 死亡={int(b['__E'].sum())} C(ModelB)={cc:.4f}")

    # 随机 2 基因面板基准（本队列功效足够）
    print("[8] 随机 2 基因面板基准（3000 次）")
    cols = [g for g in avail]
    rr = np.random.default_rng(11); rnd = []
    for _ in range(3000):
        pair = [cols[i] for i in rr.choice(len(cols), 2, replace=False)]
        dd = pd.DataFrame({pair[0]: allb[pair[0]], pair[1]: allb[pair[1]], "T": T, "E": E})
        try:
            cph = CoxPHFitter().fit(dd, "T", "E")
            rnd.append(cidx(T, E, cph.predict_log_partial_hazard(dd).values))
        except Exception:
            pass
    rnd = np.array(rnd)
    obs = out["ModelB"]["c_index"]
    out["random_panel"] = {"n_fitted": int(len(rnd)), "mean": float(rnd.mean()), "sd": float(rnd.std()),
                           "p95": float(np.percentile(rnd, 95)),
                           "pct_matching_or_beating": float((rnd >= obs).mean()),
                           "percentile_of_observed": float((rnd < obs).mean() * 100)}
    print(f"    随机 mean={rnd.mean():.4f} sd={rnd.std():.4f} p95={np.percentile(rnd,95):.4f}；"
          f"观测 {obs:.4f} 超过 {out['random_panel']['percentile_of_observed']:.1f}%")

    save = pd.DataFrame({"T": T, "E": E, "platform": allb["__platform"].values,
                         "scoreA": score_of(coefA, allb)[0], "scoreB": sB, "prolif": sP}).set_index(allb.index)
    save.to_csv(os.path.join(DATA, "external_GSE14520.csv"))
    json.dump(out, open(os.path.join(DATA, "external_GSE14520_summary.json"), "w"),
              indent=2, ensure_ascii=False)
    print("\n===== GSE14520 外部验证完成 =====")


if __name__ == "__main__":
    main()
