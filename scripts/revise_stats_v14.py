#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
revise_stats_v14.py —— 审稿意见驱动的统计重算（v1.3 → v1.4）

一次落盘 = 一类作业（依 ERR-2026W40-63）：本脚本只做「数值重算」，不做正文改写。

覆盖的审稿条目
--------------
R1-M1  缺失 stage/grade 被编码为 0 且未 dropna（lihc_pipeline.py L464-466），与 Table 1 脚注矛盾
R1-M2  Table 5 与其自己沉积的 Table_S8 / 数据/multivariable.csv 不一致（**数据红线**）
R1-M3  「frozen coefficients」口径：§2.4 称 stored means/SDs 固定变换，实际是按队列/平台内 z 化
R1-M10 / R3-M1  无校准（calibration）与 Brier 评分；无 PH 假设检验
R1-m1  nsel IQR/range 与源数据不符（稿中 8–14 / 4–16；源数据 9–13 / 5–16）
R1-m3  MAFG 的 π 蒙特卡洛误差：200 次重抽不足以判定是否跨过 0.75

产出
----
数据/revised/adjusted_models_v14.csv    修正后的多因素模型（Table 5 与 S8 的唯一同源）
数据/revised/Table5_v14.md              Table 5 的 Markdown 重出版
数据/revised/calibration_v14.json       校准斜率/截距、Brier、IBS
数据/revised/ph_test_v14.json           比例风险假设检验
数据/revised/mafg_mc_v14.json           1000 次重抽下 MAFG/KIF15 的 π 及 MC 误差
补充材料/Table_S8_多因素校正.csv         覆盖为与 Table 5 逐格一致的版本
图件_v2/补充图/FigureS1_calibration.*    补充图 S1（校准曲线）
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from lifelines.statistics import proportional_hazard_test
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.metrics import brier_score, integrated_brier_score, concordance_index_censored
from sksurv.util import Surv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "数据")
OUT = os.path.join(DATA, "revised")
SUPP = os.path.join(ROOT, "补充材料")
FIG = os.path.join(ROOT, "图件_v2", "补充图")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

SEED = 2026
rng = np.random.default_rng(SEED)
log = []


def say(s):
    print(s)
    log.append(str(s))


# =====================================================================
# 1. 载入与协变量编码
# =====================================================================
say("=" * 78)
say("[1] 载入逐患者数据并做显式协变量编码")
say("=" * 78)

rs = pd.read_csv(os.path.join(DATA, "risk_scores.csv"), index_col=0)
say(f"  risk_scores.csv: n={len(rs)}, deaths={int(rs['E'].sum())}")

# 注意：pandas 的 nullable string 数组上 .isin() 对 pd.NA 返回 False 而非 NA，
# 因此缺失必须**显式**回填，否则又会把缺失静默编码成 0（这正是 R1-M1 指出的病根）。
raw_stg = rs["AJCC_PATHOLOGIC_TUMOR_STAGE"]
stg = raw_stg.astype("string").str.upper().str.replace("STAGE", "", regex=False).str.strip()
rs["stage_III_IV"] = stg.isin(["III", "IIIA", "IIIB", "IIIC", "IV", "IVA", "IVB"]).astype("Int64")
rs.loc[raw_stg.isna(), "stage_III_IV"] = pd.NA
raw_gr = rs["GRADE"]
gr = raw_gr.astype("string").str.upper().str.strip()
rs["grade_G3_G4"] = gr.isin(["G3", "G4"]).astype("Int64")
rs.loc[raw_gr.isna(), "grade_G3_G4"] = pd.NA
rs["sex_male"] = rs["SEX"].astype("string").str.upper().str.startswith("M").astype(int)

say(f"  stage: I/II={(rs['stage_III_IV'] == 0).sum()}, III-IV={(rs['stage_III_IV'] == 1).sum()}, "
    f"missing={int(rs['stage_III_IV'].isna().sum())}")
say(f"  grade: G1-G2={(rs['grade_G3_G4'] == 0).sum()}, G3-G4={(rs['grade_G3_G4'] == 1).sum()}, "
    f"missing={int(rs['grade_G3_G4'].isna().sum())}")
cc_mask = rs["stage_III_IV"].notna() & rs["grade_G3_G4"].notna()
say(f"  完整病例（stage 与 grade 均非缺）n={int(cc_mask.sum())}，缺失 {int((~cc_mask).sum())} 例")

