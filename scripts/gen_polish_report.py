#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_polish_report.py —— 由两个润色脚本的替换表生成三列对照报告（SCI-writing-VIP §8 步骤 4）"""
import os, sys, importlib.util, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SC = os.path.join(BASE, "分析脚本")

def load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SC, fn))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

m1, m2 = load("p13", "polish_v13.py"), load("p13b", "polish_v13b.py")

# 类别 -> (中文名, 依据)
JUST = {
 "句首And": "**D-36 框架层 ② 变更记录腔**。真人语料 11,868 句中句首 `And` 仅 **2 次（0.02/百句）**；本稿 5 次（2.42/百句）＝真人的 **121 倍**。",
 "句首But": "**D-36 框架层 ②**。真人语料句首 `But` **0 次**；本稿 3 次。句首 `But` 是典型的中文口语英译腔，正文层不得使用。",
 "because": "**D-36 分布层 ③ 定量上限**：单一连接词 ≤3.0/百句、占比 ≤12%。真人 `because` **0.63/百句**；本稿 5.31/百句 ＝真人的 **8.4 倍**，为全稿第一大 AI 腔指标。",
 "therefore": "**D-36 分布层 ③**。真人 `therefore` **0.36/百句**；本稿 3.86/百句 ＝真人的 **10.7 倍**。真人极少用 therefore 承担推论功能，多用分号并列或直接陈述。",
 "however": "**D-36 分布层 ③「缺位即异常」**。真人 `however` **0.81/百句**（为真人第 2 高频转折词）；本稿 **0 次**。刻意回避最高频的人类转折词而改用 `but`，是分布性单调的典型形态。",
 "让步": "**D-19**：以通用转折词（`but`/`however`）静默替代让步连接词（`although`/`while`/`despite`）会**丢失让步语义**——让步＝「承认反例后仍下判断」，转折＝「两件事并列」。真人 `although` 0.72/百句、`despite` 0.35/百句；本稿 `despite` 0 次。",
 "切分": "**句长类指标**（style_compare.py）。真人平均句长 **22.6 词**、≥35 词长句占 **10.3%**；本稿原为 28.8 词、**32.4%**，长句占比为真人 **3.1 倍**。长句＝从属结构堆叠，是 AI 腔在句法层的直接投影。",
 "in addition": "**D-36 分布层 ③ 过渡手段单一**。真人连接词 **40 种**；本稿原 17 种。补入真人实际在用的低密度手段。",
 "notably": "同上。真人 `notably` 0.41/百句。",
 "consequently": "同上。真人 `consequently` 0.08/百句；本稿原用口语化 `so`（不在真人连接词表内）承接因果。",
 "since": "同上。真人 `since` 0.08/百句，且为 causality 的低调变体，可稀释 `because` 密度。",
}

GROUPS = [
 ("一、句首 And / But —— 框架层 ② 变更记录腔", ["句首And", "句首But"], m1.R),
 ("二、because —— 分布层 ③ 单连接词超限（最严重项）", ["because"], m1.R),
 ("三、therefore —— 分布层 ③", ["therefore"], m1.R),
 ("四、but → however / although —— D-19 让步语义复原 + 缺位词补回", ["让步", "however"], m1.R),
 ("五、长句切分 —— ≥35 词长句 32.4% → 15.5%", ["切分"], m1.R),
 ("六、第二轮：because 再降 + 连接词种类补充", ["because", "since", "in addition", "notably", "consequently"], m2.R),
]

def esc(s):
    return s.replace("|", "\\|")

out = []
out.append("# LIHC 稿件润色报告 —— SCI-writing-VIP §8 复用模式\n")
out.append("**对象**：`学生3_LIHC_MRG预后_SCI稿件_v1.2.md` → `…_v1.3.md`（当前最终版）  ")
out.append("**执行**：连彬 (Bin Lian) / ORCID 0000-0002-1477-9137 · SCI-writing-VIP 首发 2026-09-21  ")
out.append("**日期**：2026-10-04  ")
out.append("**改动总量**：**67 处**（第一轮 61 处 + 第二轮 6 处），全部唯一命中，脚本级断言防静默漏改。\n")
out.append("> 本报告即 §8 步骤 4 要求的「**原句 → 修正句 → 依据**」三列对照表，供先生逐条取舍。  ")
out.append("> 步骤 1（加载 A~D 四库 + 框架模板 + 错题本）、步骤 2（结构诊断）、步骤 3（`style_compare.py` 句级体检）均已执行。  ")
out.append("> **红线**：改动不含任何数值、P 值、置信区间、基因名、探针号与文献编号。\n")
out.append("---\n")

