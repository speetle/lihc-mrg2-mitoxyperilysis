#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_raw_data.py —— 拉取本研究全部原始输入（公开数据，无需授权）

本研究的可复现性依赖两类原始输入：
  (A) cBioPortal REST API（TCGA-LIHC）—— 由 lihc_pipeline.py **自动**拉取，无需本脚本；
  (B) GEO 的三个外部文件 —— 原分析时手工放置于 /tmp，本脚本把它自动化。

用法
  python fetch_raw_data.py --check          # 只做 HEAD 校验，不下载（推荐先跑）
  python fetch_raw_data.py                  # 下载到 /tmp（与现有脚本的硬编码路径一致）
  python fetch_raw_data.py --dir ./raw      # 下载到指定目录

⚠️ 现有 external_GSE14520.py / external_GSE76427.py / gse76427_prolif_control.py
   读取的是 /tmp 下的固定文件名，若用 --dir 改路径，请另行设置软链或改脚本常量。

全部 URL 已于 2026-10-04 逐一 HEAD 校验为 HTTP 200。
"""
import os, sys, gzip, argparse, hashlib, urllib.request, urllib.error

# (远端 URL, 本地期望文件名, 最小可接受字节数)
ITEMS = [
    # 注：Extra_Supplement 是纯临床表（242 肿瘤 + 220 对照），压缩后仅约 7.3 KB，故下限设小
    ("https://ftp.ncbi.nlm.nih.gov/geo/series/GSE14nnn/GSE14520/suppl/GSE14520_Extra_Supplement.txt.gz",
     "GSE14520_suppl.txt.gz", 2_000),
    ("https://ftp.ncbi.nlm.nih.gov/geo/series/GSE14nnn/GSE14520/matrix/GSE14520-GPL571_series_matrix.txt.gz",
     "GSE14520_GPL571.txt.gz", 1_000_000),
    ("https://ftp.ncbi.nlm.nih.gov/geo/series/GSE14nnn/GSE14520/matrix/GSE14520-GPL3921_series_matrix.txt.gz",
     "GSE14520_GPL3921.txt.gz", 1_000_000),
    ("https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL3nnn/GPL3921/annot/GPL3921.annot.gz",
     "GPL3921.annot.gz", 10_000),
    ("https://ftp.ncbi.nlm.nih.gov/geo/series/GSE76nnn/GSE76427/matrix/GSE76427_series_matrix.txt.gz",
     "GSE76427_series_matrix.txt.gz", 500_000),
    ("https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL10nnn/GPL10558/annot/GPL10558.annot.gz",
     "GPL10558.annot.gz", 10_000),
]


def head_ok(url, timeout=30):
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Length")
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:                       # noqa: BLE001
        return "ERR:%s" % type(e).__name__, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/tmp", help="下载目标目录（默认 /tmp，与现有脚本一致）")
    ap.add_argument("--check", action="store_true", help="只做 HEAD 校验，不下载")
    a = ap.parse_args()
    os.makedirs(a.dir, exist_ok=True)

    bad = 0
    for url, name, minbytes in ITEMS:
        dst = os.path.join(a.dir, name)
        status, clen = head_ok(url)
        mark = "✅" if status == 200 else "❌"
        print("%s %-34s HTTP %-6s %s" % (mark, name, status,
                                         ("%s bytes" % clen) if clen else ""))
        if status != 200:
            bad += 1
            continue
        if a.check:
            continue
        print("     下载 %s ..." % url.split("/")[-1], end=" ", flush=True)
        urllib.request.urlretrieve(url, dst)
        n = os.path.getsize(dst)
        assert n >= minbytes, "下载不完整：%s 仅 %d 字节（期望 ≥ %d）" % (dst, n, minbytes)
        with gzip.open(dst, "rb") as f:          # 完整性校验
            f.read(1 << 16)
        h = hashlib.md5(open(dst, "rb").read()).hexdigest()
        print("OK  %d bytes  md5 %s" % (n, h))

    if a.check:
        print("\n校验结束：%d 项失败（0 = 全部可用）" % bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