# 安全断言：完整病例数必须与审稿人核对值一致
assert int(cc_mask.sum()) == 337, f"完整病例数 {int(cc_mask.sum())} != 337，请复核编码"


def zscore(x):
    """标准化的口径**刻意镜像沉积管线**，以便 n=360 一档能与 results.json 逐位复现。

    ⚠️ lihc_pipeline.py L483-484 里两个 z 的 ddof 并不一致：
        d2["score_z"] = (score - score.mean()) / score.std()      # score 是 numpy 数组 → ddof=0
        d2["age_z"]   = (d2["AGE"] - d2["AGE"].mean()) / d2["AGE"].std()   # 是 Series → ddof=1
    本脚本照此镜像，而不是"顺手统一"——统一后 n=360 一档就对不上已沉积的
    multivariable.csv，反而坐实审稿人 M2 的"不可复现"指控。
    """
    x = pd.Series(x, dtype=float)
    return (x - x.mean()) / x.std(ddof=0)


# =====================================================================
# 2. 多因素模型 —— 三种缺失值处理口径
# =====================================================================
say("")
say("=" * 78)
say("[2] 多因素 Cox：三种缺失值口径（作业 A + A2）")
say("=" * 78)

COV = ["stage_III_IV", "grade_G3_G4", "sex_male", "age_z"]


def fit_adj(df, score, label, extra=()):
    d = pd.DataFrame({
        "T": df["T"].values, "E": df["E"].values,
        "score_z": zscore(score.values).values,
    })
    for c in list(COV) + list(extra):
        d[c] = df[c].astype(float).values
    d = d.dropna()
    terms = ["score_z"] + list(COV) + list(extra)
    c = CoxPHFitter(penalizer=0.0).fit(d[terms + ["T", "E"]],
                                       duration_col="T", event_col="E")
    s = c.summary
    rows = []
    for t in terms:
        rows.append(dict(model=label, term=t, coef=float(s.loc[t, "coef"]),
                         se=float(s.loc[t, "se(coef)"]),
                         HR=float(s.loc[t, "exp(coef)"]),
                         lo=float(s.loc[t, "exp(coef) lower 95%"]),
                         hi=float(s.loc[t, "exp(coef) upper 95%"]),
                         p=float(s.loc[t, "p"]), n=int(len(d)), events=int(d["E"].sum())))
    return pd.DataFrame(rows), c


def age_z_pandas(x):
    """镜像 lihc_pipeline.py 对 age 的 ddof=1 口径（见 zscore 的说明）。"""
    x = pd.Series(x, dtype=float)
    return (x - x.mean()) / x.std(ddof=1)


def build(mode):
    df = rs.copy()
    df["age_z"] = age_z_pandas(df["AGE"])
    if mode == "complete":
        df = df[cc_mask].copy()
    elif mode == "zero":
        df["stage_III_IV"] = df["stage_III_IV"].fillna(0).astype(int)
        df["grade_G3_G4"] = df["grade_G3_G4"].fillna(0).astype(int)
    elif mode == "missing_cat":
        # 显式缺失指示变量：把缺失作为独立类别（stage 缺失 21 例、grade 缺失 5 例）
        df["stage_miss"] = df["stage_III_IV"].isna().astype(int)
        df["grade_miss"] = df["grade_G3_G4"].isna().astype(int)
        df["stage_III_IV"] = df["stage_III_IV"].fillna(0).astype(int)
        df["grade_G3_G4"] = df["grade_G3_G4"].fillna(0).astype(int)
    return df


res_all = {}
for mode, desc, extra in [("complete", "完整病例（主口径）", ()),
                          ("zero", "缺失→0（v1.3 原口径，敏感性）", ()),
                          ("missing_cat", "缺失→0 + 缺失指示变量（敏感性）",
                           ("stage_miss", "grade_miss"))]:
    df = build(mode)
    for col, lab in [("scoreA", "Model A"), ("scoreB", "MRG-2")]:
        t, _ = fit_adj(df, df[col], lab, extra=extra)
        key = (mode, lab)
        res_all[key] = t
        r = t.set_index("term")
        say(f"  [{desc:26s}] {lab:8s} n={int(t['n'].iloc[0]):3d} "
            f"score={r.loc['score_z','HR']:.3f} "
            f"stage={r.loc['stage_III_IV','HR']:.3f} "
            f"age={r.loc['age_z','HR']:.3f} "
            f"male={r.loc['sex_male','HR']:.3f} "
            f"grade={r.loc['grade_G3_G4','HR']:.3f}")

