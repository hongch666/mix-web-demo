#!/bin/bash

# 脚本说明：
# 安装或卸载仓库的 Git 钩子（版本化在 .githooks 目录，通过 core.hooksPath 生效）
#   install   将 core.hooksPath 指向 .githooks（默认动作）
#   uninstall 清除 core.hooksPath，恢复使用 .git/hooks
#   enable    按能力启用：commit（提交检查）、skills（技能同步）、all（默认）
#   disable   按能力停用，取值同上；开关写在本仓库 git config，互不影响
#   status    显示 hooksPath 与两项能力的开闭状态
# 用法：./scripts/hooks-init.sh [install|uninstall|enable|disable|status] [commit|skills|all]

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
SCOPE="${2:-all}"
CONFIG_COMMIT="mix.hooks.commit"
CONFIG_SKILLS="mix.hooks.skills"

# 读取能力开关：提交检查默认关闭，技能同步默认启用（与钩子内的判断保持一致）
switch_value() {
    git config --get "$1" 2>/dev/null || true
}

commit_enabled() {
    case "$(printf '%s' "$(switch_value "$CONFIG_COMMIT")" | tr '[:upper:]' '[:lower:]')" in
        true | 1 | yes | on) return 0 ;;
        *) return 1 ;;
    esac
}

skills_enabled() {
    local value
    value="$(switch_value "$CONFIG_SKILLS")"
    case "$(printf '%s' "${value:-true}" | tr '[:upper:]' '[:lower:]')" in
        false | 0 | no | off) return 1 ;;
        *) return 0 ;;
    esac
}

enable_scope() {
    case "$1" in
        all)
            git config "$CONFIG_COMMIT" true
            git config "$CONFIG_SKILLS" true
            print_info "已启用: 提交检查、技能同步"
            ;;
        commit)
            git config "$CONFIG_COMMIT" true
            print_info "已启用: 提交检查"
            ;;
        skills)
            git config "$CONFIG_SKILLS" true
            print_info "已启用: 技能同步"
            ;;
        *)
            print_error "未知能力: $1"
            echo "可选: commit、skills、all"
            exit 1
            ;;
    esac
}

disable_scope() {
    case "$1" in
        all)
            git config "$CONFIG_COMMIT" false
            git config "$CONFIG_SKILLS" false
            print_info "已关闭: 提交检查、技能同步"
            ;;
        commit)
            git config "$CONFIG_COMMIT" false
            print_info "已关闭: 提交检查"
            ;;
        skills)
            git config "$CONFIG_SKILLS" false
            print_info "已关闭: 技能同步"
            ;;
        *)
            print_error "未知能力: $1"
            echo "可选: commit、skills、all"
            exit 1
            ;;
    esac
}

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
        print_info "默认行为: pull 后自动执行 ./mix skills；提交检查默认关闭"
        print_info "提交检查: ./mix hooks enable commit 开启（enable 后提交时跑 lint/compile/test，未通过则阻止提交）"
        print_info "技能同步: 默认开启，./mix hooks disable skills 可关闭（rebase 拉取走 post-rewrite）"
        print_info "临时跳过: SKIP_HOOKS=1 git commit/pull ... 或 git commit --no-verify"
        print_info "Windows 说明: 钩子由 Git for Windows 内置的 sh 执行，无需 PowerShell 版本"
        ;;
    uninstall)
        git config --unset core.hooksPath 2>/dev/null || true
        print_info "已清除 core.hooksPath，Git 恢复使用默认 .git/hooks"
        ;;
    enable)
        enable_scope "$SCOPE"
        ;;
    disable)
        disable_scope "$SCOPE"
        ;;
    status)
        current="$(git config --get core.hooksPath || true)"
        if [ -n "$current" ]; then
            print_info "当前 core.hooksPath=$current"
        else
            print_warn "未配置 core.hooksPath，钩子未启用"
        fi
        if commit_enabled; then
            print_info "提交检查（pre-commit）: 启用"
        else
            print_warn "提交检查（pre-commit）: 关闭（默认关闭，启用执行 ./mix hooks enable commit）"
        fi
        if skills_enabled; then
            print_info "技能同步（post-merge / post-rewrite）: 启用"
        else
            print_warn "技能同步（post-merge / post-rewrite）: 关闭（启用执行 ./mix hooks enable skills）"
        fi
        echo "钩子文件:"
        ls -1 "$HOOKS_DIR" 2>/dev/null || print_warn "未找到 $HOOKS_DIR 目录"
        ;;
    *)
        print_error "未知动作: $ACTION"
        echo "可选: install、uninstall、enable、disable、status"
        exit 1
        ;;
esac
