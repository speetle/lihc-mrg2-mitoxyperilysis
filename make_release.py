#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_release.py —— 从活动目录重新装配代码与数据发布包（幂等、防漂移）

设计原则：**本包是生成物**。活动目录（分析脚本/、数据/、补充材料/、图件_v2/）才是唯一真相；
本脚本每次运行都重新装配 scripts/、data/、supplementary/、figures/，因此包内不会有陈旧副本。

用法
  python make_release.py                 # 装配目录 + 打 zip（含 figures）
  python make_release.py --no-figures    # 不打图件（包更小）
  python make_release.py --zip-only      # 只按现有内容打 zip
  python make_release.py --include-local # 连 A 类脚本一并打包（默认不打包；B 类始终不打包）
"""
import os, sys, re, shutil, zipfile, hashlib, argparse, datetime, ast

HERE = os.path.dirname(os.path.abspath(__file__))
# 发布包位于 <交付目录>/发布包_代码与数据/
DELIV = os.path.dirname(HERE)
SRC = {
    "scripts":     os.path.join(DELIV, "分析脚本"),
    "data":        os.path.join(DELIV, "数据"),
    "supplementary": os.path.join(DELIV, "补充材料"),
    "figures":     os.path.join(DELIV, "图件_v2"),
}
# 稿件：图注与正文中引用的数字都在这份文件里，作为校验锚一并收录
ANCHOR = os.path.join(DELIV, "学生3_LIHC_MRG预后_SCI稿件_v1.10.md")

JUNK_DIRS = {"__pycache__", "历史版本_v1.0", "旧分析脚本", ".ipynb_checkpoints"}
JUNK_SUFFIX = (".bak", ".pyc", ".log")
JUNK_PREFIX = ("._", "~$")

# zip 条目统一用固定时间戳 → 整包逐字节可复现（连续两轮 SHA256 必须相同）
FIXED_DT = (2026, 10, 5, 0, 0, 0)

# ── 两类脚本不予公开（装配时自动识别、跳过，并如实登记于《未发布脚本清单.md》，不隐藏）
#    A 类：写死本机绝对路径 —— 公开后既泄露本机目录结构、在他人机器上也必然失败
#    B 类：内嵌**已退役的署名占位符** —— 终稿已按 sir 确认改为**单一作者**，
#          公开等于把已删除的占位符带回公开视野（属「公开＝产生第二个版本」同族缺陷）
LOCAL_PATH_RE = re.compile(r"/Users/[A-Za-z0-9_.\-]+/")
RETIRED_RE = re.compile(r"\[Student\s+name\]")
REASONS = {
    "A": "A 类：含本机绝对路径",
    "B": "B 类：含已退役的署名占位符",
}


def keep(name):
    if name.startswith(JUNK_PREFIX) or name.endswith(JUNK_SUFFIX):
        return False
    if ".bak_" in name:
        return False
    return True


def withhold_reason(path):
    """返回 'A' / 'B' / None —— 该文件是否应扣下，以及理由类别。"""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
    except OSError:
        return None
    if LOCAL_PATH_RE.search(txt):
        return "A"
    if RETIRED_RE.search(txt):
        return "B"
    return None


def copy_tree(src, dst, exts=None, withhold_cats=frozenset()):
    n, skipped = 0, []
    if not os.path.isdir(src):
        return n, skipped
    for dp, dns, fns in os.walk(src):
        dns[:] = [d for d in dns if d not in JUNK_DIRS and not d.startswith(".")]
        rel = os.path.relpath(dp, src)
        out = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(out, exist_ok=True)
        for f in sorted(fns):
            if not keep(f):
                continue
            if exts and not f.lower().endswith(exts):
                continue
            if withhold_cats:
                why = withhold_reason(os.path.join(dp, f))
                if why and why in withhold_cats:
                    skipped.append((os.path.relpath(os.path.join(dp, f), src), why))
                    continue
            shutil.copy2(os.path.join(dp, f), os.path.join(out, f))
            n += 1
    return n, skipped


def file_head(rel):
    """取脚本模块 docstring（无则首个非注释行）前 60 字，用于登记清单。"""
    try:
        with open(os.path.join(SRC["scripts"], rel), encoding="utf-8",
                  errors="ignore") as fh:
            src = fh.read()
    except OSError:
        return "（读取失败）"
    try:
        doc = ast.get_docstring(ast.parse(src)) or ""
    except SyntaxError:
        doc = ""
    if doc:
        return " ".join(doc.split())[:60]
    for x in src.splitlines():
        x = x.strip()
        if x and not x.startswith("#"):
            return x[:60]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--zip-only", action="store_true")
    ap.add_argument("--include-local", action="store_true",
                    help="连 A 类（含本机绝对路径）脚本一并打包；B 类不受此开关影响")
    a = ap.parse_args()

    stamp = datetime.datetime.now().strftime("%Y%m%d")
    counts, all_skipped = {}, {}
    if not a.zip_only:
        for name, src in SRC.items():
            if name == "figures" and a.no_figures:
                continue
            dst = os.path.join(HERE, name)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            exts = None
            cats = frozenset()
            if name == "figures":
                # 矢量 + 位图，够审稿人看，不塞中间态；投稿用 EPS/TIFF 体积大，
                # 属提交附件、不入公开包
                exts = (".pdf", ".png")
            if name == "scripts":
                cats = frozenset({"B"}) if a.include_local else frozenset({"A", "B"})
            n, sk = copy_tree(src, dst, exts, withhold_cats=cats)
            counts[name] = n
            if sk:
                all_skipped[name] = sk
        if os.path.exists(ANCHOR):
            shutil.copy2(ANCHOR, os.path.join(HERE, "稿件锚_学生3_LIHC_v1.10.md"))
            counts["稿件锚"] = 1

        if all_skipped:
            by = {"A": [], "B": []}
            for f, why in all_skipped.get("scripts", []):
                by[why].append(f)
            lines = ["# 未随公开包发布的脚本（如实登记）", "",
                     "以下脚本出现在活动目录 `分析脚本/`，但**未打入公开包**。两类理由，逐类登记：", "",
                     "**A 类**：内部写死了本机绝对路径（`/Users/…`），公开后既泄露本机目录结构、"
                     "在他人机器上也必然失败。",
                     "**B 类**：内嵌**已退役的署名占位符**——终稿已按 sir 确认改为**单一作者**，"
                     "公开等于把已删除的占位符带回公开视野。", "",
                     "A 类多为**稿件处理脚本**（压缩、排版、逐轮一次性变换），对「重算数字」并非必需；"
                     "分析链本身（队列、建模、嵌套 CV、外部验证、校准、PH 诊断、图件、质控）的脚本均已随包发布。",
                     "B 类全部为**稿件处理脚本**，与分析链无关。", "",
                     "如需连同 A 类一并发布，请先把绝对路径改为相对 `__file__` 解析，再运行 "
                     "`python make_release.py --include-local`。**B 类不受该开关影响，始终不入包。**", ""]
            for cat in ("A", "B"):
                lines += ["## " + REASONS[cat], "",
                          "| 脚本 | 用途（据文件头） |", "|---|---|"]
                for f in sorted(by[cat]):
                    lines.append("| `%s` | %s |" % (f, file_head(f) or "（读取失败）"))
                lines += ["", "小计 **%d** 个。" % len(by[cat]), ""]
            lines += ["**合计 %d 个**（A 类 %d ＋ B 类 %d）。"
                      % (len(by["A"]) + len(by["B"]), len(by["A"]), len(by["B"]))]
            with open(os.path.join(HERE, "未发布脚本清单.md"), "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
        elif os.path.exists(os.path.join(HERE, "未发布脚本清单.md")):
            os.remove(os.path.join(HERE, "未发布脚本清单.md"))

    dist = os.path.join(HERE, "dist")
    os.makedirs(dist, exist_ok=True)
    zpath = os.path.join(dist, "学生3_LIHC_代码与数据_v1.0.3_%s.zip" % stamp)
    files = []
    for dp, dns, fns in os.walk(HERE):
        dns[:] = [d for d in dns
                  if d != "dist" and d not in JUNK_DIRS and not d.startswith(".")]
        for f in fns:
            files.append(os.path.join(dp, f))

    # ── 发布前硬闸门：公开包里不得出现本机绝对路径，也不得出现已退役的署名占位符
    leaks = []
    for p in files:
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
        except OSError:
            continue
        if LOCAL_PATH_RE.search(txt):
            leaks.append((os.path.relpath(p, HERE), "A"))
        elif RETIRED_RE.search(txt):
            leaks.append((os.path.relpath(p, HERE), "B"))
    if leaks:
        for rel, cat in leaks:
            print("❌ [%s 类泄漏] %s" % (cat, rel))
        raise SystemExit("❌ 发布前闸门未通过：包内仍有 %d 个文件含禁列字符串" % len(leaks))
    print("✅ 发布前闸门通过：包内 0 处本机绝对路径、0 处已退役署名占位符")

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(files):
            rel = os.path.relpath(p, HERE)
            # ★ 固定时间戳：zip 条目默认写「源文件 mtime」，而 `未发布脚本清单.md` 是每次
            #   运行新写的 → 连续两轮 SHA 会不同。固定后整包逐字节可复现
            #   （口径与图件/PDF 的 SOURCE_DATE_EPOCH 修法一致）。
            zi = zipfile.ZipInfo(rel, date_time=FIXED_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = (0o755 if rel.endswith(".sh") else 0o644) << 16
            with open(p, "rb") as fh:
                z.writestr(zi, fh.read())

    h = hashlib.sha256()
    with open(zpath, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    mb = os.path.getsize(zpath) / 1024 / 1024

    print("装配清单：")
    for k, v in counts.items():
        print("  %-14s %d 个文件" % (k, v))
    print("\n压缩包：%s" % os.path.relpath(zpath, DELIV))
    print("  大小   : %.1f MB" % mb)
    print("  文件数 : %d" % len(files))
    print("  SHA256 : %s" % h.hexdigest())
    print("\n⚠️ 上传/推送前请确认：")
    print("   1. 许可已落定：代码 LICENSE（MIT）、数据 LICENSE-DATA.md（CC BY 4.0）——无需再改名")
    print("   2. CITATION.cff 的 repository-code 已填")
    print("   3. 作者栏已按 sir 2026-10-05 确认改为**单一作者** Bin Lian；"
          "CITATION.cff 的学生作者 TODO 块已删除")


if __name__ == "__main__":
    main()