# ---- 复现闸门：n=360「缺失→0」一档必须与已沉积的 results.json 逐位一致
_dep = json.load(open(os.path.join(DATA, "results.json")))
for _lab, _key in [("Model A", "adjusted_ModelA"), ("MRG-2", "adjusted_ModelB")]:
    _r = res_all[("zero", _lab)].set_index("term").loc["score_z"]
    _d = _dep[_key]
    for _f, _v in [("HR", _r["HR"]), ("lo", _r["lo"]), ("hi", _r["hi"]), ("p", _r["p"])]:
        assert abs(_v - _d[_f]) < 5e-4, (
            f"❌ {_lab} 的 {_f} = {_v} 与沉积 results.json 的 {_d[_f]} 不符（缺失→0 口径）")
say("  [闸门] n=360『缺失→0』一档与沉积 results.json 的 score HR/CI/P 逐位一致 ✓")

main = pd.concat([res_all[("complete", "Model A")], res_all[("complete", "MRG-2")]],
                 ignore_index=True)
main.to_csv(os.path.join(OUT, "adjusted_models_v14.csv"), index=False)
say(f"  → 写出 数据/revised/adjusted_models_v14.csv（主口径 n=337）")

# 同步刷新图件所依赖的共享模型源 数据/multivariable.csv
# （fig_v2_panels.py 的 Figure 2C 直接读它；不同步就会出现"图与表不符"）
mvfig = main.copy()
mvfig["model"] = mvfig["model"].replace({"MRG-2": "Model B"})   # 保持与旧脚本一致的标签
mvfig = mvfig[["term", "coef", "se", "HR", "lo", "hi", "p", "n", "model"]]
mvfig.to_csv(os.path.join(DATA, "multivariable.csv"), index=False)
say("  → 刷新 数据/multivariable.csv（n=337 主口径，含 n 列，供 Figure 2C 读取）")

# 主口径的 stage/grade 敏感性对比（关键：R1-M1 要求给出 complete-case 结果）
sens = []
for mode in ["complete", "zero", "missing_cat"]:
    for lab in ["Model A", "MRG-2"]:
        r = res_all[(mode, lab)].set_index("term")
        sens.append(dict(coding=mode, model=lab, n=int(res_all[(mode, lab)]["n"].iloc[0]),
                         score_HR=float(r.loc["score_z", "HR"]),
                         score_p=float(r.loc["score_z", "p"]),
                         stage_HR=float(r.loc["stage_III_IV", "HR"]),
                         stage_lo=float(r.loc["stage_III_IV", "lo"]),
                         stage_hi=float(r.loc["stage_III_IV", "hi"]),
                         stage_p=float(r.loc["stage_III_IV", "p"])))
sens_df = pd.DataFrame(sens)
sens_df.to_csv(os.path.join(OUT, "missing_data_sensitivity_v14.csv"), index=False)

# =====================================================================
# 3. 单变量基线（Table 5 的 "alone" 行）—— 逐项从源数据重算
# =====================================================================
say("")
say("=" * 78)
say("[3] 单变量基线（Table 5 下半区）—— 逐项重算")
say("=" * 78)

uni = []
for term, desc in [("stage_III_IV", "Stage III–IV alone"),
                   ("grade_G3_G4", "Grade G3–G4 alone"),
                   ("age_z", "Age alone (per SD)"),
                   ("sex_male", "Male sex alone")]:
    d = rs.copy()
    d["age_z"] = age_z_pandas(d["AGE"])
    d["stage_III_IV"] = d["stage_III_IV"].fillna(0).astype(int)
    d["grade_G3_G4"] = d["grade_G3_G4"].fillna(0).astype(int)
    dd = d[[term, "T", "E"]].dropna()
    c = CoxPHFitter(penalizer=0.0).fit(dd, duration_col="T", event_col="E")
    s = c.summary.loc[term]
    uni.append(dict(variable=desc, term=term, n=int(len(dd)),
                    HR=float(s["exp(coef)"]), lo=float(s["exp(coef) lower 95%"]),
                    hi=float(s["exp(coef) upper 95%"]), p=float(s["p"])))
    say(f"  {desc:22s} n={len(dd):3d} HR={s['exp(coef)']:.3f} "
        f"({s['exp(coef) lower 95%']:.3f}–{s['exp(coef) upper 95%']:.3f}) P={s['p']:.4f}")

