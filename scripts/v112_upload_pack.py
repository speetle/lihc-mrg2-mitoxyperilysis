#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
v112_upload_pack.py —— 装配唯一投稿夹 `投稿_DDS/`（LIHC → Digestive Diseases and Sciences）

**这个夹子就是 sir 上传时唯一要打开的文件夹。**

分工（避免同一事实两处各写一遍、并排才矛盾）：
  · 本脚本出 `00_上传清单_DDS.md` —— **机器生成**的文件清单（EM 的 Item Type ＋ 包内路径
    ＋ 字节数），是「传哪些文件」的**唯一权威**；
  · `00_投稿操作单_DDS.{md,docx}` 只讲**在 EM 里怎么点**，文件清单引用前者，不再复述字节数。

本脚本做五件事：
 1. 建/刷新 `03_Figures/`：主图 6 张取 `图件_v2/投稿格式/*.eps`
    （DDS 明文收 EPS/TIFF，**不收 PDF**）；不给 Tables / Figure legends 单独占位 ——
    二者已内嵌在稿件 DOCX 里。
 2. 建/刷新 `04_Supplementary/`：每个 CSV 加 3 行 `#` 注释头（Springer SI 要求每个文件
    自证文章题名/期刊/作者/通讯地址邮箱），**数值部分逐字节不变**（脚本内断言）；
    补充图 S1（EPS）与 TRIPOD 清单（DOCX）一并放入。
 3. 刷新 `05_Graphical_Abstract.{tif,png}`：取 `图件_v2/图形摘要/`。
 4. 校验 `01_Cover_Letter.docx` 与 `02_Manuscript_LIHC_MRG2.docx` 在位
    （前者由目录重组步骤放入；后者由 `v112_submission_format.py` 生成）；
    校验 `06_审稿人候选_核验记录.md` 在位。
 5. 写 `00_上传清单_DDS.md`。

**不动的东西**：`00_投稿操作单_DDS.*`、`01_Cover_Letter.*`、`06_审稿人候选_核验记录.md`
由人工/其他脚本维护，本脚本只读不写（只做在位断言）。

设计原则：03/04/05 三个子目录**完全是生成物**，可反复重跑；所有副本都断言与原件的字节关系。
    - 逐字节相同：封面信 / 稿件 / 图件 / TRIPOD DOCX / 图形摘要
    - 去注释头后逐字节相同：每个补充 CSV
"""
import hashlib
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
DELIV = os.path.dirname(HERE)
OUT = os.path.join(DELIV, "投稿_DDS")

MS = os.path.join(DELIV, "Manuscript_LIHC_v1.12.md")
COVER = os.path.join(OUT, "01_Cover_Letter.docx")            # 由重组步骤放入
MANU = os.path.join(OUT, "02_Manuscript_LIHC_MRG2.docx")     # 由 v112_submission_format.py 生成
OPNOTE = os.path.join(OUT, "00_投稿操作单_DDS.md")
REVIEWERS = os.path.join(OUT, "06_审稿人候选_核验记录.md")
FIGDIR = os.path.join(DELIV, "图件_v2", "投稿格式")
GADIR = os.path.join(DELIV, "图件_v2", "图形摘要")
SUPDIR = os.path.join(DELIV, "补充材料")
TRIPOD_DOCX = os.path.join(DELIV, "Supplementary_Item_1_TRIPOD_checklist.docx")

# 本脚本独占的子目录（每次重跑先清空再重装）
OWNED = ["03_Figures", "04_Supplementary"]
# 只读、只断言在位；每项自带 (上传序, EM Item Type)，避免清单里出现空槽位
EXTERNAL = [
    (OPNOTE, "00_投稿操作单_DDS.md", "-", "（不上传 · 操作步骤）", "人工维护的操作单"),
    (COVER, "01_Cover_Letter.docx", "1", "Cover Letter", "由目录重组步骤放入"),
    (MANU, "02_Manuscript_LIHC_MRG2.docx", "2", "Manuscript",
     "由 分析脚本/v112_submission_format.py 生成"),
    (REVIEWERS, "06_审稿人候选_核验记录.md", "-", "（不上传 · EM 里逐条填）",
     "人工维护的审稿人核验记录"),
]

TITLE = ("Stability selection does not guarantee external transport: a mitoxyperilysis score "
         "fails validation in hepatocellular carcinoma")
JOURNAL = "Digestive Diseases and Sciences"
AUTHOR = ("Bin Lian, School of Health, Guangzhou Vocational and Technical University of "
          "Science and Technology, Guangzhou, Guangdong, China")
EMAIL = "drmilo@gkd.edu.cn"

FIG_MAIN = ["Figure%d.eps" % i for i in range(1, 7)]
FIG_SUP = ["FigureS1_calibration.eps"]
GA_FILES = ["Graphical_Abstract.tif", "Graphical_Abstract.png"]
# 图形摘要随附短句：DDS 规定 140–200 字符（IFA p.5）
GA_LEGEND = ("A stage-independent mitoxyperilysis score passes every internal check yet fails "
             "external transport: report nested estimates, seed replication and a random-panel "
             "benchmark before claiming transport.")


def die(msg):
    raise SystemExit("❌ " + msg)


def read_bytes(p):
    with open(p, "rb") as fh:
        return fh.read()


def sha_of(p):
    return hashlib.sha256(read_bytes(p)).hexdigest()


def copy_assert(src, dst):
    """复制并断言逐字节一致。"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    if sha_of(src) != sha_of(dst):
        die("副本与原件字节不一致：%s" % os.path.basename(dst))
    return len(read_bytes(dst))


