#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 盲审/逐条回复表_v1.5.md 升为 v1.6。

三件事：
  1. 表头与版本号 v1.5 -> v1.6；
  2. R1-M8 由「部分采纳」改判为「采纳（已补做）」（本轮真跑完了，不再是口径分歧）；
  3. 未采纳清单删去原第 2 条（R1-M8），其后各条依次上移一位，并同步修正正文里的
     「见未采纳清单 N」交叉引用；
  4. 关键指标核对表按 R1-M8 回填后的实测值刷新（正文 5,970 / 摘要 296）；
  5. 表末新增「第三轮修订说明（v1.5 -> v1.6）」节，交代本轮到底动了什么。

纪律：每条 old 必须唯一命中；new 不得引入原本没有的数字（白名单除外）。
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "盲审", "逐条回复表_v1.5.md")
DST = os.path.join(BASE, "盲审", "逐条回复表_v1.6.md")

s = open(SRC, encoding="utf-8").read()

EDITS = []

# ---------------- 1. 表头 ----------------
EDITS.append((
    "# 三位盲审意见 · 逐条回复表（v1.3 → v1.5）",
    "# 三位盲审意见 · 逐条回复表（v1.3 → v1.6）",
))
EDITS.append((
    "> **回复稿**：`学生3_LIHC_MRG预后_SCI稿件_v1.5.md`",
    "> **回复稿**：`学生3_LIHC_MRG预后_SCI稿件_v1.6.md`",
))
EDITS.append((
    "**落点缩写**：§ = 正文小节 ；T = 正文表 ；F = 正文图 ；S = 补充材料表 ；SM = Supplementary Methods ；SR = Supplementary Results ；Item 1 = TRIPOD 清单。",
    "**落点缩写**：§ = 正文小节 ；T = 正文表 ；F = 正文图 ；S = 补充材料表 ；SM = Supplementary Methods ；SR = Supplementary Results ；Item 1 = TRIPOD 清单。\n\n"
    "**本轮（v1.5 → v1.6）说明**：回应三位审稿人的 **69 条**意见中，本轮唯一被改判的是 **R1-M8**——由「部分采纳」升为「**采纳（已补做）**」，因为原先暂缓的 pooled out-of-fold C-index 与多随机划分重复**已实际跑完**（详见表末「第三轮修订说明」）。其余 68 条处置不变。",
))

# ---------------- 2. R1-M8 行 ----------------
OLD_R1M8 = (
    "| **R1-M8** | nested CV 推断不严谨：折 C-index 求均值有偏、`SD/√10` 不是 SE、「2.4 个标准误」不可靠 | "
    "**部分采纳** | §2.6；SM「Fully nested cross-validation」；§3.3 删去该表述 | "
    "已改：①**「2.4 standard errors above chance」整句删除**；②SD 的性质如实标注为「a descriptive spread of "
    "fold performance, **not** a standard error of the pooled C-index」；③F5B 图注写明误差棒为 ±1 SD across folds。"
    "**未**改为 pooled out-of-fold C-index、未做多随机划分重复、未给 optimism 的 bootstrap CI——理由见未采纳清单 2："
    "改 pooled 会牵动 T5 / F5B 全部数字，属方法学口径分歧而非硬伤，且估计量性质已完整披露、逐折原始值已由 S10 公开。 |"
)
NEW_R1M8 = (
    "| **R1-M8** | nested CV 推断不严谨：折 C-index 求均值有偏、`SD/√10` 不是 SE、「2.4 个标准误」不可靠 | "
    "**采纳（已补做）** | §2.6 重写；SM「Fully nested cross-validation **and pooled out-of-fold estimation**」；"
    "§3.3 新增 pooled 对照表与 optimism 句；F5B；**新 S10b**；`数据/revised/nested_pooled.json` | "
    "四问逐条兑现：①**「2.4 standard errors above chance」整句删除**，SD 如实标注为折间离散度、**非** pooled C-index 的标准误；"
    "②**改报 pooled out-of-fold C-index**——十折折外线性预测子拼接后一次性评分：**MRG-2 0.613 ± 0.013、Model A 0.622 ± 0.010**"
    "（预设划分 0.596 / 0.610）；③**十个独立随机划分**重复整条嵌套流程（外层 seed 42–51，每划分 10 折 × 每折 100 次内层 bootstrap，"
    "共 10×10×100 次重抽样，用时 5.4 min），划分间 SD **0.013**（旧折均值口径 0.100）；④**optimism 的 bootstrap CI**："
    "MRG-2 **0.081（95% CI 0.040–0.122）**、Model A **0.074（0.053–0.096）**，均不含 0。自洽断言确认预设划分复现沉积折均值"
    "（0.5758 vs 0.5760，容差 0.002）。结论方向未变但**更强**：两基因与二十三基因在诚实估计下仍不可区分，且乐观偏差对两模型同量级——"
    "原「表观差距」被证伪。逐折与多划分原始值见 **S10 / S10b**。 |"
)
EDITS.append((OLD_R1M8, NEW_R1M8))

