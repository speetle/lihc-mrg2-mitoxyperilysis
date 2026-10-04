#!/usr/bin/env bash
# 推送到 GitHub（凭据只走环境变量，绝不落盘、绝不回显）
#
# 用法：
#   export GH_TOKEN=<你的 personal access token>     # scope 至少 repo
#   export GH_OWNER=<GitHub 用户名>
#   export GH_REPO=<仓库名，默认 lihc-mrg2-mitoxyperilysis>
#   bash push_to_github.sh
#
# 安全约定（与《SCI-writing-VIP》推送脚本一致）：
#   * 令牌只从环境变量读取，**不写入任何文件**、**不 echo**、不出现在命令行参数里
#   * 远端 URL 使用 https://x-access-token:${GH_TOKEN}@github.com/... 一次性注入，
#     推送成功后立即把它从 remote 配置里抹掉，避免残留 .git/config
set -euo pipefail
cd "$(dirname "$0")"

: "${GH_TOKEN:?请先 export GH_TOKEN=<token>}"
: "${GH_OWNER:?请先 export GH_OWNER=<GitHub 用户名>}"
REPO="${GH_REPO:-lihc-mrg2-mitoxyperilysis}"
BRANCH="${GH_BRANCH:-main}"

if [ ! -d .git ]; then
  git init -q
  git checkout -q -b "$BRANCH"
fi

git add -A
git -c user.name="${GH_OWNER}" -c user.email="${GH_OWNER}@users.noreply.github.com" \
    commit -q -m "Release v1.0.3: code and data for LIHC MRG transport-failure study" || echo "（无新改动可提交）"

# 用一次性的 remote URL 注入令牌，推送后立刻移除
git remote remove origin 2>/dev/null || true
git remote add origin "https://x-access-token:${GH_TOKEN}@github.com/${GH_OWNER}/${REPO}.git"
git push -q -u origin "$BRANCH"
git remote remove origin
git remote add origin "https://github.com/${GH_OWNER}/${REPO}.git"

echo "✅ 已推送：https://github.com/${GH_OWNER}/${REPO}"
echo
echo "下一步（建立 DOI，供稿件 Availability of code 段引用）："
echo "  1) GitHub 仓库 → Settings → 勾选 Public（Zenodo 只能抓公开仓库）"
echo "  2) 在 https://zenodo.org/account/settings/github/ 打开本仓库的开关"
echo "  3) GitHub 仓库 → Releases → Draft a new release → tag 填 v1.0.3 → Publish"
echo "  4) Zenodo 随即生成 DOI，把 DOI 填回稿件 Declarations 的 Availability of code 段"
echo "  5) 建议同时填进 CITATION.cff 的 repository-code 字段"
