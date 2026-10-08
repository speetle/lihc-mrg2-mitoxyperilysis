# LIHC —— 代码与数据发布包

**配套稿件**：*Stability selection does not guarantee external transport: a mitoxyperilysis score fails validation in hepatocellular carcinoma*
**作者（通讯作者）**：连彬（Bin Lian），School of Health, Guangzhou Vocational and Technical University of Science and Technology，drmilo@gkd.edu.cn，ORCID 0000-0002-1477-9137
**快照日期**：2026-10-05

---

## 一、这个包里有什么

```
├── scripts/          分析、制图与质控脚本（29 个 .py ＋ 4 个 Illustrator .jsx ＋ 1 个豁免 JSON ＋ 1 个面板清单；被扣下的 51 个脚本见 未发布脚本清单.md：A 类 28 ＋ B 类 9 ＋ C 类 14）
├── data/             脚本产出的机器可读中间产物（逐患者数据、系数、JSON 汇总）
├── supplementary/    补充表 S1–S16、S4b、TRIPOD 对照清单（投稿用）
├── figures/          6 张主图 + 1 张补充图的 PDF/PNG（可选，见 make_release.py；
│                     投稿用的 EPS/TIFF 属附件、不入公开包）
├── requirements.txt  依赖锁定（pip freeze 快照）
├── 数据字典.md        每个 data/ 与 supplementary/ 文件的字段说明与来源
├── 复现步骤.md        从零到全部数字的复现路径（含每步预期输出）
├── RERUN.sh          一键重跑（在干净 venv 内）
├── make_release.py   打包脚本：从活动目录重新装配本包，保证不漂移
├── push_to_github.sh 推送脚本：以「克隆远端 → 镜像同步 → 提交 → 推回」更新仓库（保留提交历史）；支持 `--dry-run` 预演（机制部分离线、不需令牌；随后**联网**只读克隆真远端做影响面核对，连不上则**降级并以退出码 3 结束**，不算通过）；凭据只走环境变量 GH_TOKEN，不落盘
├── CITATION.cff      Zenodo / GitHub 引用元数据
├── LICENSE           代码许可（MIT）
├── LICENSE-DATA.md   数据许可（CC BY 4.0）＋上游数据来源与各自条款
├── 未发布脚本清单.md   未随包发布的脚本逐条登记（A 类 28 ＋ B 类 9 ＋ C 类 14，共 51 件）
├── 稿件锚_LIHC_v1.12.md 终稿的 Markdown 快照，供图注/正文数值一致性比对（由 make_release.py 复制自交付目录）
└── .gitignore
```

## 二、复现性声明

本研究的全部数字均由本包内的脚本从**公开数据**产出，不存在任何手工填入的数值：

- **发现队列**：cBioPortal `lihc_tcga_pan_can_atlas_2018`（TCGA-LIHC）
- **主外部队列**：GEO **GSE14520**（Roessler et al.）
- **效能不足的阴性对照**：GEO **GSE76427**
- **面板定义**：课题组前期研究（母论文 P1），面板链 101 小鼠 → 92 人类直系同源 → 91 在 TCGA-LIHC 可评估

机械校验随包提供（下表已标出哪几支**不在包内**，被扣下的原因与完整清单见 `未发布脚本清单.md`）：

| 校验器 | 作用 | 最近一次结果 | 是否随包 |
|---|---|---|---|
| `数值指纹.py` | 抽取全稿数值与引文编号的多重集，作为改动基线 | 914 种数值 / 43 组引文 | ✅ |
| `compress_gate.py` | 压缩前后**唯一数值不得丢失、不得凭空新增、引文编号多重集不变** | 通过（含 11 条已核销项，均指向一次实跑产物） | ✅ |
| `figcheck_overlap.py` | 图件「文字压数据」机械判据（文字压数据 / 越界邻面板 / 面板互压 / 图例压数据 / 文字互压） | 6 图命中 0 | ✅ |
| `figcheck_lihc.py` | 图件字号下限、tight 宽度、坐标刻度重叠 | 6/6 通过 | ❌ 见 `未发布脚本清单.md` |
| `ref_audit_v15.py` | 参考文献双源交叉核验（PubMed esummary + Crossref） | Crossref 41/41、PubMed 39/39、问题 0 | ❌ 见 `未发布脚本清单.md` |

⚠️ `ref_audit_v15.py` 若自行改写后使用，**必须批量调用**（PubMed 一次多 PMID、Crossref `filter=doi:` 每 20 条一批）。逐条查询会因单次 HTTPS 往返约 5.5 s 而超出执行窗口被杀。

## 三、怎么用

环境准备：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

一键重跑（约 40–60 分钟；含 10 个独立随机划分的完全嵌套 CV）：

```bash
bash RERUN.sh
```

只想重跑其中某一项 —— 下面四条命令依次是：**稳健性六件套**、**主外部验证**、
**pooled out-of-fold C-index ＋ 多随机划分**、**图件机械校验**：

```bash
python scripts/stats_hardening.py
python scripts/external_GSE14520.py
python scripts/r1m8_nested_pooled.py
python scripts/figcheck_overlap.py
```

## 四、重要提醒

1. **本包不含 .bak / 历史版本**：`make_release.py` 在装配时会剔除所有备份与归档，`data/` 与 `supplementary/` 为当前有效版本。
2. **许可**：代码 **MIT**（`LICENSE`），数据 **CC BY 4.0**（`LICENSE-DATA.md`）。
   数据部分的上游来源（TCGA / GEO）各自条款不因本许可而改变，再分发须一并遵守。
3. **凭据与推送**：`push_to_github.sh` 以「**克隆远端 → 镜像同步工作树 → 提交 → 推回**」的方式更新仓库，**保留提交历史、可快进**（不要改用 `git init` 后直推：本包不是 git 仓库、远端已有连续提交，会因历史无关被 GitHub 拒绝）。令牌只从环境变量 `GH_TOKEN` 读取，只出现在**临时克隆**的 remote URL 中，推送后临时目录即删除 → **本包内不残留 `.git`、不残留凭据**。先跑 `bash push_to_github.sh --dry-run` 做预演：机制部分推入本机临时裸仓库（**不需令牌、不联网**），随后**联网只读克隆真远端**核对影响面 —— 会打印「本地包文件数 = 真远端 HEAD 树文件数」与**真远端上将被删除的文件清单**。⚠️ 这一步连不上 github.com 时**降级并以退出码 3 结束**（不是 0），此时**真远端影响面未核对**，联网后须重跑；整个预演过程 **GitHub 上什么都不会变**。远端已存在同名标签时**不覆盖**，重复运行安全。
4. **被扣下的脚本如实登记**：`未发布脚本清单.md` 逐条列出**未入包**的脚本及理由（写死本机绝对路径／内嵌已退役的署名占位符／含内部课题编号前缀），不隐藏。装配时由 `make_release.py` 的**三道**发布前闸门机械判定——**包内出现任一类禁列字符串即拒绝出包**。
   **C 类不做字面量改写**：其中多数是**逐轮稿件处理脚本**，路径指向 `历史版本/` 里**按原名保存**的历史稿件；改写字面量会把它变成**伪引用**，故一律扣下并登记，而非改写。
5. **本包是生成物**：请勿手工编辑包内文件；改动请改活动目录，然后重跑 `make_release.py`。