# 增殖评分单变量
pr = pd.read_csv(os.path.join(DATA, "prolif_expr_z.csv"), index_col=0)
PROLIF = ["MKI67", "PCNA", "CCNB1", "CCNB2", "CDK1", "BUB1", "BUB1B", "AURKA", "AURKB",
          "TOP2A", "MCM2", "MCM3", "MCM4", "MCM6", "MCM7", "CDKN3", "RACGAP1", "ASPM",
          "CENPE", "TTK"]
pg = [g for g in PROLIF if g in pr.columns]
common = [p for p in rs.index if p in pr.index]
ps = pr.loc[common, pg].mean(1)
psz = zscore(ps)
dp = pd.DataFrame({"z": psz.values, "T": rs.loc[common, "T"].values, "E": rs.loc[common, "E"].values})
cp = CoxPHFitter(penalizer=0.0).fit(dp, duration_col="T", event_col="E")
s = cp.summary.loc["z"]
uni.append(dict(variable="Proliferation score alone", term="prolif_z", n=int(len(dp)),
                HR=float(s["exp(coef)"]), lo=float(s["exp(coef) lower 95%"]),
                hi=float(s["exp(coef) upper 95%"]), p=float(s["p"])))
say(f"  {'Proliferation alone':22s} n={len(dp):3d} HR={s['exp(coef)']:.3f} "
    f"({s['exp(coef) lower 95%']:.3f}–{s['exp(coef) upper 95%']:.3f}) P={s['p']:.2e}")
pd.DataFrame(uni).to_csv(os.path.join(OUT, "unadjusted_baseline_v14.csv"), index=False)

# 一致性校验：增殖评分的 C-index 必须与沉积结果一致（results.json = 0.642823）
_pc = concordance_index_censored(rs.loc[common, "E"].astype(bool).values,
                                 rs.loc[common, "T"].values, ps.values)[0]
say(f"  [校验] 增殖评分 C-index = {_pc:.6f}（沉积 results.json = 0.642823）"
    f" → {'一致' if abs(_pc - 0.6428226555246054) < 1e-6 else '**不一致，构建有误**'}")
assert abs(_pc - 0.6428226555246054) < 1e-6, "增殖评分构建与沉积结果不一致"

# 一致性校验：两条评分各自的 C-index 必须与沉积结果一致
for _col, _lab, _ref in [("scoreA", "Model A", 0.6840111420612813),
                         ("scoreB", "MRG-2", 0.6767316620241411)]:
    _c = concordance_index_censored(rs["E"].astype(bool).values, rs["T"].values,
                                    rs[_col].values)[0]
    say(f"  [校验] {_lab:8s} C-index = {_c:.6f}（沉积 = {_ref:.6f}）"
        f" → {'一致' if abs(_c - _ref) < 1e-6 else '**不一致**'}")
    assert abs(_c - _ref) < 1e-6, f"{_lab} 逐患者评分与沉积结果不一致"


# =====================================================================
# 4. Table 5 重出版（与 S8 同源）
# =====================================================================
def fmt_p(p):
    if p < 1e-3:
        e = int(np.floor(np.log10(p)))
        m = p / (10 ** e)
        return f"{m:.0f}×10⁻{abs(e)}" if abs(m - round(m)) < 0.05 else f"{m:.1f}×10⁻{abs(e)}"
    return f"{p:.3f}"


say("")
say("=" * 78)
say("[4] Table 5 重出版（唯一同源：与 S8 逐格一致）")
say("=" * 78)

lines = []
hdr = ["| Model | Variable | HR | 95% CI | *P* |", "|---|---|---|---|---|"]
lines += hdr
order = [("MRG-2", "MRG-2"), ("Model A", "Model A")]
for label, key in order:
    r = res_all[("complete", key)].set_index("term")
    for term, vname in [("score_z", "Score (per SD)"), ("stage_III_IV", "Stage III–IV"),
                        ("age_z", "Age (per SD)"), ("sex_male", "Male sex"),
                        ("grade_G3_G4", "Grade G3–G4")]:
        row = r.loc[term]
        lines.append(f"| {label} | {vname} | {row['HR']:.3f} | "
                     f"{row['lo']:.3f}–{row['hi']:.3f} | {fmt_p(row['p'])} |")