def table_desc():
    """从稿件里抽 Supplementary Table Sx 的一句话说明（单一权威：稿件正文）。"""
    t = open(MS, encoding="utf-8").read()
    pat = re.compile(r"^\*\*Supplementary Table (S\d+b?)\.\*\*\s*(.+)$", re.M)
    return {m.group(1): m.group(2).strip() for m in pat.finditer(t)}


def main():
    # ── 0. 前置检查 ──────────────────────────────────────────────
    for p in [MS, TRIPOD_DOCX] + [s for s, _, _, _, _ in EXTERNAL]:
        if not os.path.exists(p):
            die("缺文件：%s" % p)
    for f in FIG_MAIN + FIG_SUP:
        if not os.path.exists(os.path.join(FIGDIR, f)):
            die("缺图件：%s" % f)
    for f in GA_FILES:
        if not os.path.exists(os.path.join(GADIR, f)):
            die("缺图形摘要：%s" % f)

    desp = table_desc()
    if len(desp) < 16:
        die("稿件里只解析到 %d 条 Supplementary Table 说明（应 ≥16）" % len(desp))
    if not (140 <= len(GA_LEGEND) <= 200):
        die("图形摘要短句长度 %d 不在 DDS 规定的 140–200 字符内" % len(GA_LEGEND))

    os.makedirs(OUT, exist_ok=True)
    for d in OWNED:
        p = os.path.join(OUT, d)
        if os.path.isdir(p):
            shutil.rmtree(p)

    manifest = []                    # (上传序, EM Item Type, 包内相对路径, 字节)

    # ── 外部件：只登记，不复制 ───────────────────────────────────
    for p, rel, order, itype, _who in EXTERNAL:
        manifest.append((order, itype, rel, os.path.getsize(p)))

    # ── 3. Figures（EPS；DDS 不收 PDF）───────────────────────────
    for f in FIG_MAIN:
        sz = copy_assert(os.path.join(FIGDIR, f), os.path.join(OUT, "03_Figures", f))
        manifest.append(("5", "Figure", "03_Figures/%s" % f, sz))

    # ── 4. Supplementary ─────────────────────────────────────────
    os.makedirs(os.path.join(OUT, "04_Supplementary"), exist_ok=True)

    csvs = sorted(f for f in os.listdir(SUPDIR) if f.lower().endswith(".csv"))
    if len(csvs) < 18:
        die("补充材料 CSV 只有 %d 个（应 ≥18）" % len(csvs))

    stamped = []
    for f in csvs:
        m = re.search(r"Table_(S\d+b?)_", f)
        if not m:
            die("CSV 文件名里取不到 S 编号：%s" % f)
        sid = m.group(1)
        if sid not in desp:
            die("稿件里没有 Supplementary Table %s 的说明" % sid)
        raw = read_bytes(os.path.join(SUPDIR, f))
        head = (
            "# %s\n" % TITLE
            + "# %s | %s | %s\n" % (JOURNAL, AUTHOR, EMAIL)
            + "# Supplementary Table %s. %s Data rows below the three comment lines are "
              "byte-identical to the deposited derived-data file.\n" % (sid, desp[sid])
        ).encode("utf-8")
        dst = os.path.join(OUT, "04_Supplementary", "Supplementary_Table_%s.csv" % sid)
        with open(dst, "wb") as fh:
            fh.write(head + raw)
        # ── 断言：剥掉 `#` 注释行后与原文件逐字节一致 ──
        back = read_bytes(dst)
        stripped = b"".join(ln for ln in back.splitlines(keepends=True)
                            if not ln.startswith(b"#"))
        if stripped != raw:
            die("S%s 去注释头后与原 CSV 不一致" % sid)
        if not back.startswith(b"# ") or back.count(b"\n", 0, len(head)) != 3:
            die("S%s 注释头不是 3 行" % sid)
        stamped.append(sid)
        manifest.append(("6", "Supplementary Material",
                         "04_Supplementary/Supplementary_Table_%s.csv" % sid, len(back)))

    # 补充图 S1（EPS）
    f = FIG_SUP[0]
    sz = copy_assert(os.path.join(FIGDIR, f), os.path.join(OUT, "04_Supplementary", f))
    manifest.append(("6", "Supplementary Material", "04_Supplementary/%s" % f, sz))

    # TRIPOD 清单
    rel = "04_Supplementary/Supplementary_Item_1_TRIPOD_checklist.docx"
    sz = copy_assert(TRIPOD_DOCX, os.path.join(OUT, rel))
    manifest.append(("6", "Supplementary Material", rel, sz))

    # ── 5. 图形摘要（单独一个 "figure" 槽位）────────────────────
    for f in GA_FILES:
        sz = copy_assert(os.path.join(GADIR, f), os.path.join(OUT, "05_%s" % f))
        manifest.append(("6", "Figure (graphical abstract)", "05_%s" % f, sz))

    # ── 6. 上传清单（机器生成，唯一权威）────────────────────────
    lines = [
        "# 上传清单（Digestive Diseases and Sciences）",
        "",
        "> 本清单由 `分析脚本/v112_upload_pack.py` **机器生成**，是「传哪些文件」的唯一权威；",
        "> 操作步骤见同目录 `00_投稿操作单_DDS.md`。",
        "> 本目录 03/04/05 三个子目录为**生成物**，不要手工改动；",
        "> 活动源目录仍是 `分析脚本/`、`数据/`、`补充材料/`、`图件_v2/`。",
        "",
        "## 文件清单（按 DDS 规定的上传顺序）",
        "",
        "| 上传序 | EM 里的 Item Type | 本目录文件 | 字节 |",
        "|---|---|---|---|",
    ]
    def _ord(rec):
        o = rec[0]
        return (0, int(o), rec[2]) if o.isdigit() else (1, 0, rec[2])

    for order, itype, rel, sz in sorted(manifest, key=_ord):
        lines.append("| %s | %s | `%s` | %s |" % (order, itype, rel, format(sz, ",")))
    lines += [
        "",
        "**上传顺序依据**：DDS Instructions for Authors —— "
        "`1. Cover letter → 2. Manuscript → 3. Tables → 4. Figure legends → 5. Figures → 6. Other`。"
        "Tables 与 Figure legends 已内嵌稿件 DOCX，本目录不单独占位。",
        "",
        "## 图形摘要（Online Abstract Figure）",
        "",
        "`05_Graphical_Abstract.tif`（备选 `.png`）作为**单独一个 figure 槽位**上传，标签用 "
        "**\"Online Abstract Figure\"**，随附短句（%d 字符，DDS 规定 140–200）：" % len(GA_LEGEND),
        "",
        "> " + GA_LEGEND,
        "",
        "规格：**920×300 px**、TIFF **%.1f KB**（上限 150 KB）、Arial；"
        "由 Matplotlib 从 `数据/*.json` 直绘（**非生成式 AI 图像**）。" % (
            os.path.getsize(os.path.join(GADIR, "Graphical_Abstract.tif")) / 1024),
        "",
        "## 关于补充表的 `#` 注释头",
        "",
        "Springer 要求每个补充材料文件自证文章题名、期刊、作者与通讯地址邮箱。"
        "本目录每个 CSV 前 3 行是 `#` 注释（文章题名 / 期刊｜作者｜邮箱 / 表号与说明），"
        "**其后的数值部分与 `补充材料/` 里的原始 CSV 逐字节相同** —— "
        "装配脚本每次运行都会断言这一点。用 pandas 读取时加 `comment='#'` 即可。",
        "",
        "## 图件为何是 EPS",
        "",
        "DDS 明写收 `TIFF, GIF, JPEG, EPS, PPT, Postscript`，并且「**PDF is not an acceptable "
        "file format for manuscripts or figures**」。故上传件取 EPS（矢量、字体已嵌入）；"
        "TIFF 600 dpi 版在同目录 `图件_v2/投稿格式/` 里作为备选，不要上传 PNG 或 PDF。",
        "",
        "## 仍需在 EM 界面里填写、不落文本文件的内容",
        "",
        "- **Suggested reviewers**（DDS 要 4–6 位，须给出姓名/院系/单位/邮箱）在 EM 对应步骤逐条填入；",
        "  候选与核验出处见本目录 `06_审稿人候选_核验记录.md`。",
        "- **Author contributions / Competing interests** 在 EM 界面里填写"
        "（Springer：「Only the information submitted via the interface will be used in the "
        "final published version」）。",
    ]
    with open(os.path.join(OUT, "00_上传清单_DDS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    # ── 7. 收尾自检 ─────────────────────────────────────────────
    total = sum(sz for _, _, _, sz in manifest)
    nfile = sum(1 for dp, dns, fns in os.walk(OUT) for _ in fns)
    print("OK -> %s" % os.path.relpath(OUT, DELIV))
    print("    上传件登记 %d 项 | 夹内文件合计 %d 个 | 登记字节合计 %.2f MB"
          % (len(manifest), nfile, total / 1048576))
    nat = sorted(stamped, key=lambda s: (int(re.match(r"S(\d+)", s).group(1)), s))
    print("    图件 EPS %d | 补充 CSV %d（%s…%s）| 补充图 EPS 1 | TRIPOD 1 | 图形摘要 %d"
          % (len(FIG_MAIN), len(stamped), nat[0], nat[-1], len(GA_FILES)))
    print("    断言：全部副本逐字节一致；每个 CSV 去注释头后与原件逐字节一致")


if __name__ == "__main__":
    main()
