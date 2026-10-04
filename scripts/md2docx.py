# -*- coding: utf-8 -*-
"""Markdown -> DOCX（LIHC v1.9 版；由 LGG v5.6 的 md2docx 移植）。

相对 LIHC v1.8 的旧转换器，三处硬改动：

① **行内解析器改为递归下降 tokenizer。** 旧版用 `re.split` 一次切分，斜体块
   里嵌反引号就漏掉，反引号原样落进 Word。新版把 code span 一律只留文字、
   不留反引号。

② **正文引文转为真上标。** `[1,2]`、`[29,30]`、`[11,15,16]`、`[15–17]` 这类
   纯数字方括号，在正文段落里渲染成 Word 上标（去掉方括号，Vancouver /
   ICMJE 编号式）。必须放过的三类：参考文献表本身、`[Author]`、`[V]`。

   ⚠️ **LIHC 特有修正（2026-10-05）**：LGG 版用「进入 `## References` 后
      `in_refs` 永久为真」的写法。LIHC 的参考文献表**之后**还有
      `## Supplementary Methods`，其中第 542 行含两条正文引文 `[38]`、`[28]`
      ——照搬会把这两条漏成字面方括号。此处改为**遇到下一个 `##` 标题即重置**
      （仅 `## References` 段内为真）。

③ **支持 `^...^` 上标标记。** 作者与单位标记 `^1^`、`^1,*^`、`^*^` 渲染成
   Word 上标，不再出现字面 caret。

④ **参考文献条目改为悬挂缩进 + 字面序号**，不走 Word 自动编号
   （`numPr` 命中数必须为 0）。

运行：python md2docx.py <in.md> <out.docx> [字号]
"""
import re, sys, inspect
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

MONO = 'Consolas'


def setfont(doc, latin='Times New Roman', cjk='宋体', size=10.5):
    st = doc.styles['Normal']; st.font.name = latin; st.font.size = Pt(size)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), cjk)
    for s in ['Heading 1', 'Heading 2', 'Heading 3', 'Title']:
        try:
            f = doc.styles[s].font; f.name = latin; f.color.rgb = RGBColor(0, 0, 0)
            doc.styles[s].element.rPr.rFonts.set(qn('w:eastAsia'), cjk)
        except Exception:
            pass


# --------------------------------------------------------------------------
# 行内解析
# --------------------------------------------------------------------------
# 顺序即优先级：code / 上标 / 删除线 / 粗体 / 斜体。
# 上标放在粗体之前，是为了让 `^1,*^` 里的星号被整体吃掉、不被当成斜体定界符。
TOKEN = re.compile(
    r'(`[^`]+`'                    # 行内代码
    r'|\^[^\^\n]{1,80}?\^'         # ^上标^
    r'|~~[^~\n]{1,200}?~~'         # ~~删除线~~
    r'|\*\*.+?\*\*'                # **粗体**
    r'|(?<!\*)\*(?!\*)[^*\n]+?\*(?!\*))'   # *斜体*
)

# 纯数字方括号引文：[11] / [29,30] / [11,15,16] / [15–17] / [10,38–40]
CITE = re.compile(r'\[(\d{1,2}(?:\s*[\u2013-]\s*\d{1,2})?'
                  r'(?:\s*,\s*\d{1,2}(?:\s*[\u2013-]\s*\d{1,2})?)*)\]')


def _rec(text):
    """把一段文本切成 run 列表。返回 [dict(t, b, i, mono, sup, strike)]。"""
    out = []
    pos = 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            out.append(dict(t=text[pos:m.start()]))
        seg = m.group(0)
        if seg.startswith('`'):
            out.append(dict(t=seg[1:-1], mono=True))
        elif seg.startswith('^'):
            out.append(dict(t=seg[1:-1], sup=True))
        elif seg.startswith('~~'):
            out.append(dict(t=seg[2:-2], strike=True))
        elif seg.startswith('**'):
            for r in _rec(seg[2:-2]):
                r['b'] = True
                out.append(r)
        else:
            for r in _rec(seg[1:-1]):
                r['i'] = True
                out.append(r)
        pos = m.end()
    if pos < len(text):
        out.append(dict(t=text[pos:]))
    return out


