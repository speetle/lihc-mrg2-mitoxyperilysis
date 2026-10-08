#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIHC —— MRG 预后模型全流程（真实数据，无编造）  v2

数据源：cBioPortal REST API, study = lihc_tcga_pan_can_atlas_2018
表达谱：..._rna_seq_v2_mrna_median_all_sample_Zscores
        ..._rna_seq_v2_mrna_median_all_sample_ref_normal_Zscores
突变谱：..._mutations

统计栈与 LGG 交付件保持一致：lifelines 0.30.3 + scikit-survival 0.28.0
"""
import os, sys, json, time, gzip, math, argparse, urllib.request, urllib.error, urllib.parse
import numpy as np
import pandas as pd
from scipy.stats import chi2, mannwhitneyu, fisher_exact, spearmanr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
for fam in ["Arial Unicode MS", "Heiti SC", "PingFang SC", "Microsoft YaHei", "SimHei"]:
    if any(f.name == fam for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [fam]; break
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["pdf.fonttype"] = 42

from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test
from sksurv.metrics import concordance_index_censored, cumulative_dynamic_auc
from sksurv.linear_model import CoxnetSurvivalAnalysis
from sksurv.util import Surv

API = "https://www.cbioportal.org/api"
STUDY = "lihc_tcga_pan_can_atlas_2018"
ZPROF = STUDY + "_rna_seq_v2_mrna_median_all_sample_Zscores"
RPROF = STUDY + "_rna_seq_v2_mrna_median_all_sample_ref_normal_Zscores"
SLIST = STUDY + "_rna_seq_v2_mrna"

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
FIG = os.path.join(BASE, "图件")
os.makedirs(DATA, exist_ok=True); os.makedirs(FIG, exist_ok=True)
PANEL_FILE = os.path.join(HERE, "mrg_panel.txt")
SEED = 42


# ------------------------------------------------------------------ HTTP
def _read(req, timeout=300):
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw


def http(url, data=None, tries=5, timeout=300):
    last = None
    for k in range(tries):
        try:
            body = json.dumps(data).encode() if data is not None else None
            req = urllib.request.Request(url, data=body)
            req.add_header("Accept-Encoding", "gzip")
            if data is not None:
                req.add_header("Content-Type", "application/json")
            return json.loads(_read(req, timeout))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (400, 404):
                return None
        except Exception as e:
            last = f"{type(e).__name__}:{e}"
        time.sleep(2 + 3 * k)
    print(f"    [warn] {last} {url[:90]}", file=sys.stderr)
    return None


def http_form(url, fields, tries=4, timeout=120):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode())
            req.add_header("Accept-Encoding", "gzip")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            return json.loads(_read(req, timeout))
        except Exception:
            time.sleep(2 + 2 * k)
    return None


def symbol_to_entrez(genes, cache):
    genes = [g.upper() for g in genes if g]
    if os.path.exists(cache):
        try:
            old = {k: int(v) for k, v in json.load(open(cache)).items()}
            if all(g in old for g in genes):
                return old
        except Exception:
            pass
    s2e = {}
    for i in range(0, len(genes), 80):
        chunk = genes[i:i + 80]
        res = http_form("https://mygene.info/v3/query",
                        {"q": ",".join(chunk), "scopes": "symbol", "species": "human",
                         "fields": "symbol,entrezgene", "size": str(len(chunk) + 10)})
        if res:
            for h in res:
                q = str(h.get("query", "")).upper()
                if h.get("entrezgene") and q:
                    s2e[q] = int(h["entrezgene"])
        time.sleep(0.3)
    for g in [g for g in genes if g not in s2e][:40]:
        r = http(f"{API}/genes/{urllib.parse.quote(g)}")
        if r and r.get("entrezGeneId"):
            s2e[g] = int(r["entrezGeneId"])
    try:
        json.dump(s2e, open(cache, "w"))
    except Exception:
        pass
    return s2e


def fetch_molecular(profile, s2e, cache, sample_list=SLIST):
    if os.path.exists(cache):
        try:
            df = pd.read_csv(cache, index_col=0)
            if df.shape[0] > 100:
                print(f"    [cache] {os.path.basename(cache)} {df.shape}")
                return df
        except Exception:
            pass
    md = http(f"{API}/molecular-profiles/{profile}/molecular-data/fetch",
              {"sampleListId": sample_list, "entrezGeneIds": sorted(set(s2e.values()))})
    if not md:
        return None
    ent2sym = {v: k for k, v in s2e.items()}
    rows = []
    for r in md:
        sid = r.get("sampleId", "")
        sym = (r.get("gene", {}) or {}).get("hugoGeneSymbol") or ent2sym.get(r.get("entrezGeneId"))
        v = r.get("value")
        if sym and v not in (None, "", "NA"):
            rows.append((r.get("uniquePatientKey") or sid[:12], str(sym).upper(), float(v)))
    if not rows:
        return None
    expr = (pd.DataFrame(rows, columns=["pat", "gene", "v"])
            .groupby(["pat", "gene"])["v"].mean().unstack())
    expr = expr.loc[:, expr.std() > 1e-6]
    expr.to_csv(cache)
    print(f"    {os.path.basename(cache)} {expr.shape}")
    return expr


def fetch_clinical():
    out = {}
    for dtype in ("PATIENT", "SAMPLE"):
        page = 0
        while page < 8:
            cd = http(f"{API}/studies/{STUDY}/clinical-data"
                      f"?projection=DETAILED&clinicalDataType={dtype}"
                      f"&pageSize=30000&pageNumber={page}")
            if not cd:
                break
            for r in cd:
                aid = (r.get("clinicalAttribute", {}) or {}).get("clinicalAttributeId")
                if aid:
                    out.setdefault(r["uniquePatientKey"], {})[aid] = r.get("value")
            if len(cd) < 30000:
                break
            page += 1
    return out


# ------------------------------------------------------------------ 统计封装
def cox_uni(df, time_col, event_col, covars):
    """lifelines 单因素 Cox，逐协变量拟合"""
    rows = []
    for g in covars:
        try:
            c = CoxPHFitter()
            c.fit(df[[g, time_col, event_col]], duration_col=time_col,
                  event_col=event_col)
            s = c.summary.loc[g]
            rows.append({"gene": g, "beta": s["coef"], "se": s["se(coef)"],
                         "HR": s["exp(coef)"], "HR_lo": s["exp(coef) lower 95%"],
                         "HR_hi": s["exp(coef) upper 95%"], "z": s["z"], "p": s["p"]})
        except Exception:
            pass
    return pd.DataFrame(rows)


def cox_multi(df, time_col, event_col, covars, penalizer=0.0):
    c = CoxPHFitter(penalizer=penalizer)
    c.fit(df[covars + [time_col, event_col]], duration_col=time_col, event_col=event_col)
    s = c.summary
    out = pd.DataFrame({"term": s.index, "coef": s["coef"].values,
                        "se": s["se(coef)"].values, "HR": s["exp(coef)"].values,
                        "lo": s["exp(coef) lower 95%"].values,
                        "hi": s["exp(coef) upper 95%"].values,
                        "p": s["p"].values})
    return c, out


def cidx(t, e, s):
    return concordance_index_censored(np.asarray(e, bool), np.asarray(t, float),
                                      np.asarray(s, float))[0]


def km_median(t, e):
    t = np.asarray(t, float); e = np.asarray(e, bool)
    if len(t) == 0:
        return float("nan")
    k = KaplanMeierFitter().fit(t, e)
    try:
        return float(k.median_survival_time_)
    except Exception:
        return float("nan")


def reverse_km_median_followup(t, e):
    return km_median(t, ~np.asarray(e, bool))


def bootstrap_c(score, t, e, B=1000, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(t); vals = []
    for _ in range(B):
        idx = rng.integers(0, n, n)
        try:
            vals.append(cidx(t[idx], e[idx], score[idx]))
        except Exception:
            pass
    if not vals:
        return (float("nan"), float("nan"))
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def silhouette(X, lab):
    from numpy.linalg import norm
    n = len(lab); sils = []
    for i in range(n):
        same = np.where(lab == lab[i])[0]
        a = np.mean([norm(X[i] - X[j]) for j in same if j != i]) if len(same) > 1 else 0.0
        bs = []
        for c in np.unique(lab):
            if c == lab[i]:
                continue
            oth = np.where(lab == c)[0]
            bs.append(np.mean([norm(X[i] - X[j]) for j in oth]))
        b = min(bs) if bs else 0.0
        sils.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return float(np.mean(sils))


def kmeans_np(X, k, seed=0, iters=200):
    rng = np.random.default_rng(seed)
    center = X[rng.choice(len(X), k, replace=False)].copy()
    lab = np.zeros(len(X), int)
    for _ in range(iters):
        d = np.linalg.norm(X[:, None, :] - center[None, :, :], axis=2)
        new = d.argmin(1)
        if (new == lab).all():
            break
        lab = new
        for c in range(k):
            if (lab == c).any():
                center[c] = X[lab == c].mean(0)
    return lab


# ------------------------------------------------------------------ main
def main():
    t0 = time.time()
    panel = [l.strip().upper() for l in open(PANEL_FILE) if l.strip()]
    print(f"[0] MRG 面板（人类同源）：{len(panel)} 个")

    s2e = symbol_to_entrez(panel, os.path.join(DATA, ".entrez.json"))
    expr = fetch_molecular(ZPROF, s2e, os.path.join(DATA, "lihc_expr_z.csv"))
    if expr is None:
        print("表达获取失败"); return
    genes_eval = [g for g in panel if g in expr.columns and expr[g].notna().sum() > 340]
    dropped = [g for g in panel if g not in genes_eval]
    expr = expr[genes_eval].dropna()
    print(f"[1] 可评估 MRG：{len(genes_eval)}；不可评估：{dropped}；完整表达患者：{expr.shape[0]}")

    expr_rn = fetch_molecular(RPROF, s2e, os.path.join(DATA, "lihc_expr_refnormal_z.csv"))

    clin = fetch_clinical()
    cdf = pd.DataFrame.from_dict(clin, orient="index")
    pats = [p for p in expr.index if p in cdf.index]
    df = cdf.loc[pats].copy().join(expr, how="inner")
    df["OS_MONTHS"] = pd.to_numeric(df["OS_MONTHS"], errors="coerce")
    df["OS_EVENT"] = df["OS_STATUS"].astype(str).str.startswith("1").astype(int)
    df["AGE"] = pd.to_numeric(df["AGE"], errors="coerce")
    df = df[df["OS_MONTHS"].notna() & df["OS_MONTHS"].gt(0) & df["AGE"].notna()]
    df = df.rename(columns={"OS_MONTHS": "T", "OS_EVENT": "E"})
    print(f"[2] 分析队列：n={df.shape[0]}，事件={int(df['E'].sum())}，"
          f"中位随访(反KM)={reverse_km_median_followup(df['T'], df['E']):.1f} 月")

    out = {"n": int(df.shape[0]), "events": int(df["E"].sum()),
           "n_panel_human": len(panel), "n_evaluable": len(genes_eval),
           "dropped": dropped,
           "median_followup_reverseKM": float(reverse_km_median_followup(df["T"], df["E"])),
           "median_age": float(df["AGE"].median()),
           "male_pct": float(100 * df["SEX"].astype(str).str.upper().str.startswith("M").mean())}

    # ---------------- 单因素
    print("[3] 单因素 Cox（lifelines）")
    udf = cox_uni(df, "T", "E", genes_eval).sort_values("p")
    udf.to_csv(os.path.join(DATA, "univariate_cox.csv"), index=False)
    sig = udf[udf["p"] < 0.05]
    out["n_univariate_sig"] = int(len(sig))
    print(f"    P<0.05：{len(sig)}/{len(udf)}")

    # ---------------- Model A：L2 岭多因素
    print("[4] Model A（L2 岭多因素 Cox, penalizer=1.0）")
    A_genes = list(sig["gene"])
    XA = df[A_genes].copy()
    XA = (XA - XA.mean()) / XA.std()
    dfA = XA.copy(); dfA["T"] = df["T"].values; dfA["E"] = df["E"].values
    cA, coefA = cox_multi(dfA, "T", "E", A_genes, penalizer=1.0)
    coefA.to_csv(os.path.join(DATA, "modelA_coef.csv"), index=False)
    scoreA = cA.predict_partial_hazard(dfA).values.reshape(-1)
    scoreA = np.log(scoreA)
    out["modelA"] = {"n_genes": len(A_genes)}

    # ---------------- Model B：LASSO-Cox + 稳定性选择
    print("[5] Model B（LASSO-Cox + 200×bootstrap 稳定性选择）")
    Xz = df[genes_eval].copy()
    means, sds = Xz.mean(), Xz.std()
    Xm = ((Xz - means) / sds).values
    y = Surv.from_arrays(df["E"].astype(bool).values, df["T"].values)
    alphas = np.logspace(-1.2, -3.0, 60)
    est = CoxnetSurvivalAnalysis(l1_ratio=1.0, alphas=alphas.tolist(), fit_baseline_model=False)
    est.fit(Xm, y)
    # 10 折 CV 选 alpha
    rng = np.random.default_rng(SEED)
    folds = np.array_split(rng.permutation(len(df)), 10)
    cv = []
    for a in est.alphas_:
        cs = []
        for f in folds:
            tr = np.setdiff1d(np.arange(len(df)), f)
            try:
                m = CoxnetSurvivalAnalysis(l1_ratio=1.0, alphas=[a]).fit(Xm[tr], y[tr])
                w = m.coef_[:, 0]
                cs.append(cidx(df["T"].values[f], df["E"].values[f], Xm[f] @ w))
            except Exception:
                pass
        cv.append(np.mean(cs) if cs else np.nan)
    cv = np.array(cv)
    i_min = int(np.nanargmax(cv))
    se_cv = np.nanstd(cv) / math.sqrt(10)
    i_1se = int(np.where(cv >= cv[i_min] - se_cv)[0][0])
    a1se = float(est.alphas_[i_1se])
    n1 = int(np.sum(np.abs(est.coef_[:, i_1se]) > 1e-8))
    nm = int(np.sum(np.abs(est.coef_[:, i_min]) > 1e-8))
    out["lasso"] = {"alpha_min": float(est.alphas_[i_min]), "n_at_min": nm,
                    "cv_at_min": float(cv[i_min]), "alpha_1se": a1se,
                    "n_at_1se": n1, "cv_at_1se": float(cv[i_1se])}
    print(f"    α_min={est.alphas_[i_min]:.5f}({nm}基因,CV={cv[i_min]:.4f})；"
          f"α_1se={a1se:.5f}({n1}基因,CV={cv[i_1se]:.4f})")

    NB = 200
    freq = {g: 0 for g in genes_eval}
    nsel = []
    rr = np.random.default_rng(2026)
    for b in range(NB):
        bs = rr.integers(0, len(df), len(df))
        try:
            m = CoxnetSurvivalAnalysis(l1_ratio=1.0, alphas=[a1se]).fit(Xm[bs], y[bs])
            w = m.coef_[:, 0]
            sel = [g for g, c in zip(genes_eval, w) if abs(c) > 1e-8]
            for g in sel:
                freq[g] += 1
            nsel.append(len(sel))
        except Exception:
            pass
    st = pd.DataFrame({"gene": genes_eval, "freq": [freq[g] / NB for g in genes_eval]})
    st = st.sort_values("freq", ascending=False)
    st.to_csv(os.path.join(DATA, "modelB_stability.csv"), index=False)
    stable = list(st[st["freq"] >= 0.75]["gene"])
    out["lasso"]["median_selected"] = int(np.median(nsel)) if nsel else None
    out["lasso"]["n_pi75"] = len(stable)
    print(f"    bootstrap 中位入选 {int(np.median(nsel))}；π≥0.75 → {len(stable)} 基因 {stable}")

    # 稳定性集 → 多因素 Cox 逐步剔除
    cur = stable[:]; removed = []
    while len(cur) > 1:
        dfb = ((df[cur] - df[cur].mean()) / df[cur].std()).copy()
        dfb["T"] = df["T"].values; dfb["E"] = df["E"].values
        _, tb = cox_multi(dfb, "T", "E", cur, penalizer=0.0)
        if (tb["p"] >= 0.05).any() and len(cur) > 2:
            drop = tb.loc[tb["p"].idxmax(), "term"]
            removed.append(drop); cur = [g for g in cur if g != drop]
        else:
            break
    dfb = ((df[cur] - df[cur].mean()) / df[cur].std()).copy()
    dfb["T"] = df["T"].values; dfb["E"] = df["E"].values
    cB, coefB = cox_multi(dfb, "T", "E", cur, penalizer=0.0)
    coefB.to_csv(os.path.join(DATA, "modelB_coef.csv"), index=False)
    scoreB = np.log(cB.predict_partial_hazard(dfb).values.reshape(-1))
    out["modelB"] = {"stable": stable, "final_genes": cur, "removed": removed,
                     "n_genes": len(cur)}
    print(f"    Model B 最终 {len(cur)} 基因 {cur}；事后剔除 {removed}")

    # ---------------- 风险评分评估
    print("[6] 风险评分、KM、时间依赖 ROC")
    surv_train = Surv.from_arrays(df["E"].astype(bool).values, df["T"].values)

    def evaluate(score, label):
        r = {}
        gm = np.median(score)
        grp = (score > gm).astype(int)
        r["n_high"] = int(grp.sum()); r["n_low"] = int((1 - grp).sum())
        r["median_OS_low"] = float(km_median(df["T"].values[grp == 0], df["E"].values[grp == 0]))
        r["median_OS_high"] = float(km_median(df["T"].values[grp == 1], df["E"].values[grp == 1]))
        lr = logrank_test(df["T"].values[grp == 1], df["T"].values[grp == 0],
                          df["E"].values[grp == 1], df["E"].values[grp == 0])
        r["logrank_p"] = float(lr.p_value)
        z = (score - score.mean()) / score.std()
        c1 = CoxPHFitter().fit(pd.DataFrame({"z": z, "T": df["T"].values, "E": df["E"].values}),
                               duration_col="T", event_col="E")
        s1 = c1.summary.loc["z"]
        r["HR_per_SD"] = float(s1["exp(coef)"]); r["HR_lo"] = float(s1["exp(coef) lower 95%"])
        r["HR_hi"] = float(s1["exp(coef) upper 95%"]); r["p_cont"] = float(s1["p"])
        r["c_index"] = float(cidx(df["T"].values, df["E"].values, score))
        lo, hi = bootstrap_c(score, df["T"].values, df["E"].values, B=1000)
        r["c_index_CI"] = [lo, hi]
        times = np.arange(12, 121, 6).astype(float)
        try:
            auc, mean_auc = cumulative_dynamic_auc(surv_train, surv_train, score, times)
            r["auc_times"] = times.tolist()
            r["auc"] = [float(x) for x in auc]
            r["mean_auc"] = float(mean_auc)
            r["auc_135"] = {1: float(auc[list(times).index(12)]),
                            3: float(auc[list(times).index(36)]),
                            5: float(auc[list(times).index(60)])}
        except Exception as e:
            r["auc_err"] = str(e)
        print(f"    {label}: 高/低={r['n_high']}/{r['n_low']}, 中位OS {r['median_OS_low']:.1f} vs "
              f"{r['median_OS_high']:.1f}, log-rank P={r['logrank_p']:.3e}, C={r['c_index']:.4f} "
              f"({r.get('c_index_CI')}), HR/SD={r['HR_per_SD']:.3f}")
        return r, grp

    resA, grpA = evaluate(scoreA, "Model A"); out["modelA"].update(resA)
    resB, grpB = evaluate(scoreB, "Model B"); out["modelB"].update(resB)
    # 方向一致性
    flipA = sum(1 for _, x in coefA.iterrows()
                if (udf[udf.gene == x["term"]]["beta"].values[0] < 0) != (x["coef"] < 0))
    flipB = sum(1 for _, x in coefB.iterrows()
                if (udf[udf.gene == x["term"]]["beta"].values[0] < 0) != (x["coef"] < 0))
    out["modelA"]["sign_flips"] = int(flipA)
    out["modelB"]["sign_flips"] = int(flipB)

    rs = df[["T", "E", "AGE", "SEX", "AJCC_PATHOLOGIC_TUMOR_STAGE", "GRADE",
             "TMB_NONSYNONYMOUS"]].copy()
    rs["scoreA"] = scoreA; rs["groupA"] = grpA
    rs["scoreB"] = scoreB; rs["groupB"] = grpB
    rs.to_csv(os.path.join(DATA, "risk_scores.csv"))

    # ---------------- 多因素校正
    print("[7] 多因素校正")
    stg = df["AJCC_PATHOLOGIC_TUMOR_STAGE"].astype(str).str.upper()
    df["stage_III_IV"] = stg.str.contains("III|IV", na=False).astype(int)
    df["grade_G3_G4"] = df["GRADE"].astype(str).str.upper().str.contains("G3|G4", na=False).astype(int)
    df["sex_male"] = df["SEX"].astype(str).str.upper().str.startswith("M").astype(int)
    base = {}
    for nm in ["AGE", "sex_male", "stage_III_IV", "grade_G3_G4"]:
        try:
            cc = CoxPHFitter().fit(df[[nm, "T", "E"]], duration_col="T", event_col="E")
            s = cc.summary.loc[nm]
            base[nm] = {"HR": float(s["exp(coef)"]), "lo": float(s["exp(coef) lower 95%"]),
                        "hi": float(s["exp(coef) upper 95%"]), "p": float(s["p"]),
                        "C": float(cidx(df["T"].values, df["E"].values, df[nm].values))}
        except Exception:
            pass
    out["baseline"] = base

    mv_rows = []
    for score, lab in [(scoreA, "Model A"), (scoreB, "Model B")]:
        d2 = df.copy()
        d2["score_z"] = (score - score.mean()) / score.std()
        d2["age_z"] = (d2["AGE"] - d2["AGE"].mean()) / d2["AGE"].std()
        covars = ["score_z", "age_z", "sex_male", "stage_III_IV", "grade_G3_G4"]
        _, tb = cox_multi(d2, "T", "E", covars, penalizer=0.0)
        tb["model"] = lab
        mv_rows.append(tb)
        print(f"    {lab}: score HR={tb.loc[0,'HR']:.3f} ({tb.loc[0,'lo']:.3f}-{tb.loc[0,'hi']:.3f}), "
              f"P={tb.loc[0,'p']:.2e}")
    mvdf = pd.concat(mv_rows, ignore_index=True)
    mvdf.to_csv(os.path.join(DATA, "multivariable.csv"), index=False)
    for lab in ("Model A", "Model B"):
        sub = mvdf[mvdf.model == lab]
        out["adjusted_" + lab.replace(" ", "")] = {
            "HR": float(sub.iloc[0]["HR"]), "lo": float(sub.iloc[0]["lo"]),
            "hi": float(sub.iloc[0]["hi"]), "p": float(sub.iloc[0]["p"])}

    # ---------------- 增殖评分对照
    print("[8] 增殖评分对照（20 基因）")
    PROLIF = ["MKI67", "PCNA", "CCNB1", "CCNB2", "CDK1", "BUB1", "BUB1B", "AURKA",
              "AURKB", "TOP2A", "MCM2", "MCM3", "MCM4", "MCM6", "MCM7", "CDKN3",
              "RACGAP1", "ASPM", "CENPE", "TTK"]
    s2p = symbol_to_entrez(PROLIF, os.path.join(DATA, ".entrez_prolif.json"))
    pexpr = fetch_molecular(ZPROF, s2p, os.path.join(DATA, "prolif_expr_z.csv"))
    prolif_info = {}
    if pexpr is not None:
        pg = [g for g in PROLIF if g in pexpr.columns]
        pp = pexpr.loc[[p for p in df.index if p in pexpr.index], pg].mean(1)
        common = [p for p in df.index if p in pp.index]
        ps = pp.loc[common].values
        d3 = df.loc[common].copy()
        out["prolif_genes_used"] = len(pg)
        for score, lab in [(scoreA, "A"), (scoreB, "B")]:
            sc = pd.Series(score, index=df.index).loc[common].values
            rho, pv = spearmanr(sc, ps)
            prolif_info[lab] = {"spearman_rho": float(rho), "p": float(pv), "n": len(common)}
            d3["score_z"] = (sc - sc.mean()) / sc.std()
            d3["prolif_z"] = (ps - ps.mean()) / ps.std()
            _, tj = cox_multi(d3, "T", "E", ["score_z", "prolif_z"], penalizer=0.0)
            prolif_info[lab]["joint_score"] = {"HR": float(tj.iloc[0]["HR"]),
                                               "p": float(tj.iloc[0]["p"])}
            prolif_info[lab]["joint_prolif"] = {"HR": float(tj.iloc[1]["HR"]),
                                                "p": float(tj.iloc[1]["p"])}
            d3["age_z"] = (d3["AGE"] - d3["AGE"].mean()) / d3["AGE"].std()
            _, tj2 = cox_multi(d3, "T", "E",
                               ["score_z", "prolif_z", "age_z", "sex_male", "stage_III_IV", "grade_G3_G4"],
                               penalizer=0.0)
            prolif_info[lab]["joint_adj_score_p"] = float(tj2.iloc[0]["p"])
            prolif_info[lab]["joint_adj_prolif_p"] = float(tj2.iloc[1]["p"])
            prolif_info[lab]["prolif_alone_C"] = float(cidx(d3["T"].values, d3["E"].values, ps))
        out["prolif"] = prolif_info
        print(f"    增殖评分 rho：A={prolif_info['A']['spearman_rho']:.3f}, "
              f"B={prolif_info['B']['spearman_rho']:.3f}")

    # ---------------- k-means
    print("[9] k-means 分子分型")
    Xk = ((df[genes_eval] - df[genes_eval].mean()) / df[genes_eval].std()).values
    U, S, Vt = np.linalg.svd(Xk - Xk.mean(0), full_matrices=False)
    evr = (S ** 2) / np.sum(S ** 2)
    out["pca_evr"] = [float(evr[0]), float(evr[1])]
    km = {}
    for k in (2, 3, 4):
        best = None
        for sd in (7, 11, 23):
            lab = kmeans_np(Xk, k, seed=sd)
            sil = silhouette(Xk, lab)
            if best is None or sil > best[0]:
                best = (sil, lab)
        km[k] = best
    bestk = max(km, key=lambda k: km[k][0])
    lab = km[bestk][1]
    lr = logrank_test(df["T"].values[lab == 0], df["T"].values[lab == 1],
                      df["E"].values[lab == 0], df["E"].values[lab == 1])
    out["kmeans"] = {"best_k": int(bestk),
                     "sil": {str(k): round(km[k][0], 4) for k in km},
                     "sizes": [int((lab == c).sum()) for c in range(bestk)],
                     "deaths": [int(df["E"].values[lab == c].sum()) for c in range(bestk)],
                     "logrank_p": float(lr.p_value)}
    print(f"    最优 k={bestk}, silhouette={km[bestk][0]:.4f}, 例数={out['kmeans']['sizes']}, "
          f"log-rank P={lr.p_value:.3e}")
    np.save(os.path.join(DATA, "kmeans_labels.npy"), lab)
    np.save(os.path.join(DATA, "pcs.npy"), (U * S)[:, :4])

    # ---------------- 免疫浸润
    print("[10] 免疫浸润（ssGSEA-lite）")
    IMMUNE = {
        "CD8_T": ["CD8A", "CD8B", "GZMA", "GZMB", "PRF1", "IFNG"],
        "CD4_T": ["CD4", "IL7R", "CCR7", "LCK", "CD3D", "CD3E"],
        "Treg": ["FOXP3", "IL2RA", "CTLA4", "TIGIT", "IKZF2"],
        "NK": ["KLRD1", "NKG7", "GNLY", "KLRB1"],
        "B_cell": ["MS4A1", "CD79A", "CD79B", "CD19", "IGHM"],
        "M1_macro": ["CD68", "IL1B", "NOS2", "PTGS2", "TNF"],
        "M2_macro": ["CD163", "MRC1", "MS4A4A", "CLEC10A", "VSIG4"],
        "DC": ["ITGAX", "HLA-DRA", "HLA-DPB1", "CD1C", "THBD"],
        "Neutrophil": ["S100A8", "S100A9", "CSF3R", "FCGR3B"],
        "Checkpoint": ["PDCD1", "CD274", "CTLA4", "LAG3", "HAVCR2", "TIGIT"],
        "IFN_signature": ["IFNG", "STAT1", "CXCL9", "CXCL10", "IDO1"],
    }
    need = sorted({g for v in IMMUNE.values() for g in v})
    s2i = symbol_to_entrez(need, os.path.join(DATA, ".entrez_imm.json"))
    ie = fetch_molecular(ZPROF, s2i, os.path.join(DATA, "immune_expr_z.csv"))
    imms = []
    if ie is not None:
        common = [p for p in df.index if p in ie.index]
        ie2 = ie.loc[common]
        gv = pd.Series(grpB, index=df.index).loc[common]
        pos = 0; tot = 0
        for feat, gl in IMMUNE.items():
            present = [g for g in gl if g in ie2.columns]
            if len(present) < 2:
                continue
            sc = ie2[present].mean(1)
            a = sc[gv == 1]; b_ = sc[gv == 0]
            u, pv = mannwhitneyu(a, b_, alternative="two-sided")
            diff = float(a.mean() - b_.mean())
            imms.append({"feature": feat, "n_genes": len(present),
                         "low": float(b_.mean()), "high": float(a.mean()),
                         "diff": diff, "p": float(pv)})
            tot += 1
            if diff > 0:
                pos += 1
        pd.DataFrame(imms).to_csv(os.path.join(DATA, "immune_infiltration.csv"), index=False)
        out["immune"] = {"n_features": tot, "n_higher_in_high_risk": pos}
        print(f"    {tot} 项特征中 {pos} 项在高风险组更高")

    # ---------------- 突变
    print("[11] 突变频率")
    MUT = ["TP53", "CTNNB1", "TTN", "AXIN1", "ARID1A", "ARID2", "TSC1", "TSC2",
           "NFE2L2", "KEAP1", "ALB", "APOB", "RB1", "PTEN", "PIK3CA", "BAP1"]
    s2m = symbol_to_entrez(MUT, os.path.join(DATA, ".entrez_mut.json"))
    prof = None
    for p in http(f"{API}/studies/{STUDY}/molecular-profiles") or []:
        if p.get("molecularAlterationType") == "MUTATION_EXTENDED":
            prof = p["molecularProfileId"]; break
    data = http(f"{API}/molecular-profiles/{prof}/mutations/fetch",
                {"sampleListId": STUDY + "_sequenced",
                 "entrezGeneIds": [s2m[g] for g in MUT if g in s2m]})
    if data:
        json.dump(data, open(os.path.join(DATA, "mutations_raw.json"), "w"))
        ent2sym = {v: k for k, v in s2m.items()}
        samp = http(f"{API}/studies/{STUDY}/samples?projection=DETAILED") or []
        s2p = {s["sampleId"]: s["uniquePatientKey"] for s in samp}
        groups = dict(zip(df.index, grpB))
        nhi = int((grpB == 1).sum()); nlo = int((grpB == 0).sum())
        patmut = {}
        for m in data:
            pk = m.get("uniquePatientKey") or s2p.get(m.get("sampleId"))
            g = (m.get("gene") or {}).get("hugoGeneSymbol") or ent2sym.get(m.get("entrezGeneId"))
            if pk in groups and g:
                patmut.setdefault(pk, set()).add(g)
        rows = []
        for g in MUT:
            hi = sum(1 for p, s in patmut.items() if groups[p] == 1 and g in s)
            lo = sum(1 for p, s in patmut.items() if groups[p] == 0 and g in s)
            if hi + lo == 0:
                continue
            try:
                _, pv = fisher_exact([[hi, nhi - hi], [lo, nlo - lo]])
            except Exception:
                pv = float("nan")
            rows.append({"gene": g, "high_n": hi, "low_n": lo,
                         "high_pct": 100 * hi / nhi, "low_pct": 100 * lo / nlo,
                         "p": float(pv)})
        if rows:
            mdf = pd.DataFrame(rows).sort_values("p")
            mdf.to_csv(os.path.join(DATA, "mutations.csv"), index=False)
            print(f"    突变基因 {len(mdf)} 个；有突变记录的患者 {len(patmut)}")
            out["mutation_n_high"] = nhi; out["mutation_n_low"] = nlo
        else:
            print("    [warn] 突变未映射到队列患者")

    # ---------------- 肿瘤 vs 正常（ref-normal Z）
    if expr_rn is not None:
        common = [p for p in df.index if p in expr_rn.index]
        rn = expr_rn.loc[common, [g for g in genes_eval if g in expr_rn.columns]]
        means_rn = rn.mean()
        n_up = int((means_rn > 1).sum()); n_dn = int((means_rn < -1).sum())
        out["refnormal"] = {"n_eval": int(rn.shape[1]), "n_up_z1": n_up, "n_down_z1": n_dn,
                            "mean_z_median": float(means_rn.median())}
        means_rn.to_csv(os.path.join(DATA, "tumor_vs_normal.csv"))
        print(f"    ref-normal Z：{n_up} 个基因 z>1，{n_dn} 个 z<-1")

    out["runtime_s"] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(DATA, "results.json"), "w"), indent=2, ensure_ascii=False)
    print("\n===== 完成 =====")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
