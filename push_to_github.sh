#!/usr/bin/env bash
# push_to_github.sh —— 把本包推送到 GitHub（**历史保留式更新**）
#
# 为什么不是 `git init` 再 push：
#   本机 `发布包_代码与数据/` 不是 git 仓库（装配脚本每次重建内容，不保留 .git），
#   而远端 main 上已经有连续提交（v1.0.3 → v1.0.4）。从零 `git init` 会产生
#   一段**与远端无关**的历史，GitHub 会以 non-fast-forward 拒绝推送。
#   故本脚本改为「克隆远端 → 镜像同步工作树 → 提交 → 推回」，历史连续、可快进。
#
# 用法
#   bash push_to_github.sh --dry-run      # 预演：机制部分推到本机临时裸仓库（不需 token）；
#                                         #        随后**联网**只读克隆真远端做影响面核对
#                                         #        （连不上则降级并**以退出码 3** 结束，不算通过）
#   export GH_TOKEN=<PAT>              # scope 至少 repo（fine-grained 需 Contents: Read and write）
#   export GH_OWNER=speetle            # 可选，默认 speetle
#   bash push_to_github.sh          # 真推；推送前打印变更摘要并要一次确认
#   bash push_to_github.sh --yes          # 跳过确认（脚本化用）
#
# 可选覆盖：GH_REPO（默认 lihc-mrg2-mitoxyperilysis）、GH_BRANCH（默认 main）、
#          GH_TAG（默认 v1.0.5）、
#          GH_REMOTE_URL（覆盖远端地址）——⚠️ 该模式下会**真推**到你给的地址，
#          即使加了 --dry-run 也一样（--dry-run 只拒绝确认提示与额外核对，不阻止本次推送）；
#          且此时「影响面核对」不适用（预演与核对是同一份远端），会以退出码 3 结束。
#
# 安全约定
#   * token 只从环境变量读取，只出现在**临时克隆**的 remote URL 中，不写入本包目录
#   * 临时目录在退出时删除 → 本包内不残留 .git、不残留凭据
#   * 远端已存在同名标签时**不覆盖**（幂等重跑安全）
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SELF_DIR"

DRY=0
YES=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --yes|-y)  YES=1 ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "未知参数：${a}（可用：--dry-run / --yes）" >&2; exit 2 ;;
  esac
done

GH_OWNER="${GH_OWNER:-speetle}"
GH_REPO="${GH_REPO:-lihc-mrg2-mitoxyperilysis}"
GH_BRANCH="${GH_BRANCH:-main}"
GH_TAG="${GH_TAG:-v1.0.5}"
MSG="${GH_MSG:-Release $GH_TAG: mirror the refreshed package (v1.12 anchor; withheld-script register 51 = A28+B10+C13)}"
CLEAN_URL="https://github.com/${GH_OWNER}/${GH_REPO}.git"

# ── 溯源：待推内容必须与交付目录一致，先做一道本机自检
if [ ! -f "$SRC/make_release.py" ]; then
  echo "❌ $SRC 不像发布包目录（缺 make_release.py）。请在包内运行本脚本。" >&2
  exit 1
fi
for f in README.md CITATION.cff LICENSE LICENSE-DATA.md 未发布脚本清单.md; do
  [ -f "$SRC/$f" ] || { echo "❌ 缺文件：$f —— 先跑 make_release.py 重装本包。" >&2; exit 1; }
done
# 本包**不应**带自己的 .git：一旦有，`git push` 会推那套与远端无关的历史
# （这正是当初 non-fast-forward 的成因）。有就停，别让人误用。
if [ -d "$SRC/.git" ]; then
  echo "❌ 本包内出现 .git/ —— 本包不是 git 仓库，推送走的是「克隆远端再镜像」。" >&2
  echo "   请先移走 $SRC/.git，再重跑本脚本。" >&2
  exit 1
fi

WORK="$(mktemp -d "${TMPDIR%/}/lihc_push.XXXXXX")"
cleanup() { rm -rf "$WORK" 2>/dev/null || true; }
trap cleanup EXIT