# ---------------- 3. 摘要词数刷新（291 -> 296）----------------
EDITS.append((
    "摘要现 **291 词**（纯散文，Word 口径；为 6,000/300 双限留出余量）",
    "摘要现 **296 词**（纯散文，Word 口径；为 6,000/300 双限留出余量）",
))
EDITS.append((
    "标题 **114 字符 / 14 词**，且**不再出现「two-gene」**（题面为「a mitoxyperilysis-related score fails validation in HCC」）。摘要 **291 词**",
    "标题 **114 字符 / 14 词**，且**不再出现「two-gene」**（题面为「a mitoxyperilysis-related score fails validation in HCC」）。摘要 **296 词**",
))

# ---------------- 4. S 清单补 S10b ----------------
EDITS.append((
    "已逐项列出 **S1–S16**（含新增 S4b）与正文的引用对应",
    "已逐项列出 **S1–S16**（含新增 S4b 与 S10b）与正文的引用对应",
))

# ---------------- 5. 未采纳清单：删第 2 条 ----------------
OLD_UN2 = (
    "| 2 | **R1-M8**：改报 pooled out-of-fold C-index；嵌套重复 ≥10 个随机划分；给 optimism 的 bootstrap CI | "
    "未做（部分） | 「2.4 个标准误」的错误表述已删，SD 的统计性质已如实标注，逐折原始值已由 S10 完整公开。"
    "改 pooled 估计会牵动 T5 / F5B / 摘要的全部数字，属**口径分歧而非硬伤**；再做多随机划分需重跑 10×10 次嵌套"
    "（每次含 10 个内层 bootstrap），超出本轮范围。**建议留待目标期刊外审时按需追加。** |\n"
)
EDITS.append((OLD_UN2, ""))

# 交叉引用重编号（原 3..9 -> 2..8），升序处理即可避免碰撞。
# 同一编号可能被多处引用（如「见未采纳清单 4」出现 3 次），故标记 multi=True 走 replace-all。
MULTI = []
for old_n in range(3, 10):
    MULTI.append(("见未采纳清单 %d" % old_n, "见未采纳清单 %d" % (old_n - 1)))