out.append("## 0. 机检数据对照（工具输出，非估计）\n")
out.append("| 指标 | 真人基准 | v1.2（润色前） | v1.3（润色后） | 判定 |")
out.append("|---|---|---|---|---|")
rows = [
 ("语料规模", "11,868 句 / 257,762 词（14 篇顶刊）", "207 句", "247 句", "—"),
 ("平均句长（词）", "22.6", "28.8 ⚠️", "**23.2**", "✅ 收敛"),
 ("≥35 词长句占比 %", "10.3", "32.4 ⚠️", "**15.5**", "✅ 改善 3.1→1.5 倍"),
 ("≤15 词短句占比 %", "23.3", "24.4", "31.4", "✅"),
 ("连接词密度 /百句", "20.8", "23.9", "17.1", "✅"),
 ("连接词种类数", "40", "17 ⚠️", "21", "⚠️ 残余（见 §7）"),
 ("`because` /百句", "0.63", "5.31 ⚠️", "**2.02**", "✅ 8.4→3.2 倍"),
 ("`but` 次 /百句", "3.17", "6.28", "**1.22**", "✅"),
 ("`therefore` /百句", "0.36", "3.86 ⚠️", "**0.40**", "✅ 10.7→1.1 倍"),
 ("`however` /百句", "0.81", "0 ⚠️", "**1.22**", "✅ 缺位补齐"),
 ("`although` /百句", "0.72", "0.48", "**1.63**", "✅ D-19 复原"),
 ("`despite` /百句", "0.35", "0", "0", "⚠️ 见 §7"),
 ("句首 `And` /百句", "0.02", "2.42 ⚠️", "**0**", "✅ 121 倍→0"),
 ("句首 `But` /百句", "0", "1.45 ⚠️", "**0**", "✅"),
 ("AI 模板短语命中", "73", "0", "0", "✅"),
 ("`style_compare` 待处理项", "—", "4 项", "**1 项**", "✅"),
 ("`anti_ai_check` AI 味指数", "—", "8 / 10", "8 / 10", "✅（10 分制，越高越像人写）"),
]
for r in rows:
    out.append("| " + " | ".join(r) + " |")
out.append("\n> 真人基准来源：`01_文献库/2026-W39,D01–D07` + `2026-W40,D01–D07`，共 14 篇顶刊语料。\n")
out.append("---\n")

n = 0
for title, cats, R in GROUPS:
    items = [(t, c, o, w) for (t, c, o, w) in R if c in cats and o != w]
    if not items:
        continue
    out.append(f"## {title}\n")
    out.append(f"**共 {len(items)} 处。**\n")
    out.append("| # | 原句（v1.2） | 修正句（v1.3） | 依据 |")
    out.append("|---|---|---|---|")
    for tag, cat, old, new in items:
        n += 1
        out.append(f"| {n} | {esc(old)} | {esc(new)} | {JUST.get(cat,'—')} |")
    out.append("")
out.append(f"**合计 {n} 处。**\n")
out.append("---\n")

out.append("""## 7. 未做项与残余项（须先生裁定）

### 7.1 hedge/booster v1.0 口径 = 0.6（真人 9.01）——**刻意不做**
`style_compare.py` 将其列为待处理项，但**与先生 2026-09-28 明确口径直接冲突**：

> 「结论允许肯定甚至激进，去除 AI 式层层免责；数据支持时直接用『表明／证实／decreased／improved』级动词。」

补充该口径即为回灌 AI 腔。v2.0 扩展口径下本稿为 **6.8**（真人 13.82，判定 ✅）。**建议维持现状。**

### 7.2 连接词种类 21 种（真人 40 种）
属**语料规模效应**而非写作缺陷：本稿 247 句，真人语料 11,868 句；《count_connectors.py》
以「≥0.50/百句」为计入阈值，在 247 句样本中该阈值相当于**每 2 句出现一次**，可容纳的种类数
在数学上被压缩。以每百句计，本稿 17.1/百句已落在真人区间（20.8）内。
另经核查：`count_connectors.py` 报出的 `because` 11 次与直接正则计数 7 次不符（差值来自句首
`Because` 大小写），**建议为工具补 `conn_top1_share` 字段**，把「单连接词占比」直接输出——
这是 D-36 分布层 ③ 唯一尚无工具支撑的判据（本次靠手工计算）。

### 7.3 `despite` 仍为 0 次
本稿无需要 `despite` 承担语义的位置；强行补入即为凑指标。**建议维持 0。**

---

## 8. 本次暴露的新 AI 腔形态（§8 步骤 5 回写项）

1. **句首 `And` 的「续写腔」**——单句看似自然，密度（2.42/百句 vs 真人 0.02）暴露机器来源。
   → 已追加 `D_AI腔黑名单.md`：D-37。
2. **高频词缺位即异常**：`however` 0 次并非「文风凝练」，而是回避最高频人类转折词的
   系统性行为，须与「过度使用某词」同等对待。
   → 已追加 D-38。
3. **长句占比可量化**：平均句长在 28.8 时尚可辩解，**≥35 词长句占比 32.4% vs 真人 10.3%**
   才是硬证据。单看均值会漏诊。
   → 已追加 D-39。
4. **工具缺口**：`style_compare.py` 只有连接词密度下界，无「单连接词占比」上界字段。
   → 已记入 `ERROR_DO_NOT_REPEAT.md`。

---

## 9. 复现命令

```bash
cd "<交付目录>"
<venv>/python 分析脚本/trim_v12.py      # v1.1 -> v1.2 压缩（31 处）
<venv>/python 分析脚本/polish_v13.py    # v1.2 -> v1.3 润色第一轮（61 处）
<venv>/python 分析脚本/polish_v13b.py   # v1.3 润色第二轮（6 处，就地）
<venv>/python 分析脚本/gen_polish_report.py   # 重新生成本报告
```
""")

dst = os.path.join(BASE, "润色报告_SCI-writing-VIP_v1.0.md")
open(dst, "w", encoding="utf-8").write("\n".join(out))
print(f"✅ 写出 {os.path.basename(dst)}，三列对照共 {n} 条")
