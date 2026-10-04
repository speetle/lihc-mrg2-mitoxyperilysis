#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIHC 图件「遮挡」机械自检 —— figcheck_lihc.py 的补充，不是替代。

为什么必须新增（2026-10-04 先生指出 fig2C/3A/4A/4B/5C/6A 有文字遮挡）：
  原有 figcheck_lihc.py 只查三件事 ——
    ① 字号下限  ② 文字超出整幅画布  ③ **同一条轴同一侧**的刻度两两互压。
  它**从来不查**「注记压在数据上」「本面板标签伸进邻面板」「两个文字互相压」，
  所以六处遮挡一路全绿放行。

⚠️ 与生成器**同源**：障碍物几何、覆盖面积、落点判定全部 import 自
   make_figures_v2（经 fig_v2_panels 转出），不在此处重写一遍 ——
   否则护栏与生成器口径会各自漂移（全局规则 15）。

判据（全部机械，不靠肉眼）：
  D  文字 ↔ 数据：本面板的注记/刻度标签，不得与数据图元相交。
     矩形（柱/图像）算覆盖面积；点类（折线/散点）算实际落点。
  E  文字 ↔ 邻面板：任何文字的框不得与**同图另一面板**的 axes 矩形相交。
  F  面板矩形互不相交。
  G  图例 ↔ 数据。
  I  文字 ↔ 文字 / 图例：任意两个文字框不得互相压（含图例文字）。

用法：
    python figcheck_overlap.py            # 全部 6 图
    python figcheck_overlap.py 3          # 只查 Figure3
    python figcheck_overlap.py -v         # 打印每条命中的原始数据
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fig_v2_panels as F  # noqa: E402
from make_figures_v2 import (  # noqa: E402
    TEXT_DATA_TOL, LEGEND_DATA_TOL,
    data_obstacles, rect_cover, points_inside,
)

# 本脚本自己独立的 8 图（1–6）以外，图件函数在 fig_v2_panels
PAD = 1.0


def _bbox_overlap_frac(a, b):
    """相交面积占 a 面积的比例（a 是被保护的对象：文字/图例）。"""
    w = min(a.x1, b.x1) - max(a.x0, b.x0)
    h = min(a.y1, b.y1) - max(a.y0, b.y0)
    if w <= 0 or h <= 0:
        return 0.0
    return (w * h) / max(1e-9, a.width * a.height)


def text_items(ax, rend):
    """返回 [(kind, Text, bbox)]；kind ∈ {'anno','tick','axislabel','title'}。

    ⚠️ 必须跳过**不可见坐标轴**的刻度标签（2026-10-04 实测）：twinx 生成的
       ax2 自带一套与主轴位置相同的 x 刻度 Text；ax2.xaxis 被设为不可见，
       但那些 Text 的 `get_visible()` 仍为 True → 会被当成"两个文字 100% 互压"
       （Figure3 报了 4 条 0.0001/0.001/0.01/0.1 的假阳性）。
    """
    out = []
    for t in ax.texts:
        if t.get_text().strip() and t.get_visible():
            try:
                out.append(("anno", t, t.get_window_extent(rend)))
            except Exception:
                pass
    for axis, labels in ((ax.xaxis, ax.get_xticklabels()),
                         (ax.yaxis, ax.get_yticklabels())):
        if not axis.get_visible():
            continue
        for t in labels:
            if t.get_text().strip() and t.get_visible():
                try:
                    out.append(("tick", t, t.get_window_extent(rend)))
                except Exception:
                    pass
    for kind, t in (("axislabel", ax.xaxis.label), ("axislabel", ax.yaxis.label),
                    ("title", ax.title)):
        if t.get_text().strip() and t.get_visible():
            try:
                out.append((kind, t, t.get_window_extent(rend)))
            except Exception:
                pass
    return out


def panel_axes(fig):
    """只取带 gid=panel_* 的轴作为「面板」；inset / colorbar / twinx 不算。"""
    out = []
    for a in fig.axes:
        g = a.get_gid() or ""
        if g.startswith("panel_"):
            out.append((g.split("_", 1)[1], a))
    return out


def _gid(a):
    if a is None:
        return "fig"
    return a.get_gid() or "(无gid)"


