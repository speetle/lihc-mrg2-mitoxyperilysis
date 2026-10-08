#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
v112_submission_format.py —— 由 v1.12 稿件 DOCX 出「投稿版 DOCX」（DDS 版式）

依据：Digestive Diseases and Sciences *Instructions for Authors*（官方 PDF 2022-09-01）原文
    "Format of all manuscripts should be set as follows: 12-point font size, double-spaced
     with 1-inch margins, and only one space after periods and commas."

v1.12 → 投稿版的路径（sir 2026-10-05 目录重组后）：
    源：`<交付根>/Manuscript_LIHC_v1.12.docx`                  （源资产，留在交付根）
    出：`<交付根>/投稿_DDS/02_Manuscript_LIHC_MRG2.docx`        （上传件，进唯一投稿夹）
  源稿留根、投稿版进夹 —— 夹内因此**只有一份稿件 DOCX**，
  不会出现「源稿／含图版／投稿版」三份并存、无人知道该传哪份的情况。

本脚本只改**版式**，一字不动内容：
    - 正文（样式 Normal）字号 10.5 pt → 12 pt
    - 行距 → 双倍
    - 页边距 → 1 英寸（2.54 cm）
    - 目录/表格内文字保持其原字号：7 列表格按 12 pt 会溢出页宽，
      这是通行做法；DDS 该条约束的是稿件正文。
**不输出**含图版（投稿正文不含图，图件单独上传）。

硬断言（改版式不得动内容）：
    A 段落数、表数、每行单元格数不变
    B 段落与表格提取文本逐字符不变
    C 上标 run 数不变、字面 caret 数不变
    D 源稿上标 run == 45（3 头部标记 + 42 正文引文）
"""
import os
import re

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Pt, Inches

HERE = os.path.dirname(os.path.abspath(__file__))
DELIV = os.path.dirname(HERE)
SRC = os.path.join(DELIV, "Manuscript_LIHC_v1.12.docx")
DST = os.path.join(DELIV, "投稿_DDS", "02_Manuscript_LIHC_MRG2.docx")


def die(m):
    raise SystemExit("❌ " + m)


def snapshot(path):
    d = Document(path)
    sup = 0
    for p in d.paragraphs:
        for r in p.runs:
            if r.font.superscript:
                sup += 1
    tables = []
    for t in d.tables:
        rows = []
        for row in t.rows:
            cells = []
            for c in row.cells:
                cells.append(c.text)
                for p in c.paragraphs:
                    for r in p.runs:
                        if r.font.superscript:
                            sup += 1
            rows.append(cells)
        tables.append(rows)
    return {
        "paras": [p.text for p in d.paragraphs],
        "tables": tables,
        "sup": sup,
        "caret": "\n".join([p.text for p in d.paragraphs]
                           + [c for tb in tables for r in tb for c in r]).count("^"),
    }


def main():
    if not os.path.exists(SRC):
        die("缺源稿：%s" % SRC)
    before = snapshot(SRC)
    if before["sup"] != 45:
        die("源稿上标 run 应为 45，实测 %d" % before["sup"])

    d = Document(SRC)

    # 1) 页边距 → 1 英寸
    for s in d.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)

    # 2) 正文样式 → 12 pt / 双倍行距
    st = d.styles["Normal"]
    st.font.size = Pt(12)
    pf = st.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    pf.line_spacing = 2.0

    # 3) 显式继承了 10.5 pt 的少量 run 一并抬到 12 pt（不改显式的表格小字号）
    n_bump = 0
    for p in d.paragraphs:
        if p.style.name == "Normal":
            for r in p.runs:
                if r.font.size is None or r.font.size == Pt(10.5):
                    r.font.size = Pt(12)
                    n_bump += 1

    # 4) 标题样式统一为双倍行距（Heading 由 md2docx 显式设过间距）
    for name in ["Heading 1", "Heading 2", "Heading 3", "Heading 4"]:
        try:
            d.styles[name].paragraph_format.line_spacing = 2.0
        except KeyError:
            pass

    os.makedirs(os.path.dirname(DST), exist_ok=True)
    d.save(DST)

    after = snapshot(DST)

    # ── 断言 ────────────────────────────────────────────────────
    if before["paras"] != after["paras"]:
        die("段落文本被改动")
    if before["tables"] != after["tables"]:
        die("表格内容被改动")
    if before["sup"] != after["sup"]:
        die("上标 run 数变了：%d -> %d" % (before["sup"], after["sup"]))
    if before["caret"] != after["caret"]:
        die("字面 caret 数变了：%d -> %d" % (before["caret"], after["caret"]))

    body = [p.text for p in Document(DST).paragraphs]
    dbl = [i for i, s in enumerate(body, 1) if re.search(r"[.!?,;:] {2,}", s)]
    if dbl:
        print("⚠ DDS「标点后只留一个空格」未满足的行（前 8 条）：%s" % dbl[:8])

    d2 = Document(DST)
    s0 = d2.sections[0]
    print("OK -> %s" % os.path.relpath(DST, DELIV))
    print("    Normal 字号 %.1f pt | 行距 %s | 边距 %.2f in"
          % (d2.styles["Normal"].font.size.pt,
             d2.styles["Normal"].paragraph_format.line_spacing, s0.top_margin.inches))
    print("    段落 %d | 表 %d | 上标 run %d | 字面 ^ %d | 抬升正文 run %d"
          % (len(after["paras"]), len(after["tables"]), after["sup"], after["caret"], n_bump))
    print("    断言 A–D 全过：内容、表结构与上标计数逐项未变")


if __name__ == "__main__":
    main()
