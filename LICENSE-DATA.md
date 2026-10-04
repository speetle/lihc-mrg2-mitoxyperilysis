# 数据许可 —— Creative Commons Attribution 4.0 International (CC BY 4.0)

适用于本包 `data/`、`supplementary/`、`figures/` 三个目录下的全部文件
（逐患者派生数据、分析输出表、补充表与图件）。

## 条款

本数据采用 **CC BY 4.0** 许可发布。
完整法律文本：<https://creativecommons.org/licenses/by/4.0/legalcode>
中文版摘要：<https://creativecommons.org/licenses/by/4.0/deed.zh>

在**署名原作者与出处**的前提下，允许复制、分发、改编与商业使用本数据。

## 建议署名格式

> Lian B. (2026). *Code and data for: Stability selection does not guarantee external transport:
> a mitoxyperilysis score fails validation in hepatocellular carcinoma.*
> [Data set]. Zenodo / GitHub. License: CC BY 4.0

机器可读版本见本包 `CITATION.cff`。

## 上游数据来源与各自条款（**不因本许可而改变**）

本包 `data/` 中的原始队列数据**不是本研究的原创数据**，只是为复算而整理的可再分发派生表，
其上游来源与条款如下，**再分发时须同时遵守上游条款**：

| 文件 | 上游来源 | 上游标识 | 上游条款 |
|---|---|---|---|
| TCGA-LIHC 逐患者表 | cBioPortal / GDC | `lihc_tcga_pan_can_atlas_2018` | TCGA 数据使用政策；受试者层面数据为公开去标识数据 |
| TCGA-LIHC 突变表 | cBioPortal / GDC | 同上 | 同上 |
| GSE14520 | NCBI GEO（Roessler 等） | GSE14520, PMID 21159642 | NCBI GEO 数据使用政策 |
| GSE76427 | NCBI GEO（Grinchuk 等） | GSE76427, PMID 28860220 | NCBI GEO 数据使用政策 |

## 代码部分

`scripts/` 与 `RERUN.sh` 下的代码采用 **MIT** 许可，见同目录 `LICENSE`。

## 豁免说明

本许可**不适用于**：
- 任何第三方上游原始数据本身（见上表，遵循各自条款）；
- 稿件正文与图件中已发表于期刊的版本（以期刊版权协议为准）。