if [ -n "${GH_REMOTE_URL:-}" ]; then
  # 自定远端（镜像到自建仓库，或离线自测）：地址原样使用，不注入 token
  ORIGIN_URL="$GH_REMOTE_URL"
  echo "◆ 自定远端（不注入 token）：$ORIGIN_URL"
elif [ "$DRY" -eq 1 ]; then
  # 预演：造一个本机裸仓库当远端，全程不联网、不需要 token
  ORIGIN_URL="$WORK/remote.git"
  git init -q --bare "$ORIGIN_URL"
  git -C "$ORIGIN_URL" symbolic-ref HEAD "refs/heads/$GH_BRANCH"
  echo "◆ 预演模式：远端 = 本机裸仓库 $ORIGIN_URL"
else
  : "${GH_TOKEN:?请先 export GH_TOKEN=<你的 personal access token>}"
  ORIGIN_URL="https://x-access-token:${GH_TOKEN}@github.com/${GH_OWNER}/${GH_REPO}.git"
  echo "◆ 真实推送：远端 = $CLEAN_URL"
fi

# ── 带看门狗的克隆（真推路径）
#    为什么必须设上限：本机实测 github.com 的 443 被代理拦截时 `git clone` 会**挂死**
#    （HTTP/2 framing error / CONNECT tunnel failed，6 分钟无返回），整个脚本静默卡住。
#    macOS 无 coreutils 的 `timeout`，故用后台任务 + 轮询（与预演段同一口径）。
#    ⚠️ 2026-10-10 实测：**正常**克隆本仓库（0.5 MB / 168 文件）在弱网下要 **102 秒**，
#       而旧阈值 60 秒会把它**误杀**并报成「443 被拦截」—— 阈值必须高于实测合法耗时。
#       现设 480 × 0.5 s = **240 秒**（约为实测合法耗时的 2.4 倍）。
#    返回码：1 = 看门狗超时（疑似网络被拦截）；其余 = git 自身退出码（多为凭据/权限）。
_clone_wd() {
  local _p _n _err
  _err="$WORK/clone.err"
  GIT_TERMINAL_PROMPT=0 git clone "$@" 2>"$_err" &
  _p=$!; _n=0
  while kill -0 "$_p" 2>/dev/null; do
    _n=$((_n + 1))
    if [ "$_n" -ge 480 ]; then
      kill "$_p" 2>/dev/null || true
      wait "$_p" 2>/dev/null || true
      return 1
    fi
    sleep 0.5
  done
  wait "$_p"
}

echo "◆ 克隆远端（只取 ${GH_BRANCH}）…"
_rc=0
if [ "$DRY" -eq 1 ] && [ -z "${GH_REMOTE_URL:-}" ]; then
  # 预演：临时裸仓库是**刚建的空仓库**，`--branch main` 必然报「远端无此分支」→ 直接用无分支的一次克隆，
  #        免得每次预演都先失败一次再走重试（2026-10-08 版正是在重试路径上误报「克隆失败」）。
  _clone_wd -q "$ORIGIN_URL" "$WORK/repo" || _rc=$?
else
  _clone_wd -q --branch "$GH_BRANCH" --single-branch "$ORIGIN_URL" "$WORK/repo" || _rc=$?
  if [ "$_rc" -ne 0 ]; then
    rm -rf "$WORK/repo"      # 第一次可能留下半成品目录，重试前先清干净
    _rc=0                    # ★ 必须显式清零：`cmd || _rc=$?` 在**命令成功**时**不会**执行赋值，
                             #   于是 _rc 会留着上一次的失败码 → 判据读到「假失败」。这就是 2026-10-08 版坏掉的成因。
    _clone_wd -q "$ORIGIN_URL" "$WORK/repo" || _rc=$?
  fi
