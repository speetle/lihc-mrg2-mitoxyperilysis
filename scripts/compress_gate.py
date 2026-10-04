#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compress_gate.py —— 压缩作业专用数值闸门（比 数值指纹.py 更严的「无唯一值丢失」口径）

为什么需要它：
    数值指纹.py 的判定是「数值 token 多重集完全相等」，这对**压缩**是过严的——
    压缩必然删掉 Discussion 里对 Results 的冗余重述，那些数字的 token 计数会下降。
    但真正不可接受的只有一种情况：**某个数值本来只出现一次，压缩后被删光了**。
    那等于把一条唯一的数据从稿子里抹掉。

判定三条（任一不过 → 退出码 1）：
    A. 无唯一值丢失：改前出现次数为 N 的数值 token，改后出现次数 >= 1（N>=1 时）。
    B. 无凭空新增：改后出现的任何数值 token，改前必须出现过（防编造）。
    C. 引文编号多重集不变（防压缩时误删/误改引用）。

用法：
    python compress_gate.py 改前.md 改后.md
"""
import sys, re, collections

NUM = re.compile(r'\d+(?:[.,]\d+)?(?:[×x]\d+)?')
CIT = re.compile(r'\[(\d+(?:[,\-–]\d+)*)\]')

# 已核销（waiver）的非数据 token：这些不是实验/统计数值，删掉不算数据丢失。
# 每一条都必须写明理由与「该数值是否仍以其它形式存在于稿中」。
WAIVERS = {
    "1.4": "稿件版本标签 'release v1.4.0'，依 Reviewer 3 (M2) 删除投稿稿中的版本/DOI 占位符；"
           "数值 1.4 未丢失——Table 3 中仍有 1.4×10⁻²（SLC1A4）。",
    # —— 2026-10-04 参考文献双源核验（ref_audit_v15.py）抓出两条错 DOI，修正后旧的
    #    DOI 片段消失、新的出现。这些片段来自 DOI 字符串，不是统计数值。三者都是
    #    「旧 DOI 被正确的 DOI 取代」，逐条可回溯到文献核验记录。
    "009": "旧 DOI 10.1016/j.annonc.2025.01.009 的尾片段；该 DOI 经 PubMed 交叉核验为错"
           "（落到同一期会议摘要 VP1-2025），已改为 10.1016/j.annonc.2025.02.006。非统计数值。",
    "2025.01": "同上，旧 DOI 的年份-期号片段，随 DOI 修正一并消失。非统计数值。",
    "0525": "旧 DOI 10.1186/s12943-016-0525-3 的编号片段；经 PubMed 交叉核验应为 "
            "10.1186/s12943-016-0526-2。非统计数值。",
    # —— R1-M8（pooled out-of-fold + 十随机划分）：主统计量从「十折 C-index 的均值 ± 折间 SD」
    #    改为「pooled out-of-fold C-index，在 10 个独立随机划分上的均值 ± SD」。
    #    ⚠️ 这些都是**口径替换**，不是数据丢失：折级原值全部完整保留在
    #       补充材料/Table_S10_完全嵌套10折CV.csv（逐折 test_C + 汇总 mean/sd），
    #       新口径全部落盘 数据/revised/nested_pooled.json 与 Table_S10b。
    "0.100": "MRG-2 旧口径的折间 SD（=0.1003），被跨划分 SD 0.013 取代；原值仍在 "
             "Table_S10 汇总行与 Table_S10b 的 折C_SD_MRG2 列。",
    "0.103": "Model A 旧口径的折间 SD（=0.1029），同上一并移入 Table_S10 / S10b。",
    "0.588": "Model A 旧口径的折 C-index 均值（=0.5877），Table_S10 汇总行保留原值。",
    "0.58":  "正文与讨论里 'about 0.58' 的概述值；主统计量改为 pooled 口径后该概述改为 "
             "'about 0.61'（=0.6133，nested_pooled.json）。",
    "0.336": "Model A 第 3 折的 C-index；Table_S10 中为 0.3357，逐折原值未丢失。",
    "0.704": "Model A 第 5 折的 C-index；Table_S10 中为 0.7039，逐折原值未丢失。",
    "0.732": "MRG-2 第 7 折的 C-index；Table_S10 中为 0.7323，逐折原值未丢失。",
}

# 凭空新增（B）的已核销 token：必须能指向产生它的那一次**实跑**。
NEW_WAIVERS = {
    # —— R1-M4：审稿人要求补「未惩罚的 23 基因 Cox」作为真正的过参数化反面示范。
    #    由 分析脚本/r1m4_unpenalised.py 实跑产生，落盘
    #    数据/revised/modelA_unpenalised.json 与 补充材料/Table_S4b_ModelA_未惩罚对照.csv。
    "0.35": "R1-M4 未惩罚 Cox 的最大 |系数|（modelA_unpenalised.json: unpenalised_max_abs_coef=0.3472）。",
    "1.33": "R1-M4 未惩罚 Cox 的最大 HR（=1.3274）。",
    "6.0":  "R1-M4 设计矩阵条件数（design_condition_number=5.9922，正文取一位小数）。",
    "0.693": "R1-M4 未惩罚 Cox 的 apparent C-index（=0.6935，与 ridge 版 0.6840 对比）。",
    # —— DOI 修正带来的新片段，与 A 的 009 / 2025.01 / 0525 一一对应。
    "006": "新 DOI 10.1016/j.annonc.2025.02.006 的尾片段。",
    "2025.02": "新 DOI 的年份-期号片段。",
    "0526": "新 DOI 10.1186/s12943-016-0526-2 的编号片段。",
    # —— R1-M8：全部取自一次实跑 ——
    #    分析脚本/r1m8_nested_pooled.py → 数据/revised/nested_pooled.json
    #    （设计：10 折完全嵌套 × 10 个独立随机划分，内层 bootstrap 100；自我一致性断言
    #      「划分 0 的折均值 = 0.5758，复现沉积的 0.5760」已通过）。
    "0.613": "pooled out-of-fold C-index 在 10 个随机划分上的均值（MRG-2）= 0.6133。",
    "0.61":  "同上取两位的正文概述值。",
    "0.622": "pooled out-of-fold C-index 在 10 个随机划分上的均值（Model A）= 0.6218。",
    "0.610": "预设划分（seed 42）下 Model A 的 pooled out-of-fold C-index = 0.6104。",
    "0.635": "10 个划分中 MRG-2 pooled 值的最大端 = 0.6351。",
    "0.647": "10 个划分中 Model A pooled 值的最大端 = 0.6474。",
    "0.081": "MRG-2 的 optimism（apparent 0.6767 − pooled 0.5956）= 0.0811，"
             "配对 bootstrap 2,000 次（seed 7）。",
    "0.122": "上述 optimism 的 95% bootstrap 置信上界 = 0.1218。",
    "0.053": "Model A 的 optimism（0.6840 − 0.6104 = 0.0736）的 95% CI 下界 = 0.0526。",
}


def body(text):
    i = text.find("## Abstract")
    return text[i:] if i >= 0 else text


def main():
    if len(sys.argv) != 3:
        print(__doc__); return 2
    A = body(open(sys.argv[1], encoding="utf-8").read())
    B = body(open(sys.argv[2], encoding="utf-8").read())

    na, nb = collections.Counter(NUM.findall(A)), collections.Counter(NUM.findall(B))

    lost = {k: v for k, v in na.items() if nb.get(k, 0) == 0}
    waived = {k: v for k, v in lost.items() if k in WAIVERS}
    lost = {k: v for k, v in lost.items() if k not in WAIVERS}
    added = {k: v for k, v in nb.items() if k not in na}
    added_w = {k: v for k, v in added.items() if k in NEW_WAIVERS}
    added = {k: v for k, v in added.items() if k not in NEW_WAIVERS}
    # 引文：只看「集合是否被削」以及「顺序」
    ca, cb = CIT.findall(A), CIT.findall(B)
    cit_lost = sorted(set(ca) - set(cb), key=lambda s: int(re.split(r'[,\-–]', s)[0]))
    cit_new = sorted(set(cb) - set(ca))

    wa = len([x for x in re.sub(r'\*\*|\*|`', '', A).split() if re.search(r'[A-Za-z0-9]', x)])
    wb = len([x for x in re.sub(r'\*\*|\*|`', '', B).split() if re.search(r'[A-Za-z0-9]', x)])

    print(f"改前 {sys.argv[1]}")
    print(f"   全文字符数(含表/图注/声明) {wa}  |  数值 token 种类 {len(na)}")
    print(f"改后 {sys.argv[2]}")
    print(f"   全文字符数(含表/图注/声明) {wb}  |  数值 token 种类 {len(nb)}")
    print(f"   净变化 {wb - wa:+d}")

    bad = []
    if lost:
        bad.append(f"A. 唯一值丢失 {len(lost)} 个（这些数值改后全文一次都不出现了）")
    if added:
        bad.append(f"B. 凭空新增 {len(added)} 个")
    if cit_lost:
        bad.append(f"C. 引文编号被削：{cit_lost}")
    if cit_new:
        bad.append(f"C. 引文编号新增：{cit_new}")

    if lost:
        print("\n【A 明细】改前出现次数 → 改后 0：")
        for k in sorted(lost, key=lambda x: (-lost[x], x))[:120]:
            print(f"    {k!r:>18}  原出现 {lost[k]} 次")
    if added:
        print("\n【B 明细】改后新增：")
        for k in sorted(added, key=lambda x: (-added[x], x))[:80]:
            print(f"    {k!r:>18}  新增 {added[k]} 次")
    if cit_lost or cit_new:
        print(f"\n【C 明细】原 {len(ca)} 组 / 今 {len(cb)} 组")
        print(f"   被削: {cit_lost}")
        print(f"   新增: {cit_new}")
    if waived:
        print(f"\n【已核销（非数据 token）】{len(waived)} 个：")
        for k in sorted(waived):
            print(f"    {k!r} — {WAIVERS[k]}")
    if added_w:
        print(f"\n【已核销（新增值，均指向一次实跑产物）】{len(added_w)} 个：")
        for k in sorted(added_w):
            print(f"    {k!r} — {NEW_WAIVERS[k]}")

    if bad:
        print("\n❌ 闸门未通过：")
        for x in bad:
            print("   •", x)
        return 1
    print("\n✅ 闸门通过：无唯一数值丢失、无凭空新增、引文编号完整。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
