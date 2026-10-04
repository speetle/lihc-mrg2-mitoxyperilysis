#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规范化 摘要压缩豁免_v1.7.json：把「去向」从 nums 里拆出来独立成段，便于审计。"""
import json, os, re
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(BASE, "分析脚本", "摘要压缩豁免_v1.7.json")
d = json.load(open(P, encoding="utf-8"))
old = dict(d["nums"])
clean, where = {}, {}
for k, v in old.items():
    if k.endswith(":where"):
        where[k[:-6]] = v
    else:
        clean[k] = v
d["nums"] = dict(sorted(clean.items()))
d["where"] = dict(sorted(where.items()))
ORDER = ["作业","依据","原则","nums","where","cits_shift","emph"]
json.dump({k: d[k] for k in ORDER if k in d}, open(P,"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("豁免项数：", len(clean), "｜去向条目：", len(where))
print("nums :", d["nums"])