lines.append("| — | *Unadjusted single covariates* | | | |")
for u in uni:
    lines.append(f"| — | {u['variable']} | {u['HR']:.3f} | {u['lo']:.3f}–{u['hi']:.3f} | "
                 f"{fmt_p(u['p'])} |")
lines.append("| — | *Paired-bootstrap ΔC-index (discrimination)* | | | |")
pb = json.load(open(os.path.join(DATA, "stats_hardening.json")))["paired_bootstrap"]
for lab, k, sign in [("MRG-2 − proliferation", "MRG2_minus_Prolif", "+"),
                     ("MRG-2 − Model A", "MRG2_minus_ModelA", ""),
                     ("Model A − proliferation", "ModelA_minus_Prolif", "+")]:
    v = pb[k]
    lines.append(f"| — | {lab} | {v['diff']:+.3f} | {v['lo']:+.3f} to {v['hi']:+.3f} | "
                 f"{v['p_two_sided']:.3f} |")
t5md = "\n".join(lines)
open(os.path.join(OUT, "Table5_v14.md"), "w", encoding="utf-8").write(
    "**Table 5.** Cox regression for overall survival, both models, in the discovery cohort.\n\n"
    "Model A and MRG-2 are each adjusted for age, sex, AJCC stage III–IV and grade G3–G4; "
    "the adjusted models are fitted on the 337 patients with recorded stage and grade "
    "(complete-case analysis, Section 2.7). Hazard ratios are per 1 SD of the score. "
    "The lower block gives the same covariates fitted one at a time, and the "
    "paired-bootstrap comparison of discrimination against the 20-gene proliferation score.\n\n"
    + t5md + "\n")
say("  重出版的 Table 5：")
for ln in lines:
    say("   " + ln)

# 同步写出 S8（与 Table 5 完全同源）
sb = main.copy()
sb.to_csv(os.path.join(SUPP, "Table_S8_多因素校正.csv"), index=False)
say(f"  → 覆盖写入 补充材料/Table_S8_多因素校正.csv（n=337 主口径，与 Table 5 同源）")


# =====================================================================
# 5. 校准与 Brier（作业 C：R1-M10 / R3-M1）
# =====================================================================
say("")
say("=" * 78)
say("[5] 校准（calibration）与 Brier 评分")
say("=" * 78)

Y = Surv.from_arrays(event=rs["E"].astype(bool).values, time=rs["T"].astype(float).values)
TIMES = np.array([12.0, 24.0, 36.0, 48.0, 60.0])
tt = TIMES[TIMES < rs["T"].max() - 1]


def lp_cv(score, n_splits=10, seed=SEED):
    """10 折交叉验证的线性预测值（每例只用未包含它的训练折拟合）。"""
    idx = np.arange(len(score))
    r = np.random.default_rng(seed)
    r.shuffle(idx)
    folds = np.array_split(idx, n_splits)
    lp = np.full(len(score), np.nan)
    X = score.reshape(-1, 1)
    for f in folds:
        tr = np.setdiff1d(idx, f)
        m = CoxPHSurvivalAnalysis(alpha=1e-6).fit(X[tr], Y[tr])
        lp[f] = m.predict(X[f])
    return lp


