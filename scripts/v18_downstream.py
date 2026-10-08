#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v1.8 下游同步（LIHC）—— 题名去缩写后，把散落在各处的那一句改一致。

涉及：
  1. 补充材料 Item 1（TRIPOD 清单）与其生成脚本 make_supplement_v15.py；
  2. 发布包：CITATION.cff（题名 + 许可）+ README.md（题名 + 许可段 + 数值指纹数目）
             + LICENSE-DATA.md（题名）；
  3. 盲审逐条回复表 v1.7 -> v1.8（R2-m1 那一行的题名与字数口径 + 追加第五轮说明）。

**只改题名相关字串**，其余一字不动；每处替换都断言命中次数。
"""
import os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(BASE, "发布包_代码与数据")
ARCH = os.path.join(BASE, "历史版本_v1.0", "第五轮_v1.8")

FRAG_OLD = "a mitoxyperilysis-related score fails validation in HCC"
FRAG_NEW = "a mitoxyperilysis score fails validation in hepatocellular carcinoma"

report = []


def patch(path, pairs, label=None):
    s = open(path, encoding="utf-8").read()
    s0 = s
    for old, new in pairs:
        n = s.count(old)
        if n == 0 and new in s:
            # 幂等：该文件本来就已是新写法（例如 LICENSE-DATA.md 是本次新建的）
            report.append("  · %-46s 已是新写法，跳过" % os.path.basename(path))
            continue
        assert n >= 1, "未命中：%s\n  在 %s" % (old[:70], path)
        s = s.replace(old, new)
        report.append("  · %-46s ×%d  %s" % (os.path.basename(path), n, old[:44]))
    if s != s0:
        open(path, "w", encoding="utf-8").write(s)
    return s


# ───────────────────────── 1. 题名片段：五处
print("【1】题名片段替换")
for p in [
    os.path.join(BASE, "补充材料", "Supplementary_Item_1_TRIPOD清单.md"),
    os.path.join(PKG, "CITATION.cff"),
    os.path.join(PKG, "README.md"),
    os.path.join(PKG, "LICENSE-DATA.md"),
    os.path.join(BASE, "分析脚本", "make_supplement_v15.py"),
]:
    patch(p, [(FRAG_OLD, FRAG_NEW)])

# ───────────────────────── 2. CITATION.cff 许可落定
print("\n【2】CITATION.cff 许可落定")
CIT = os.path.join(PKG, "CITATION.cff")
patch(CIT, [
    ('license: MIT          # ← 待确认，见 LICENSE_待确认.md',
     'license: MIT'),
    ('# 数据部分的许可见 LICENSE-DATA（建议 CC BY 4.0）',
     '# 数据部分许可：CC BY 4.0 —— 见 LICENSE-DATA.md（含上游数据来源与各自条款）'),
])

# ───────────────────────── 3. README.md
print("\n【3】发布包 README.md")
RM = os.path.join(PKG, "README.md")
patch(RM, [
    ('├── LICENSE_待确认.md 许可条款（**需连彬确认后改名 LICENSE**）',
     '├── LICENSE           代码许可（MIT）\n'
     '├── LICENSE-DATA.md   数据许可（CC BY 4.0）＋上游数据来源与各自条款'),
    ('├── figures/          6 张主图 + 1 张补充图的 PDF/PNG（可选，见 make_release.py）',
     '├── figures/          6 张主图 + 1 张补充图的 PDF/PNG（可选，见 make_release.py；\n'
     '│                     投稿用的 EPS/TIFF 属附件、不入公开包）'),
    ('| 912 种数值 / 43 组引文 |', '| 914 种数值 / 43 组引文 |'),
    ('2. **许可未定**：`LICENSE_待确认.md` 给出建议条款，**请连彬确认后改名 `LICENSE`**；未确认前本包不构成授权。',
     '2. **许可**：代码 **MIT**（`LICENSE`），数据 **CC BY 4.0**（`LICENSE-DATA.md`）。\n'
     '   数据部分的上游来源（TCGA / GEO）各自条款不因本许可而改变，再分发须一并遵守。'),
])

# ───────────────────────── 4. 盲审逐条回复表 v1.7 -> v1.8
print("\n【4】盲审逐条回复表 v1.7 -> v1.8")
SRC = os.path.join(ARCH, "逐条回复表_v1.7.md")
DST = os.path.join(BASE, "盲审", "逐条回复表_v1.8.md")
s = open(SRC, encoding="utf-8").read()

OLD_ROW = ('标题改为「**Stability selection does not guarantee external transport: '
           'a mitoxyperilysis-related score fails validation in HCC**」'
           '（**114 字符 / 14 词**，符合 ≤120 字符与 ≤20 词）；')
NEW_ROW = ('标题改为「**Stability selection does not guarantee external transport: '
           'a mitoxyperilysis score fails validation in hepatocellular carcinoma**」'
           '（**113 字符，不计空格**；DDS 官方口径 `no more than 120 characters '
           '(not including spaces)`，达标）；')
assert s.count(OLD_ROW) == 1, "R2-m1 题名行未命中"
s = s.replace(OLD_ROW, NEW_ROW, 1)

OLD_RUN = '运行标题同步改为「Stability selection does not predict external transport in HCC」。'
NEW_RUN = '运行标题同步改为「Stability selection does not predict external transport」（去缩写，55 字符）。'
assert s.count(OLD_RUN) == 1, "R2-m1 运行标题未命中"
s = s.replace(OLD_RUN, NEW_RUN, 1)

# 指标表补一行题名
OLD_METRIC = "| 摘要（纯散文） | ≤ 250 词（DDS Original Article） | **238** | ✅ |"
NEW_METRIC = ("| 题名 | ≤ 120 字符（不计空格）／无缩写（DDS） | **113 字符**，无缩写 | ✅ |\n"
              + OLD_METRIC)
assert s.count(OLD_METRIC) == 1
s = s.replace(OLD_METRIC, NEW_METRIC, 1)

TAIL = """