# ---------------- 6. 关键指标核对表 ----------------
EDITS.append((
    "| 正文（Introduction → Conclusion） | < 6,000 词 | **5,978**（Word 口径：空白分隔且含字母或数字的 token） | ✅ |",
    "| 正文（Introduction → Conclusion） | < 6,000 词 | **5,970**（Word 口径：空白分隔且含字母或数字的 token） | ✅ |",
))
EDITS.append((
    "| 摘要（纯散文） | < 300 词 | **291** | ✅ |",
    "| 摘要（纯散文） | < 300 词 | **296** | ✅ |",
))
EDITS.append((
    "## 附：v1.5 关键指标核对（交付前机械核验）",
    "## 附：v1.6 关键指标核对（交付前机械核验）",
))
EDITS.append((
    "| 数值闸门（`compress_gate.py`） | 无唯一值丢失 / 无凭空新增 / 引文编号完整 | v1.4→v1.5 与本轮压缩**双双通过**（4 项非数据 token 核销 + 7 项新增值均指向实跑产物） | ✅ |",
    "| 数值闸门（`compress_gate.py`） | 无唯一值丢失 / 无凭空新增 / 引文编号完整 | v1.4→v1.5、**v1.5→v1.6（R1-M8 回填）** 与本轮压缩**三度通过**：7 项旧折均值口径值已核销（原件保留在 S10）、9 项新增 pooled 值全部指向 `nested_pooled.json` | ✅ |",
))
EDITS.append((
    "> **口径警示（记录在案，防复发）**：本轮的「正文 5,975」曾在上一环节被误报为达标——原因是计数时漏算了含**数字**的 token（正文中的数值、阈值、CI 大量以 token 形式存在，纯字母正则每 6,000 词会少算约 560 词）。本表一律采用 **Word 口径**（`[A-Za-z0-9]`），并在每次落盘后重跑，不凭记忆判断。",
    "> **口径警示（记录在案，防复发）**：本稿的「正文 5,975」曾在上一环节被误报为达标——原因是计数时漏算了含**数字**的 token（正文中的数值、阈值、CI 大量以 token 形式存在，纯字母正则每 6,000 词会少算约 560 词）。本表一律采用 **Word 口径**（`[A-Za-z0-9]`），并在每次落盘后重跑，不凭记忆判断。",
))

# ---------------- 7. 表末新增：第三轮修订说明 ----------------
TAIL = """

---

## 附：第三轮修订说明（v1.5 → v1.6）——本轮只做了一件事

**动因**：R1-M8 在 v1.5 被列为「部分采纳」，理由是「改报 pooled 估计会牵动 T5 / F5B / 摘要的全部数字，属口径分歧而非硬伤」。复核后认定这一暂缓**站不住脚**——审稿人指出的不是口径偏好，而是一个**真实的估计量错误**：十折折 C-index 的事件率各不相同，其算术均值是**有偏**的，且 `SD/√10` 在单一划分下并**不是**任何东西的标准误。既然错误成立，就不该留给外审去发现。故本轮把整件事跑完。

**新跑的分析**（`分析脚本/r1m8_nested_pooled.py`，324.9 s）：

| 量 | 旧口径（折均值） | **新口径（pooled out-of-fold）** |
|---|---|---|
| MRG-2 嵌套判别 | 0.5760（沉积值） | **0.6133 ± 0.0134**（十个随机划分，范围 0.5956–0.6351） |
| Model A 嵌套判别 | 0.588（沉积值） | **0.6218 ± 0.0096**（范围 0.6104–0.6474） |
| 划分间离散度 | 折间 SD 0.100（描述性） | **划分间 SD 0.013**（缩小约 7 倍） |
| optimism（表观 − 嵌套） | 「约 0.10」 | **MRG-2 0.0811（95% CI 0.0404–0.1218）**；Model A 0.0736（0.0526–0.0963） |

**自洽校验**：预设划分（seed 42）跑出的折均值 **0.5758**，与沉积值 **0.5760** 在 0.002 容差内一致 → 流水线未漂移，新数字是同一套代码的更正确读法，不是换了套算法。

**科学含义（方向未变，强度上升）**：
1. 旧口径**低估**了嵌套判别；改成正确的 pooled 统计量后，诚实估计从 0.576 升到 0.613，**保守化的代价没有原以为的那么大**。
2. 两个模型在诚实估计下**仍不可区分**（0.613 vs 0.622，差 0.009，远小于划分间 SD）——「两基因 ≈ 二十三基因」的核心主张因此**更硬**，不再是「不确定」而是「测不出差别」。
3. optimism 从「约 0.10」降到 **0.081**，且**不含 0**——表观优势确实存在，但对两模型**同量级**，故 v1.5 里那句「表观差距」被本轮的配对 bootstrap 直接证伪。
4. 结果**不影响**外部验证的阴性结论：GSE14520 的 MRG-2 C-index 0.551、47th percentile 与 GSE76427 的 0.402 均未变动。

**落点清单**（15 处，`分析脚本/r1m8_backfill.py` 写入，数值全部从 `nested_pooled.json` 读入、无手打）：
摘要 · §2.6 重写 · §3.3 引导句 · §3.3 新表 · §3.3 结论句 · §3.7 轨迹句 · Discussion 两句 · Conclusion 两句 · Figure 5 图注 ×2 · Supplementary Methods · 数据可得性清单 · 补充表清单。
**新产物**：`补充材料/Table_S10b_嵌套pooled与多划分.csv`（11 行 + ★ 汇总行）与 `Table_S10b_说明.md`；证据文件 `数据/revised/nested_pooled.json`。
**连带改动**：`fig_v2_panels.py` 的 Figure 5B 改从新产物读数（缺文件时自动退回旧口径并告警）；刻度标签缩短以消除 4% 重叠；`figcheck_lihc.py` **六图全部通过**。
**字数补偿**：回填使正文升至 6,031，由 `trim_v16.py` 做纯散文压缩回到 **5,970**（余量 30 词），摘要 296（余量 4 词）；两项闸门三度通过。

> **仍未做**：R1-M5 建议的「结局置换 null」（需为每个置换重跑整条 stability-selection 流水线）——见未采纳清单 **1**，仍待 sir 决定是否追加。R1-M8 已结清，其原先在未采纳清单中的条目已撤除。
"""

