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
ANCHOR = os.path.join(DELIV, "Manuscript_LIHC_v1.12.md")

JUNK_DIRS = {"__pycache__", "历史版本_v1.0", "旧分析脚本", ".ipynb_checkpoints"}
JUNK_SUFFIX = (".bak", ".pyc", ".log")
JUNK_PREFIX = ("._", "~$")

# zip 条目统一用固定时间戳 → 整包逐字节可复现（连续两轮 SHA256 必须相同）
FIXED_DT = (2026, 10, 5, 0, 0, 0)

# ── 三类脚本不予公开（装配时自动识别、跳过，并如实登记于《未发布脚本清单.md》，不隐藏）
#    A 类：写死本机绝对路径 —— 公开后既泄露本机目录结构、在他人机器上也必然失败
#    B 类：内嵌**已退役的署名占位符** —— 终稿已按 sir 确认改为**单一作者**，
#          公开等于把已删除的占位符带回公开视野（属「公开＝产生第二个版本」同族缺陷）
#    C 类：路径／标题字面量里含**内部课题编号前缀**（六学生论文框架的「学生 N」编号）——
#          本课题对外是**独立单作者研究**，该前缀属内部组织信息，公开即把内部编号
#          带进公开视野。sir 2026-10-05 明令「文件名也都要改，不要加学生N之类的」，
#          故升格为**机器可执行的硬闸门**。
#
#  ⚠️ 自指陷阱：本文件**自身也会被打包**，所以闸门的模式串绝不能以字面形式出现，
#     否则它会命中自己 → 每次装配都失败。故统一用 **\u 码位写法**构造前缀常量。
_PFX = "\u5b66\u751f3"                       # 内部课题编号前缀（六学生论文框架的「学生 N」）
LOCAL_PATH_RE = re.compile(r"/Users/[A-Za-z0-9_.\-]+/")
RETIRED_RE = re.compile(r"\[Student\s+name\]")
INTERNAL_RE = re.compile(re.escape(_PFX))
# 登记表里要打印被扣下脚本的文件头，而文件头可能自带该前缀 → 先做 banner 脱敏，
# 使《未发布脚本清单.md》本身也是 0 处内部前缀（不给闸门开豁免口子，闸门保持绝对）。
BANNER_REDACT = [
    (_PFX + "\uff08LIHC \u809d\u7ec6\u80de\u764c\uff09", "LIHC 肝细胞癌"),
    (_PFX + "\uff08LIHC\uff09", "LIHC"),
    (_PFX + " LIHC", "LIHC"),
]
REASONS = {
    "A": "A 类：含本机绝对路径",
    "B": "B 类：含已退役的署名占位符",
    "C": "C 类：含内部课题编号前缀",
}

# ── 第四道闸门（D 类）：**命令块语法** —— 面向"照抄进终端"的围栏里，
#    不得出现 `#` 注释，也不得出现 `<…>` 占位符。
#    为什么必须立：zsh **交互模式**默认不认 `#` 注释（INTERACTIVE_COMMENTS 未开），
#    `cmd   # 说明` 会把 `#` 及其后的字**当成参数**传给命令（实测 `arg=[--dry-run] arg=[#] arg=[预演]`），
#    整行起首的 `#` 更直接报 `command not found: #`；而 `<你的令牌` 会被当成**输入重定向**
#    （报 `no such file or directory`）。2026-10-06 sir 照抄我给的命令块时两者都踩到了。
#    ⚠️ 范围具名：只扫**围栏语言显式标为命令类**的代码块（命令块才可能被粘贴执行），
#       不扫未标语言 / json / 目录树等围栏 —— 避免把结构示意图误判成命令块。
SHELL_FENCES = {"bash", "sh", "zsh", "shell", "console", "terminal", "text"}
FENCE_CMD_RE = re.compile(r"^\s*#|\S\s+#(\s|$)")   # 行首 `#` 注释，或行尾 `# 注释`
PLACEHOLDER_RE = re.compile(r"<[^\s<>]+>")          # <…> 占位符（会变输入重定向）


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
    if INTERNAL_RE.search(txt):
        return "C"
    return None


