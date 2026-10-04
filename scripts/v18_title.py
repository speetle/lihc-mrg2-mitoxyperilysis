#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v1.8：题名去缩写（DDS 官方指南 `Do not use abbreviations in titles`）。

改前：
  Stability selection does not guarantee external transport: a mitoxyperilysis-related
  score fails validation in HCC
改后：
  Stability selection does not guarantee external transport: a mitoxyperilysis
  score fails validation in hepatocellular carcinoma

只动首行（题名）与第 3 行（运行标题），其余逐字节不变。
运行标题同步去掉 `in HCC`，保持无缩写。
"""
import os, re, hashlib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.7.md")
DST = os.path.join(BASE, "学生3_LIHC_MRG预后_SCI稿件_v1.8.md")

OLD_TITLE = ("Stability selection does not guarantee external transport: "
             "a mitoxyperilysis-related score fails validation in HCC")
NEW_TITLE = ("Stability selection does not guarantee external transport: "
             "a mitoxyperilysis score fails validation in hepatocellular carcinoma")
OLD_RUN = "Stability selection does not predict external transport in HCC"
NEW_RUN = "Stability selection does not predict external transport"

s = open(SRC, encoding="utf-8").read()
lines = s.split("\n")

assert lines[0] == "# " + OLD_TITLE, "首行不是预期题名：%r" % lines[0]
assert lines[2] == "**Running title:** " + OLD_RUN, "第 3 行不是预期运行标题：%r" % lines[2]

lines[0] = "# " + NEW_TITLE
lines[2] = "**Running title:** " + NEW_RUN
out = "\n".join(lines)

# ---- 断言：除这两行外逐字节不变 ----
a = s.split("\n"); b = out.split("\n")
assert len(a) == len(b), "行数变化：%d -> %d" % (len(a), len(b))
diff = [i for i in range(len(a)) if a[i] != b[i]]
assert diff == [0, 2], "改动行不止首行与第 3 行：%s" % diff

# ---- DDS 题名硬限 ----
# 官方 IFA 原文（media.springer.com/.../10620_DDS_IFA_12122022.pdf）：
#   "Titles should state the main findings of the article, not focus on design of the
#    research, and should not exceed 120 characters (not including spaces) in length.
#    Do not use abbreviations in titles."
# 注意：上限口径是「不计空格」。含空格计数会误判（v1.8 首跑即栽在这里）。
n_char_ns = len(NEW_TITLE.replace(" ", ""))
n_char_ns_old = len(OLD_TITLE.replace(" ", ""))
n_word = len([w for w in NEW_TITLE.split() if re.search(r"[A-Za-z0-9]", w)])
print("题名字符数（DDS 口径，不计空格）：%d -> %d  （上限 120，%s）"
      % (n_char_ns_old, n_char_ns, "通过" if n_char_ns <= 120 else "超限"))
print("题名字符数（含空格，仅备查）    ：%d -> %d" % (len(OLD_TITLE), len(NEW_TITLE)))
print("题名词数：%d -> %d" % (len(OLD_TITLE.split()), n_word))
print("运行标题：%d -> %d 字符（去缩写后）" % (len(OLD_RUN), len(NEW_RUN)))
assert n_char_ns <= 120, "新题名（不计空格）仍超 120：%d" % n_char_ns
assert n_word <= 20, "词数偏多：%d" % n_word
assert "HCC" not in NEW_TITLE
assert "HCC" not in NEW_RUN

open(DST, "w", encoding="utf-8").write(out)
h = hashlib.md5(out.encode("utf-8")).hexdigest()
print("\n已落盘：%s  %d 字节  MD5 %s" % (os.path.basename(DST), os.path.getsize(DST), h))
