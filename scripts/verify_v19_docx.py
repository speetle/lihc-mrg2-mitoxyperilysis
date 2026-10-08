#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_v19_docx.py —— 在**生成的 DOCX 上**核验投稿前零残留（不看源 md）。

为什么必须核在 DOCX 上：LGG 与 LIHC 都踩过同一个坑 —— 源 md 干净，Word 里
却漏出字面 caret、字面方括号、Word 自动编号。md 是中间件，DOCX 才是交付件。

判据（任一不过 → 退出码 1）：

  A. 字面 caret `^` = 0（作者行的 `^1` / `^1*` 必须变成真上标）
  B. 正文残留 `[数字]` 方括号 = 0（引文必须变成真上标、不带方括号）
  C. 上标 run 计数与分类：引文 42 + 头部标记 3 = 45（v1.10 起作者为单一作者，
     头部标记由 4 降为 3：`1,*` / `1` / `*`）
  D. 作者行 = `Authors: Bin Lian, PhD1,*`，其中 `1,*` 上标（PhD 为 v1.12 起按 DDS 题名页
     硬要求补的最高学位；下方另设「Correspondence 行同样带 PhD」的配套断言，防只改一处）
  D2. Correspondence 行含 `Bin Lian, PhD` —— 与 D 同源，两处必须同时成立
  E. `* Corresponding author.` 独立成段，`*` 上标
  F. 关键词 ≤ 5 个
  G. 参考文献序号 1..N 为**字面文本**、连续；`numPr` 命中数 = 0；N 由 md 侧决定
  H. 表结构不变量：数据行 `w:tc` 数 == 表头 `w:tc` 数（不能用 row.cells 数）
  I. 摘要词数 ≤ 250；正文（Introduction→Conclusion）≤ 6000（Word 口径）

