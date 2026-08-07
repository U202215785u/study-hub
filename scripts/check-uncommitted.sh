#!/bin/bash
# check-uncommitted.sh — 检查所有 git worktree（含主目录）的未提交/未跟踪内容
#
# 为什么需要它：git worktree 的未提交改动是"隔离"的，只存在于它所在的
# worktree 工作目录里，不随分支/合并走；worktree 被 remove 时未提交内容直接丢失。
# 所以在"切换分支 / git merge / 清理 worktree / checkout 覆盖"之前，先跑本脚本。
#
# 用法:   bash scripts/check-uncommitted.sh
# 退出码: 0 = 所有 worktree 干净，可以安全切换/合并/清理
#         1 = 存在未提交内容，请先 commit 或 stash
# 只读检查，不改动任何文件。

cd "$(dirname "$0")/.." || exit 2
ROOT="$(pwd)"
echo "== 仓库: $ROOT =="

dirty=0
total=0

# --porcelain 输出逐行解析，路径含空格也安全（worktree 行可能带引号）
while IFS= read -r line; do
  case "$line" in
    worktree*)
      wt="${line#worktree }"
      wt="${wt%\"}"; wt="${wt#\"}"   # 去掉首尾引号
      total=$((total + 1))
      count="$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
      br="$(git -C "$wt" branch --show-current 2>/dev/null)"
      [ -z "$br" ] && br="detached@$(git -C "$wt" rev-parse --short HEAD 2>/dev/null)"
      if [ "$count" -gt 0 ]; then
        echo "  ⚠  [$br] $wt  →  $count 个未提交/未跟踪项"
        dirty=1
      else
        echo "  ✓  [$br] $wt  →  干净"
      fi
      ;;
  esac
done < <(git worktree list --porcelain)

echo
if [ "$dirty" -eq 0 ]; then
  echo "✅ 全部 $total 个工作树干净，可以安全切换分支 / 合并 / 清理"
  exit 0
else
  echo "⚠️  存在未提交内容！切换分支 / 合并 / 清理 worktree 前必须先提交或 stash。"
  echo "   记住：未提交内容只存在于它所在的工作树，不随分支和合并走，"
  echo "         worktree 被清理时未提交内容会直接丢失。"
  exit 1
fi