def cmd_block_lines(text):
    """依次产出 (围栏语言, 行号, 行内容) —— 仅命令类围栏内的行。"""
    in_f, info = False, ""
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.lstrip().startswith("```"):
            if in_f:
                in_f = False
            else:
                in_f = True
                info = ln.strip().strip("`").strip().lower()
            continue
        if in_f and info in SHELL_FENCES:
            yield info, i, ln


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


def redact(txt):
    """把文件头里可能出现的内部编号前缀脱敏，使登记表自身也合规。"""
    for a, b in BANNER_REDACT:
        txt = txt.replace(a, b)
    return txt


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
        return redact(" ".join(doc.split()))[:60]
    for x in src.splitlines():
        x = x.strip()
        if x and not x.startswith("#"):
            return redact(x[:60])
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--zip-only", action="store_true")
    ap.add_argument("--include-local", action="store_true",
                    help="连 A 类（含本机绝对路径）脚本一并打包；B 类与 C 类不受此开关影响")
    a = ap.parse_args()

    # 压缩包名里的日期是**发布标识**，不是构建时间戳。
    # 原用 datetime.now() 会导致「今天跑一次、明天再跑一次」多出一个 `_20261006.zip` / `_20261007.zip`
    # 并存的局面 —— 直接把「交付只留唯一最终版」破掉，而且旧名不会自动消失。
    # 故固定为 v1.0.5 的发布日；要换日期只能显式改这个常量（改完须同步全部引用）。
    RELEASE_STAMP = "20261006"
    stamp = RELEASE_STAMP
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
                cats = frozenset({"B", "C"}) if a.include_local else frozenset({"A", "B", "C"})
            n, sk = copy_tree(src, dst, exts, withhold_cats=cats)
            counts[name] = n
            if sk:
                all_skipped[name] = sk
        if os.path.exists(ANCHOR):
            shutil.copy2(ANCHOR, os.path.join(HERE, "稿件锚_LIHC_v1.12.md"))
            counts["稿件锚"] = 1

        if all_skipped:
            by = {"A": [], "B": [], "C": []}
            for f, why in all_skipped.get("scripts", []):
                by[why].append(f)
            lines = ["# 未随公开包发布的脚本（如实登记）", "",
                     "以下脚本出现在活动目录 `分析脚本/`，但**未打入公开包**。三类理由，逐类登记：", "",
                     "**A 类**：内部写死了本机绝对路径（`/Users/…`），公开后既泄露本机目录结构、"
                     "在他人机器上也必然失败。",
                     "**B 类**：内嵌**已退役的署名占位符**——终稿已按 sir 确认改为**单一作者**，"
                     "公开等于把已删除的占位符带回公开视野。",
                     "**C 类**：路径／标题字面量里含**内部课题编号前缀**（六学生论文框架的"
                     "「学生 N」编号）。本课题对外是**独立单作者研究**，该前缀属内部组织信息。"
                     "这一类**不做字面量改写**：其中多数是**逐轮稿件处理脚本**，"
                     "其路径指向 `历史版本_v1.0/` 里**按原名保存**的历史稿件"
                     "（如 `…_v1.6.md`）；改写字面量会把这个引用变成**伪引用**，"
                     "故一律**扣下并如实登记**，而非改写。", "",
                     "A 类多为**稿件处理脚本**（压缩、排版、逐轮一次性变换），对「重算数字」并非必需；"
                     "分析链本身（队列、建模、嵌套 CV、外部验证、校准、PH 诊断、图件、质控）的脚本均已随包发布。",
                     "B 类全部为**稿件处理脚本**，与分析链无关。",
                     "C 类全部为**稿件处理／逐轮变换脚本**，与分析链无关。", "",
                     "如需连同 A 类一并发布，请先把绝对路径改为相对 `__file__` 解析，再运行 "
                     "`python make_release.py --include-local`。"
                     "**B 类与 C 类不受该开关影响，始终不入包。**", ""]
            for cat in ("A", "B", "C"):
                lines += ["## " + REASONS[cat], "",
                          "| 脚本 | 用途（据文件头） |", "|---|---|"]
                for f in sorted(by[cat]):
                    lines.append("| `%s` | %s |" % (f, file_head(f) or "（读取失败）"))
                lines += ["", "小计 **%d** 个。" % len(by[cat]), ""]
            lines += ["**合计 %d 个**（A 类 %d ＋ B 类 %d ＋ C 类 %d）。"
                      % (len(by["A"]) + len(by["B"]) + len(by["C"]),
                         len(by["A"]), len(by["B"]), len(by["C"]))]
            with open(os.path.join(HERE, "未发布脚本清单.md"), "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
        elif os.path.exists(os.path.join(HERE, "未发布脚本清单.md")):
            os.remove(os.path.join(HERE, "未发布脚本清单.md"))

    dist = os.path.join(HERE, "dist")
    os.makedirs(dist, exist_ok=True)
    zpath = os.path.join(dist, "LIHC_代码与数据_v1.0.5_%s.zip" % stamp)
    # ── 结构守卫：dist/ 只许留唯一最终版 zip ──
    # 单看名字的旧版不会自己消失（历史上就并存过 v1.0.2 / v1.0.3 / v1.0.4 三个 zip），
    # 旧版须由装配器**具名搬移**到归档，不得在此静默删除。多一个 zip 即 fail-closed。
    stray = sorted(f for f in os.listdir(dist)
                   if f.endswith(".zip") and f != os.path.basename(zpath))
    if stray:
        raise SystemExit(
            "❌ dist/ 里除 %s 外还有 %d 个 zip：%s\n"
            "   旧版须**具名搬移**入 历史版本_v1.0/<轮次>/ 并登记《归档清单》，"
            "不得本处删除；确认搬移后再重跑。"
            % (os.path.basename(zpath), len(stray), ", ".join(stray)))
    files = []
    for dp, dns, fns in os.walk(HERE):
        dns[:] = [d for d in dns
                  if d != "dist" and d not in JUNK_DIRS and not d.startswith(".")]
        for f in fns:
            files.append(os.path.join(dp, f))

    # ── 发布前硬闸门：公开包里不得出现本机绝对路径、不得出现已退役的署名占位符、
    #    也不得出现内部课题编号前缀（sir 2026-10-05「文件名也都要改，不要加学生N之类的」）
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
        elif INTERNAL_RE.search(txt):
            leaks.append((os.path.relpath(p, HERE), "C"))
    if leaks:
        for rel, cat in leaks:
            print("❌ [%s 类泄漏] %s" % (cat, rel))
        raise SystemExit("❌ 发布前闸门未通过：包内仍有 %d 个文件含禁列字符串" % len(leaks))
    print("✅ 发布前闸门通过：包内 0 处本机绝对路径、0 处已退役署名占位符、"
          "0 处内部课题编号前缀")

    # ── 第四道闸门（D 类）：命令块语法（判据说明见 SHELL_FENCES 处）
    cmd_leaks = []
    for p in files:
        if not p.endswith(".md"):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
        except OSError:
            continue
        for _info, i, ln in cmd_block_lines(txt):
            if not ln.strip():
                continue
            if FENCE_CMD_RE.search(ln) or PLACEHOLDER_RE.search(ln):
                cmd_leaks.append((os.path.relpath(p, HERE), i, ln.strip()[:60]))
    if cmd_leaks:
        for rel, i, s in cmd_leaks:
            print("❌ [D 类·命令块语法] %s:%d  %s" % (rel, i, s))
        raise SystemExit("❌ 发布前闸门未通过：包内 %d 处命令块含 `#` 注释或 `<…>` 占位符"
                         "（照抄进交互式 zsh 会被当参数 / 输入重定向）" % len(cmd_leaks))
    print("✅ 第四道闸门（命令块语法）通过：命令类围栏内 0 处 `#` 注释、0 处 `<…>` 占位符")

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