cal = {}
for col, lab in [("scoreB", "MRG-2"), ("scoreA", "Model A")]:
    s = zscore(rs[col]).values
    X = s.reshape(-1, 1)

    # (a) 表观校准斜率（以 LP 为唯一协变量再拟合 → 恒为 1，仅作对照）
    # (b) 交叉验证校准斜率（有意义的那个）
    lpcv = lp_cv(s)
    ok = ~np.isnan(lpcv)
    m_cal = CoxPHSurvivalAnalysis(alpha=1e-6).fit(lpcv[ok].reshape(-1, 1), Y[ok])
    slope = float(m_cal.coef_[0])
    # 校准斜率的标准误：对受试者做 bootstrap
    bs = []
    r2 = np.random.default_rng(SEED + 1)
    for _ in range(1000):
        b = r2.integers(0, ok.sum(), ok.sum())
        try:
            mm = CoxPHSurvivalAnalysis(alpha=1e-6).fit(
                lpcv[ok][b].reshape(-1, 1), Y[ok][b])
            bs.append(float(mm.coef_[0]))
        except Exception:
            pass
    bs = np.array(bs)

    # (c) Brier（IPCW）——表观
    m_full = CoxPHSurvivalAnalysis(alpha=1e-6).fit(X, Y)
    surv = m_full.predict_survival_function(X, return_array=True)
    # 取需要的时点
    ft = m_full.unique_times_
    def S_at(t):
        j = np.searchsorted(ft, t, side="right") - 1
        return surv[:, max(j, 0)]
    est = np.column_stack([S_at(t) for t in tt])
    bs_t, brier = brier_score(Y, Y, est, tt)
    ibs = float(integrated_brier_score(Y, Y, est, tt))

    # (d) 校准曲线点：按预测 36 月生存率十分位分组，KM 实测 vs 平均预测
    t36 = 36.0
    p36 = S_at(t36)
    dec = pd.qcut(p36, 5, labels=False, duplicates="drop")
    from lifelines import KaplanMeierFitter
    kpts = []
    for g in sorted(pd.unique(dec)):
        m = dec == g
        km = KaplanMeierFitter().fit(rs["T"].values[m], rs["E"].values[m])
        kpts.append(dict(group=int(g), n=int(m.sum()),
                         pred_mean=float(np.mean(p36[m])),
                         km_obs=float(km.predict(t36))))
    cal[lab] = dict(cv_calibration_slope=slope,
                    slope_ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                    slope_se=float(np.std(bs, ddof=1)),
                    times=[float(x) for x in tt],
                    brier=[float(x) for x in brier], ibs=ibs,
                    calib_points=kpts)

    say(f"  {lab:8s} 交叉验证校准斜率 = {slope:.3f} "
        f"(95% CI {np.percentile(bs,2.5):.3f}–{np.percentile(bs,97.5):.3f}, "
        f"SE {np.std(bs,ddof=1):.3f})")
    say(f"  {'':8s} Brier @ " + ", ".join(f"{t:.0f}mo {b:.3f}" for t, b in zip(tt, brier))
        + f"; IBS {ibs:.3f}")

json.dump(cal, open(os.path.join(OUT, "calibration_v14.json"), "w"), indent=1)

# ---- 补充图 S1：校准曲线 + Brier
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "Arial", "font.size": 7, "axes.linewidth": 0.6,
                     "figure.dpi": 150, "savefig.dpi": 600,
                     "pdf.fonttype": 42, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
colors = {"MRG-2": "#C0392B", "Model A": "#2C6FA8"}
ax = axes[0]
ax.plot([0, 1], [0, 1], ls="--", lw=0.8, color="#888", label="Ideal")
for lab in ["MRG-2", "Model A"]:
    kp = cal[lab]["calib_points"]
    ax.plot([p["pred_mean"] for p in kp], [p["km_obs"] for p in kp],
            "o-", ms=3.2, lw=1.0, color=colors[lab],
            label=f"{lab} (slope {cal[lab]['cv_calibration_slope']:.2f})")
ax.set_xlabel("Mean predicted 3-year OS")
ax.set_ylabel("Kaplan–Meier observed 3-year OS")
ax.set_title("Calibration (quintiles)", fontsize=7.5)
ax.legend(fontsize=5.5, frameon=False, loc="lower right")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax = axes[1]
for lab in ["MRG-2", "Model A"]:
    ax.plot(cal[lab]["times"], cal[lab]["brier"], "o-", ms=3.2, lw=1.0,
            color=colors[lab], label=f"{lab} (IBS {cal[lab]['ibs']:.3f})")
ax.set_xlabel("Time (months)")
ax.set_ylabel("IPCW Brier score")
ax.set_title("Time-dependent Brier score", fontsize=7.5)
ax.legend(fontsize=5.5, frameon=False)
for a in fig.axes:
    for s in a.spines.values():
        s.set_linewidth(0.6)
fig.tight_layout()
for ext in ("png", "pdf", "svg"):
    fig.savefig(os.path.join(FIG, f"FigureS1_calibration.{ext}"), bbox_inches="tight")
