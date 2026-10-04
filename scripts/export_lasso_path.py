#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出 LASSO-Cox 的完整 α 路径与 10 折 CV 曲线（供 Figure 3A 使用）。

背景：v1 的 Figure 3A 只画了两条竖线与两个点，**从未画出 CV 曲线本身**，
      而正文 §3.3 声称"The 10-fold cross-validation curve was flat"——
      图与文不符。本脚本重算并沉积曲线，使该面板内容真实可复算。

设置与 lihc_pipeline.py / stats_hardening.py 完全一致：
  alpha = logspace(-1.2, -3.0, 60)、l1_ratio=1.0、10 折、seed=42。
产出：数据/lasso_cv_path.json
"""
import os, sys, json, math, importlib.util
import numpy as np
from sksurv.util import Surv

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main():
    sh = load_module(os.path.join(HERE, "stats_hardening.py"), "shmod2")
    df, genes, pg = sh.load()
    T = df["T"].values.astype(float); E = df["E"].values.astype(int)
    X = df[genes]; Xz = (X - X.mean()) / X.std()
    sh._Tf, sh._Ef = T, E                      # lasso_path_cv 内部算 C-index 要用
    y = Surv.from_arrays(E.astype(bool), T.astype(float))

    est, cv, i_min, i_1se, a1se, amin = sh.lasso_path_cv(Xz.values, y, n_folds=10, seed=sh.SEED)
    al = np.asarray(est.alphas_, float)
    cv = np.asarray(cv, float)
    ng = np.array([int(np.sum(np.abs(est.coef_[:, i]) > 1e-8)) for i in range(len(al))])
    se = float(np.nanstd(cv) / math.sqrt(10))

    out = {"alphas": al.tolist(), "cv": np.nan_to_num(cv, nan=0.5).tolist(),
           "n_genes": ng.tolist(),
           "alpha_1se": float(a1se), "n_at_1se": int(ng[i_1se]), "cv_1se": float(cv[i_1se]),
           "alpha_min": float(amin), "n_at_min": int(ng[i_min]), "cv_min": float(cv[i_min]),
           "se_cv": se, "n_folds": 10}
    json.dump(out, open(os.path.join(DATA, "lasso_cv_path.json"), "w"), indent=2)

    dep = json.load(open(os.path.join(DATA, "results.json")))["lasso"]
    print(f"重算  1SE: α={a1se:.5f} ({ng[i_1se]} genes, CV={cv[i_1se]:.4f})")
    print(f"沉积  1SE: α={dep['alpha_1se']:.5f} ({dep['n_at_1se']} genes, CV={dep['cv_at_1se']:.4f})")
    print(f"重算  min: α={amin:.5f} ({ng[i_min]} genes, CV={cv[i_min]:.4f})")
    print(f"沉积  min: α={dep['alpha_min']:.5f} ({dep['n_at_min']} genes, CV={dep['cv_at_min']:.4f})")
    print(f"CV 曲线范围 {np.nanmin(cv):.4f} – {np.nanmax(cv):.4f}（极差 {np.nanmax(cv)-np.nanmin(cv):.4f}，"
          f"SE={se:.4f}）→ 曲线{'平坦' if (np.nanmax(cv)-np.nanmin(cv))<3*se else '不平坦'}")
    ok = (abs(a1se - dep["alpha_1se"]) < 1e-12 and ng[i_1se] == dep["n_at_1se"]
          and abs(amin - dep["alpha_min"]) < 1e-12 and ng[i_min] == dep["n_at_min"])
    print("一致性:", "✅ 与沉积结果一致" if ok else "❌ 不一致")
    print("-> 数据/lasso_cv_path.json")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
