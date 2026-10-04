#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 600 dpi 位图转成投稿可用的 TIFF（DDS 等 Springer 系刊收 TIFF／EPS／JPEG，不收 PNG／PDF）。

输入：图件_v2/FigureN.png（600 dpi）与 图件_v2/补充图/FigureS1_calibration.png
输出：图件_v2/投稿格式/FigureN.tif、FigureS1_calibration.tif（LZW 无损，DPI 写回 600）

转完打印每张的像素、物理尺寸（mm）与字节数，便于与 EPS 的 BoundingBox 对照。
"""
import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "图件_v2")
OUT = os.path.join(FIG, "投稿格式")
os.makedirs(OUT, exist_ok=True)

TARGETS = [(os.path.join(FIG, "Figure%d.png" % i), "Figure%d.tif" % i) for i in range(1, 7)]
TARGETS.append((os.path.join(FIG, "补充图", "FigureS1_calibration.png"), "FigureS1_calibration.tif"))

print("%-26s %-14s %-16s %-10s %s" % ("文件", "像素", "物理尺寸(600dpi)", "字节", "模式"))
print("-" * 90)
for src, name in TARGETS:
    if not os.path.exists(src):
        print("%-26s [缺失] %s" % (name, src))
        continue
    im = Image.open(src)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    dst = os.path.join(OUT, name)
    im.save(dst, format="TIFF", compression="tiff_lzw", dpi=(600, 600))
    w_mm = im.size[0] / 600.0 * 25.4
    h_mm = im.size[1] / 600.0 * 25.4
    print("%-26s %-14s %-16s %-10s %s" % (
        name, "%dx%d" % im.size, "%.1f x %.1f mm" % (w_mm, h_mm),
        "%.1f MB" % (os.path.getsize(dst) / 1048576.0), im.mode))

print("\n已落盘：%s" % os.path.relpath(OUT, BASE))