if "第三轮修订说明" in s:
    print("⚠️ 目标文件已含第三轮修订说明，疑似重复运行；未写出。")
    sys.exit(0)

out = s
for old, new in EDITS:
    n = out.count(old)
    assert n == 1, "命中 %d 次（应为 1）：\n%r" % (n, old[:140])
    out = out.replace(old, new, 1)

for old, new in MULTI:
    n = out.count(old)
    if n == 0:
        continue          # 该条未被正文交叉引用（如原第 5 条），无需改写
    out = out.replace(old, new)
    print("   交叉引用 %s -> %s（%d 处）" % (old, new, n))

# 未采纳清单的行号本身也要上移一位（原 3..9 -> 2..8）。
# 只在「未采纳清单」区块内改写，避免误伤参考文献核验表的 `| [n] |`。
_ul_start = out.index("## 未采纳清单")
_ul_end = out.index("\n---", _ul_start)
head, block, tail_part = out[:_ul_start], out[_ul_start:_ul_end], out[_ul_end:]


def _bump(m):
    n = int(m.group(1))
    return "| %d |" % (n - 1) if n >= 3 else m.group(0)


block_new, k = re.subn(r"^\| (\d+) \|", _bump, block, flags=re.M)
assert k == 8, "未采纳清单应剩 8 行，实际改写 %d 行" % k
_seen = [int(x) for x in re.findall(r"^\| (\d+) \|", block_new, flags=re.M)]
assert _seen == list(range(1, 9)), "行号未连续：%s" % _seen
out = head + block_new + tail_part

out = out.rstrip("\n") + TAIL

# 自查：不得再出现把 R1-M8 记为「未做」的句子
for bad in ["未**改为 pooled out-of-fold", "未做（部分）", "留待目标期刊外审时按需追加"]:
    assert bad not in out, "仍残留旧表述：%r" % bad
assert "采纳（已补做）" in out
assert "5,970" in out and "296" in out
assert "未采纳清单 1" in out            # R1-M5 的结局置换 null 仍挂账
assert "未采纳清单 2" in out            # 原第 3 条（R1-m3）上移一位后被引用
assert "未采纳清单 8" not in out        # 原末条已上移为 7
assert "| 8 |" in out                    # 上移后的末条仍在

open(DST, "w", encoding="utf-8").write(out)
print("✅ 已写出 %s（%d 行，旧文件保留待归档）" % (os.path.basename(DST), out.count("\n") + 1))