fi
if [ "$_rc" -ne 0 ]; then
  echo "❌ 克隆远端失败：${CLEAN_URL}（本次**未改动远端**）" >&2
  if [ "$DRY" -eq 1 ] && [ -z "${GH_REMOTE_URL:-}" ]; then
    echo "   判定：预演目标是**本机临时裸仓库**（不涉网络）—— 属 git 自身错误，与 443/代理无关。" >&2
    echo "   git 原始输出末尾：" >&2
    tail -n 3 "$WORK/clone.err" 2>/dev/null | sed 's/^/     /' >&2
  elif [ "$_rc" -eq 1 ]; then
    echo "   判定：240 秒内无响应 —— 疑似 github.com 的 443 被代理/防火墙拦截。" >&2
    echo "   → 本机 git 通道长期不可用时，改走 api.github.com 的 Git Data API 镜像推送，不要在此反复重试。" >&2
  else
    echo "   判定：**非超时**失败（git 退出码 ${_rc}）—— 多为令牌/权限问题（GH_TOKEN 是否含 repo 写权限？）。" >&2
    echo "   git 原始输出末尾：" >&2
    tail -n 3 "$WORK/clone.err" 2>/dev/null | sed 's/^/     /' >&2
  fi
  exit 3
fi

cd "$WORK/repo"
git config core.quotepath false   # 中文路径按原样显示，不打印八进制转义
git -c advice.detachedHead=false checkout -q "$GH_BRANCH" 2>/dev/null || true

BEFORE="$(git rev-parse --short HEAD 2>/dev/null || echo '(空仓库，尚无提交)')"

echo "◆ 镜像同步工作树（以本包为准，删除远端多余文件）…"
rsync -a --delete \
  --exclude='/.git' --exclude='/dist' --exclude='/__pycache__' \
  --exclude='__pycache__' --exclude='.DS_Store' \
  "$SRC/" "$WORK/repo/"

git add -A
echo
if [ "$DRY" -eq 1 ]; then
  # ⚠️ 预演时的「远端」是上面那个**空的**临时裸仓库 → 所有文件必然都显示为新增（A）。
  #    若照原样写「相对远端」，那行「168 files changed」会被读成「GitHub 上要改 168 个文件」——不实。
  echo "◆ 变更摘要（预演：相对那个**空的**临时裸仓库 —— 故全部显示为新增，**不代表** GitHub 的实际增删）"
else
  echo "◆ 变更摘要（相对真远端 ${GH_BRANCH}）"
fi
if git diff --cached --quiet; then
  echo "  （无改动：本包内容与远端逐文件一致）"
  CHANGED=0
else
  git status --short | sed 's/^/  /'
  echo
  echo "  统计：$(git diff --cached --shortstat | sed 's/^ *//')"
  CHANGED=1
fi

if [ "$DRY" -eq 1 ]; then
  echo
  echo "◆ 预演：提交并推入本机裸仓库，验证历史连续（快进）…"
fi

if [ "$CHANGED" -eq 1 ]; then
  if [ "$YES" -eq 0 ] && [ "$DRY" -eq 0 ]; then
    printf "◆ 确认推送到 %s ？[y/N] " "$CLEAN_URL"
    read -r reply || reply=""
    case "$reply" in
      y|Y|yes|YES) ;;
      *) echo "已取消：远端未改动。"; exit 1 ;;
    esac
  fi
  git -c user.name="$GH_OWNER" \
      -c user.email="${GH_OWNER}@users.noreply.github.com" \
      commit -q -m "$MSG"
fi

git push -q origin "HEAD:refs/heads/$GH_BRANCH"
AFTER="$(git rev-parse --short HEAD)"

# 标签：远端已存在则不覆盖（幂等重跑安全）
if git ls-remote --exit-code --tags origin "refs/tags/$GH_TAG" >/dev/null 2>&1; then
  echo "◆ 远端已存在标签 $GH_TAG —— 本次不重推（如需覆盖：手工 git push --force origin refs/tags/${GH_TAG}）"
  TAGGED="（已存在，未动）"
else
  git tag -f "$GH_TAG" >/dev/null
  git push -q origin "refs/tags/$GH_TAG"
  TAGGED="已推"
fi