用法：python verify_v19_docx.py <docx> [md]
"""
import sys, re, collections
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

W = qn('w:tc')
CITE = re.compile(r'\[(\d{1,2}(?:\s*[\u2013-]\s*\d{1,2})?'
                  r'(?:\s*,\s*\d{1,2}(?:\s*[\u2013-]\s*\d{1,2})?)*)\]')


def tokens(s):
    """Word 口径词数：空白分隔且含字母或数字的 token。"""
    return [t for t in re.split(r'\s+', s)
            if t and re.search(r'[A-Za-z0-9]', t)]


def table_widths(doc):
    """逐表返回 (表头 w:tc 数, [数据行 w:tc 数...])。数原始 w:tc，不用 row.cells。"""
    out = []
    for t in doc.tables:
        rows = t._tbl.findall(qn('w:tr'))
        widths = [len(r.findall(W)) for r in rows]
        if widths:
            out.append((widths[0], widths[1:]))
    return out


def main(path, md_path=None):
    doc = Document(path)
    fail = []

    def check(name, ok, detail=""):
        print(("✅ " if ok else "❌ ") + name + ("" if not detail else " | " + detail))
        if not ok:
            fail.append(name)

    # 收集（按段落序号分「正文前头部」与「正文」两区，用于上标分类）
    abs_idx = next((i for i, p in enumerate(doc.paragraphs)
                    if p.text.strip() == 'Abstract'), 10 ** 9)
    all_sup, all_text = [], []
    sups_head, sups_body = [], []
    lit_caret = 0
    brack = []
    for i, p in enumerate(doc.paragraphs):
        all_text.append(p.text)
        lit_caret += p.text.count('^')
        brack += CITE.findall(p.text)
        for r in p.runs:
            if r.font.superscript:
                all_sup.append(r.text)
                (sups_head if i < abs_idx else sups_body).append(r.text)
    # 表内文字也要查（表格里不该有字面 caret / 方括号引文）
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                txt = "\n".join(x.text for x in c.paragraphs) if c.paragraphs else c.text
                lit_caret += txt.count('^')
                brack += CITE.findall(txt)

    # A / B
    check("A 字面 caret `^` = 0", lit_caret == 0, f"命中 {lit_caret}")
    check("B 残留 [数字] 方括号 = 0", len(brack) == 0, f"命中 {len(brack)}：{brack[:6]}")

    # C 上标分类：摘要之前的头部标记应恰为 3 个（1,* / 1 / *），
    #   正文区应恰为 42 个引文编号。按位置分类，不靠字形猜。
    ok_c = (len(sups_head) == 3 and len(sups_body) == 42
            and all(re.fullmatch(r'\d+(?:[,\u2013\-]\d+)*', s.strip())
                    or s.strip() in ('1,*', '*') for s in sups_head)
            and all(re.fullmatch(r'\d+(?:[,\u2013\-]\d+)*', s.strip())
                    for s in sups_body))
    check("C 上标 run = 45（头部标记 3 + 正文引文 42）", ok_c,
          f"总 {len(all_sup)} = 头部 {len(sups_head)} {sups_head} + 正文 {len(sups_body)}")

    # D 作者行（v1.12 起：按 DDS IFA 题名页要求补最高学位）
    auth = [p for p in doc.paragraphs if p.text.strip().startswith('Authors:')]
    ok_d = False; det_d = "未找到 Authors 行"
    if len(auth) == 1:
        p = auth[0]
        det_d = repr(p.text)
        sup_txts = [r.text for r in p.runs if r.font.superscript]
        ok_d = (p.text.strip() == 'Authors: Bin Lian, PhD1,*'
                and sup_txts == ['1,*']
                and '^' not in p.text)
    check("D 作者行 = `Authors: Bin Lian, PhD1,*`（`1,*` 真上标；PhD 为 DDS 题名页硬要求）", ok_d, det_d)

    # E Corresponding author 段
    corr = [p for p in doc.paragraphs if p.text.strip() == '* Corresponding author.']
    ok_e = len(corr) == 1 and [r.text for r in corr[0].runs if r.font.superscript] == ['*']
    check("E `* Corresponding author.` 独立成段，`*` 上标", ok_e,
          f"命中 {len(corr)} 段")

    # D2 Correspondence 行（与 D 同源：学位必须两处同时带上）
    corr_p = [p for p in doc.paragraphs if p.text.strip().startswith('Correspondence:')]
    ok_d2 = len(corr_p) == 1 and 'Bin Lian, PhD' in corr_p[0].text
    check("D2 Correspondence 行含 `Bin Lian, PhD`（与 D 同源）", ok_d2,
          repr(corr_p[0].text[:90]) if corr_p else "未找到 Correspondence 行")

    # F 关键词
    kw = [p for p in doc.paragraphs if p.text.strip().startswith('Keywords:')]
    n_kw = 0; det_f = "未找到 Keywords 行"
    if len(kw) == 1:
        body = kw[0].text.split(':', 1)[1]
        items = [x.strip() for x in body.split(';') if x.strip()]
        n_kw = len(items)
        det_f = f"{n_kw} 个：{items}"
    check("F 关键词 ≤ 5 个", len(kw) == 1 and 1 <= n_kw <= 5, det_f)

    # G 参考文献序号字面连续（条数由 md 侧的参考文献表长度决定，不写死）
    numpr = len(doc.element.body.findall('.//' + qn('w:numPr')))
    ref_start = None
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip().lower().rstrip(':') == 'references':
            ref_start = i; break
    refs = []
    if ref_start is not None:
        for p in doc.paragraphs[ref_start + 1:]:
            m = re.match(r'^(\d{1,3})\.\s+\S', p.text.strip())
            if m:
                refs.append(int(m.group(1)))
            elif p.text.strip().lower().startswith(('supplementary', 'appendix')):
                break
    n_ref_md = None
    if md_path:
        mdt = open(md_path, encoding='utf-8').read()
        sec = mdt.split('## References', 1)[1].split('\n## ', 1)[0]
        n_ref_md = len([l for l in sec.split('\n')
                        if re.match(r'^\d{1,3}\.\s+\S', l.strip())])
    ok_g = (numpr == 0 and refs == list(range(1, len(refs) + 1)) and len(refs) > 0
            and (n_ref_md is None or len(refs) == n_ref_md))
    check("G 参考文献序号 1..N 字面连续、无 Word 自动编号、条数=md",
          ok_g,
          f"条目 {len(refs)} 条、序号连续={refs == list(range(1, len(refs)+1))}、"
          f"numPr={numpr}、md 侧 {n_ref_md} 条")

    # H 表结构不变量
    bad = []
    for k, (hw, body) in enumerate(table_widths(doc), 1):
        for r, w in enumerate(body, 1):
            if w != hw:
                bad.append(f"表{k} 第{r}数据行 {w} vs 表头 {hw}")
    check("H 表结构不变量（数据行 w:tc == 表头 w:tc）", not bad,
          f"{len(doc.tables)} 张表" + ("" if not bad else "；" + "；".join(bad[:4])))

    # I 字数（口径与 compress_gate.py / r1m8_backfill.py 完全一致）
    #   正文 = `1. Introduction` → `Declarations`；摘要 = `Abstract` → `Keywords`
    #   ⚠️ 必须**按文档顺序**遍历段落与表格：python-docx 的 `doc.paragraphs`
    #      不含表格单元格文字，而 md 侧口径把正文内的表格文字算进去了
    #      （LIHC 正文 §3.1 里就嵌了一张表）——只数段落会少 67 个 token，
    #      于是这条自检会误报"DOCX 与 md 不一致"。
    blocks = []                      # [(kind, text)]
    for child in doc.element.body.iterchildren():
        if child.tag == qn('w:p'):
            blocks.append(('p', Paragraph(child, doc).text.strip()))
        elif child.tag == qn('w:tbl'):
            t = Table(child, doc)
            for row in t.rows:
                for c in row.cells:
                    for cp in c.paragraphs:
                        blocks.append(('t', cp.text.strip()))
    txts = [t for _, t in blocks]

    def seg(a, b):
        """两个标题**之间**的文字（不含两端标题本身），与 md 侧 split 口径对齐。"""
        try:
            ia = next(i for i, t in enumerate(txts) if re.match(a, t))
            ib = next(i for i, t in enumerate(txts) if i > ia and re.match(b, t))
        except StopIteration:
            return None
        return "\n".join(txts[ia + 1:ib])

    abst = seg(r'^Abstract$', r'^(\*\*)?Keywords')
    body = seg(r'^1\.\s*Introduction', r'^Declarations$')
    n_abs = len(tokens(abst)) if abst else -1
    n_body_docx = len(tokens(body)) if body else -1
    check("I 摘要 ≤ 250 词", 0 < n_abs <= 250, f"{n_abs} 词")

    # 正文词数同时在 md 上复算一遍，两侧必须一致（防 DOCX 转换丢字）
    n_body_md = n_abs_md = None
    if md_path:
        mdt = open(md_path, encoding='utf-8').read()
        try:
            n_body_md = len(tokens(mdt.split('## 1. Introduction')[1]
                                   .split('## Declarations')[0]))
            n_abs_md = len(tokens(mdt.split('## Abstract')[1]
                                  .split('**Keywords')[0]))
        except IndexError:
            n_body_md = None
    ok_i = (0 < n_body_docx <= 6000
            and (n_body_md is None or n_body_docx == n_body_md)
            and (n_abs_md is None or n_abs == n_abs_md))
    check("I 正文 ≤ 6000 词（Word 口径，与 md 侧一致）", ok_i,
          f"DOCX {n_body_docx} 词" + ("" if n_body_md is None else f" | md {n_body_md} 词")
          + ("" if n_abs_md is None else f"；摘要 DOCX {n_abs} / md {n_abs_md}"))

    print()
    if fail:
        print(f"❌ 未通过 {len(fail)} 项：" + "、".join(fail))
        return 1
    print("✅ DOCX 投稿前零残留全过（9 组判据）")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
