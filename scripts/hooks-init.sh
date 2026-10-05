#!/bin/bash

# 脚本说明：
# 安装或卸载仓库的 Git 钩子（版本化在 .githooks 目录，通过 core.hooksPath 生效）
#   install   将 core.hooksPath 指向 .githooks（默认动作）
#   uninstall 清除 core.hooksPath，恢复使用 .git/hooks
#   status    显示当前钩子配置
# 用法：./scripts/hooks-init.sh [install|uninstall|status]

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cd "$WORKDIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    print_error "当前目录不是 Git 仓库，无法安装钩子"
    exit 1
fi

HOOKS_DIR=".githooks"
ACTION="${1:-install}"

case "$ACTION" in
    install)
        if [ ! -d "$HOOKS_DIR" ]; then
            print_error "未找到 $HOOKS_DIR 目录，请确认仓库文件完整"
            exit 1
        fi
        # 尽量补上可执行位；Windows 文件系统不支持该语义，chmod 失败不影响使用
        find "$HOOKS_DIR" -type f -exec chmod +x {} \; 2>/dev/null || true
        git config core.hooksPath "$HOOKS_DIR"
        print_info "Git 钩子已启用: core.hooksPath=$HOOKS_DIR"
        print_info "提交时会自动格式化并运行 lint/compile/test，未通过则阻止提交"
        print_info "临时跳过: SKIP_HOOKS=1 git commit ... 或 git commit --no-verify"
        print_info "Windows 说明: 钩子由 Git for Windows 内置的 sh 执行，无需 PowerShell 版本"
        ;;
    uninstall)
        git config --unset core.hooksPath 2>/dev/null || true
        print_info "已清除 core.hooksPath，Git 恢复使用默认 .git/hooks"
        ;;
    status)
        current="$(git config --get core.hooksPath || true)"
        if [ -n "$current" ]; then
            print_info "当前 core.hooksPath=$current"
        else
            print_warn "未配置 core.hooksPath，钩子未启用"
        fi
        ls -1 "$HOOKS_DIR" 2>/dev/null || print_warn "未找到 $HOOKS_DIR 目录"
        ;;
    *)
        print_error "未知动作: $ACTION"
        echo "可选: install、uninstall、status"
        exit 1
        ;;
esac
