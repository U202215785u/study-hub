#!/bin/bash
set -e

# Study Hub Frontend Build Script
# 解决 Windows Git Bash 下项目路径含空格导致 Vite ESM 解析崩溃的问题
# DEC-022: 必须使用无空格工作目录进行构建
# DEC-023: 增加并发互斥锁，防止多代理同时构建导致产物覆盖

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMP_DIR="/c/temp/study-hub-fe-build"
LOCK_FILE="/c/temp/study-hub-fe-build.lock"

# ========== 并发互斥锁 ==========
# 使用文件锁防止多个代理同时构建（Windows Git Bash 无 flock，用标记文件实现）
LOCK_TIMEOUT=300  # 5分钟超时
LOCK_WAIT=0

while [ -f "$LOCK_FILE" ]; do
    LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)))
    if [ "$LOCK_AGE" -gt "$LOCK_TIMEOUT" ]; then
        echo "[WARN] 检测到超时锁文件，强制清理..."
        rm -f "$LOCK_FILE"
        break
    fi
    echo "[WAIT] 另一个构建正在进行，等待中... (${LOCK_WAIT}s)"
    sleep 2
    LOCK_WAIT=$((LOCK_WAIT + 2))
    if [ "$LOCK_WAIT" -gt "$LOCK_TIMEOUT" ]; then
        echo "[ERROR] 等待构建超时 (${LOCK_TIMEOUT}s)，退出"
        exit 1
    fi
done

# 创建锁文件（包含当前 PID 和时间戳）
echo "$$ $(date +%s)" > "$LOCK_FILE"

# 确保退出时清理锁文件
cleanup_lock() {
    rm -f "$LOCK_FILE"
}
trap cleanup_lock EXIT

# ================================

echo "========================================"
echo "Study Hub Frontend Build"
echo "Source: $SCRIPT_DIR"
echo "Temp build dir: $TEMP_DIR"
echo "Lock: $LOCK_FILE"
echo "========================================"

# 清理旧临时目录
if [ -d "$TEMP_DIR" ]; then
    echo "[1/5] Cleaning old temp directory..."
    rm -rf "$TEMP_DIR"
fi

# 复制必要源文件到无空格临时目录（排除 node_modules / dist / 日志）
echo "[2/5] Copying source files to temp directory (no spaces)..."
mkdir -p "$TEMP_DIR"

cp -r "$SCRIPT_DIR/src" "$TEMP_DIR/"
cp -r "$SCRIPT_DIR/public" "$TEMP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/package.json" "$TEMP_DIR/"
cp "$SCRIPT_DIR/package-lock.json" "$TEMP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/vite.config.js" "$TEMP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/vite-empty.config.js" "$TEMP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/tailwind.config.js" "$TEMP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/postcss.config.js" "$TEMP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/index.html" "$TEMP_DIR/"

# 进入临时目录构建
cd "$TEMP_DIR"

echo "[3/5] Installing dependencies..."
npm install

echo "[4/5] Building..."
npm run build

# 复制产物回原项目
echo "[5/5] Copying dist back to project..."
rm -rf "$SCRIPT_DIR/dist"
cp -r "$TEMP_DIR/dist" "$SCRIPT_DIR/dist"

# 可选：保留临时目录用于调试，或取消下行注释自动清理
# rm -rf "$TEMP_DIR"

echo "========================================"
echo "Build complete: $SCRIPT_DIR/dist"
echo "========================================"
