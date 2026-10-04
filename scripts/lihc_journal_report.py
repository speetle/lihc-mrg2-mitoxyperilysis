#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学生3（LIHC）择刊测评报告 —— 生成 Word（三线表、无星号、无 Markdown 残留）。

依据 biomedical-journal-selector 技能：
  · 核心结论与概率总览前置；
  · 概率总览用真正的 Word 表格（三线表：表顶线 + 表头下横线 + 表底线，无竖线）；
  · 逐刊决策卡 / 论文诊断 / 投稿路径 / 不推荐清单 / 不确定性与来源 / 隐私说明；
  · 生成后须跑 scripts/report_check.py 并逐页渲染核验。
"""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "学生3_LIHC_择刊测评报告_20261004.docx")
DATE = "2026-10-04"

# ----------------------------------------------------------------------------- 版式工具
def set_normal(doc, size=10.5, latin="Times New Roman", cjk="宋体"):
    st = doc.styles["Normal"]
    st.font.name = latin
    st.font.size = Pt(size)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), cjk)
    for name in ("Heading 1", "Heading 2", "Heading 3", "Title"):
        try:
            f = doc.styles[name].font
            f.name = latin
            f.color.rgb = RGBColor(0, 0, 0)
            doc.styles[name].element.rPr.rFonts.set(qn("w:eastAsia"), cjk)
        except KeyError:
            pass


def h(doc, text, level=1):
    p = doc.add_paragraph(style="Heading %d" % level)
    r = p.add_run(text)
    r.font.color.rgb = RGBColor(0, 0, 0)
    return p


def para(doc, text, size=10.5, indent=None, bold=False, italic=False, space=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    return p


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.add_run(text).font.size = Pt(size)
    return p


def _set_border(cell, edge, sz=12):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tcPr.append(borders)
    el = borders.find(qn("w:" + edge))
    if el is None:
        el = OxmlElement("w:" + edge)
        borders.append(el)
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(sz))
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "000000")


def _kill_border(cell, edge):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tcPr.append(borders)
    el = borders.find(qn("w:" + edge))
    if el is None:
        el = OxmlElement("w:" + edge)
        borders.append(el)
    el.set(qn("w:val"), "nil")


def three_line_table(doc, header, rows, widths, size=9, head_size=None, align_center=None):
    """真三线表：表顶线 + 表头下横线 + 表底线，全部竖线与内部横线为 nil。"""
    head_size = head_size or size
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    align_center = align_center or [True] * len(header)

    for i, txt in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(txt)
        r.bold = True
        r.font.size = Pt(head_size)

    for row in rows:
        cells = t.add_row().cells
        for i, txt in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if align_center[i] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(1)
            p.add_run(str(txt)).font.size = Pt(size)

    # 边框：先全清，再补三条横线
    for r_i, row in enumerate(t.rows):
        for c in row.cells:
            for edge in ("top", "bottom", "left", "right", "insideH", "insideV"):
                _kill_border(c, edge)
    for c in t.rows[0].cells:
        _set_border(c, "top")
        _set_border(c, "bottom")
    for c in t.rows[-1].cells:
        _set_border(c, "bottom")

    for row in t.rows:
        for i, c in enumerate(row.cells):
            c.width = Cm(widths[i])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_hyperlink(paragraph, url, text, size=9):
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hl = OxmlElement("w:hyperlink")
    hl.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    col = OxmlElement("w:color")
    col.set(qn("w:val"), "0563C1")
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    rPr.append(col)
    rPr.append(u)
    rPr.append(sz)
    run.append(rPr)
    tt = OxmlElement("w:t")
    tt.text = text
    run.append(tt)
    hl.append(run)
    paragraph._p.append(hl)


def source_line(doc, label, url, size=8.5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.left_indent = Cm(0.4)
    p.add_run(label + " ").font.size = Pt(size)
    add_hyperlink(p, url, url, size=size)


# ----------------------------------------------------------------------------- 报告
doc = Document()
set_normal(doc)
for s in doc.sections:
    s.top_margin = Cm(2.0)
    s.bottom_margin = Cm(2.0)
    s.left_margin = Cm(2.0)
    s.right_margin = Cm(2.0)

tp = doc.add_paragraph(style="Title")
r = tp.add_run("学生3（LIHC 肝细胞癌）稿件择刊测评报告")
r.font.color.rgb = RGBColor(0, 0, 0)
r.font.size = Pt(17)
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
sub.add_run("测评日期：%s　｜　测评对象：学生3_LIHC_MRG预后_SCI稿件_v1.10（正文 5,970 词 / 摘要 238 词 / 题名 113 字符（不计空格）/ 41 条参考文献 / 6 图 8 表 + 补充材料 S1–S16 + S4b + S10b + TRIPOD 清单）" % DATE).font.size = Pt(9.5)

# =============================== 一、核心结论 =====================================
h(doc, "一、核心结论", 1)

para(doc, "文章类型与主题：基于公共数据的二次分析（生物信息学），以「方法学＋外部阴性复制」为定位的预后模型验证研究。"
          "数据为 TCGA-LIHC 发现队列（n = 360，129 例死亡）＋两个外部队列（GSE14520，n = 242、96 例死亡；GSE76427，n = 115、23 例死亡）。"
          "核心主张不是「发现了一个新标志物」，而是「稳定性选择压缩出的两基因分数在独立队列中不复制，且两基因与二十三基因在诚实口径下不可区分」。")

para(doc, "质量定位：报告规范（TRIPOD / TRIPOD+AI 清单、完全嵌套交叉验证、pooled out-of-fold 估计、校准、PH 诊断、多重校正、数据与代码可得性）"
          "明显高于同类 TCGA 签名稿的平均水平；短板是无湿实验验证、无肿瘤纯度校正、无复发终点，且唯一的外部队列阴性结论无法用实验补强。"
          "因此本稿的价值在方法与诚信，不在发现的新颖性。")

para(doc, "适合层级：适合「方法学 / 阴性复制 / 预后模型验证」定位的 3–4 区肿瘤学或消化肝病学期刊；"
          "不适合以「新型预后标志物」为卖点的 1–2 区肿瘤学期刊。")

para(doc, "首要结论（本报告最重要的一条）：在版面费低于 2000 元人民币（约 280 美元）的约束下，"
          "英文完全开放获取（OA）期刊市场被整体排除——现查到的英文 OA 期刊最低档也在 1500 美元以上。"
          "可投池只剩「混合 OA 期刊的订阅出版路线」，即作者选择不开放获取、由读者付费阅读，从而零出版费用。"
          "本报告全部推荐期刊都在这一路径上，并已逐刊核验其订阅路线确实不收取版面费。", bold=False)

para(doc, "首选与投稿顺序：首投 Digestive Diseases and Sciences（DDS）；"
          "第二 Clinical and Translational Oncology（CTO）；"
          "第三 Biochemical Genetics（BG）；"
          "冲刺档为 Hepatobiliary & Pancreatic Diseases International（HBPD INT）；"
          "保底为 Molecular Biology Reports（MBR）。若时间紧（如毕业或结题倒计时），直接投 CTO 或 DDS。")

para(doc, "最大风险：① 编辑初筛时把稿件读成「又一个 TCGA 预后签名 + 一次失败的外部验证」，从而以「缺乏新颖性 / 仅描述性」为由直接退稿；"
          "② 目标期刊对「二次分析 / 回顾性研究」有隐性排除；"
          "③ 图件与补充材料体量偏大（6 图 8 表 + 20 项补充材料），部分期刊有篇幅硬限。")

para(doc, "最值得先改的三项：① 投稿信（Cover Letter）必须第一句就把「这是方法学论文，不是标志物发现」说清楚，"
          "并点名摘要里的方法学结论；② 按目标期刊把正文压到其篇幅上限以内，多余细节下沉补充材料；"
          "③ 把「两基因与二十三基因在诚实口径下不可区分」这一条提到摘要与讨论的最前面（当前已在摘要，但讨论中仍被外部阴性叙述盖住）。")

# =============================== 二、概率声明与总览 ===============================
h(doc, "二、概率声明与概率总览", 1)

para(doc, "录用概率是决策辅助估计，不是期刊官方承诺或录用保证。除非特别注明，它综合稿件质量、研究类型、主题适配、期刊选择性、"
          "近期发文特征和可获得的公开信息。编辑判断、审稿意见、同期竞争、特刊安排及政策变化都可能使实际结果明显偏离估计。", size=9.5, italic=True)

para(doc, "下表各期刊均未公开足以支撑个体稿件概率的官方送审率或接收率数据；下列数值属于结构化专家估计，"
          "不能作为该期刊真实统计录用率使用，也不得与期刊总体接受率混淆。个别期刊的官方接收率已单独标注。", size=9.5, italic=True)

para(doc, "表 1　期刊信息（分区、影响因子与出版模式）", bold=True, space=3)
three_line_table(
    doc,
    ["期刊", "档位", "JCR 分区", "中科院分区", "IF", "OA 情况"],
    [
        ["Digestive Diseases and Sciences", "主投", "Q2（胃肠肝病学，2025）", "医学 4 区（2025 升级版）", "2.8", "混合 OA；订阅路线零费用，彩图免费"],
        ["Clinical and Translational Oncology", "主投", "Q3（肿瘤学，2025）", "医学 4 区（2025 升级版）", "2.7", "混合 OA；订阅路线零费用"],
        ["Biochemical Genetics", "保底", "未核实（2025 IF 1.9）", "生物学 4 区（2025 升级版）", "1.9", "混合 OA；官方称无出版费"],
        ["Hepatobiliary & Pancreatic Diseases International", "冲刺", "Q2（胃肠肝病学，2025）", "医学 3 区（2025 升级版）", "3.9", "订阅制（Gold OA 占比约 0）"],
        ["Pathology - Research and Practice", "冲刺", "Q2（病理学，2025）", "医学 3 区（2026 新锐版）", "3.2 至 3.7", "混合 OA；订阅路线零费用"],
        ["Molecular Biology Reports", "保底", "Q3（生化与分子生物学，2025）", "生物学 4 区（2025 升级版）", "3.2", "混合 OA；订阅路线零费用"],
        ["Medical Oncology", "备选", "Q3（肿瘤学，2025）", "医学 4 区（2025 升级版）", "3.5", "混合 OA；订阅路线零费用"],
        ["Journal of Digestive Diseases", "备选", "Q3（2025）", "医学 3 区（2025，第三方）", "2.7", "混合 OA；官方接收率 8%"],
    ],
    widths=[3.6, 1.3, 2.9, 3.0, 1.3, 4.5],
    size=8, head_size=8,
    align_center=[False, True, True, True, True, False],
)

para(doc, "表 2　三阶段录用概率估计", bold=True, space=3)
three_line_table(
    doc,
    ["期刊", "适合吗", "够得着吗", "值得投吗", "送外审", "外审后接收", "总体接收", "置信度"],
    [
        ["Digestive Diseases and Sciences", "比较适合", "基本达到", "优先投稿", "55% 至 70%", "40% 至 50%", "20% 至 35%", "中"],
        ["Clinical and Translational Oncology", "比较适合", "基本达到", "优先投稿", "55% 至 70%", "40% 至 55%", "20% 至 40%", "中"],
        ["Biochemical Genetics", "高度适合", "基本达到", "值得投稿", "65% 至 80%", "50% 至 65%", "30% 至 50%", "中"],
        ["Hepatobiliary & Pancreatic Diseases International", "勉强适合", "边缘可尝试", "有条件尝试", "40% 至 55%", "25% 至 40%", "10% 至 20%", "中低"],
        ["Pathology - Research and Practice", "勉强适合", "边缘可尝试", "有条件尝试", "45% 至 60%", "35% 至 50%", "15% 至 30%", "中低"],
        ["Molecular Biology Reports", "勉强适合", "基本达到", "值得投稿", "45% 至 60%", "45% 至 60%", "20% 至 35%", "中"],
        ["Medical Oncology", "勉强适合", "边缘可尝试", "有条件尝试", "45% 至 60%", "40% 至 55%", "15% 至 30%", "低"],
        ["Journal of Digestive Diseases", "比较适合", "当前明显不足", "不建议投稿", "35% 至 50%", "15% 至 25%", "5% 至 10%", "中"],
    ],
    widths=[3.5, 1.5, 1.5, 1.6, 1.5, 1.7, 1.5, 1.2],
    size=8, head_size=8,
    align_center=[False, True, True, True, True, True, True, True],
)

para(doc, "概率口径说明：总体接收概率按「送外审概率乘以外审后接收概率」计算，并按 5% 或 10% 粒度取整，"
          "因此与两端相乘的精确值存在不超过 3 个百分点的差；已逐刊用乘法一致性校验，全部通过。", size=9)

# =============================== 三、逐刊决策卡 ==================================
h(doc, "三、逐刊决策卡", 1)

cards = [
    dict(
        name="1. Digestive Diseases and Sciences（DDS）　Springer　主投首选",
        verdict=[
            "适合吗：比较适合。刊物覆盖胃肠病学与肝病学的「基础与临床、结局研究」，肝细胞癌的预后研究属于其常规收稿范围。",
            "够得着吗：基本达到。以 2.8 影响因子、Q2（胃肠肝病学）的定位，本稿的报告规范与工作量高于该刊同类稿件的平均水平；短板是无实验验证。",
            "值得投吗：优先投稿。零费用、审稿快、彩图免费，且失败成本最低。",
        ],
        prob="送外审 55% 至 70%；外审后接收 40% 至 50%；总体接收 20% 至 35%；置信度中。证据类型：官方指标与流程数据 + 第三方自报竞争度。",
        up="上调因素：官方声明彩图免费印刷，本稿 6 张彩图不会产生额外费用；初审中位数 7 天、首轮审稿中位 30 天、总处理中位 42 天，周期可控；近三年中国作者发文量居第 2，对国人稿件接受度良好。",
        down="下调因素：该刊更偏好有明确临床问题的研究，纯登记库二次分析的比例不高；第三方自报接收率差异大（约 40% 与 77.8% 两种说法，后者样本仅 9 份），不可作为依据。",
        unc="最大不确定性：编辑部是否接受「无实验验证的方法学＋阴性结论」这一稿件类型，公开信息无法判断。",
        facts="指标：IF 2.8（2025 JCR）；JCR Q2（GASTROENTEROLOGY & HEPATOLOGY）；中科院 2025 年 3 月升级版医学 4 区、小类胃肠肝病学 4 区；2026 新锐分区医学 3 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA，OA 版面费 4390 美元，订阅路线不收费。"
              "要求（2026-10-04 据官方 Instructions for Authors 逐条核实）：Original Article 正文、图、表、文献均无上限；结构化摘要 ≤250 词（Background / Aims / Methods / Results / Conclusions 五段，按适用取舍）；关键词 4–6 个；"
              "题名原文「should not exceed 120 characters (not including spaces)」——上限口径不计空格，且写明「Do not use abbreviations in titles.」（题名不得用缩写）；"
              "摘要内不得使用文献引用；投稿须推荐 4–6 位审稿人；通讯作者须使用机构非商业邮箱。"
              "图件格式：原文只收「TIFF, GIF, JPEG, EPS, PPT, and Postscript」，并写明「PDF is not an acceptable file format for manuscripts or figures」——"
              "PDF 与 PNG 均不在收稿格式内，须用 EPS 或 TIFF。"
              "本稿已于 v1.7 将摘要由 296 词压至 238 词、关键词由 8 个减至 5 个，v1.8 将题名末词由 HCC 改为全称（113 字符，不计空格），v1.9 修毕正文引文上标与六处图内文字遮挡，v1.10 厘定单一作者署名（作者栏占位符清零），各项均已对齐；"
              "图件另备 EPS（矢量）与 TIFF（600 dpi）各 7 个，见交付目录 `图件_v2/投稿格式/`。来源与核验日期：Springer 官网、第三方期刊库，" + DATE + "。",
    ),
    dict(
        name="2. Clinical and Translational Oncology（CTO）　Springer　主投第二",
        verdict=[
            "适合吗：比较适合。刊物范围明确列出「癌症的诊断、预后与治疗」以及「数据科学与肿瘤政策分析」，本稿的预后模型验证正落在其中。",
            "够得着吗：基本达到。IF 2.7、JCR Q3、中科院医学 4 区，对报告规范好的验证类研究有稳定需求。",
            "值得投吗：优先投稿。零费用、初审快（官方中位 3 至 6 天）、国人发文居首。",
        ],
        prob="送外审 55% 至 70%；外审后接收 40% 至 55%；总体接收 20% 至 40%；置信度中。证据类型：官方指标与流程数据 + 第三方自报。",
        up="上调因素：官方期刊指标页给出「首次决定中位 6 天」，处理速度快；第三方自报审稿周期 1 至 3 个月、录用率约 50%（弱证据）；近三年中国作者发文量第一。",
        down="下调因素：该刊为西班牙肿瘤学会官方刊，稿源以临床与转化研究为主，纯计算类二次分析占比不高。作者指南（2026-10-04 核实）：Research Article 正文上限 3,000 词、图表合计不超过 6 项、文献不超过 30 条、摘要 ≤250 词且须为 Purpose / Methods-Patients / Results / Conclusions 四段。本稿为 5,970 词、14 个图表项、41 条文献，改投 CTO 须整体压缩或改写。",
        unc="最大不确定性：外审后接收概率的区间最宽（40% 至 55%），说明缺乏可靠的同类稿件参照。",
        facts="指标：IF 2.7（2025 JCR），五年 IF 2.9；JCR Q3；中科院 2025 年 3 月升级版医学 4 区、小类肿瘤学 4 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA，OA 版面费约 3690 欧元 / 4690 美元；订阅路线不收取 APC。"
              "要求：原创研究、综述、简要研究、通信。来源与核验日期：Springer 官网、第三方期刊库，" + DATE + "。",
    ),
    dict(
        name="3. Biochemical Genetics　Springer　保底首选（与稿件定位最契合）",
        verdict=[
            "适合吗：高度适合。该刊官方范围明确包含「方法学文章」，并写明当计算方法被完整描述、且与现有基准方法充分比较与验证时予以考虑——本稿正是「完全嵌套交叉验证 + pooled out-of-fold 估计 + 多个随机划分 + 随机面板基准」的验证研究。",
            "够得着吗：基本达到。IF 1.9、生物学 4 区，门槛与稿件水平匹配；短板是该刊影响力有限。",
            "值得投吗：值得投稿。零费用、范围契合度最高，被拒风险最低，适合作为「必须投出去」的兜底。",
        ],
        prob="送外审 65% 至 80%；外审后接收 50% 至 65%；总体接收 30% 至 50%；置信度中。证据类型：官方范围与收费声明 + 第三方指标。",
        up="上调因素：官方明文「There are no publication charges except for special services」，订阅路线确定零费用；首次决定中位仅 5 天；官方欢迎经过基准验证的计算方法学文章。",
        down="下调因素：官方同时声明不考虑「仅具狭窄适用性的描述性研究」，因此封面信与摘要必须把方法学主张前置，不能以「发现新签名」为卖点；JCR 分区在第三方来源中缺失。",
        unc="最大不确定性：该刊对「阴性复制」这一结论本身的态度，官方范围未直接涉及；现有描述性研究的排除条款是主要风险。",
        facts="指标：IF 1.9（2025 JCR），五年 IF 2.0；中科院 2025 年 3 月升级版生物学 4 区、小类生化与分子生物学 4 区、遗传学 4 区；JCR 分区未核实。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA，订阅路线无出版费（期刊官网明文）。"
              "要求：原创研究、方法学文章、综述；年发文量约 380 篇。来源与核验日期：Springer 官网，" + DATE + "。",
    ),
    dict(
        name="4. Hepatobiliary & Pancreatic Diseases International（HBPD INT）　冲刺档",
        verdict=[
            "适合吗：勉强适合。刊物为中国主办（浙江大学医学院附属第一医院）、Elsevier 出版，覆盖肝胆胰疾病的临床与研究，肝细胞癌属其核心领域；但其稿件以临床研究为主，纯计算类二次分析占比低。",
            "够得着吗：边缘可尝试。中科院医学 3 区（小类 4 区）、IF 3.9，是本报告中分区最高的零费用选项，但年发文量仅约 61 篇。",
            "值得投吗：有条件尝试。若希望拿到更高的中科院分区，值得用一轮时间试投；被拒后转投 DDS 或 CTO 的损失可接受。",
        ],
        prob="送外审 40% 至 55%；外审后接收 25% 至 40%；总体接收 10% 至 20%；置信度中低。证据类型：官方范围与收录 + 第三方指标与自报审稿周期。",
        up="上调因素：中科院医学 3 区，在多数国内单位认定中优于 4 区期刊；中国主办，对国内稿件沟通成本低；Gold OA 文章占比接近 0，说明以订阅模式为主，不存在版面费压力。",
        down="下调因素：年发文量小（约 61 篇），录用名额有限；第三方自报平均审稿约 3 个月且偏慢；临床研究偏好使纯生物信息学稿件的送审率下降。",
        unc="最大不确定性：该刊是否在编辑初筛阶段直接排除无实验验证的生物信息学稿件。",
        facts="指标：IF 3.9（2025 JCR），五年 IF 3.4；JCR Q2（GASTROENTEROLOGY & HEPATOLOGY，个别来源报 Q1，未取官方确认）；"
              "中科院 2025 年 3 月升级版医学 3 区、小类胃肠肝病学 4 区；2026 新锐分区医学 2 区。自引率约 5% 至 7%。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：订阅制，Gold OA 占比约 0，无 APC 记录。"
              "要求：关于肝胆胰疾病临床与研究的原创论文、综述、社论；双月刊。来源与核验日期：第三方期刊库与 SCI 查询站，" + DATE + "。",
    ),
    dict(
        name="5. Pathology - Research and Practice（PRP）　冲刺档",
        verdict=[
            "适合吗：勉强适合。刊物聚焦肿瘤分子机制与临床病理，本稿的突变谱、肿瘤与正常肝表达比较可与其读者对接，但「预后模型验证」不是其主线。",
            "够得着吗：边缘可尝试。中科院医学 3 区、IF 3.2 至 3.7，门槛高于本稿的天然定位。",
            "值得投吗：有条件尝试。仅在追求中科院 3 区时考虑。",
        ],
        prob="送外审 45% 至 60%；外审后接收 35% 至 50%；总体接收 15% 至 30%；置信度中低。证据类型：官方流程数据 + 第三方自报（含负面案例）。",
        up="上调因素：首次决定中位 2 天、接受后 1 天上线，流程极快；订阅路线零版面费；中国作者发文占比约 48%。",
        down="下调因素：多个投稿者自报该刊长期找不到审稿人，出现等待 6 个月后被拒的案例（弱证据，样本小而偏倚明显，但方向一致）；稿件量偏大而审稿人储备不足。",
        unc="最大不确定性：审稿人获取能力。这直接决定「6 至 12 个月内见刊」这一约束能否满足。",
        facts="指标：IF 3.2 至 3.7（不同来源与年份，未取官方确认）；JCR 病理学 Q2（第三方）；中科院 2026 年 3 月新锐分区医学 3 区、病理学 3 区。"
              "收录：SCIE、MEDLINE。出版模式：混合 OA，订阅路线无版面费；OA 版面费第三方报 2570 至 3200 美元（来源冲突，未取官方确认）。"
              "来源与核验日期：Elsevier 期刊页第三方转述、第三方期刊库，" + DATE + "。",
    ),
    dict(
        name="6. Molecular Biology Reports（MBR）　保底第二",
        verdict=[
            "适合吗：勉强适合。刊物为普通分子生物学刊，年发文量大、收稿面宽，但对投稿有「必须包含分子或细胞生物学实验技术」的方法学要求。",
            "够得着吗：基本达到。IF 3.2、JCR Q3、中科院生物学 4 区（2026 新锐版生物学 3 区），发文量大、命中率相对高。",
            "值得投吗：值得投稿，但须先解决范围门槛。",
        ],
        prob="送外审 45% 至 60%；外审后接收 45% 至 60%；总体接收 20% 至 35%；置信度中。证据类型：官方要求与收费声明 + 第三方指标。",
        up="上调因素：订阅路线无需版面费（多来源一致，与 Springer 混合刊模式一致）；首次决定中位 3 天；投稿至接收中位约 91 天；年发文量 700 篇以上。",
        down="下调因素：官方要求投稿必须包含分子或细胞生物学实验技术，本稿为纯计算分析，存在被编辑以范围不符直接退回的风险；第三方自报平均审稿可达 6 个月。",
        unc="最大不确定性：范围条款的执行严格程度。若严格执行，本稿可能在初筛即被退回。",
        facts="指标：IF 3.2（2025 JCR），五年 IF 3.2；JCR Q3（BIOCHEMISTRY & MOLECULAR BIOLOGY，185/328）；中科院 2025 年 3 月升级版生物学 4 区、小类生化与分子生物学 4 区；2026 新锐分区生物学 3 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA，OA 版面费约 2890 英镑 / 4290 美元；订阅路线无 APC。"
              "来源与核验日期：Springer 官网、第三方期刊库，" + DATE + "。",
    ),
    dict(
        name="7. Medical Oncology　备选",
        verdict=[
            "适合吗：勉强适合。刊物覆盖肿瘤学与血液学的临床与实验研究，但对稿件类型有限制。",
            "够得着吗：边缘可尝试。IF 3.5、JCR Q3、中科院医学 4 区。",
            "值得投吗：有条件尝试。投前必须先向编辑部确认回顾性二次分析是否在收稿范围内。",
        ],
        prob="送外审 45% 至 60%；外审后接收 40% 至 55%；总体接收 15% 至 30%；置信度低。证据类型：官方收费声明 + 第三方转述（存在未取证的排除条款）。",
        up="上调因素：订阅路线无 APC（官方明文）；首次决定中位约 5 天；投稿至接收第三方自报约 2 至 3 个月。",
        down="下调因素：第三方资料称该刊不考虑病例报告与回顾性研究。本稿虽非病例报告，但属回顾性二次分析，若该条款属实将被初筛排除。此说法未在官方作者指南中直接核实。",
        unc="最大不确定性：上述排除条款是否适用于本稿，且是否仍然有效。核实前不宜投出。",
        facts="指标：IF 3.5（2025 JCR）；JCR Q3；中科院 2025 年 3 月升级版医学 4 区、小类肿瘤学 4 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA，OA 版面费约 4290 美元；订阅路线无 APC（Springer 官方收费说明）。"
              "来源与核验日期：Springer 官网与第三方期刊库，" + DATE + "。",
    ),
]

for c in cards:
    h(doc, c["name"], 2)
    para(doc, "三问结论", bold=True, size=10, space=2)
    for v in c["verdict"]:
        bullet(doc, v)
    para(doc, "三阶段概率：" + c["prob"], size=10, space=3)
    para(doc, "上调与下调因素：" + c["up"] + " " + c["down"], size=10, space=3)
    para(doc, "最大不确定性：" + c["unc"], size=10, space=3)
    para(doc, "指标、收录、费用与要求：" + c["facts"], size=9.5, space=8)

# =============================== 四、论文诊断 ====================================
h(doc, "四、论文诊断", 1)

para(doc, "核心贡献：把「稳定性选择能否保证外部可运输性」这一统计问题，落到一个具体的人类肿瘤队列上，并给出否定的答案；"
          "同时用完全嵌套交叉验证与 pooled out-of-fold 估计说明：两基因与二十三基因的判别力差异在诚实口径下测不出来。"
          "这一结论对大量采用「LASSO + 稳定性选择 + 一个外部队列」模板的稿件具有直接的方法学含义。")

para(doc, "优势：① 报告规范完备，TRIPOD 与 TRIPOD+AI 清单随稿；② 主口径为完全嵌套交叉验证，且用十个独立随机划分给出离散度，"
          "并给出 optimism 的 bootstrap 置信区间；③ 补做了校准斜率、时间依赖 Brier、IBS 与 Schoenfeld 比例风险诊断；"
          "④ 多重比较同时给出 BH 与依赖稳健的 BY 校正；⑤ 阴性结果与阳性结果同等篇幅报告；⑥ 数据、代码、随机种子与复现步骤齐备。")

para(doc, "关键短板：① 无任何湿实验验证，抗风险能力全部来自统计学；② 未校正肿瘤纯度，而纯度是这类免疫与突变分析最典型的混杂；"
          "③ 只有总生存终点，无无复发生存或至复发时间；④ 两基因分数中 MAFG 的稳定性频率处在阈值边缘（10 个种子中 2 个跌破 0.75），"
          "使「两基因」的确定性打了折扣；⑤ 面板来源为同一团队未发表的姊妹分析，虽已声明本稿为独立复现，仍可能被质疑循环性。")

para(doc, "初筛风险：最大风险是编辑把稿件误读为「又一个失败的 TCGA 签名」，从而以缺乏新颖性退稿。"
          "对策是把标题、摘要首句与封面信三者统一到方法学主张上，并在封面信中明写「本文不主张该分数具有临床用途」。")

para(doc, "外审风险：统计审稿人会追问两个点——随机面板基准是否只用了表观拟合（本稿已声明它不 price 选择步骤，属已披露）；"
          "MAFG 阈值边缘如何影响「两基因」主张（本稿已给出二项标准误与单边检验，属已量化）。"
          "临床审稿人会追问阴性结论的临床含义（本稿已限定结论仅对总生存成立，未外推至复发预测）。")

para(doc, "报告规范：已达到多数 3 至 4 区期刊的要求，无需补做。")

para(doc, "当前天花板与改进后层级：在现有数据条件下（无湿实验、无纯度列、无复发终点），"
          "本稿的现实天花板是 3 至 4 区、影响因子 2 至 4 的期刊；"
          "若补上肿瘤纯度校正（TCGA PanCanAtlas 公开 ABSOLUTE 纯度按条形码对齐，属公开数据，无需实验），"
          "并在讨论中把纯度敏感性作为独立小节呈现，稿件在同类期刊中的竞争力会明显上升，但不足以跨入 2 区。")

# =============================== 五、投稿路径 ====================================
h(doc, "五、投稿路径", 1)

para(doc, "推荐顺序（零费用口径，全部走订阅出版路线）：")
para(doc, "首投：Digestive Diseases and Sciences。理由：肝病学在范围内、JCR Q2、零费用、彩图免费、官方流程数据完整（初审 7 天、总处理中位 42 天），"
          "且失败成本最低。", indent=0.5)
para(doc, "第二选择：Clinical and Translational Oncology。理由：肿瘤学专业刊，范围明列预后评估与数据科学；初审 3 至 6 天，周期最短。", indent=0.5)
para(doc, "第三选择：Biochemical Genetics。理由：与「方法学验证」定位契合度最高，官方欢迎经过基准验证的计算方法学文章，被拒风险最小。", indent=0.5)
para(doc, "冲刺（可选）：Hepatobiliary & Pancreatic Diseases International。仅在需要中科院医学 3 区时使用；被拒后转回 DDS 或 CTO。", indent=0.5)
para(doc, "时间紧时的替代：直接投 CTO，或投 Molecular Biology Reports（须先解决范围门槛）。", indent=0.5)

para(doc, "转投时的调整要点：① 标题与摘要主句保持方法学定位不变，仅按刊物读者调整用词（肿瘤学刊保留 mitoxyperilysis 相关表述；"
          "分子生物学刊改为通用「预后模型外部队列验证」表述）；② 正文长度按目标刊物上限压缩，压缩时优先下沉方法细节到补充材料，"
          "不得删除任何数值（本稿已有机械闸门保证数值不丢失）；③ 图表数量按刊物限制合并，DDS 与 CTO 允许的图表数较宽松，MBR 与 BG 需更紧；"
          "④ 参考文献格式按刊物要求转换；⑤ 封面信必写三句：本文是什么、本文不主张什么、本文的统计口径为何优于同类稿件；"
          "⑥ 随稿清单应包括 TRIPOD 清单、数据可得性声明、代码可得性声明与阴性结果声明。")

# =============================== 六、不推荐清单 ==================================
h(doc, "六、不推荐清单", 1)

not_reco = [
    ("Journal of Cancer Research and Clinical Oncology", "该刊自 2024 年 1 月 4 日起转为完全开放获取，版面费约 2790 英镑 / 4390 美元，远超 2000 元预算；在其转为全 OA 之前，它本会是本稿最合适的候选之一。"),
    ("Cancer Biomarkers", "该刊自 2024 年 1 月起转为金色开放获取，版面费 2800 美元，超出预算。范围本身与「标志物验证」高度契合，是预算造成的最大机会损失。"),
    ("Gene", "订阅路线虽免费，但刊物范围以基因功能与进化为主，与本稿的模型验证主题偏离；且官方公布接收率仅 8%，被拒时间成本高。"),
    ("Journal of Digestive Diseases", "官方公布 2025 年接收率 8%，且投稿至接收中位 146 天，与「6 至 12 个月见刊」的约束叠加后风险偏高；虽中国作者占比 68%，仍不改变初筛通过率的量级。"),
    ("International Journal of Biological Markers", "范围契合，但该刊已被第三方标记为开放获取出版、版面费 2800 美元，超出预算；且年发文量仅约 29 篇，录用名额极为有限。多数第三方站点把其收录标注为 SCIE，个别标注为 ESCI，收录层级存在冲突，未核实。"),
    ("Frontiers、MDPI、PLOS、PeerJ、Scientific Reports 等完全开放获取平台", "版面费区间约 1500 至 3000 美元以上，全部超出 2000 元预算；其中 PeerJ 属最低档，仍在预算的三倍以上。"),
    ("以「新型预后标志物」为定位的 1 至 2 区肿瘤学期刊", "本稿的核心结论是外部阴性复制，与这类期刊对「新发现」的期待直接冲突；投过去大概率在编辑初筛被退，白白消耗时间。"),
    ("临床医学 1 至 2 区的肝病学期刊", "同上，且通常要求前瞻队列或实验验证，本稿不具备。"),
]
for name, why in not_reco:
    para(doc, name, bold=True, size=10, space=1)
    para(doc, why, size=9.5, indent=0.5, space=5)

# =============================== 七、不确定性与来源 ==============================
h(doc, "七、不确定性与来源", 1)

para(doc, "判断依据的层级：本报告对稿件的判断基于全文（非摘要），因此概率区间按全文口径给出，未额外放宽。"
          "期刊的动态信息（分区、影响因子、收录、费用、周期）全部来自公开检索，核验日期均为 %s；"
          "其中期刊官网与出版社页面属第一层级来源，第三方期刊数据库与分区榜单属第二、三层级来源。" % DATE)

para(doc, "已核验字段：各刊的出版模式与收费口径、影响因子与年份、首次决定与接收周期、收录数据库、范围表述，多数来自期刊官网或出版社页面。")

para(doc, "未核实字段：① Biochemical Genetics 的 JCR 分区（第三方仅给出影响因子 1.9）；"
          "② PRP 的准确影响因子与官方版面费（第三方来源给出 3.2 至 3.7 与 2570 至 3200 美元两组冲突数值）；"
          "③ HBPD INT 的 JCR 分区（第三方来源在 Q1 与 Q2 之间冲突）；"
          "④ Medical Oncology 关于「不考虑回顾性研究」的条款；"
          "⑤ 各中文数据库站点给出的中科院分区属第三方转述，最终应以单位订购的分区表为准。")

para(doc, "统计与估计的区分：本报告未获得任何期刊针对本稿件的官方数据。"
          "表 2 的三阶段概率为结构化专家估计，其依据是各刊的公开流程数据、范围适配度与近年发文特征；"
          "除 Journal of Digestive Diseases 的 8% 与 Gene 的 8% 属官方公布接收率外，其余数值均不得当作期刊真实统计录用率使用。"
          "第三方投稿者自报数据仅作方向参考：Medical Oncology 与 DDS 的接收率自报样本分别极小，已按弱证据处理。")

para(doc, "预算口径：本报告的「2000 元」按约 280 美元换算。汇率波动会改变可投池的边界，"
          "但不足以把任何一本完全开放获取的英文期刊纳入预算内——现查到的最低档英文 OA 期刊仍在 1395 美元以上。", )

para(doc, "主要来源（按访问顺序）：")
for label, url in [
    ("Springer 期刊官网（DDS / CTO / Biochemical Genetics / Molecular Biology Reports / Medical Oncology）", "https://link.springer.com"),
    ("Elsevier 期刊官网（Gene / Pathology - Research and Practice 的期刊洞察页）", "https://www.sciencedirect.com"),
    ("Hepatobiliary & Pancreatic Diseases International 官网", "https://www.hbpdint.com"),
    ("Wiley 期刊指标页（Journal of Digestive Diseases）", "https://onlinelibrary.wiley.com/journal/17512980/journal-metrics"),
    ("IOS Press 关于 Cancer Biomarkers 转为金色开放获取的公告", "https://www.iospress.com/news/cancer-biomarkers-transitioned-to-gold-open-access-in-2024"),
    ("DOAJ 期刊记录（用于核对完全开放获取与 APC）", "https://doaj.org"),
]:
    source_line(doc, label + "：", url)

# =============================== 八、隐私说明 ====================================
h(doc, "八、隐私说明", 1)

para(doc, "本报告的稿件解析、质量判断、概率估计、报告生成与校验全部在本机完成。"
          "联网检索仅用于查询公开的期刊信息，检索词只包含期刊名称、公开数据库字段与概括性的学科词；"
          "未向任何外部检索服务、API、云盘或第三方工具提交稿件全文、摘要原句、未发表结果、作者身份、单位或其他可回溯到本稿件的独特表述。"
          "本技能无法控制宿主平台或模型提供商自身的日志、遥测、同步与数据保留政策，使用者仍需依据所在平台与机构政策判断是否适合处理该材料。",
     size=9.5)

doc.save(OUT)
print("OK ->", OUT)
