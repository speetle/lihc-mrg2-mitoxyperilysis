#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生3 LIHC —— 图件 v2（期刊规格重绘）
=====================================
相对 v1 的修复：
  1. 版面尺寸改为期刊真实规格（双栏 183 mm / 7.2 in；单栏 89 mm / 3.5 in），
     字号按最终印刷尺寸设定（正文 7 pt / 刻度 6.5 pt / panel 字母 9 pt），
     解决"缩到双栏宽后字号仅约 4.8 pt"导致的看不清。
  2. 修复 Figure 3 被 bbox_inches="tight" 撑成 3760x87642 px 条带的缺陷
     ——全部注记改用 transform=ax.transAxes，杜绝数据坐标越界。
  3. 修复 Figure 3A：原脚本只画了两条竖线与两个点，从未画出 CV 曲线，
     而正文声称"CV 曲线平坦"。本脚本重算完整 alpha 路径 + 10 折 CV 曲线。
  4. 修复 Figure 6：原脚本 91 个基因标签字号仅 5 pt。改为双面板横向条形，
     标签 6 pt，可读。
  5. Figure 5C：原图无空分布原始数组。本脚本重算两个队列各 3000 个随机
     2 基因面板的 C-index 分布，并与已沉积的 mean/sd 做一致性断言。
  6. 输出：600 dpi PNG + 矢量 PDF + 分层矢量 SVG（文字保留为 <text>，
     每个 panel 带 <g id="panel_X">，可在 Adobe Illustrator 中按面板拖动
     并另存为 .ai 源文件）。同时导出每个 panel 的单体 SVG/PDF 便于自由组图。