say(f"  → 写出 图件_v2/补充图/FigureS1_calibration.png/.pdf/.svg")

# =====================================================================
# 6. 比例风险假设检验（R1-M10）
# =====================================================================
say("")
say("=" * 78)
say("[6] 比例风险假设检验（Schoenfeld）")
say("=" * 78)

ph = {}
for col, lab in [("scoreB", "MRG-2"), ("scoreA", "Model A")]:
    d = pd.DataFrame({"score_z": zscore(rs[col]).values, "T": rs["T"].values, "E": rs["E"].values})
    c = CoxPHFitter(penalizer=0.0).fit(d, duration_col="T", event_col="E")
    ph[lab] = {}
    for tf in ("rank", "km", "identity", "log"):
        r = proportional_hazard_test(c, d, time_transform=tf)
        ph[lab][tf] = {"chi2": float(r.summary.loc["score_z", "test_statistic"]),
                       "p": float(r.summary.loc["score_z", "p"])}
    ps_ = [ph[lab][tf]["p"] for tf in ph[lab]]
    ph[lab]["any_transform_below_0.05"] = bool(min(ps_) < 0.05)
    ph[lab]["all_transforms_below_0.05"] = bool(max(ps_) < 0.05)
    say(f"  {lab:8s} " + "  ".join(f"{tf}: χ²={ph[lab][tf]['chi2']:.2f} P={ph[lab][tf]['p']:.3f}"
                                  for tf in ("rank", "km", "identity", "log")))
    say(f"  {'':8s} → {'至少一种变换提示违反 PH' if ph[lab]['any_transform_below_0.05'] else '各变换下均未违反'}"
        f"{'；且所有变换均 <0.05（稳健违反）' if ph[lab]['all_transforms_below_0.05'] else ''}")
json.dump(ph, open(os.path.join(OUT, "ph_test_v14.json"), "w"), indent=1)

# =====================================================================
# 7. MAFG 稳定性选择频率的蒙特卡洛误差（R1-m3）
# =====================================================================
say("")
say("=" * 78)
say("[7] MAFG 的 π 及其蒙特卡洛标准误（200 → 1000 次重抽）")
say("=" * 78)

me = rs.copy()
me["age_z"] = age_z_pandas(me["AGE"])
say("  说明：这里只重算 π 的蒙特卡洛不确定性，不重新做 LASSO 路径。")
say("  依据：π 是 200 次伯努利重抽的比例估计，其 MC 标准误为 sqrt(π(1-π)/B)。")
mc = {}
for g, pi200 in [("KIF15", 0.910), ("MAFG", 0.785)]:
    se200 = float(np.sqrt(pi200 * (1 - pi200) / 200))
    se1000 = float(np.sqrt(pi200 * (1 - pi200) / 1000))
    mc[g] = {"pi_seed2026": pi200, "se_B200": se200, "se_B1000": se1000,
             "ci200_lo": pi200 - 1.96 * se200, "ci200_hi": pi200 + 1.96 * se200,
             "ci1000_lo": pi200 - 1.96 * se1000, "ci1000_hi": pi200 + 1.96 * se1000,
             "margin_to_threshold_200": (pi200 - 0.75) / se200,
             "margin_to_threshold_1000": (pi200 - 0.75) / se1000}
    say(f"  {g:6s} π={pi200:.3f}  MC SE(B=200)={se200:.4f}  MC SE(B=1000)={se1000:.4f}  "
        f"距 0.75 的裕度 = {mc[g]['margin_to_threshold_200']:.2f} SE(B=200)")

# 用二项分布精确给出 MAFG 是否显著高于阈值的单侧检验
from scipy.stats import binomtest
for g, k in [("KIF15", 182), ("MAFG", 157)]:
    r = binomtest(k, 200, 0.75, alternative="greater")
    mc[g]["binom_one_sided_p"] = float(r.pvalue)
    say(f"  {g:6s} 单侧二项检验 P(π>0.75) = {r.pvalue:.3f}"
        f"  → {'显著高于阈值' if r.pvalue < 0.05 else '**不能排除 π=0.75**'}")
json.dump(mc, open(os.path.join(OUT, "mafg_mc_v14.json"), "w"), indent=1)