def check(fig, name, verbose=False):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    if not hasattr(fig.canvas, "get_renderer"):
        FigureCanvasAgg(fig)
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()

    panels = panel_axes(fig)
    findings = {k: [] for k in "DEFGI"}

    obst_by_ax = {id(a): data_obstacles(a, rend) for _l, a in panels}

    # ---- F：面板矩形互不相交
    for i in range(len(panels)):
        for j in range(i + 1, len(panels)):
            l1, a1 = panels[i]
            l2, a2 = panels[j]
            f1 = a1.get_position()
            f2 = a2.get_position()
            w = min(f1.x1, f2.x1) - max(f1.x0, f2.x0)
            h = min(f1.y1, f2.y1) - max(f1.y0, f2.y0)
            if w > 1e-6 and h > 1e-6:
                findings["F"].append((l1, l2, w * h))

    # ---- 本图全部文字（含 twinx 轴、含 fig.texts）
    all_texts = []
    seen = set()
    for a in fig.axes:
        for k, t, bb in text_items(a, rend):
            # ⚠️ twinx 与主轴**共用同一个 xaxis 对象**，get_xticklabels() 返回同一批
            #    Text —— 不去重会把每条 x 刻度当成"两个文字 100% 互压"（实测假阳性）。
            if id(t) in seen:
                continue
            seen.add(id(t))
            all_texts.append((a, k, t, bb))
    for t in fig.texts:                      # add_atrisk / 轴外脚注
        if t.get_text().strip() and t.get_visible() and id(t) not in seen:
            seen.add(id(t))
            all_texts.append((None, "figtext", t, t.get_window_extent(rend)))

    # ---- D：文字 ↔ 同轴数据
    for a, kind, t, bb in all_texts:
        if a is None or id(a) not in obst_by_ax:
            continue
        rects, points = obst_by_ax[id(a)]
        frac = rect_cover(bb, rects)
        hist = points_inside(bb, points)
        if frac > TEXT_DATA_TOL or hist:
            findings["D"].append((_gid(a), kind, t.get_text(), frac, hist))

    # ---- E：文字 ↔ 邻面板 axes 矩形
    for a, kind, t, bb in all_texts:
        for ltr, pa in panels:
            if pa is a:
                continue
            # ⚠️ Axes 没有 get_bbox()（只有 Figure/Artist 有）；取窗口范围。
            frac = _bbox_overlap_frac(bb, pa.get_window_extent(rend))
            if frac > TEXT_DATA_TOL:
                findings["E"].append((_gid(a), kind, t.get_text(), ltr, frac))

    # ---- G：图例 ↔ 数据
    for ltr, a in panels:
        leg = a.get_legend()
        if leg is None:
            continue
        try:
            lbb = leg.get_window_extent(rend)
        except Exception:
            continue
        rects, points = obst_by_ax[id(a)]
        frac = rect_cover(lbb, rects)
        hist = points_inside(lbb, points)
        if frac > LEGEND_DATA_TOL or hist:
            findings["G"].append((ltr, frac, hist))

    # ---- I：文字 ↔ 文字 / 图例
    boxes = [(_gid(a), k, t.get_text(), bb) for (a, k, t, bb) in all_texts]
    for ltr, a in panels:
        leg = a.get_legend()
        if leg is not None:
            try:
                boxes.append((ltr, "legend", "legend@" + ltr,
                              leg.get_window_extent(rend)))
            except Exception:
                pass
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            g1, k1, t1, b1 = boxes[i]
            g2, k2, t2, b2 = boxes[j]
            if k1 == "tick" and k2 == "tick" and g1 == g2:
                continue          # 同轴同侧刻度互压已由 figcheck_lihc 判据 C 覆盖
            w = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
            hh = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
            if w <= 0 or hh <= 0:
                continue
            small = min(b1.width * b1.height, b2.width * b2.height)
            frac = (w * hh) / max(1e-9, small)
            if frac > TEXT_DATA_TOL:
                findings["I"].append((g1, k1, t1, g2, k2, t2, frac))

    n = sum(len(v) for v in findings.values())
    ok = n == 0
    print(f"{'✅' if ok else '❌'} Figure{name}: 面板 {len(panels)} | "
          f"D 压数据 {len(findings['D'])} | E 越界邻面板 {len(findings['E'])} | "
          f"F 面板互压 {len(findings['F'])} | G 图例压数据 {len(findings['G'])} | "
          f"I 文字互压 {len(findings['I'])}")

    def _show(rows, fmt):
        seenk = set()
        for r in rows:
            key = fmt(r)
            if key in seenk:
                continue
            seenk.add(key)
            print("      · " + key)
            if verbose:
                print("        raw:", r)

    _show(findings["D"], lambda r: f"[D] {r[0]} {r[1]} {r[2][:30]!r}："
                                   f"被矩形盖 {r[3]:.0%}，落点 {r[4] or '—'}")
    _show(findings["E"], lambda r: f"[E] {r[0]} {r[1]} {r[2][:28]!r} "
                                   f"越界进入面板 {r[3]} {r[4]:.0%}")
    _show(findings["F"], lambda r: f"[F] 面板 {r[0]} 与 {r[1]} 的 axes 矩形重叠")
    _show(findings["G"], lambda r: f"[G] 面板 {r[0]} 图例：被矩形盖 {r[1]:.0%}，"
                                   f"落点 {r[2] or '—'}")
    _show(findings["I"], lambda r: f"[I] {r[0]} {r[1]} {r[2][:24]!r} ↔ "
                                   f"{r[3]} {r[4]} {r[5][:24]!r} 互压 {r[6]:.0%}")
    return ok


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    verbose = "-v" in sys.argv
    want = set(args) if args else {"1", "2", "3", "4", "5", "6"}
    D = F.load()
    allok = True
    pairs = [("1", F.fig1), ("2", F.fig2), ("3", F.fig3),
             ("4", F.fig4), ("5", F.fig5), ("6", F.fig6)]
    for nm, fn in pairs:
        if nm not in want:
            continue
        _r, axmap = fn(D)
        fig = next(iter(axmap.values())).figure
        allok &= check(fig, nm, verbose)
        plt.close("all")
    print("\n" + ("✅ 无遮挡" if allok else "❌ 存在遮挡，需修"))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