def _citesplit(runs):
    """把普通 run 里的 [n] / [n,m] / [n-m] 拆成上标 run。"""
    out = []
    for r in runs:
        if r.get('mono') or r.get('sup') or r.get('strike') or '[' not in r['t']:
            out.append(r); continue
        t = r['t']; pos = 0; found = False
        for m in CITE.finditer(t):
            found = True
            if m.start() > pos:
                out.append(dict(r, t=t[pos:m.start()]))
            out.append(dict(r, t=m.group(1), sup=True))
            pos = m.end()
        # 注意：`[Author]`、`E[V]` 这类方括号里没有数字，一个都不匹配时
        # 必须原样保留**一次**。早先的写法在 pos==0 时既走了 `pos < len(t)`
        # 分支又走了 `pos == 0` 分支，于是整段被复制两遍（作者行一度印成
        # `[Author] [Author]1, ...`）。
        if not found:
            out.append(r); continue
        if pos < len(t):
            out.append(dict(r, t=t[pos:]))
    return out


def _emit(p, runs, size=None, force_bold=False):
    for r in runs:
        if not r['t']:
            continue
        run = p.add_run(r['t'])
        run.bold = bool(r.get('b')) or force_bold
        run.italic = bool(r.get('i'))
        run.font.strike = bool(r.get('strike'))
        if r.get('sup'):
            run.font.superscript = True
        if r.get('mono'):
            run.font.name = MONO
            run._element.rPr.rFonts.set(qn('w:eastAsia'), MONO)
        if size is not None:
            run.font.size = Pt(size)


def add_runs(p, text, force_bold=False, size=None, cites=True):
    runs = _rec(text)
    if cites:
        runs = _citesplit(runs)
    _emit(p, runs, size=size, force_bold=force_bold)


# --------------------------------------------------------------------------
# 表格 / 正文
# --------------------------------------------------------------------------
def is_sep(line):
    return bool(re.match(r'^\|[\s:\-|]+\|$', line.strip()))


def write_table(doc, rows, cites_all=True):
    if not rows:
        return
    hdr = [c.strip() for c in rows[0].strip('|').split('|')]
    body = [[c.strip() for c in r.strip('|').split('|')] for r in rows[1:]]
    ncol = len(hdr)
    t = doc.add_table(rows=1, cols=ncol)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(hdr):
        cell = t.rows[0].cells[i]; cell.text = ''
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, h, force_bold=True, size=9, cites=cites_all)
    for brow in body:
        cells = t.add_row().cells
        for i in range(ncol):
            v = brow[i] if i < len(brow) else ''
            cells[i].text = ''
            p = cells[i].paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(p, v, cites=cites_all)
            for rr in p.runs:
                rr.font.size = Pt(9)
    doc.add_paragraph()