---

## 附：第五轮修订说明（v1.7 → v1.8）——本轮也只做了一件事

**本轮唯一的改动，是让题名符合首选刊 DDS 的题名规范。除首行与第 3 行外，正文逐字节未动。**

| 项 | 改前（v1.7） | 改后（v1.8） | 依据 |
|---|---|---|---|
| 题名末词 | `…fails validation in HCC` | `…fails validation in hepatocellular carcinoma` | DDS：`Do not use abbreviations in titles.` |
| 题名长度 | 101 字符（不计空格） | **113 字符（不计空格）** | DDS：`should not exceed 120 characters (not including spaces)` |
| 运行标题 | `…does not predict external transport in HCC` | `…does not predict external transport` | 同上，去缩写 |

### 为什么第三轮改题名时没改掉 `HCC`

第三轮（R2-m1）改题名时，我是**照自设的「≤120 字符、≤20 词」口径**核的——
那个口径既没有出处，也把「含空格」当成了分母。DDS 官方 *Instructions for Authors* 的原文是
**`should not exceed 120 characters (not including spaces)`**，**不计空格**。同一句话还有第二句
**`Do not use abbreviations in titles.`**，而 `HCC` 正是缩写。

**这与第四轮的「摘要 296 词 / 关键词 8 个」是同一个病根：自设口径 ≠ 期刊口径。**
已作为第五轮教训再次计入交付说明。

### 同轮一并核实、因此新发现的两条 DDS 规范（都会影响投稿文件，不是文字）

1. **图件格式**：DDS 明列可收 `TIFF, GIF, JPEG, EPS, PPT, and Postscript`，并写明
   **`PDF is not an acceptable file format for manuscripts or figures`**——PNG 也不在列。
   → 已另做 `图件_v2/投稿格式/`：**EPS（矢量）＋ TIFF（600 dpi）各 7 个**，
   来源是 Illustrator 原生导出的 `.ai` 源文件（见 `图件_v2/组图源文件/`）。
2. **通讯作者必须用机构非商业邮箱**（`drmilo@gkd.edu.cn` 合规）、**须推荐 4–6 位审稿人**。
"""

s = s.rstrip() + TAIL
assert "test the assumption" not in s
open(DST, "w", encoding="utf-8").write(s)
print("  已落盘 盲审/逐条回复表_v1.8.md  %d 字节" % os.path.getsize(DST))

print("\n完成。共 %d 处替换。" % len(report))
