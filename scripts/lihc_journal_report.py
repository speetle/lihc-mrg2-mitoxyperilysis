#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIHC 择刊测评报告 v2（2026-10-06 复核）—— 生成 Word。

相对 v1（2026-10-04）的变更，全部来自本轮联网重核：
  · 约束升级：预算由「<2000 元」改为「0 元」，时间约束写明「1 年内接收」；
  · Digestive and Liver Disease 已于 2026-01-01 转为完全金色 OA（APC 2,960 美元）→ 移出零费用池；
  · 各刊 IF 与分区统一改用 2025 JCR（2026 年 6 月发布）官方口径；
  · 新增 Pathology - Research and Practice 与 Medical Oncology 的官方流程/费用数据；
  · 新增同类论文实证（DDS 两篇 HCC 基因签名预后模型、PRP 一篇 HCC 预后签名）；
  · 新增官方接收率：Clinics and Research in Hepatology and Gastroenterology 12%（据以移入不推荐清单）。

生成后须跑 skills/biomedical-journal-selector/scripts/report_check.py 并逐页渲染核验。
"""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "归档_过程性文件", "择刊测评报告_20261006.docx")
DATE = "2026-10-06"


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

    for row in t.rows:
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
r = tp.add_run("LIHC 肝细胞癌稿件择刊测评报告（第二轮·零费用约束复核）")
r.font.color.rgb = RGBColor(0, 0, 0)
r.font.size = Pt(16)
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
sub.add_run(
    "测评日期：%s　｜　测评对象：Manuscript_LIHC_v1.12（正文 5,970 词 / 摘要 238 词 / 题名 113 字符（不计空格）"
    "/ 41 条参考文献 / 6 图 8 表 / 补充材料 S1–S16 + S4b + S10b + TRIPOD 清单）" % DATE
).font.size = Pt(9.5)
sub2 = doc.add_paragraph()
sub2.alignment = WD_ALIGN_PARAGRAPH.LEFT
sub2.add_run(
    "投出约束（本次新增）：① 出版费用 0 元人民币，即完全不支付任何版面费或文章处理费；② 自投稿之日起 1 年内获得接收决定。"
).font.size = Pt(9.5)

# =============================== 一、核心结论 =====================================
h(doc, "一、核心结论", 1)

para(doc, "文章类型与主题：基于公共数据的二次分析（生物信息学），以「方法学 ＋ 外部阴性复制」为定位的预后模型验证研究。"
          "数据为 TCGA-LIHC 发现队列（n = 360，129 例死亡）＋两个外部队列（GSE14520，n = 242、96 例死亡；GSE76427，n = 115、23 例死亡）。"
          "核心主张不是「发现了一个新标志物」，而是「稳定性选择压缩出的两基因分数在独立队列中不复制，且两基因与二十三基因在诚实口径下不可区分」。")

para(doc, "质量定位：报告规范（TRIPOD / TRIPOD+AI 清单、完全嵌套交叉验证、pooled out-of-fold 估计、校准、比例风险诊断、多重校正、"
          "数据与代码可得性）明显高于同类 TCGA 签名稿的平均水平；短板是无湿实验验证、无肿瘤纯度校正、无复发终点，"
          "且唯一的外部队列是阴性结论，无法用实验补强。因此本稿的价值在方法与诚信，不在发现的新颖性。")

para(doc, "适合层级：适合「方法学 / 阴性复制 / 预后模型验证」定位的 3 至 4 区肿瘤学或消化肝病学期刊；"
          "不适合以「新型预后标志物」为卖点的 1 至 2 区肿瘤学期刊。")

para(doc, "首要结论（本报告最重要的一条）：在「0 元」硬约束下，可投池只剩两类——"
          "① 混合开放获取（OA）期刊的订阅出版路线，作者不选择开放获取、由读者或机构付费阅读，从而零出版费用；"
          "② 纯订阅制期刊。凡完全金色 OA 的期刊一律出局，无论其分区高低。"
          "上一版报告按「2000 元」口径撰写，本次按「0 元」重核后，可投池的边界没有变宽，只有变窄："
          "本轮又查出 Digestive and Liver Disease 已于 2026 年 1 月 1 日转为完全金色 OA（文章处理费 2,960 美元），"
          "不能再计入零费用池。", bold=False)

para(doc, "首选与投稿顺序：首投 Digestive Diseases and Sciences（DDS，与上一版一致）；"
          "第二 Pathology - Research and Practice（PRP）；第三 Medical Oncology（MO）；"
          "冲刺档 Hepatobiliary & Pancreatic Diseases International（HBPD INT，费用状态须先问清）；"
          "保底 Biochemical Genetics（BG）；兜底 Molecular Biology Reports（MBR）或 Indian Journal of Gastroenterology（IJG）。")

para(doc, "本轮相对上一版的三处实质变化："
          "① DDS 仍是首投，且本轮查到两份直接同类论文（该刊 2025 至 2026 年已刊出 HCC 基因签名预后模型研究），契合度由推断变为实证；"
          "② 新增 PRP 为第二选择——官方订阅路线明文不收费、初审 4 天、投稿至接收 92 天，是本报告中「分区较高且到接收最快」的组合，"
          "且该刊 2026 年已刊出 HCC 预后签名论文；"
          "③ Medical Oncology 的 2025 影响因子升至 4.7、中科院 2026 新锐分区医学 3 区，成为零费用池中影响力最高的选项，"
          "但其官方限 Original Article 5,000 词 / 45 条文献 / 6 个图表项，本稿（5,970 词 / 41 文献 / 14 个图表项）须先压缩合并。")

para(doc, "最大风险：① 编辑初筛时把稿件读成「又一个 TCGA 预后签名加一次失败的外部验证」，从而以「缺乏新颖性 / 仅描述性」为由直接退稿；"
          "② 目标期刊对「二次分析 / 回顾性研究」有隐性排除；"
          "③ 图件与补充材料体量偏大（6 图 8 表加 20 项补充材料），部分期刊有篇幅硬限；"
          "④ 个别目标刊的出版模式正在变动（本轮已实测到一例由订阅转全 OA），投前须复核当期刊面政策。")

para(doc, "最值得先改的三项：① 投稿信第一句就把「这是方法学论文，不是标志物发现」说清楚，并点名摘要里的方法学结论；"
          "② 若改投对篇幅有硬限的刊物（Medical Oncology 5,000 词、Clinical and Translational Oncology 3,000 词），"
          "优先把方法细节下沉到补充材料，不得删除任何数值（本稿已有机械闸门保证数值不丢失）；"
          "③ 把「两基因与二十三基因在诚实口径下不可区分」这一条提到讨论最前面——当前已在摘要，但讨论中仍被外部阴性叙述盖住。")

# =============================== 二、概率声明与总览 ===============================
h(doc, "二、概率声明与概率总览", 1)

para(doc, "录用概率是决策辅助估计，不是期刊官方承诺或录用保证。除非特别注明，它综合稿件质量、研究类型、主题适配、期刊选择性、"
          "近期发文特征和可获得的公开信息。编辑判断、审稿意见、同期竞争、特刊安排及政策变化都可能使实际结果明显偏离估计。",
     size=9.5, italic=True)

para(doc, "下列各期刊均未公开足以支撑个体稿件概率的官方送审率或接收率数据；下列数值属于结构化专家估计，"
          "不能作为该期刊真实统计录用率使用，也不得与期刊总体接受率混淆。个别期刊的官方接收率已单独标注。",
     size=9.5, italic=True)

para(doc, "表 1　期刊信息（分区、影响因子与出版模式）", bold=True, space=3)
three_line_table(
    doc,
    ["期刊", "档位", "JCR 分区", "中科院分区", "IF", "OA 情况"],
    [
        ["Digestive Diseases and Sciences", "主投·首投", "Q2（胃肠肝病学，2025）",
         "2025 升级版医学 4 区；2026 新锐医学 3 区", "2.8", "混合 OA；订阅路线零费用（官方）"],
        ["Pathology - Research and Practice", "主投·第二", "Q1（病理学，2025 至 2026，按 JCI）",
         "2025 升级版医学 4 区、病理学 3 区；2026 新锐医学 3 区", "3.7", "混合 OA；官方明文订阅路线不向作者收费"],
        ["Medical Oncology", "主投·第三", "Q2（肿瘤学，2025 至 2026，按 JCI）",
         "2025 升级版医学 4 区；2026 新锐医学 3 区", "4.7", "混合 OA；订阅路线零费用（官方）"],
        ["Clinical and Translational Oncology", "备选", "Q3（肿瘤学，2025）",
         "2025 升级版医学 4 区；2026 新锐医学 3 区", "2.7", "混合 OA；订阅路线零费用（官方）"],
        ["Molecular Biology Reports", "备选", "Q3（生化与分子生物学，2025）",
         "2025 升级版生物学 4 区；2026 新锐生物学 3 区", "3.2", "混合 OA；订阅路线零费用（官方）"],
        ["Hepatobiliary & Pancreatic Diseases International", "冲刺", "Q2（胃肠肝病学，第三方，未取官方确认）",
         "2025 升级版医学 3 区、小类胃肠肝病学 4 区", "3.9", "订阅与 OA 状态来源冲突，费用未核实"],
        ["Biochemical Genetics", "保底", "未核实（第三方未给出分区）",
         "2025 升级版生物学 4 区、生化与分子生物学 4 区", "1.9", "混合 OA；官方明文无出版费"],
        ["Indian Journal of Gastroenterology", "保底", "Q3（胃肠肝病学，2025）",
         "2026 新锐医学 4 区", "2.5", "混合 OA；订阅路线零费用（官方）"],
    ],
    widths=[3.4, 1.5, 3.0, 3.6, 1.0, 3.7],
    size=8, head_size=8,
    align_center=[False, True, True, False, True, False],
)

para(doc, "表 2　三阶段录用概率估计", bold=True, space=3)
three_line_table(
    doc,
    ["期刊", "适合吗", "够得着吗", "值得投吗", "送外审", "外审后接收", "总体接收", "置信度"],
    [
        ["Digestive Diseases and Sciences", "比较适合", "基本达到", "优先投稿", "55% 至 70%", "40% 至 50%", "20% 至 35%", "中"],
        ["Pathology - Research and Practice", "比较适合", "基本达到", "优先投稿", "45% 至 60%", "35% 至 50%", "15% 至 30%", "中低"],
        ["Medical Oncology", "勉强适合", "边缘可尝试", "有条件尝试", "45% 至 60%", "35% 至 50%", "15% 至 30%", "中低"],
        ["Clinical and Translational Oncology", "比较适合", "基本达到", "有条件尝试", "55% 至 70%", "40% 至 55%", "20% 至 40%", "中"],
        ["Molecular Biology Reports", "勉强适合", "基本达到", "值得投稿", "40% 至 55%", "45% 至 60%", "20% 至 35%", "中低"],
        ["Hepatobiliary & Pancreatic Diseases International", "勉强适合", "边缘可尝试", "有条件尝试", "40% 至 55%", "25% 至 40%", "10% 至 20%", "中低"],
        ["Biochemical Genetics", "高度适合", "基本达到", "值得投稿", "65% 至 80%", "50% 至 65%", "30% 至 50%", "中"],
        ["Indian Journal of Gastroenterology", "勉强适合", "基本达到", "值得投稿", "55% 至 70%", "45% 至 60%", "25% 至 40%", "低"],
    ],
    widths=[3.5, 1.5, 1.5, 1.6, 1.5, 1.7, 1.5, 1.2],
    size=8, head_size=8,
    align_center=[False, True, True, True, True, True, True, True],
)

para(doc, "概率口径说明：总体接收概率按「送外审概率乘以外审后接收概率」计算，并按 5% 或 10% 粒度取整，"
          "因此与两端相乘的精确值存在不超过 3 个百分点的差；本报告 8 本候选已逐本用乘法一致性校验，全部通过。"
          "时间为条件约束而非概率因子：表中「送外审 45% 至 60%」一类的数值，指的是到稿后 1 年内完成「投稿—审稿—接收」全流程的概率，"
          "已把各刊公开的流程中位数计入判断。", size=9)

# =============================== 三、逐刊决策卡 ==================================
h(doc, "三、逐刊决策卡", 1)

cards = [
    dict(
        name="1. Digestive Diseases and Sciences（DDS）　Springer　主投·首投",
        verdict=[
            "适合吗：比较适合。刊物覆盖胃肠病学与肝病学的基础、转化与临床研究，肝细胞癌预后研究属常规收稿范围。"
            "本轮已查到两份直接同类论文：该刊 2026 年刊出「核糖体生物发生相关基因构建 HCC 风险预测模型」"
            "（doi 10.1007/s10620-026-09787-9，PMID 41774333），2025 年刊出「铜死亡相关预后签名：生物信息学与体外分析」"
            "（doi 10.1007/s10620-025-09354-8，PMID 40866730）。契合度由此前的外推改为实证。",
            "够得着吗：基本达到。以影响因子 2.8、JCR Q2（胃肠肝病学）的定位，本稿的报告规范与工作量高于该刊同类稿件的平均水平；短板依旧是无实验验证。",
            "值得投吗：优先投稿。零费用、彩图不另收费、初审中位 7 天，且整包投稿件（EPS 图件、12 磅双倍行距稿件、图形摘要、审稿人名单）"
            "已按该刊要求做完并逐件校验，改投他刊都需返工，唯独投它零返工。",
        ],
        prob="送外审 55% 至 70%；外审后接收 40% 至 50%；总体接收 20% 至 35%；置信度中。证据类型：官方指标与流程数据 ＋ 官方同类论文实证。",
        up="上调因素：官方期刊页给出「投稿至首次决定中位 7 天」；订阅路线零费用（官方期刊页出版模式标为 Hybrid）；"
           "本稿全部硬要求（题名 113 字符不计空格且无缩写、摘要 238 词、关键词 5 个、正文图表文献均无上限、矢量图字体已嵌入）已逐条对齐，"
           "不存在因格式被退回的风险。",
        down="下调因素：该刊更偏好有明确临床问题的研究，纯公共数据库二次分析占比不高；"
             "第三方自报接收率在约 40% 与 77.8% 之间分歧（后者样本仅 9 份），按弱证据处理，不作为依据。",
        unc="最大不确定性：编辑部是否接受「无实验验证的方法学加阴性结论」这一稿件类型，公开信息无法判断。",
        facts="指标：影响因子 2.8、五年影响因子 3.0（均 2025 JCR，Springer 官方期刊页，核验 %s）；"
              "JCR Q2（GASTROENTEROLOGY & HEPATOLOGY）；中科院 2025 年 3 月升级版医学 4 区、小类胃肠肝病学 4 区；2026 新锐分区医学 3 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA；订阅路线零费用，开放获取路线按刊面另计。"
              "官方要求：题名不超过 120 字符（不计空格）且不得使用缩写；结构化摘要不超过 250 词；关键词 4 至 6 个；"
              "Original Article 的正文、图、表、文献均无上限；投稿须推荐 4 至 6 位审稿人；通讯作者须使用机构邮箱；"
              "图件只收 TIFF、GIF、JPEG、EPS、PPT 与 Postscript，明确写明 PDF 不是可接受的稿件或图件格式。"
              "来源与核验日期：Springer 官方期刊页、该刊官方 Instructions for Authors（2022-09-01 版）、Europe PMC，%s。" % (DATE, DATE),
    ),
    dict(
        name="2. Pathology - Research and Practice（PRP）　Elsevier　主投·第二",
        verdict=[
            "适合吗：比较适合。该刊主题领域为肿瘤研究、分子医学、肿瘤学与病理学，"
            "2026 年已刊出 HCC 预后签名论文「以 R-loop 评分定义的共识亚型与可泛化预后签名：多组学分析」"
            "（doi 10.1016/j.prp.2026.156656，PMID 42636674），证明其接收本类稿件；"
            "但该文附体外验证，本稿无实验部分，故按「比较适合」而非「高度适合」。",
            "够得着吗：基本达到。影响因子 3.7，按 JCI 计为 Q1（病理学），中科院 2026 新锐分区医学 3 区、病理学 3 区。",
            "值得投吗：优先投稿。官方明文订阅路线不向作者收费，正向满足 0 元约束；"
            "官方流程数据是本报告中「分区较高且到接收最快」的组合（初审 4 天、审稿后决定 47 天、投稿至接收 92 天），"
            "并另有一条 2 天由接收上线，与 1 年内接收的约束高度兼容。",
        ],
        prob="送外审 45% 至 60%；外审后接收 35% 至 50%；总体接收 15% 至 30%；置信度中低。证据类型：官方流程与收费数据 ＋ 官方同类论文实证。",
        up="上调因素：官方期刊洞察页把订阅路线写成「不向作者收取出版费，文章即时向订阅者开放」；"
           "投稿至接收中位 92 天，接受后 2 天上线，是本报告候选中最快的一组；"
           "中国作者在该刊发文量占比高，对国内作者沟通成本低。",
        down="下调因素：该刊以病理形态学与临床病理关联为主线，纯计算类二次分析不是主线；"
             "多个投稿者自报该刊审稿人储备不足，出现等待数月后被拒的案例（弱证据，样本小、幸存者偏倚明显，但方向一致）。",
        unc="最大不确定性：审稿人获取能力。若出现长期找不到审稿人的情形，1 年内接收这一约束会被直接击穿。",
        facts="指标：影响因子 3.7（Elsevier 官方期刊洞察页，核验 %s）；JCR 病理学 Q1（按 JCI，2025 至 2026 版，第三方汇总）；"
              "中科院 2025 年 3 月升级版医学 4 区、小类病理学 3 区；2026 新锐分区医学 3 区、病理学 3 区。"
              "收录：MEDLINE、SCIE。出版模式：支持开放获取（作者可选），开放获取文章处理费 3,200 美元；"
              "订阅路线官方明文「不向作者收取出版费」。"
              "官方流程：投稿至首次决定 4 天；投稿至审稿后决定 47 天；投稿至接收 92 天；接收至在线 2 天。"
              "来源与核验日期：Elsevier 官方期刊洞察页、Europe PMC，%s。该刊作者指南页面对非登录访问返回验证挑战，正文篇幅与图表上限未能核到，属未核实。" % (DATE, DATE),
    ),
    dict(
        name="3. Medical Oncology　Springer　主投·第三（影响力最高，但须先压缩）",
        verdict=[
            "适合吗：勉强适合。该刊声明传播肿瘤学与血液学的临床与实验研究，尤其免疫治疗与化疗领域的实验治疗学。"
            "本轮抽查其近年 HCC 稿件，多为药理与机制实验（如天然产物抑制 HCC、细胞治疗综述），"
            "纯公共数据预后建模不是其主流，故下调为「勉强适合」。",
            "够得着吗：边缘可尝试。影响因子 4.7（2025 JCR）为中科院 2026 新锐分区医学 3 区，"
            "是本报告零费用池中影响力最高的一本，但 2025 年发文量由前一年的约 307 篇升至约 624 篇，扩容期的稿件门槛不好判断。",
            "值得投吗：有条件尝试。零费用、投稿至接收中位 115 天（IQR 99 至 135 天），时间上完全兼容；"
            "但官方限 Original Article 正文 5,000 词、45 条文献、6 个图表项，本稿须整体压缩并把 8 张表合并进 6 项限额，改稿成本不为零。",
        ],
        prob="送外审 45% 至 60%；外审后接收 35% 至 50%；总体接收 15% 至 30%；置信度中低。证据类型：官方指标与限制条款 ＋ 第三方时间统计。",
        up="上调因素：影响因子 4.7、中科院 2026 新锐分区医学 3 区，是本池中学术认定最高的一本；"
           "官方期刊页给出「投稿至首次决定中位 14 天」；投稿至接收 115 天中位（IQR 99 至 135 天，基于近年 PubMed 记录的接收与投稿日期差）；"
           "自引率约 2.3%，未进入 2020 至 2026 各版中科院国际期刊预警名单。",
        down="下调因素：官方对原著的篇幅与图表项有硬限，本稿 5,970 词、41 条文献、14 个图表项全部超出；"
             "该刊 HCC 稿件以湿实验与药理为主，纯计算稿的初筛适配度偏低；影响因子一年内由约 3.4 升至 4.7、发文量翻倍，"
             "属明显的扩容与指标跃升期，未来门槛走向不确定。",
        unc="最大不确定性：扩容期编辑部对「无实验验证的计算类稿件」的取舍标准，公开信息无法判断。",
        facts="指标：影响因子 4.7、五年影响因子 4.0（均 2025 JCR，Springer 官方期刊页，核验 %s）；"
              "JCR 肿瘤学 Q2（按 JCI，2025 至 2026 版）；中科院 2025 年 3 月升级版医学 4 区、小类肿瘤学 4 区；2026 新锐分区医学 3 区、肿瘤学 3 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA（官方期刊页标为 Hybrid）；订阅路线零费用（Springer 混合刊政策）。"
              "官方要求（该刊投稿指南原文）：Original article 正文上限 5,000 词、45 条文献、6 个图或表；"
              "Short scientific communication 2,500 词、20 条文献、2 个图或表；并要求通讯作者使用机构邮箱。"
              "来源与核验日期：Springer 官方期刊页与投稿指南、第三方时间统计站，%s。" % (DATE, DATE),
    ),
    dict(
        name="4. Clinical and Translational Oncology（CTO）　Springer　备选（须整体压缩）",
        verdict=[
            "适合吗：比较适合。刊物范围涵盖癌症的诊断、预后与治疗以及数据科学与肿瘤政策分析，本稿的预后模型外部验证正落在其中。",
            "够得着吗：基本达到。影响因子 2.7，JCR Q3（肿瘤学），中科院 2025 升级版医学 4 区、2026 新锐医学 3 区。",
            "值得投吗：有条件尝试。零费用、初审最快（官方中位 6 天），但官方限 Research Article 正文 3,000 词、"
            "图表合计不超过 6 项、文献不超过 30 条，本稿须大幅压缩改写，属本报告中改稿成本最高的一条路径，故降为备选。",
        ],
        prob="送外审 55% 至 70%；外审后接收 40% 至 55%；总体接收 20% 至 40%；置信度中。证据类型：官方指标与流程数据。",
        up="上调因素：官方期刊页给出「投稿至首次决定中位 6 天」，为候选中最快之一；订阅路线零费用（官方明文）；"
           "近三年中国作者发文量在该刊居前列，对国内稿件接受度良好。",
        down="下调因素：官方篇幅限制与本稿差距最大（3,000 词对 5,970 词、6 项图表对 14 项、30 条文献对 41 条），"
             "压缩时必须下沉方法细节而不得删数值；该刊为西班牙肿瘤学会官方刊，稿源以临床与转化研究为主，纯计算分析占比不高。",
        unc="最大不确定性：压缩到 3,000 词后，本稿「完全嵌套交叉验证＋随机面板基准＋十种子复现」的方法学卖点能否保住，取决于压哪些段落。",
        facts="指标：影响因子 2.7、五年影响因子 2.9（均 2025 JCR，Springer 官方期刊页，核验 %s）；JCR Q3（ONCOLOGY，按 JCI）；"
              "中科院 2025 年 3 月升级版医学 4 区、小类肿瘤学 4 区；2026 新锐分区医学 3 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA；官方明文「本刊提供订阅出版选项，发表不收费，读者需订阅阅读」。"
              "官方要求：Research Article 正文上限 3,000 词、图表合计不超过 6 项、文献不超过 30 条、摘要不超过 250 词且为四段结构。"
              "来源与核验日期：Springer 官方期刊页与开放获取经费页，%s。" % (DATE, DATE),
    ),
    dict(
        name="5. Molecular Biology Reports（MBR）　Springer　备选（须先解决范围门槛）",
        verdict=[
            "适合吗：勉强适合。刊物为通用分子生物学刊，收稿面宽、发文量大，但要求稿件包含分子或细胞生物学实验技术。"
            "本轮已查到该刊 2025 至 2026 年的 HCC 稿件（如 DBF4B 促 HCC 进展），说明 HCC 主题在范围内，但那些稿件均含实验。",
            "够得着吗：基本达到。影响因子 3.2、JCR Q3（生化与分子生物学），中科院 2025 升级版生物学 4 区、2026 新锐生物学 3 区。",
            "值得投吗：值得投稿，但须先解决范围门槛。零费用、初审 3 天（官方中位），命中率相对高，适合作为兜底。",
        ],
        prob="送外审 40% 至 55%；外审后接收 45% 至 60%；总体接收 20% 至 35%；置信度中低。证据类型：官方要求与流程数据 ＋ 第三方指标。",
        up="上调因素：订阅路线零费用（Springer 混合刊政策）；官方期刊页给出「投稿至首次决定中位 3 天」，为候选中最快；"
           "年发文量大（约 700 篇以上），录用名额充足。",
        down="下调因素：官方要求投稿必须包含分子或细胞生物学实验技术，本稿为纯计算分析，"
             "存在被编辑以范围不符直接退回的风险；第三方自报平均审稿可达 6 个月。",
        unc="最大不确定性：范围条款的执行严格程度。若严格执行，本稿可能在初筛即被退回，时间成本约为两周。",
        facts="指标：影响因子 3.2、五年影响因子 3.2（均 2025 JCR，Springer 官方期刊页，核验 %s）；JCR Q3（BIOCHEMISTRY & MOLECULAR BIOLOGY）；"
              "中科院 2025 年 3 月升级版生物学 4 区、小类生化与分子生物学 4 区；2026 新锐分区生物学 3 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA；订阅路线零费用。"
              "来源与核验日期：Springer 官方期刊页，%s。" % (DATE, DATE),
    ),
    dict(
        name="6. Hepatobiliary & Pancreatic Diseases International（HBPD INT）　冲刺（费用状态须先问清）",
        verdict=[
            "适合吗：勉强适合。刊物由中国主办（浙江大学医学院附属第一医院）、Elsevier 出版，覆盖肝胆胰疾病的临床与研究，"
            "肝细胞癌属其核心领域；但稿件以临床研究为主，纯计算类二次分析占比低。",
            "够得着吗：边缘可尝试。影响因子 3.9、中科院 2025 升级版医学 3 区，是本报告中分区最高的一档；但年发文量仅约 63 篇，录用名额有限。",
            "值得投吗：有条件尝试，且必须先澄清费用。本轮核验发现该刊出版模式在来源之间直接冲突："
            "多个第三方刊物库标注为「非开放获取、Gold OA 占比约 4%」，而另一个第三方来源称其为开放获取期刊、"
            "接收后需支付 3,790 美元；而 Elsevier 官方期刊洞察页未列出任何出版选项或费用条目。"
            "在费用状态澄清之前投出去，存在违反 0 元约束的实质风险，因此排在 DDS 与 PRP 之后。",
        ],
        prob="送外审 40% 至 55%；外审后接收 25% 至 40%；总体接收 10% 至 20%；置信度中低。证据类型：官方收录与范围 ＋ 冲突的第三方费用信息。",
        up="上调因素：中科院医学 3 区，在多数国内单位认定中优于 4 区；中文母语编辑部，沟通成本低；"
           "若确为订阅制，则零费用成立，且该刊为本池中分区最高者。",
        down="下调因素：费用状态未核实且来源冲突；年发文量小，录用名额有限；"
             "第三方自报投稿至接收中位约 151 天，在 1 年约束下余量偏薄。",
        unc="最大不确定性：该刊当前的出版模式与是否收取文章处理费。这是本报告中唯一一条会直接决定「能不能投」的未知项。",
        facts="指标：影响因子 3.9（2025 JCR，Elsevier 官方期刊洞察页，核验 %s）；CiteScore 7.2（同一页面）；"
              "中科院 2025 年 3 月升级版医学 3 区、小类胃肠肝病学 4 区，2026 新锐分区医学 2 区（第三方）。"
              "收录：Scopus、MEDLINE、SCIE。出版模式：未核实——Elsevier 官方洞察页未列出版选项；"
              "第三方刊物库称非开放获取，另一第三方来源称开放获取且收费 3,790 美元。费用结论在澄清前不得采用。"
              "来源与核验日期：Elsevier 官方期刊洞察页、第三方刊物库，%s。" % (DATE, DATE),
    ),
    dict(
        name="7. Biochemical Genetics　Springer　保底首选（与稿件定位最契合，代价是影响力）",
        verdict=[
            "适合吗：高度适合。该刊官方投稿指南把 Methodology 单列为一类稿件，并写明「欢迎生化遗传学领域的实验方法与计算方法」，"
            "本稿正是「完全嵌套交叉验证 ＋ pooled out-of-fold 估计 ＋ 十种子复现 ＋ 随机面板基准」的方法学验证研究。",
            "够得着吗：基本达到。影响因子 1.9、中科院 2025 升级版生物学 4 区，门槛与稿件天然定位匹配；代价是该刊影响力有限。",
            "值得投吗：值得投稿。官方明文「除特殊服务外不收取出版费」，订阅路线零费用确定；初审中位 5 天；"
            "范围契合度全池最高、被拒风险最低，适合作为「必须投出去」的兜底。",
        ],
        prob="送外审 65% 至 80%；外审后接收 50% 至 65%；总体接收 30% 至 50%；置信度中。证据类型：官方范围与收费声明 ＋ 官方指标。",
        up="上调因素：官方期刊页明文「除特殊服务外无出版费」，是候选中最明确的零费用承诺；"
           "官方期刊页给出「投稿至首次决定中位 5 天」；官方投稿指南单列 Methodology 稿件类型并明确欢迎计算方法；"
           "该刊要求研究类稿件提供图形摘要，本稿已有 920 乘 300 像素的图形摘要可直接使用。",
        down="下调因素：官方同时声明不考虑「仅具狭窄适用性、样本极小或存在伪重复的描述性研究」，"
             "因此投稿信与摘要必须把方法学主张前置，不能以「发现新签名」为卖点；"
             "第三方来源未给出该刊的 JCR 分区，属未核实；影响因子 1.9 是本池最低。",
        unc="最大不确定性：该刊对「阴性复制」这一结论本身的态度。官方范围未直接涉及，描述性研究的排除条款是主要风险。",
        facts="指标：影响因子 1.9、五年影响因子 2.0（均 2025 JCR，Springer 官方期刊页，核验 %s）；JCR 分区未核实（第三方未给出）；"
              "中科院 2025 年 3 月升级版生物学 4 区、小类生化与分子生物学 4 区。"
              "收录：SCIE、Scopus、MEDLINE。出版模式：混合 OA；官方明文订阅路线无出版费。"
              "官方要求：欢迎原创研究、Methodology（实验方法与计算方法均可）、Database、Brief Report、综述等类型；"
              "研究类稿件须提供图形摘要。来源与核验日期：Springer 官方期刊页与投稿指南，%s。" % (DATE, DATE),
    ),
    dict(
        name="8. Indian Journal of Gastroenterology　Springer　保底第二",
        verdict=[
            "适合吗：勉强适合。刊物覆盖胃肠病学与肝病学，发表原创科学研究，HCC 属其主题范围，"
            "但该刊的读者与稿源以印度与南亚临床人群为主，纯计算类二次分析占比低。",
            "够得着吗：基本达到。影响因子 2.5、JCR Q3（胃肠肝病学）、中科院 2026 新锐分区医学 4 区，门槛不高。",
            "值得投吗：值得投稿。零费用、混合 OA 订阅路线即可，适合作最后兜底；主要顾虑是年发文量仅约 94 篇，录用名额有限。",
        ],
        prob="送外审 55% 至 70%；外审后接收 45% 至 60%；总体接收 25% 至 40%；置信度低。证据类型：第三方指标 ＋ 官方出版模式。",
        up="上调因素：混合 OA 期刊，订阅路线零费用；影响因子 2.5、中科院 4 区，门槛与本稿匹配；未进入各版中科院预警名单。",
        down="下调因素：年发文量小（约 94 篇），录用名额有限；缺少官方公布的流程中位数，时间判断只能依赖第三方经验，"
             "而第三方在 1 年约束下的可靠性不足；该刊对临床人群与地区特色的偏好可能压低纯计算稿的送审率。",
        unc="最大不确定性：是否公开任何流程数据。当前无官方周期数据可核，时间约束无法验证。",
        facts="指标：影响因子 2.5、五年影响因子 2.2（第三方汇总，2025 JCR 口径）；JCR Q3（GASTROENTEROLOGY & HEPATOLOGY）；"
              "中科院 2026 新锐分区医学 4 区、小类胃肠肝病学 4 区（第三方）。"
              "收录：SCIE。出版模式：混合 OA，订阅路线零费用（出版社页面）。年发文量约 94 篇。"
              "来源与核验日期：第三方刊物库与分区榜单，%s；该刊流程中位数未获取，标注未核实。" % DATE,
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
          "这一结论对大量采用「LASSO 加稳定性选择加一个外部队列」模板的稿件具有直接的方法学含义。")

para(doc, "优势：① 报告规范完备，TRIPOD 与 TRIPOD+AI 清单随稿；② 主口径为完全嵌套交叉验证，并用十个独立随机划分给出离散度，"
          "同时给出 optimism 的 bootstrap 置信区间；③ 补做了校准斜率、时间依赖 Brier、IBS 与 Schoenfeld 比例风险诊断；"
          "④ 多重比较同时给出 BH 与依赖稳健的 BY 校正；⑤ 阴性结果与阳性结果同等篇幅报告；⑥ 数据、代码、随机种子与复现步骤齐备，"
          "且公开仓库与稿件中的可用性声明同步。")

para(doc, "关键短板：① 无任何湿实验验证，抗风险能力全部来自统计学；② 未校正肿瘤纯度，而纯度是这类免疫与突变分析最典型的混杂；"
          "③ 只有总生存终点，无无复发生存或至复发时间；④ 两基因分数中 MAFG 的稳定性频率处在阈值边缘（十个种子中两个跌破 0.75），"
          "使「两基因」的确定性打了折扣；⑤ 面板来源为同一团队未发表的姊妹分析，虽已声明本稿为独立复现，仍可能被质疑循环性。")

para(doc, "初筛风险：最大风险是编辑把稿件读成「又一个失败的 TCGA 签名」，以缺乏新颖性退稿。"
          "对策是把标题、摘要首句与封面信三者统一到方法学主张上，并在封面信中明写「本文不主张该分数具有临床用途」。"
          "本轮新增一条对策：把该刊近年同类论文作为封面信里的引用参照，证明这类稿件的读者与栏目确实存在。")

para(doc, "外审风险：统计审稿人会追问两点——随机面板基准是否只用了表观拟合（本稿已声明它不校正选择步骤，属已披露）；"
          "MAFG 阈值边缘如何影响「两基因」主张（本稿已给出二项标准误与单边检验，属已量化）。"
          "临床审稿人会追问阴性结论的临床含义（本稿已限定结论仅对总生存成立，未外推至复发预测）。")

para(doc, "报告规范：已达到多数 3 至 4 区期刊的要求，无需补做。")

para(doc, "当前天花板与改进后层级：在现有数据条件下（无湿实验、无纯度列、无复发终点），"
          "本稿的现实天花板是 3 至 4 区、影响因子 2 至 4 的期刊；"
          "若补上肿瘤纯度校正（TCGA PanCanAtlas 的 ABSOLUTE 纯度按条形码对齐即可取得，属公开数据，无需实验），"
          "并在讨论中把纯度敏感性作为独立小节呈现，稿件在同类期刊中的竞争力会明显上升，但不足以跨入 2 区。")

# =============================== 五、投稿路径 ====================================
h(doc, "五、投稿路径", 1)

para(doc, "推荐顺序（0 元口径，全部走订阅出版路线或已核实的免费期刊）：")

para(doc, "首投：Digestive Diseases and Sciences。理由：肝病学在范围内且已有两份同类论文实证；JCR Q2、中科院 2026 新锐医学 3 区；"
          "订阅路线零费用、彩图不另收费；官方初审中位 7 天；且现有投稿包按该刊要求逐件做完，投它零返工。", indent=0.5)
para(doc, "第二：Pathology - Research and Practice。理由：官方明文订阅路线不向作者收费；投稿至接收中位 92 天、接受后 2 天上线，"
          "是全池中最快的一组；影响因子 3.7，按 JCI 计入 Q1，中科院 2026 新锐医学 3 区；2026 年已刊出 HCC 预后签名论文。", indent=0.5)
para(doc, "第三：Medical Oncology。理由：影响因子 4.7、中科院 2026 新锐医学 3 区，零费用池中学术认定最高；"
          "投稿至接收中位 115 天，时间兼容。代价是须把正文压到 5,000 词、文献压到 45 条、图表合并到 6 项。", indent=0.5)
para(doc, "冲刺（可选，须先澄清费用）：Hepatobiliary & Pancreatic Diseases International。"
          "仅在需要中科院医学 3 区、且已向编辑部书面确认不收取文章处理费时使用。", indent=0.5)
para(doc, "保底：Biochemical Genetics。理由：官方单列 Methodology 稿件类型并欢迎计算方法；官方明文无出版费；初审中位 5 天；"
          "被拒风险最低，代价是影响因子 1.9。", indent=0.5)
para(doc, "兜底：Molecular Biology Reports（须先确认纯计算稿件是否在范围内）或 Indian Journal of Gastroenterology。", indent=0.5)

para(doc, "转投时的调整要点：① 标题与摘要主句保持方法学定位不变，仅按刊物读者调整用词（肿瘤学刊保留 mitoxyperilysis 相关表述；"
          "分子生物学刊改为通用的「预后模型外部队列验证」表述）；② 篇幅按目标刊物上限压缩，优先下沉方法细节到补充材料，"
          "不得删除任何数值；③ 图表按刊物限额合并（DDS 与 PRP 无硬限，Medical Oncology 限 6 项，CTO 限 6 项且正文限 3,000 词）；"
          "④ 参考文献格式按刊物要求转换；⑤ 封面信必写三句：本文是什么、本文不主张什么、本文的统计口径为何优于同类稿件；"
          "⑥ 随稿清单应包括 TRIPOD 清单、数据可得性声明、代码可得性声明与阴性结果声明。")

para(doc, "若 1 年约束优先于分区：首投仍为 DDS（初审 7 天，被拒决策快、沉没成本低）；"
          "若首投被拒且剩余时间不足 9 个月，直接跳至 Biochemical Genetics 或 Molecular Biology Reports，不再经过 PRP 与 Medical Oncology。")

# =============================== 六、不推荐清单 ==================================
h(doc, "六、不推荐清单", 1)

not_reco = [
    ("Digestive and Liver Disease（DLD）",
     "本轮新增查出：该刊已于 2026 年 1 月 1 日转为完全金色开放获取，Elsevier 官方期刊洞察页只列出「开放获取」一种出版选项，"
     "文章处理费 2,960 美元（不含税），订阅路线已从页面上消失。影响因子 4.9、中科院医学 3 区，"
     "本会是本稿在零费用池中最有价值的肝病学选项，但模式变更使其直接出局。这是本轮最大的机会损失。"),
    ("Journal of Cancer Research and Clinical Oncology",
     "该刊自 2024 年起转为完全开放获取，官方明文每篇接收文章均需支付文章处理费 2,790 英镑 / 3,290 欧元 / 4,390 美元，"
     "无订阅路线可选；且自 2024 年起卷号重新起算，投稿前须确认刊史与收录连续性。"),
    ("Clinics and Research in Hepatology and Gastroenterology",
     "Elsevier 官方期刊洞察页给出订阅路线「不向作者收费」，费用本身合规；但同一页面给出官方接收率仅 12%，"
     "且刊物自述偏重「热点话题」与快速发表的新研究，与本稿阴性复制的调性不合。"
     "低接收率加高改稿成本，使它在 1 年约束下的综合效用低于前述候选。"),
    ("Cancer Biomarkers",
     "该刊自 2024 年 1 月起转为金色开放获取，文章处理费 2,800 美元，超出零预算。"
     "其范围与「标志物验证」高度契合，是纯费用原因造成的备选损失。"),
    ("Gene",
     "订阅路线免费，但刊物范围以基因功能与进化为主，与本稿的模型验证主题偏离；官方公布接收率仅 8%，被拒时间成本高。"),
    ("Journal of Digestive Diseases",
     "官方公布 2025 年接收率 8%，投稿至接收中位 146 天，在 1 年约束下余量不足；中国作者占比虽高，不改变初筛通过率的量级。"),
    ("International Journal of Biological Markers",
     "第三方标记为开放获取出版、文章处理费 2,800 美元，超出零预算；年发文量仅约 29 篇，录用名额极有限。"
     "多数第三方站点标注为 SCIE、个别标注为 ESCI，收录层级存在冲突，未核实。"),
    ("Frontiers、MDPI、PLOS、PeerJ、Scientific Reports 等完全开放获取平台",
     "均为完全开放获取，文章处理费约 1,500 至 3,000 美元以上，全部超出零预算；其中最低档仍在预算之外。"
     "零费用约束下，这一整类平台无论分区高低都不进入可投池。"),
    ("以「新型预后标志物」为定位的 1 至 2 区肿瘤学期刊",
     "本稿的核心结论是外部阴性复制，与这类期刊对「新发现」的期待直接冲突；投过去大概率在编辑初筛被退，白白消耗时间。"),
    ("临床医学 1 至 2 区的肝病学期刊",
     "同上；且这类期刊通常要求前瞻队列或实验验证，本稿不具备。"),
]
for name, why in not_reco:
    para(doc, name, bold=True, size=10, space=1)
    para(doc, why, size=9.5, indent=0.5, space=5)

# =============================== 七、不确定性与来源 ==============================
h(doc, "七、不确定性与来源", 1)

para(doc, "判断依据的层级：本报告对稿件的判断基于全文而非摘要，因此概率区间按全文口径给出，未额外放宽。"
          "期刊的动态信息（分区、影响因子、收录、费用、周期）全部来自本轮公开检索，核验日期均为 %s。"
          "其中期刊与出版社官方页面属第一层级来源，第三方期刊数据库与分区榜单属第二、三层级来源；"
          "凡第一层级来源与第三层级冲突者，本报告一律以第一层级为准并注明冲突。" % DATE)

para(doc, "本轮已核到第一层级来源的字段："
          "DDS、CTO、Biochemical Genetics、Medical Oncology、Molecular Biology Reports 五刊的影响因子与五年影响因子（2025）、"
          "出版模式（均为 Hybrid）与投稿至首次决定中位数，均取自 Springer 官方期刊页；"
          "PRP 的影响因子、订阅路线收费表述与四项流程中位数取自 Elsevier 官方期刊洞察页；"
          "DLD 转为完全金色开放获取的公告取自 Elsevier 官方页面；"
          "Biochemical Genetics 的「除特殊服务外无出版费」与 Methodology 稿件类型取自该刊官方投稿指南；"
          "Medical Oncology 的 5,000 词 / 45 条文献 / 6 个图表项限额取自该刊官方投稿指南。")

para(doc, "未核实字段：① Hepatobiliary & Pancreatic Diseases International 的出版模式与费用"
          "（Elsevier 官方页面未列出版选项，第三方来源在「非开放获取」与「开放获取、收费 3,790 美元」之间冲突）；"
          "② Biochemical Genetics 的 JCR 分区（第三方未给出）；"
          "③ Pathology - Research and Practice 的作者指南细节（正文篇幅与图表上限；该页面拒除非登录访问）；"
          "④ Indian Journal of Gastroenterology 的官方流程中位数；"
          "⑤ 各中文数据库站点给出的中科院分区属第三方转述，最终应以所在单位订购的分区表为准。")

para(doc, "统计与估计的区分：本报告未获得任何期刊针对本稿件的官方数据。"
          "表 2 的三阶段概率为结构化专家估计，其依据是各刊的公开流程数据、范围适配度与近年发文特征；"
          "除 Clinics and Research in Hepatology and Gastroenterology 的 12% 属官方公布接收率外，"
          "其余数值均不得当作期刊真实统计录用率使用。"
          "第三方投稿者自报数据仅作方向参考，本报告对样本量过小、幸存者偏倚明显的自报数值一律按弱证据处理。")

para(doc, "预算口径：本报告的「0 元」指作者不支付任何出版费用，因此只接受混合 OA 期刊的订阅路线与纯订阅制期刊。"
          "零费用池的边界会随出版社政策变动而移动——本轮已实测到一本期刊由订阅转为完全金色开放获取，"
          "因此投出前应再次确认目标刊当期的出版模式。")

para(doc, "主要来源（按访问顺序，均于 %s 核验）：" % DATE)
for label, url in [
    ("Springer 官方期刊页（DDS 10620、CTO 12094、Biochemical Genetics 10528、Medical Oncology 12032、Molecular Biology Reports 11033）",
     "https://link.springer.com/journal/10620"),
    ("Elsevier 官方期刊洞察页（Pathology - Research and Practice）",
     "https://www.sciencedirect.com/journal/pathology-research-and-practice/about/insights"),
    ("Elsevier 官方期刊洞察页（Hepatobiliary & Pancreatic Diseases International）",
     "https://www.sciencedirect.com/journal/hepatobiliary-and-pancreatic-diseases-international/about/insights"),
    ("Elsevier 官方期刊洞察页（Digestive and Liver Disease，用于核实开放获取转型与费用）",
     "https://www.sciencedirect.com/journal/digestive-and-liver-disease/about/insights"),
    ("Elsevier 官方公告（Digestive and Liver Disease 转为金色开放获取）",
     "https://www.sciencedirect.com/journal/digestive-and-liver-disease/about/news/digestive-and-liver-disease-is-transitioning-to-gold-open-access"),
    ("Springer 官方投稿指南（Medical Oncology 篇幅与图表限额）",
     "https://link.springer.com/journal/12032/submission-guidelines"),
    ("Springer 官方投稿指南（Biochemical Genetics 稿件类型与出版费）",
     "https://link.springer.com/journal/10528/submission-guidelines"),
    ("Europe PMC（用于检索各刊近年同类论文与 DOI）",
     "https://europepmc.org"),
]:
    source_line(doc, label + "：", url)

# =============================== 八、隐私说明 ====================================
h(doc, "八、隐私说明", 1)

para(doc, "本报告的稿件解析、质量判断、概率估计、报告生成与校验全部在本机完成。"
          "联网检索仅用于查询公开的期刊信息，检索词只包含期刊名称、公开数据库字段与概括性的学科词；"
          "未向任何外部检索服务、接口、云盘或第三方工具提交稿件全文、摘要原句、未发表结果、作者身份、单位或其他可回溯到本稿件的独特表述。"
          "本技能无法控制宿主平台或模型提供商自身的日志、遥测、同步与数据保留政策，"
          "使用者仍需依据所在平台与机构政策判断是否适合处理该材料。",
     size=9.5)

doc.save(OUT)
print("OK ->", OUT)