def convert(md_path, out_path, base_size=10.5, latin='Times New Roman',
            cjk='宋体', cites_all=True):
    """cites_all=False 时把 `[n]` 当**字面文本**，只保留 `^...^` 上标标记。

    ⚠️ 为什么需要这个开关（2026-10-05 实测）：`[n]` 上标化只对**投稿正文**成立。
      回复表 / 交付说明这类文档里的方括号数字大多是**指代文献编号本身**
      （如「参考文献 [21] 注释」「R3-REF1 **[35] DOI 写错**」「`stats_hardening.json`
      的 [9,13] / [5,16]」）。无差别上标化会把「参考文献 ²¹ 注释」印出来，属于
      把对的规则用错地方。正文用默认值，其余文档传 cites_all=False。
    """
    doc = Document(); setfont(doc, latin, cjk, base_size)
    for s in doc.sections:
        s.top_margin = Cm(2.2); s.bottom_margin = Cm(2.2)
        s.left_margin = Cm(2.2); s.right_margin = Cm(2.2)
    lines = open(md_path, encoding='utf-8').read().split('\n')
    i = 0
    in_refs = False          # 仅 `## References` 段内为真；遇下一个 ## 标题即重置

    def cites():
        return cites_all and not in_refs

    # ── 静态自检：convert() 内每一处 add_runs(...) 都必须**显式**传 cites= ──
    # ⚠️ 2026-10-05 实测踩过：`# 标题` 与「有序列表」两个分支漏传 cites=，于是退回默认
    #    True，在 `--no-cites` 的交付说明里把「本轮抓出 3 条错 DOI（[2]、[10]、[35]）」
    #    印成了「（²、¹⁰、³⁵）」—— 正是这条开关本来要防的事。此处把「漏传」变成硬错。
    for _line in inspect.getsource(convert).split('\n'):
        if _line.lstrip().startswith('#'):
            continue
        for _m in re.finditer(r'add_runs\(([^()]*)\)', _line):
            assert 'cites=' in _m.group(1), (
                'convert() 内有未显式传 cites= 的 add_runs 调用：%r' % _m.group(0))

    while i < len(lines):
        line = lines[i]; st = line.strip()
        if not st:
            i += 1; continue
        if st.startswith('|') and i + 1 < len(lines) and is_sep(lines[i + 1]):
            rows = [st]; j = i + 1
            while j < len(lines) and lines[j].strip().startswith('|'):
                if not is_sep(lines[j]):
                    rows.append(lines[j].strip())
                j += 1
            write_table(doc, rows, cites_all); i = j; continue
        if st == '---':
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(6)
            from docx.oxml import OxmlElement
            pPr = p._p.get_or_add_pPr(); pbdr = OxmlElement('w:pBdr')
            b = OxmlElement('w:bottom')
            b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), '6')
            b.set(qn('w:color'), '999999')
            pbdr.append(b); pPr.append(pbdr); i += 1; continue
        if st.startswith('#### '):
            p = doc.add_paragraph(style='Heading 3')
            add_runs(p, st[5:], cites=cites()); i += 1; continue
        if st.startswith('### '):
            p = doc.add_paragraph(style='Heading 3')
            add_runs(p, st[4:], cites=cites()); i += 1; continue
        if st.startswith('## '):
            # ⚠️ 每个 ## 标题都重新判定，`## References` 之后的下一个 ## 会把它关掉。
            #    LIHC 的 `## Supplementary Methods` 在参考文献表之后，且含 [38]/[28]。
            in_refs = st[3:].strip().lower().startswith('reference')
            p = doc.add_paragraph(style='Heading 2')
            add_runs(p, st[3:], cites=cites()); i += 1; continue
        if st.startswith('# '):
            p = doc.add_paragraph(style='Heading 1')
            add_runs(p, st[2:], cites=cites())
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT; i += 1; continue
        if st.startswith('> '):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.8)
            add_runs(p, st[2:], cites=cites())
            for rr in p.runs:
                if not rr.bold:
                    rr.italic = True
                rr.font.size = Pt(base_size - 1)
            i += 1; continue
        if st.startswith('- '):
            p = doc.add_paragraph(style='List Bullet')
            add_runs(p, st[2:], cites=cites()); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.*)$', st)
        if m and not in_refs:
            p = doc.add_paragraph(style='List Number')
            add_runs(p, m.group(2), cites=cites()); i += 1; continue
        if m and in_refs:
            # 参考文献：`1. Author...` 的序号保留为字面文本，悬挂缩进，不做上标
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.first_line_indent = Cm(-0.6)
            add_runs(p, st, cites=False); i += 1; continue
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(6)
        add_runs(p, st, cites=cites()); i += 1
    doc.save(out_path)
    # 复核：落盘后数一遍，让"有没有真的转成上标"当场可见
    d2 = Document(out_path)
    sup = 0; lit = 0; citsup = []
    for p in d2.paragraphs:
        for r in p.runs:
            if r.font.superscript:
                sup += 1
                if re.fullmatch(r'[\d,\u2013\u2014\-]{1,12}', r.text):
                    citsup.append(r.text)
        lit += p.text.count('^')
    for t in d2.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    for r in p.runs:
                        if r.font.superscript:
                            sup += 1
                            if re.fullmatch(r'[\d,\u2013\u2014\-]{1,12}', r.text):
                                citsup.append(r.text)
    print('OK ->', out_path)
    print('   上标 run: %d（其中纯数字=引文上标 %d）| 字面 ^: %d | 段落: %d | 表: %d'
          % (sup, len(citsup), lit, len(d2.paragraphs), len(d2.tables)))
    if not cites_all:
        # `--no-cites` 模式：纯数字上标只可能来自显式 `^...^` 标记。若引文数 > 0，
        # 立刻把哪些 run 被误上标化打出来，不让它静默落盘。
        print('   [--no-cites] 纯数字上标 run 内容: %r' % (citsup[:12],))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    convert(args[0], args[1],
            float(args[2]) if len(args) > 2 else 10.5,
            cites_all='--no-cites' not in sys.argv)