echo
if [ "$DRY" -eq 1 ]; then
  # ⚠️ 预演实际推的是本机临时裸仓库、**不是** GitHub。
  #    若这里紧跟一句「✅ 完成 ／ 远端：https://github.com/… ／ 标签：v1.0.5 已推」，
  #    会被读成「GitHub 已更新」——那是谎报（第 24 条同族：每条输出必须能只凭它判断真实状态）。
  echo "✅ 预演完成 —— GitHub 上什么都没变"
  echo "  预演远端：${ORIGIN_URL}（本机临时裸仓库，退出即删）"
else
  echo "✅ 完成"
  echo "  远端：$CLEAN_URL"
fi
echo "  分支：$GH_BRANCH  $BEFORE → $AFTER"
echo "  标签：$GH_TAG $TAGGED"
if [ "$DRY" -eq 1 ]; then
  echo
  echo "  预演本地仓库验证（针对上面那个临时裸仓库，**不是** GitHub）："
  echo "    提交数 = $(git rev-list --count HEAD)"
  echo "    文件数 = $(git ls-tree -r --name-only HEAD | wc -l | tr -d ' ')"
  echo "    根目录 ="
  git ls-tree --name-only HEAD | sed 's/^/      /'
  echo
  # ── 对真远端的**只读**影响面核对（不写远端）──
  # 上面的预演推的是本机**空**裸仓库，只能证明「机制通」，说明不了「对真远端会发生什么」。
  # ⚠️ 这里**不写**「快进校验」：本脚本恒定「克隆真远端 → 在其 HEAD 上提交 → 推送」，
  #    新提交必然是远端 HEAD 的后代，快进是**构造保证**的。若写成判据，它永远不会为假
  #    —— 那正是第 28 条说的「永真死代码」，只会给假安全感。故这里只核实**可证伪**的两件事：
  #      ① 镜像后文件数与本地包一致（rsync 漏文件 / 排除项写错都会露）
  #      ② 打印真远端上将被删除的文件名（本轮预期只有带内部前缀的旧稿件锚）
  echo "  ◆ 对真远端的影响面核对（只读克隆，不写远端）…"
  REAL="$WORK/real"
  # 若显式给了 GH_REMOTE_URL，则「核对对象」以它为准
  REAL_URL="${GH_REMOTE_URL:-$CLEAN_URL}"
  echo "     核对对象：$REAL_URL"
  DEGRADED=0   # 1 = 真远端影响面没核对上；光看 ✅ 文字不算通过，退出码也要跟着说真话
  # 带看门狗的克隆：阈值与真推路径同一口径（480 × 0.5 s = 240 s）。
  # ⚠️ 2026-10-10 实测：本机克隆本仓库要 ~102 秒，旧阈值 30 秒必然误判为失败。
  # （macOS 自带没有 coreutils 的 `timeout`，故用后台任务 + 轮询。）
  _clone_real() {
    GIT_TERMINAL_PROMPT=0 git clone -q --branch "$GH_BRANCH" --single-branch \
        "$REAL_URL" "$REAL" 2>/dev/null &
    _p=$!; _n=0
    while kill -0 "$_p" 2>/dev/null; do
      _n=$((_n + 1))
      if [ "$_n" -ge 480 ]; then
        kill "$_p" 2>/dev/null || true
        wait "$_p" 2>/dev/null || true
        return 1
      fi
      sleep 0.5
    done
    wait "$_p"
  }
  if [ "$ORIGIN_URL" = "$REAL_URL" ]; then
    # ⚠️ 自定远端（GH_REMOTE_URL）模式下，上面那次 push **不是预演而是真推**，写的正是这个地址。
    #    此刻再克隆同一地址，必然得到「无改动 / 真远端无文件被删除」——那是**空核对**。
    #    把空核对接在 ✅ 旁边，等于把「没核对」说成「核对通过」（第 24 条：噪声不得共用同一条绿）。
    echo "     ⚠️ 不适用：本模式下预演与核对指向同一个远端（且预演那次已**真写**该远端），"
    echo "        故「将被删除的文件」必然是空的 —— 影响面在此**无法核对**。"
    echo "        离线自测的正确做法：先 cp -R 一份裸仓库副本 → GH_REMOTE_URL 指向副本 →"
    echo "        跑完本预演后，另用 git diff 在**原仓库**与副本之间比对增删。"
    DEGRADED=1
  elif _clone_real; then
    RHEAD="$(git -C "$REAL" rev-parse HEAD)"
    git -C "$REAL" config core.quotepath false   # 否则中文件名会打印成八进制转义，看不清删了什么
    rsync -a --delete \
      --exclude='/.git' --exclude='/dist' --exclude='/__pycache__' \
      --exclude='__pycache__' --exclude='.DS_Store' \
      "$SRC/" "$REAL/"
    git -C "$REAL" add -A
    git -C "$REAL" -c user.name="$GH_OWNER" \
        -c user.email="${GH_OWNER}@users.noreply.github.com" commit -q -m "$MSG" || true
    NHEAD="$(git -C "$REAL" rev-parse HEAD)"
    _n_local="$(cd "$SRC" && find . -type f \
        -not -path './.git/*' -not -path './dist/*' \
        -not -path '*/__pycache__/*' -not -name '.DS_Store' | wc -l | tr -d ' ')"
    _n_real="$(git -C "$REAL" ls-tree -r --name-only HEAD | wc -l | tr -d ' ')"
    if [ "$RHEAD" = "$NHEAD" ]; then
      echo "     （无改动：本包内容与真远端逐文件一致，推送将是空操作）"
    else
      echo "     真远端：${RHEAD:0:7} → ${NHEAD:0:7}  ｜ 变更 $(git -C "$REAL" diff --shortstat "$RHEAD" "$NHEAD" | sed 's/^ *//')"
    fi
    if [ "$_n_local" = "$_n_real" ]; then
      echo "     ✅ 镜像完整性：本地包 $_n_local 个文件 = 真远端 HEAD 树 $_n_real 个文件"
    else
      echo "     ❌ 镜像不完整：本地包 $_n_local 个文件 ≠ 真远端 HEAD 树 $_n_real 个 —— 先查 rsync 排除项。" >&2
      exit 1
    fi
    _del="$(git -C "$REAL" diff --name-only --diff-filter=D "$RHEAD" "$NHEAD")"
    if [ -z "$_del" ]; then
      echo "     真远端无文件被删除"
    else
      echo "     ⚠️ 真远端将被删除的文件（逐条确认是旧件再推）："
      echo "$_del" | sed 's/^/          /'
    fi
  else
    echo "     ⚠️ 只读克隆真远端失败（网络不通或仓库不可读）。" >&2
    echo "        → 机制预演已完成，但**真远端影响面未核对**；联网正常后请重跑本预演。" >&2
    echo "        → 联网不通时**不要**改用 GH_REMOTE_URL 自以为在核对：该模式会**真写**你给的地址，" >&2
    echo "          且核对对象与预演目标同一份 → 结果必为空。要离线自测请直接读上一条的做法。" >&2
    DEGRADED=1
  fi
  echo
  echo "  ⚠️ 这是预演，GitHub 上什么都没变。确认无误后再跑：bash push_to_github.sh"
  if [ "$DEGRADED" -eq 1 ]; then
    # 文字上说了「未核对」，退出码就不能还是 0 —— 否则 `--dry-run && 真推` 这种串法会把
    # 「降级」当「通过」放行（第 24 条：环境噪声与真实结论不得共用同一个绿）。
    echo
    echo "  ⚠️ 本预演以**退出码 3** 结束 —— 3 = 降级（真远端影响面未核对），**不是通过**。"
    echo "     判定「真通过」的唯一依据：看到「✅ 镜像完整性：… = …」与「真远端将被删除的文件」两节。"
    exit 3
  fi
else
  echo
  echo "  下一步（**等文章接收后再做**，与稿件 Availability of code 的措辞一致）："
  echo "    1) 建 Release：GitHub 仓库 → Releases → Draft a new release → tag 选 $GH_TAG → Publish"
  echo "    2) 若已开通 Zenodo 集成，Release 会自动生成该版本的 DOI"
  echo "    3) 把 DOI 填回稿件 Availability of code 段与 CITATION.cff"
  echo "  ⚠️ 本轮**不要**建 Release —— 稿件承诺的是「on acceptance 才归档到 Zenodo」。"
fi
