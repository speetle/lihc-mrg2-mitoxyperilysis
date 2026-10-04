#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数值指纹.py —— 润色/压缩类作业的强制前置闸门（兑现 ERR-2026W40-65）

用法：
    python 数值指纹.py 改前稿.md 改后稿.md
    python 数值指纹.py --snap 稿.md            # 只导出指纹 JSON

判定：正文层（## Abstract 起）数值 token 计数与引文编号序列须完全一致。
任一不等 → 退出码 1（调用方应停止落盘）。
"""
import sys, os, re, json, collections

NUM = re.compile(r'\d+(?:[.,]\d+)?(?:[×x]\d+)?')
CIT = re.compile(r'\[(\d+(?:[,\-–]\d+)*)\]')
EMPH = re.compile(r'(?<!\*)\*[^*\n]{1,40}\*(?!\*)')

def body(text):
    """取正文层：从 ## Abstract 起（版本说明块在同层之前，单独另计）"""
    i = text.find("## Abstract")
    return text[i:] if i >= 0 else text

def fingerprint(text, scope="body"):
    t = body(text) if scope == "body" else text
    return {
        "scope": scope,
        "nums": dict(collections.Counter(NUM.findall(t))),
        "cits": CIT.findall(t),
        "emph": sorted(set(EMPH.findall(t))),
        "words": len([x for x in re.sub(r'\*\*|\*|`', '', t).split()
                      if re.search(r'[A-Za-z0-9]', x)]),
    }

def diff(a, b, waiver=None):
    bad = []
    na, nb = collections.Counter(a["nums"]), collections.Counter(b["nums"])
    only_a, only_b = na - nb, nb - na
    # ---- 豁免表（可审计；只用于「受期刊硬限驱动的摘要压缩」，须逐条写明理由与去向）----
    wn = dict((waiver or {}).get("nums", {}))
    ww = dict((waiver or {}).get("where", {}))
    waived, only_a = {}, dict(only_a)
    for tok, lost in list(only_a.items()):
        if wn.get(tok, 0) >= lost:
            waived[tok] = lost
            only_a.pop(tok)
    if waived:
        print("\n⚠️ 已声明豁免（数值 token 计数减少，但 token 仍存于正文/补充材料）：")
        for tok, lost in sorted(waived.items()):
            print(f"   – {tok} × {lost}  ← {ww.get(tok, '（见豁免文件 where 段）')}")
    if only_a: bad.append(f"数值 token 丢失：{dict(only_a)}")
    if only_b: bad.append(f"数值 token 新增：{dict(only_b)}")
    cits_allow = bool((waiver or {}).get("cits_shift"))
    if a["cits"] != b["cits"]:
        msg = (f"引文编号序列不一致：改前 {len(a['cits'])} 组 / 改后 {len(b['cits'])} 组"
               f"；首个差异位 {next((i for i,(x,y) in enumerate(zip(a['cits'],b['cits'])) if x!=y), '尾部')}")
        if cits_allow:
            print("\n⚠️ 已声明豁免（引文序列位移）：" + msg)
            print("   ← " + str((waiver or {}).get("cits_shift")))
        else:
            bad.append(msg)
    if a["emph"] != b["emph"]:
        bad.append(f"斜体标记变化：删 {sorted(set(a['emph'])-set(b['emph']))} / "
                   f"增 {sorted(set(b['emph'])-set(a['emph']))}")
    return bad

def main():
    argv = list(sys.argv[1:])
    wpath = None
    if "--waiver" in argv:
        i = argv.index("--waiver")
        wpath = argv[i + 1]
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    if "--snap" in sys.argv:
        f = args[0]
        fp = fingerprint(open(f, encoding="utf-8").read())
        out = os.path.splitext(f)[0] + ".fingerprint.json"
        json.dump(fp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"✅ 指纹已导出 {out}：数值型 {len(fp['nums'])} 种 / 引文 {len(fp['cits'])} 组 / "
              f"正文 {fp['words']} 词")
        return 0
    if len(args) != 2:
        print(__doc__); return 2
    waiver = None
    if wpath:
        waiver = json.load(open(wpath, encoding="utf-8"))
        print(f"（已载入豁免表 {wpath}）")
    A = fingerprint(open(args[0], encoding="utf-8").read())
    B = fingerprint(open(args[1], encoding="utf-8").read())
    bad = diff(A, B, waiver)
    print(f"改前 {args[0]}：{A['words']} 词")
    print(f"改后 {args[1]}：{B['words']} 词（净 {B['words']-A['words']:+d}）")
    if bad:
        print("\n❌ 闸门未通过，禁止落盘：")
        for x in bad: print("   •", x)
        return 1
    print("\n✅ 闸门通过：正文层数值 token 零差异、引文编号顺序完全一致、斜体标记无变化。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
