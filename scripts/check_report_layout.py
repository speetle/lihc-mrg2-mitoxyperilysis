#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""择刊测评报告版式自检 —— 在缺 LibreOffice/Word 的机器上做可机械判定的部分。

判定项（全部为具名布尔断言，任一项为假即打印 ✗ 并以退出码 1 结束）：
  [1] 页宽减左右边距 >= 每张表的总列宽（防表格出界）
  [2] 每个单元格的估算行数 <= 8（防超窄列把一行撑成巨块）
  [3] 全部可见字号在 8 至 18 磅之间（防层级崩塌）
  [4] 每张表都是三线表：表头上下有框线、末行有下框线、全表无竖线
  [5] 可见文本不含星号、反引号、管道表格与 Markdown 井号标题
  [6] 报告含两张概率总览表（期刊信息表 + 三阶段概率表）

用法：python3 check_report_layout.py <报告.docx>
"""
import re
import sys
from zipfile import ZipFile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
TWIPS_PER_CM = 1440.0 / 2.54          # w:tcW 用的是 twip（二十分之一磅），不是 EMU
CELL_PAD_CM = 0.38                     # 单元格左右内边距合计的经验值
MAX_LINES = 8


def cm(w_twips):
    """把 w:tcW 的 twip 值换算成厘米。"""
    return (w_twips or 0) / TWIPS_PER_CM


def cjk_width(text):
    """粗略宽度（以「一个西文半角字符」为单位，全角按 2 计）。"""
    w = 0.0
    for ch in text:
        w += 2.0 if ord(ch) > 0x2000 else 1.0
    return w


def border_visible(cell, edge):
    b = cell.find("./%stcPr/%stcBorders/%s%s" % (W, W, W, edge))
    if b is None:
        return False
    return b.get(W + "val", "") not in {"", "nil", "none"}


def usable_width_cm(root):
    """页面可用宽度 = 页宽 - 左右页边距（均为 twip）。"""
    pg = root.find(".//%spgSz" % W)
    mar = root.find(".//%spgMar" % W)
    if pg is None or mar is None:
        return None
    pw = int(pg.get(W + "w", "0"))
    left = int(mar.get(W + "left", "0"))
    right = int(mar.get(W + "right", "0"))
    return cm(pw - left - right)


def main(path):
    with ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))

    fails, notes = [], []

    # [5] 可见文本卫生
    text = "\n".join((n.text or "") for n in root.iter(W + "t"))
    for token, label in (("*", "星号"), ("`", "反引号"), ("|---", "管道表格线"), ("##", "Markdown 标题")):
        if token in text:
            fails.append("[5] 可见文本含%s：%r" % (label, token))
    if re.search(r"^#{1,6}\s", text, re.M):
        fails.append("[5] 可见文本含行首 Markdown 井号标题")

    # [1][2][4] 表格
    avail = usable_width_cm(root)
    if avail is None:
        fails.append("[1] 未找到页面尺寸或页边距，无法判断表宽是否出界")
    tables = list(root.iter(W + "tbl"))
    if len(tables) < 2:
        fails.append("[6] 只找到 %d 张表，概率总览应有两张（期刊信息 + 三阶段概率）" % len(tables))
    for ti, t in enumerate(tables, 1):
        total_cm = 0.0
        for cell in t.find(W + "tr").findall(W + "tc"):
            tcW = cell.find("./%stcPr/%stcW" % (W, W))
            if tcW is not None:
                total_cm += cm(int(tcW.get(W + "w", "0")))
        notes.append("表 %d 总列宽 %.2f cm（页面可用 %.2f cm）" % (ti, total_cm, avail or 0))
        if avail is not None and total_cm > avail:
            fails.append("[1] 表 %d 总列宽 %.2f cm 超出页面可用宽度 %.2f cm" % (ti, total_cm, avail))

        # [4] 三线表
        rows = t.findall(W + "tr")
        head_ok = all(border_visible(c, "top") and border_visible(c, "bottom")
                      for c in rows[0].findall(W + "tc"))
        last_ok = all(border_visible(c, "bottom") for c in rows[-1].findall(W + "tc"))
        no_vert = all(not border_visible(c, e)
                      for c in t.iter(W + "tc") for e in ("left", "right", "insideV"))
        if not (head_ok and last_ok and no_vert):
            fails.append("[4] 表 %d 不是三线表（表头线 %s / 末行线 %s / 无竖线 %s）"
                         % (ti, head_ok, last_ok, no_vert))

        # [2] 单元格行数估算
        for ri, row in enumerate(rows):
            for ci, cell in enumerate(row.findall(W + "tc")):
                tcW = cell.find("./%stcPr/%stcW" % (W, W))
                if tcW is None:
                    continue
                col_cm = cm(int(tcW.get(W + "w", "0")))
                txt = "".join(n.text or "" for n in cell.iter(W + "t"))
                fs = None
                for r in cell.iter(W + "r"):
                    sz = r.find("./%srPr/%ssz" % (W, W))
                    if sz is not None:
                        fs = int(sz.get(W + "val")) / 2.0
                        break
                fs = fs or 10.5
                # 一个西文半角字符宽约 0.5 倍字号磅值；一列可用宽度 = 列宽 - 内边距
                usable_cm = max(0.4, col_cm - CELL_PAD_CM)
                per_line = max(1.0, (usable_cm * 28.35) / (fs * 0.5))
                lines = cjk_width(txt) / per_line
                if lines > MAX_LINES:
                    fails.append("[2] 表 %d 第 %d 行第 %d 列估算 %.1f 行（上限 %d）"
                                 % (ti, ri + 1, ci + 1, lines, MAX_LINES))

    # [3] 字号
    sizes = set()
    for sz in root.iter(W + "sz"):
        try:
            sizes.add(int(sz.get(W + "val")) / 2.0)
        except (TypeError, ValueError):
            continue
    bad = sorted(s for s in sizes if s < 8 or s > 18)
    if bad:
        fails.append("[3] 存在越界字号（磅）：%s" % bad)

    for n in notes:
        print("  ·", n)
    print("  · 可见字号（磅）：%s" % sorted(sizes))
    print("  · 可见文本长度：%d 字符" % len(text))

    if fails:
        for f in fails:
            print("✗", f)
        return 1
    print("✅ 版式自检通过：表宽未出界、单元格估算行数达标、三线表齐备、字号与文本卫生合格")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python3 check_report_layout.py <报告.docx>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
