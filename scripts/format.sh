#!/bin/bash

# 脚本说明：
# 这个脚本用于对四个服务执行代码格式化（会修改文件）
# 用法：./scripts/format.sh [service...]
#   service 可选值：spring、gozero、nestjs、fastapi，不指定时格式化全部服务

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 颜色输出
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

# 未指定服务时格式化全部服务
if [ $# -gt 0 ]; then
    SERVICES="$*"
else
    SERVICES="spring gozero nestjs fastapi"
fi

# ==================== 各服务格式化 ====================
# 返回码约定：0 表示成功，2 表示跳过（工具未安装），其它表示格式化失败

format_spring() {
    command -v mvn >/dev/null 2>&1 || return 2
    print_info "格式化 Spring 代码（Spotless）..."
    (cd "$WORKDIR/spring" && mvn -q spotless:apply)
}

format_gozero() {
    command -v golangci-lint >/dev/null 2>&1 || return 2
    print_info "格式化 GoZero 代码（golangci-lint fmt）..."
    (cd "$WORKDIR/gozero/app" && golangci-lint fmt)
}

format_nestjs() {
    command -v npm >/dev/null 2>&1 || return 2
    print_info "格式化 NestJS 代码（Prettier + ESLint --fix）..."
    # 先由 Prettier 统一排版，再用 ESLint --fix 修复可自动处理的问题
    (cd "$WORKDIR/nestjs" && npm run format && npm run lint:fix)
}

format_fastapi() {
    command -v ruff >/dev/null 2>&1 || return 2
    print_info "格式化 FastAPI 代码（Ruff）..."
    # 先统一排版，再修复可自动处理的检查项
    (cd "$WORKDIR/fastapi" && ruff format . && ruff check --fix .)
}

# ==================== 执行格式化 ====================

FAILED_SERVICES=""

for SERVICE in $SERVICES; do
    echo ""
    case "$SERVICE" in
        spring) format_spring; STATUS=$? ;;
        gozero) format_gozero; STATUS=$? ;;
        nestjs) format_nestjs; STATUS=$? ;;
        fastapi) format_fastapi; STATUS=$? ;;
        gateway)
            print_warn "gateway 为 APISIX 配置，无需代码格式化，已跳过"
            continue
            ;;
        *)
            print_error "未知服务: $SERVICE"
            echo "可选服务: spring、gozero、nestjs、fastapi"
            exit 1
            ;;
    esac

    case $STATUS in
        0)
            print_info "$SERVICE 格式化完成"
            ;;
        2)
            print_warn "$SERVICE 已跳过（对应工具未安装）"
            ;;
        *)
            print_error "$SERVICE 格式化失败"
            FAILED_SERVICES="$FAILED_SERVICES $SERVICE"
            ;;
    esac
done

echo ""
if [ -n "$FAILED_SERVICES" ]; then
    print_error "以下服务格式化失败:$FAILED_SERVICES"
    exit 1
fi

print_info "代码格式化完成"
