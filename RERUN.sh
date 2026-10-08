#!/usr/bin/env bash
# LIHC —— 一键重跑（在已激活的 venv 内执行）
# 用法：  bash RERUN.sh
# 预计：  40–60 分钟（步骤 5 的 10 个独立随机划分约占 6 分钟）
# 注意：  步骤 1 需联网（cBioPortal REST API 拉取 TCGA-LIHC）
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-python}"
step() { printf "\n\033[1m=== %s ===\033[0m\n" "$*"; }

step "0/7  校验原始数据可达性（仅 HEAD，不下载）"
$PY scripts/fetch_raw_data.py --check || true

step "1/7  主流程：队列构建 → 单因素 → Model A → Model B → 分子相关（联网）"
$PY scripts/lihc_pipeline.py

step "2/7  稳健性六件套：嵌套 CV / 种子复现 / MB 上界 / 配对 bootstrap / 随机面板"
$PY scripts/stats_hardening.py

step "3/7  外部验证：GSE14520（主）+ GSE76427（阴性对照）+ 增殖对照"
$PY scripts/external_GSE14520.py
$PY scripts/external_GSE76427.py
$PY scripts/gse76427_prolif_control.py

step "4/7  统计口径修正：校准 / PH / 缺失值敏感性 / 未惩罚对照"
$PY scripts/revise_stats_v14.py
$PY scripts/r1m4_unpenalised.py

step "5/7  pooled out-of-fold C-index + 10 个独立随机划分（R1-M8）"
$PY scripts/r1m8_nested_pooled.py

step "6/7  补充材料与图件"
$PY scripts/make_supplement_v15.py
$PY scripts/make_tables_figures.py
$PY scripts/make_figures_v2.py
$PY scripts/make_figS1_calibration.py

step "7/7  机械校验：图件版式 / 数值闸门 / 参考文献双源核验"
$PY scripts/figcheck_lihc.py
$PY scripts/数值指纹.py --snap ../Manuscript_LIHC_v1.12.md || true
$PY scripts/ref_audit_v15.py || true

printf "\n\033[1m全部步骤结束。产物在 data/ 与 supplementary/。\033[0m\n"