"""
import os, json, math, itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch

# ---------------- 字体与全局样式（期刊规格）----------------
for fam in ["Arial", "Helvetica", "Arial Unicode MS", "DejaVu Sans"]:
    if any(f.name == fam for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = fam
        FONT = fam
        break
plt.rcParams.update({
    "font.size": 7,
    "axes.labelsize": 7,
    "axes.titlesize": 7.5,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.2,
    "ytick.major.size": 2.2,
    "lines.linewidth": 1.0,
    "axes.unicode_minus": False,
    "pdf.fonttype": 42,      # PDF 内嵌 TrueType，AI 可编辑
    "svg.fonttype": "none",  # SVG 保留 <text>，AI 可编辑文字
    "figure.dpi": 150,
    "savefig.dpi": 600,
    # ⚠️ mathtext 必须显式指向同一字体（2026-10-05）。默认 fontset="dejavusans"，
    #    只要有一处 $...$ 就会把 DejaVu Sans 混进图里 —— 与全图 Arial 不一致，
    #    而且 PyMuPDF 查字体时一眼就能看到第二种字形（内存规则：mathtext.fontset
    #    必须设 custom）。设成 custom + 同名 Arial 后，$P$（斜体）与
    #    $1.9 \times 10^{-6}$（正体）都用 Arial 出。
    "mathtext.fontset": "custom",
    "mathtext.rm": FONT,
    "mathtext.it": FONT + ":italic",
    "mathtext.bf": FONT + ":bold",
})

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "数据")
FIG = os.path.join(BASE, "图件_v2")
SUP = os.path.join(BASE, "补充材料")
os.makedirs(FIG, exist_ok=True)

RED, BLUE, GREY, ORANGE, GREEN = "#C0392B", "#2C6FBB", "#7F8C8D", "#E08214", "#1A7A4C"
DC = 7.2      # double column, inches (183 mm)
SC = 3.5      # single column, inches (89 mm)


def p_fmt(p):
    """把 P 值排成**出版体例**，而不是程序员记法。

    ⚠️ 2026-10-05：原写法 `f"{p:.1e}"` 让图题印出 `log-rank P = 1.9e-06` ——
       `1.9e-06` 是 C/Python 的科学计数法，期刊图题一律写 `1.9 × 10⁻⁶`。
       这里改成 mathtext（字体已由 rcParams 的 mathtext.fontset="custom" 锁到
       Arial），并把 P 排成斜体——期刊对统计量一律斜体。
    """
    if p >= 0.001:
        return f"{p:.3f}"
    a, b = f"{p:.1e}".split("e")
    return r"$%s \times 10^{%d}$" % (a, int(b))


def _redo_registry(fig):
    """登记"依赖几何位置"的自愈放置，落盘前统一重放。

    ⚠️ 顺序陷阱（2026-10-04 实测）：任何一处 placement 都是在"当时的" axes 几何
       下测出的合规位置。之后只要有人改了 subplots_adjust / xlim / ylim，
       之前算好的合规性就可能失效 —— Figure2B 的 panel 字母就是这样在
       ensure_no_crossbleed 之后又被顶到刻度数字上（剩 4% 互压）。
       所以不靠调用顺序，靠**落盘前重放**。
    """
    reg = getattr(fig, "_lihc_redo", None)
    if reg is None:
        reg = []
        setattr(fig, "_lihc_redo", reg)
    return reg


def refresh_placements(fig):
    """按登记顺序重放所有自愈放置（panel 字母 / 注记 / 图例）。"""
    for fn in _redo_registry(fig):
        fn()


def _place_panel_letter(ax, letter, dx, dy, xmin, gap):
    """落位一次：从 (dx, dy) 起左移/上移，直到不与本轴任一刻度标签相交。"""
    fig = ax.figure
    rend = _rend(fig)
    ticks = []
    for tl in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        if not tl.get_text().strip() or not tl.get_visible():
            continue
        try:
            ticks.append(tl.get_window_extent(rend))
        except Exception:
            pass

    for cy in (dy, dy + 0.045, dy + 0.090, dy + 0.135):
        cx = dx
        while cx >= xmin - 1e-9:
            t = ax.text(cx, cy, letter, transform=ax.transAxes, fontsize=9,
                        fontweight="bold", va="bottom", ha="left")
            # ⚠️ 不必重绘整图：Text 的窗口范围只需渲染器与变换即可算，
            #    而变换（transAxes）由已固定的 axes 位置决定。
            try:
                bb = t.get_window_extent(rend)
            except Exception:
                t.remove(); cx -= gap; continue
            hit = False
            for tb in ticks:
                w = min(bb.x1, tb.x1) - max(bb.x0, tb.x0)
                h = min(bb.y1, tb.y1) - max(bb.y0, tb.y0)
                if w > 0 and h > 0 and (w * h) / max(1e-9, bb.width * bb.height) > TEXT_DATA_TOL:
                    hit = True
                    break
            if not hit:
                return t
            t.remove()
            cx -= gap
    raise RuntimeError("panel_letter：%r 找不到不压刻度的位置" % letter)


def panel_letter(ax, letter, dx=-0.14, dy=1.04, xmin=-0.45, gap=0.02):
    """panel 字母 —— **自动避开同轴刻度标签**，并在落盘前重放。

    ⚠️ 2026-10-04 先生指出 Figure1B/2B/3A/4A 的粗体字母压在刻度数字上：
       原实现把字母固定放在 (dx=-0.14, dy=1.04)，即"轴的左上角外侧"，
       而纵向刻度标签恰好占住轴左外侧约 0.10–0.16 个轴宽 ——
       顶端那个刻度数字与字母几乎完全重合（Figure4A 实测 87%）。
    坐标仍是 axes 分数，字母永远不进入数据区（Figure 3 缺陷根因）。
    """
    holder = [_place_panel_letter(ax, letter, dx, dy, xmin, gap)]

    def _redo():
        try:
            holder[0].remove()
        except Exception:
            pass
        holder[0] = _place_panel_letter(ax, letter, dx, dy, xmin, gap)

    _redo_registry(ax.figure).append(_redo)
    return holder[0]


# ============================================================
# 遮挡自愈工具 —— 生成器与检查器（figcheck_overlap.py）**共用这一套定义**
# ============================================================
# ⚠️ 为什么必须做成"自愈"而不是"调参数"（2026-10-04 先生指出六处遮挡）：
#    原脚本靠手写 wspace / 手挑注记坐标，改一次数据就要重新肉眼校一遍。
#    这里改成：把"文字不得压数据、不得越界到邻面板"变成**可测量的约束**，
#    由代码在保存前自动寻找合规位置；找不到就报错，绝不静默交付。
#    检查器 import 同一批函数，因此护栏与生成器口径**不可能漂移**。
TEXT_DATA_TOL = 0.02      # 文字框被矩形数据覆盖的面积占比上限
LEGEND_DATA_TOL = 0.005   # 图例框被矩形数据覆盖的面积占比上限
_PAD = 1.0                # bbox 收缩像素，避免"恰好贴边"的假阳性


def _rend(fig):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    if not hasattr(fig.canvas, "get_renderer"):
        FigureCanvasAgg(fig)
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def data_obstacles(ax, rend):
    """面板内的数据障碍物 -> (rects, points)。

    rects  = [(name, Bbox)]             柱、图像：真实矩形框，可算覆盖面积
    points = [(name, Nx2 显示坐标, 半径)] 折线、散点：逐顶点判

    ⚠️ 折线/散点必须逐顶点（2026-10-04 实测）：一条 KM 阶梯曲线或 CV 路径的
       **外包框**几乎等于整个面板，拿它求面积交会让任何注记都判成
       "100% 被压住"——Figure1D/3A/5A 的 100%/95% 全是这种假阳性。
       正解是取顶点实际落点，再看有没有点落进文字框。
    """
    rects, points = [], []
    leg_items = set()
    leg = ax.get_legend()
    if leg is not None:
        for h in (getattr(leg, "legend_handles", None)
                  or getattr(leg, "legendHandles", None) or []):
            leg_items.add(id(h))

    for p in ax.patches:
        if id(p) in leg_items:
            continue
        try:
            bb = p.get_window_extent(rend)
            if bb.width > 0 and bb.height > 0:
                rects.append(("patch", bb))
        except Exception:
            pass
    for im in ax.images:
        try:
            bb = im.get_window_extent(rend)
            if bb.width > 0 and bb.height > 0:
                rects.append(("image", bb))
        except Exception:
            pass
    for ln in ax.lines:
        if id(ln) in leg_items:
            continue
        try:
            xy = ln.get_xydata()
            if xy is None or len(xy) == 0:
                continue
            xy = np.asarray(xy, float)
            # ⚠️ 必须**加密采样**（2026-10-04 实测）：axvline/axhline 只有两个
            #    端点顶点，若只判端点，一条贯穿全高的竖线只在顶端和底端各留一点，
            #    中段完全检测不到 —— Figure5C 的蓝色参照线正是这样从注记文字中
            #    穿过去而判据报"无遮挡"。相邻顶点之间线性插值 60 份即可覆盖。
            if len(xy) >= 2:
                segs = []
                for i in range(len(xy) - 1):
                    t = np.linspace(0.0, 1.0, 60, endpoint=False)[:, None]
                    segs.append(xy[i] + t * (xy[i + 1] - xy[i]))
                segs.append(xy[-1:])
                xy = np.vstack(segs)
            pts = np.asarray(ln.get_transform().transform(xy), float)
            if np.isfinite(pts).all():
                points.append(("line", pts, 1.5))
        except Exception:
            pass
    for c in ax.collections:
        if id(c) in leg_items:
            continue
        try:
            off = c.get_offsets()
            if off is None or len(off) == 0:
                continue
            pts = np.asarray(c.get_offset_transform().transform(
                np.asarray(off, float)), float)
            if not np.isfinite(pts).all():
                continue
            try:
                sz = float(np.max(c.get_sizes())) if len(c.get_sizes()) else 4.0
            except Exception:
                sz = 4.0
            points.append(("coll", pts, max(1.5, math.sqrt(sz) / 2.0)))
        except Exception:
            pass
    return rects, points


def rect_cover(bb, rects, pad=_PAD):
    """框被矩形障碍物覆盖的面积占比（同一像素只计一次，避免多柱重复计）。"""
    if not rects:
        return 0.0
    x0, y0, x1, y1 = bb.x0 + pad, bb.y0 + pad, bb.x1 - pad, bb.y1 - pad
    if x1 <= x0 or y1 <= y0:
        return 0.0
    w = int(math.ceil(x1 - x0)); h = int(math.ceil(y1 - y0))
    if w <= 0 or h <= 0 or w * h > 4_000_000:
        return 0.0
    mask = np.zeros((h, w), bool)
    xs = np.linspace(x0, x1, w, endpoint=False)
    ys = np.linspace(y0, y1, h, endpoint=False)
    for _n, rb in rects:
        rx0, rx1 = max(rb.x0, x0), min(rb.x1, x1)
        ry0, ry1 = max(rb.y0, y0), min(rb.y1, y1)
        if rx1 <= rx0 or ry1 <= ry0:
            continue
        ci0 = int(np.searchsorted(xs, rx0, "left"))
        ci1 = int(np.searchsorted(xs, rx1, "left"))
        ri0 = int(np.searchsorted(ys, ry0, "left"))
        ri1 = int(np.searchsorted(ys, ry1, "left"))
        if ci1 > ci0 and ri1 > ri0:
            mask[ri0:ri1, ci0:ci1] = True
    return float(mask.mean())


def points_inside(bb, points, pad=_PAD):
    """落在框内的顶点/散点数，按来源分类。"""
    x0, y0, x1, y1 = bb.x0 + pad, bb.y0 + pad, bb.x1 - pad, bb.y1 - pad
    if x1 <= x0 or y1 <= y0:
        return {}
    hist = {}
    for nm, pts, r in points:
        if len(pts) == 0:
            continue
        ins = ((pts[:, 0] >= x0 + r) & (pts[:, 0] <= x1 - r) &
               (pts[:, 1] >= y0 + r) & (pts[:, 1] <= y1 - r))
        c = int(ins.sum())
        if c:
            hist[nm] = hist.get(nm, 0) + c
    return hist


def _box_is_clear(fig, ax, bb, axbb, rects, points, avoid=()):
    """文字/图例框是否合规：不压数据、不压已有图例、不越界到邻面板、不出图。"""
    if axbb is not None and (bb.x0 < axbb.x0 - 1 or bb.x1 > axbb.x1 + 1
                             or bb.y0 < axbb.y0 - 1 or bb.y1 > axbb.y1 + 1):
        return False
    if rect_cover(bb, rects) > TEXT_DATA_TOL:
        return False
    if points_inside(bb, points):
        return False
    for ab in avoid:                     # 已有图例：注记不得压上去
        w = min(bb.x1, ab.x1) - max(bb.x0, ab.x0)
        h = min(bb.y1, ab.y1) - max(bb.y0, ab.y0)
        if w > 0 and h > 0 and (w * h) / max(1e-9, bb.width * bb.height) > TEXT_DATA_TOL:
            return False
    fbb = fig.bbox
    return not (bb.x0 < fbb.x0 - 1 or bb.x1 > fbb.x1 + 1
                or bb.y0 < fbb.y0 - 1 or bb.y1 > fbb.y1 + 1)


def _legend_bbox(ax, rend):
    leg = ax.get_legend()
    if leg is None:
        return None
    try:
        return leg.get_window_extent(rend)
    except Exception:
        return None


def _other_text_bboxes(ax, rend, exclude):
    """同面板内其它文字的框（供注记避让，避免出现 Figure2A 那种注记压图例文字）。"""
    out = []
    for t in ax.texts:
        if t is exclude or not t.get_text().strip() or not t.get_visible():
            continue
        if t.get_transform() is not ax.transAxes and \
           not getattr(t, "get_transform", None):
            continue
        try:
            out.append((t.get_text(), t.get_window_extent(rend)))
        except Exception:
            pass
    return out


def _try_place_text(ax, s, candidates, fig, must_fit_axes, kw):
    fig = fig or ax.figure
    _rend(fig)
    h = "candidates:\n" + "\n".join("  %r" % (c,) for c in candidates)
    for x, y, ha, va in candidates:
        t = ax.text(x, y, s, transform=ax.transAxes, ha=ha, va=va, **kw)
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
        bb = t.get_window_extent(rend)
        rects, points = data_obstacles(ax, rend)
        axbb = ax.get_window_extent(rend) if must_fit_axes else None
        avoid = []
        lb = _legend_bbox(ax, rend)
        if lb is not None:
            avoid.append(lb)
        avoid += [b for _txt, b in _other_text_bboxes(ax, rend, exclude=t)]
        if _box_is_clear(fig, ax, bb, axbb, rects, points, avoid=avoid):
            return t
        t.remove()
    raise RuntimeError("place_text_clear：无合规位置可放 %r\n%s" % (s[:50], h))


def place_text_clear(ax, s, candidates, fig=None, must_fit_axes=True, **kw):
    """在候选位置中挑一个**不压数据、不压图例、不压其它文字、不出界**的位置放注记。

    candidates: [(x, y, ha, va)]，坐标是 axes 分数。
    找不到合规位置即抛错 —— 宁可报错，也不交付遮挡图。
    位置会被登记，在 savefig 前随几何变化自动重放（见 _redo_registry）。
    """
    holder = [_try_place_text(ax, s, candidates, fig, must_fit_axes, kw)]

    def _redo():
        try:
            holder[0].remove()
        except Exception:
            pass
        holder[0] = _try_place_text(ax, s, candidates, fig, must_fit_axes, kw)

    _redo_registry(ax.figure).append(_redo)
    return holder[0]


def _try_place_legend(ax, candidates, fig, must_fit_axes, handles, labels, kw):
    fig = fig or ax.figure
    old = ax.get_legend()
    if old is not None:
        old.remove()
    h = "candidates:\n" + "\n".join("  %r" % (c,) for c in candidates)
    for loc, anchor in candidates:
        leg = ax.legend(handles=handles, labels=labels, loc=loc,
                        bbox_to_anchor=anchor, **kw)
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
        try:
            lb = leg.get_window_extent(rend)
        except Exception:
            leg.remove(); continue
        rects, points = data_obstacles(ax, rend)
        axbb = ax.get_window_extent(rend) if must_fit_axes else None
        if (rect_cover(lb, rects) <= LEGEND_DATA_TOL and not points_inside(lb, points)
                and (axbb is None or (lb.x0 >= axbb.x0 - 1 and lb.x1 <= axbb.x1 + 1
                                      and lb.y0 >= axbb.y0 - 1 and lb.y1 <= axbb.y1 + 1))):
            return leg
        leg.remove()
    raise RuntimeError("place_legend_clear：无合规位置\n%s" % h)


def place_legend_clear(ax, candidates, fig=None, must_fit_axes=True, **kw):
    """在候选位置中挑一个不压数据的图例位置。candidates: [(loc, bbox_anchor|None)]。

    位置会被登记，在 savefig 前随几何变化自动重放（见 _redo_registry）。
    """
    handles = kw.pop("handles", None)
    labels = kw.pop("labels", None)
    holder = [_try_place_legend(ax, candidates, fig, must_fit_axes, handles, labels, kw)]

    def _redo():
        holder[0] = _try_place_legend(ax, candidates, fig, must_fit_axes,
                                      handles, labels, kw)

    _redo_registry(ax.figure).append(_redo)
    return holder[0]


def legend_clear_with_xheadroom(ax, handles, locs, grow=None, iters=16, **kw):
    """把图例放进空白区；放不下就**逐步向右扩 xlim**，直到图表之间让出位置。

    2026-10-04 实测：Figure6A 的 91 基因横向条形里，下半部各行的 Z 全为负，
    右半区本应天然为空；但三个图例标签（'Z > 1 (n = 22)' 等）宽约 0.30 个轴宽，
    右下角的左边缘仍压到最底行 FERMT2 的负向长条（-3.4）上。
    固定猜一个 xlim 又要反复试错，故这里把 xlim 也当**数值解**：
    每轮向右加宽一档，重测图例框与数据的相交面积，直到为零。
    """
    x0, x1 = ax.get_xlim()
    if grow is None:
        grow = 0.06 * (x1 - x0)
    for _i in range(iters + 1):
        try:
            return place_legend_clear(ax, [(l, None) for l in locs],
                                      handles=handles, **kw)
        except RuntimeError:
            pass
        x1 += grow
        ax.set_xlim(x0, x1)
    raise RuntimeError("legend_clear_with_xheadroom：向右扩宽 %d 档仍放不下" % iters)


def _texts_of(ax):
    out = [t for t in ax.texts if t.get_text().strip() and t.get_visible()]
    for t in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        if t.get_text().strip() and t.get_visible():
            out.append(t)
    return out


def crossbleed_count(fig, axes, rend):
    """统计"某面板的文字伸进另一面板 axes 矩形"的条数。"""
    boxes = {id(a): a.get_window_extent(rend) for a in axes}
    n = 0
    for a in axes:
        own = boxes[id(a)]
        for t in _texts_of(a):
            try:
                bb = t.get_window_extent(rend)
            except Exception:
                continue
            for b in axes:
                if b is a:
                    continue
                ob = boxes[id(b)]
                w = min(bb.x1, ob.x1) - max(bb.x0, ob.x0)
                hh = min(bb.y1, ob.y1) - max(bb.y0, ob.y0)
                if w > 1 and hh > 1 and (w * hh) / max(1e-9, bb.width * bb.height) > TEXT_DATA_TOL:
                    n += 1
                    break
    return n


def ensure_no_crossbleed(fig, axes, w0=0.42, step=0.05, wmax=1.60, verbose=True):
    """自动加大子图横向间距，直到**没有任何文字的框伸进邻面板的 axes 矩形**。

    2026-10-04 实测：Figure2C 的 'MRG-2 (per SD)'、Figure4B 的 'M1 macrophage'
    这类长刻度标签会横向伸进左邻面板（2C 达 23%、4B 达 11%），
    而原检查器只查同轴同侧的刻度互压，完全看不见。
    这里把 wspace 当**数值解**而不是手调参数。
    """
    w = w0
    rend = _rend(fig)
    best = None
    while w <= wmax + 1e-9:
        fig.subplots_adjust(wspace=w)
        rend = _rend(fig)
        n = crossbleed_count(fig, axes, rend)
        if n == 0:
            best = w
            break
        w += step
    if best is None:
        raise RuntimeError("ensure_no_crossbleed：wspace 加到 %.2f 仍有标签越界" % wmax)
    fig.subplots_adjust(wspace=best)
    if verbose:
        print(f"    · 面板间距自适应 wspace {w0:.2f} -> {best:.2f}（消除刻度标签越界）")
    return best


def check_panels_nonempty(fig, name):
    """拦截"坐标轴照画、面板里一条数据都没有"的静默缺陷。

    2026-10-04 实测踩坑：Figure 2C 的筛选条件写成 `mv["model"] == "adjusted_ModelB"`
    （实际取值是 "Model A"/"Model B"），命中 0 行 —— 森林图整个空白，
    但坐标轴、刻度、标题一应俱全，肉眼扫一眼完全看不出，差点就这么交付了。
    """
    bad = []
    for a in fig.axes:
        g = a.get_gid() or ""
        if not g.startswith("panel_"):
            continue
        has = bool(a.lines or a.collections or a.patches or a.containers or a.images)
        if not has:
            bad.append(g.split("_", 1)[1])
    if bad:
        raise RuntimeError(f"Figure{name} 的面板 {bad} 没有任何数据图元 —— 请检查筛选/字段口径")


def plain_ticks(fig):
    """把所有轴的刻度标签改为**纯小数**，禁用 mathtext 指数记法。

    ⚠️ 为什么必须做（2026-10-04 实测踩坑）：
    matplotlib 在窄区间线性轴或对数轴上会改用 mathtext，把刻度写成
    `6×10⁻¹` 形态；其中**指数部分按 0.7 缩放渲染**——6.5 pt 的刻度缩成
    **4.55 pt**，缩到 183 mm 双栏后仅 4.8–5.4 pt，是本稿"图看不清"的
    真正来源（不是坐标轴标签、不是 panel 字母，是**指数标**）。
    取消指数记法后，最小的刻度文字回到 6.5 pt（终稿 ≥6.9 pt）。
    """
    from matplotlib.ticker import FuncFormatter, ScalarFormatter
    fmt = FuncFormatter(lambda v, _p: f"{v:g}")
    for a in fig.axes:
        for axis in (a.xaxis, a.yaxis):
            cur = axis.get_major_formatter()
            # ⚠️ 只对**数值型**坐标轴生效。分类轴（基因名/免疫特征名）用的是
            #    FixedFormatter，若一并覆盖，刻度会被替换成序号（实测踩坑：
            #    Figure 3B 的基因名一度变成 14,13,…,1）。
            if not isinstance(cur, ScalarFormatter) and "Log" not in type(cur).__name__:
                continue
            axis.set_major_formatter(fmt)
            # 对数轴的 minor 刻度默认也带指数，一并静音
            if hasattr(axis, "set_minor_formatter"):
                axis.set_minor_formatter(FuncFormatter(lambda v, _p: ""))
    return fig


def savefig(fig, name, panels=None):
    """存 PNG(600dpi) + PDF(矢量) + SVG(分层矢量)，并自动导出单体 panel。"""
    check_panels_nonempty(fig, name)
    plain_ticks(fig)
    # ⚠️ 落盘前无条件重放所有自愈放置：plain_ticks 会改刻度文字、ensure_no_crossbleed
    #    会改 axes 几何，两者都会让"此前算好的合规位置"失效（顺序陷阱，详见
    #    _redo_registry 注释）。顺序必须是 plain_ticks -> refresh_placements -> save。
    refresh_placements(fig)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(os.path.join(FIG, f"Figure{name}.{ext}"), bbox_inches="tight",
                    pad_inches=0.02, facecolor="white")
    # 尺寸自检：防止再出现条带式缺陷
    from PIL import Image
    with Image.open(os.path.join(FIG, f"Figure{name}.png")) as im:
        w, h = im.size
    ratio = w / h
    flag = "  ⚠ 纵横比异常！" if (ratio > 8 or ratio < 0.125) else ""
    print(f"  Figure{name}: {w}x{h}px  比例 {ratio:.2f}{flag}")
    # 自动收集带 gid 的 panel 轴（inset / colorbar / twinx 无 gid，自动排除）
    if panels is None:
        panels = {}
        for a in fig.axes:
            g = a.get_gid() or ""
            if g.startswith("panel_"):
                panels[g.split("_", 1)[1]] = a
    if panels:
        save_panels(fig, name, panels)
    plt.close(fig)
    return (w, h, ratio)


def save_panels(fig, name, axmap):
    """把每个 panel 单独导出（SVG+PDF+PNG），便于在 Illustrator 里自由组图。

    ⚠️ 单位陷阱（2026-10-04 实测踩坑）：Axes.get_tightbbox() 返回的是
    **显示坐标（像素，按 fig.dpi 计）**，而 savefig 的 bbox_inches 要求**英寸**。
    直接把像素当英寸传入，会把 panel 放大 fig.dpi（=150）倍：
    Figure2 的 A 面板 PNG 因此高达 170 MB / 十余万像素宽，SVG 的 viewBox 同样被撑爆，
    在 Illustrator 里打开会缩成一个点 —— 必须除以 fig.dpi 换成英寸。
    """
    d = os.path.join(FIG, f"Figure{name}_panels")
    os.makedirs(d, exist_ok=True)
    fig.canvas.draw()                      # 必须先绘制，否则 tightbbox 无 renderer
    rend = fig.canvas.get_renderer()
    inv = fig.dpi_scale_trans.inverted()   # 像素 -> 英寸
    info = []
    for letter, ax in axmap.items():
        bb = ax.get_tightbbox(rend).transformed(inv)
        if not (0.2 < bb.width < 20 and 0.2 < bb.height < 20):
            print(f"    ⚠ panel {letter} 尺寸异常 {bb.width:.2f}x{bb.height:.2f} in，跳过单体导出")
            continue
        for ext in ("svg", "pdf", "png"):
            fig.savefig(os.path.join(d, f"{letter}.{ext}"), bbox_inches=bb,
                        pad_inches=0.03, facecolor="white",
                        dpi=600 if ext == "png" else None)
        info.append(f"{letter} {bb.width:.2f}x{bb.height:.2f}in")
    print(f"    └ 单体 panel 已导出 -> Figure{name}_panels/"
          f"（{', '.join(sorted(axmap))}；共 {len(info)*3} 个文件）")
    for s in info:
        print(f"        · {s}")


# ============================================================
def load():
    res = json.load(open(os.path.join(DATA, "results.json")))
    uni = pd.read_csv(os.path.join(DATA, "univariate_cox.csv"))
    coefA = pd.read_csv(os.path.join(DATA, "modelA_coef.csv"))
    stab = pd.read_csv(os.path.join(DATA, "modelB_stability.csv"))
    rs = pd.read_csv(os.path.join(DATA, "risk_scores.csv"), index_col=0)
    mv = pd.read_csv(os.path.join(DATA, "multivariable.csv"))
    imm = pd.read_csv(os.path.join(DATA, "immune_infiltration.csv"))
    mut = pd.read_csv(os.path.join(DATA, "mutations.csv"))
    expr = pd.read_csv(os.path.join(DATA, "lihc_expr_z.csv"), index_col=0)
    label = np.load(os.path.join(DATA, "kmeans_labels.npy"))
    pcs = np.load(os.path.join(DATA, "pcs.npy"))
    tvn = pd.read_csv(os.path.join(DATA, "tumor_vs_normal.csv"), index_col=0)
    hard = json.load(open(os.path.join(DATA, "stats_hardening.json")))
    ext = json.load(open(os.path.join(DATA, "external_GSE14520_summary.json")))
    ex14 = pd.read_csv(os.path.join(DATA, "external_GSE14520.csv"), index_col=0)
    panel = [l.strip().upper() for l in open(os.path.join(HERE, "mrg_panel.txt")) if l.strip()]
    return dict(res=res, uni=uni, coefA=coefA, stab=stab, rs=rs, mv=mv, imm=imm,
                mut=mut, expr=expr, label=label, pcs=pcs, tvn=tvn, hard=hard,
                ext=ext, ex14=ex14, panel=panel)


def km_curve(T, E):
    """单个风险组的 Kaplan–Meier 阶梯曲线，返回 (t, S)。"""
    t = np.asarray(T, float); e = np.asarray(E)
    order = np.argsort(t, kind="mergesort")
    t = t[order]; e = e[order]
    s = 1.0
    ts = [0.0]; ss = [1.0]
    at_risk = len(t)
    for i, ti in enumerate(t):
        if e[i] == 1 and at_risk > 0:
            s *= (1.0 - 1.0 / at_risk)
            ts.append(ti); ss.append(s)
        at_risk -= 1
    return np.array(ts), np.array(ss)


def at_risk_table(T, E, groups, times):
    rows = []
    for g in groups:
        m = np.asarray(groups) == g
        t = np.asarray(T)[m]
        rows.append([int((t >= tt).sum()) for tt in times])
    return rows


def add_atrisk(fig, ax, T, E, groups, names, times, fs=6.5):
    """在 KM 图正下方写 numbers-at-risk 表（**逐格排版**，不用等宽字体凑对齐）。

    ⚠️ 排版陷阱一（2026-10-04 实测踩坑）：旧写法用 ax.text(-0.5, -0.085, ...)
      以 axes 分数定位，横向溢出半个轴宽、纵向压在 xlabel 上 —— 在 2×2 拼版里
      直接盖住左邻面板（Figure1 的 at-risk 数字压在 heat map 上）。
      改为：① 位置由 xlabel 的实际渲染位置推导（fig.canvas.draw 后取 window_extent）；
            ② 全部锚定在面板左边缘 x0，只向下延伸，绝不向左溢出；
            ③ 行距按英寸换算，与实际字号绑定。

    ⚠️ 排版陷阱二（2026-10-05 实测）：上一条修完后，表体是用
      `family="monospace"` + `f"{v:>5d}"` 靠**空格垫位**排的。后果是：整张图的
      其它文字是 Arial（Helvetica 系无衬线），只有这张 at-risk 表是 DejaVu Sans
      Mono —— PDF 里实测出现 `DejaVuSansMono` 字体条目（Figure1/3/5 各 3 处），
      同一图内混用两种字形，缩放打印时一眼可见。而且等宽字比 Arial 宽 20% 以上，
      白白多占横向空间。
      改为**实测列宽 + 逐格 right 对齐**：用渲染器量出每个单元格的实际宽度，
      算列宽 → 逐格 fig.text，字体继承 rcParams（Arial），不再出现任何字体回退。
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    lab_fig = ax.xaxis.label.get_window_extent(rend).transformed(
        fig.transFigure.inverted())
    dy = (fs * 1.55 / 72.0) / fig.get_figheight()
    x0 = ax.get_position().x0
    w_ax = ax.get_position().width
    rows = at_risk_table(T, E, groups, times)

    head = ["At risk"] + [f"{t:d}" for t in times]
    body = [[nm] + [f"{v:d}" for v in row] for nm, row in zip(names, rows)]

    def tw(s):
        """一个字符串在最终图里的宽度（单位：figure 分数）。"""
        t = fig.text(0, 0, s, fontsize=fs)
        w = t.get_window_extent(rend).width / fig.bbox.width
        t.remove()
        return w

    ncol = len(times) + 1
    cw = [max([tw(head[0])] + [tw(b[0]) for b in body])]
    for k in range(len(times)):
        cw.append(max([tw(head[k + 1])] + [tw(b[k + 1]) for b in body]))
    pad = max(tw("  "), 0.004)
    total = sum(cw) + pad * (ncol - 1)
    if total > w_ax:                       # 收紧留白；仍放不下就压到单空格宽
        pad = max((w_ax - sum(cw)) / max(ncol - 1, 1), tw(" "))
        total = sum(cw) + pad * (ncol - 1)
    assert total <= w_ax + 1e-6, (
        "at-risk 表宽 %.3f > 轴宽 %.3f（figure 分数），会溢出面板" % (total, w_ax))

    y0 = lab_fig.y0 - 0.004
    fig.text(x0, y0, head[0], fontsize=fs, va="top", ha="left")
    x = x0 + cw[0] + pad
    for k in range(len(times)):
        fig.text(x + cw[k + 1], y0, head[k + 1], fontsize=fs, va="top", ha="right")
        x += cw[k + 1] + pad
    for i, b in enumerate(body):
        yy = y0 - (i + 1) * dy
        fig.text(x0, yy, b[0], fontsize=fs, va="top", ha="left")
        x = x0 + cw[0] + pad
        for k in range(len(times)):
            fig.text(x + cw[k + 1], yy, b[k + 1], fontsize=fs, va="top", ha="right")
            x += cw[k + 1] + pad


def add_footnote(fig, ax, lines, fs=6.5, dy_in=None):
    """在面板 x 轴标签**下方**写轴外脚注（多行）。

    ⚠️ 为什么要这个（2026-10-04 先生指出 Figure3A 遮挡）：3A 的 α 注记原本
       放在 axes 内的左下角，而 CV 曲线恰好在那一带穿过 —— 实测 26 个曲线顶点
       落在文字框里。面板内确实没有足够大的空口袋（曲线呈 V 形横贯全图），
       因此改为**轴外脚注**：与 add_atrisk 同一套路，锚在面板左边缘、只向下
       延伸、绝不向左溢出，天然不可能压到任何数据。
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    lab = ax.xaxis.label.get_window_extent(rend).transformed(
        fig.transFigure.inverted())
    if dy_in is None:
        dy_in = (fs * 1.45 / 72.0) / fig.get_figheight()
    x0 = ax.get_position().x0
    return [fig.text(x0, lab.y0 - 0.010 - i * dy_in, ln, fontsize=fs,
                     va="top", ha="left")
            for i, ln in enumerate(lines)]