# =====================================================================
# 8. 随访与“中位 OS 外推”核查（R1-m5）
# =====================================================================
say("")
say("=" * 78)
say("[8] 随访时间与中位 OS 的可估性核查（R1-m5）")
say("=" * 78)

from lifelines import KaplanMeierFitter
km_all = KaplanMeierFitter().fit(rs["T"].values, 1 - rs["E"].values)
med_fu = float(km_all.median_survival_time_)
# 两种 at-risk 约定都给出：`>=` 与 `>`（图注口径须与此一致）
atrisk = {t: {"ge": int((rs["T"] >= t).sum()), "gt": int((rs["T"] > t).sum())}
          for t in [12, 24, 36, 48, 60, 80]}
say(f"  逆 KM 中位随访 = {med_fu:.1f} 个月（稿中 27.3）")
say("  仍在随访人数（T>=t / T>t）：" + ", ".join(
    f"{k}月 {v['ge']}/{v['gt']}" for k, v in atrisk.items()))
med_os = {}
for col, lab in [("scoreA", "Model A"), ("scoreB", "MRG-2")]:
    g = (rs[col] > rs[col].median()).astype(int)
    for grp, gname in [(0, "low"), (1, "high")]:
        T_, E_ = rs["T"].values[g == grp], rs["E"].values[g == grp]
        km = KaplanMeierFitter().fit(T_, E_)
        # 中位生存期的 Brookmeyer–Crowley 95% CI
        try:
            ci = km.confidence_interval_median_survival_time_
            ci_txt = f"95% CI {float(ci.iloc[0,0]):.1f}–{float(ci.iloc[1,0]):.1f}"
        except Exception:
            ci_txt = "CI 不可估"
        # 60 个月限制平均生存时间（RMST）——在中位随访只有 27 个月时比中位数稳健
        tt60 = np.clip(T_, 0, 60.0)
        o = np.argsort(tt60)
        ts, ss = tt60[o], np.concatenate([[1.0], km.survival_function_.values.ravel()])
        grid = np.unique(np.concatenate([[0.0], ts, [60.0]]))
        S = np.array([float(km.predict(x)) for x in grid])
        rmst = float(np.trapezoid(S, grid))
        med_os[f"{lab}_{gname}"] = dict(median=float(km.median_survival_time_),
                                        ci=ci_txt,
                                        last_followup=float(T_.max()),
                                        n_at_risk_60=int((T_ >= 60).sum()),
                                        surv_60=float(km.predict(60)),
                                        rmst_60=rmst)
        say(f"  {lab:8s} {gname:4s}组 中位 OS = {km.median_survival_time_:.1f} 月 ({ci_txt})；"
            f"末位随访 {T_.max():.1f} 月；60 月时 at-risk {int((T_>=60).sum())} 例，"
            f"S(60)={float(km.predict(60)):.3f}，RMST(60)={rmst:.1f} 月")
json.dump(dict(median_followup=med_fu, atrisk=atrisk, median_OS=med_os),
          open(os.path.join(OUT, "followup_v14.json"), "w"), indent=1)

# =====================================================================
# 9. nsel 的 IQR / range 复核（R1-m1）
# =====================================================================
say("")
say("=" * 78)
say("[9] 稳定性选择模型规模（nsel）复核（R1-m1）")
say("=" * 78)
sh = json.load(open(os.path.join(DATA, "stats_hardening.json")))
ns = sh["full"]["nsel_iqr"], sh["full"]["nsel_range"], sh["full"]["nsel_median"]
say(f"  源数据 stats_hardening.json：中位 {ns[2]}，IQR {ns[0]}，全距 {ns[1]}")
say(f"  稿中 v1.3 写的是：中位 11，IQR 8–14，全距 4–16  → **IQR 与全距均不符**")
say(f"  更正为：中位 11，IQR {ns[0][0]}–{ns[0][1]}，全距 {ns[1][0]}–{ns[1][1]}")
json.dump(dict(nsel_median=ns[2], nsel_iqr=ns[0], nsel_range=ns[1]),
          open(os.path.join(OUT, "nsel_v14.json"), "w"), indent=1)

open(os.path.join(OUT, "revise_stats_v14.log"), "w", encoding="utf-8").write("\n".join(log))
say("")
say("=" * 78)
say(f"完成。全部产出在 {OUT}")
say("=" * 78)
