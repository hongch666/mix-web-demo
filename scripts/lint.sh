#!/bin/bash

# 脚本说明：
# 这个脚本用于对四个服务执行代码检查（只读，不修改文件）
# 用法：./scripts/lint.sh [service...]
#   service 可选值：spring、gozero、nestjs、fastapi，不指定时检查全部服务

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

# 常量类成员顺序检查（nestjs 与 fastapi 共用），python 缺失时跳过
lint_constants_order() {
    if command -v python >/dev/null 2>&1; then
        python "$WORKDIR/scripts/constants-order.py" --check "$1"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 "$WORKDIR/scripts/constants-order.py" --check "$1"
        return
    fi
    print_warn "未检测到 python，跳过常量类成员顺序检查"
    return 0
}

# 控制器返回类型检查（spring）：禁止匿名 Map，确需动态结构时须显式豁免，python 缺失时跳过
lint_controller_vo() {
    if command -v python >/dev/null 2>&1; then
        python "$WORKDIR/scripts/controller-vo.py" --check "$1"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 "$WORKDIR/scripts/controller-vo.py" --check "$1"
        return
    fi
    print_warn "未检测到 python，跳过控制器返回类型检查"
    return 0
}

# 包导入规范检查（fastapi）：目标目录有 __init__.py 导出时须从包导入，python 缺失时跳过
lint_package_imports() {
    if command -v python >/dev/null 2>&1; then
        python "$WORKDIR/scripts/package-imports.py" --check "$1"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 "$WORKDIR/scripts/package-imports.py" --check "$1"
        return
    fi
    print_warn "未检测到 python，跳过包导入规范检查"
    return 0
}

# 未指定服务时检查全部服务
if [ $# -gt 0 ]; then
    SERVICES="$*"
else
    SERVICES="spring gozero nestjs fastapi"
fi

# ==================== 各服务检查 ====================
# 返回码约定：0 表示通过，2 表示跳过（工具未安装），其它表示检查未通过

lint_spring() {
    print_info "检查 Spring 控制器返回类型（禁止匿名 Map）..."
    lint_controller_vo "$WORKDIR/spring/src/main/java/com/hcsy/spring/api/controller" || return 1
    command -v mvn >/dev/null 2>&1 || return 2
    print_info "检查 Spring 代码格式（Spotless）..."
    (cd "$WORKDIR/spring" && mvn -q spotless:check)
}

lint_gozero() {
    command -v golangci-lint >/dev/null 2>&1 || return 2
    print_info "检查 GoZero 代码（golangci-lint）..."
    (cd "$WORKDIR/gozero/app" && golangci-lint run)
}

lint_nestjs() {
    command -v npm >/dev/null 2>&1 || return 2
    print_info "检查 NestJS 代码（ESLint + Prettier）..."
    (cd "$WORKDIR/nestjs" && npm run lint && npm run format:check) || return 1

    # TypeScript 编译类型检查
    print_info "检查 NestJS 类型（tsc --noEmit）..."
    (cd "$WORKDIR/nestjs" && ./node_modules/.bin/tsc --noEmit -p tsconfig.build.json) || return 1

    print_info "检查 NestJS 常量类成员顺序..."
    lint_constants_order "$WORKDIR/nestjs/src/common/constants"
}

lint_fastapi() {
    command -v ruff >/dev/null 2>&1 || return 2
    print_info "检查 FastAPI 代码（Ruff）..."
    (cd "$WORKDIR/fastapi" && ruff check .) || return 1

    # pyright 类型检查
    if command -v pyright >/dev/null 2>&1; then
        print_info "检查 FastAPI 类型标注（pyright）..."
        (cd "$WORKDIR/fastapi" && pyright) || return 1
    elif [ -f "$WORKDIR/fastapi/.venv/Scripts/python.exe" ]; then
        print_info "检查 FastAPI 类型标注（pyright via venv）..."
        (cd "$WORKDIR/fastapi" && .venv/Scripts/python.exe -m pyright) || return 1
    else
        print_warn "pyright 未安装，跳过类型检查"
    fi

    print_info "检查 FastAPI 常量类成员顺序..."
    lint_constants_order "$WORKDIR/fastapi/app/core/constants" || return 1
    print_info "检查 FastAPI 包导入规范..."
    lint_package_imports "$WORKDIR/fastapi"
}

# ==================== 执行检查 ====================

FAILED_SERVICES=""

for SERVICE in $SERVICES; do
    echo ""
    case "$SERVICE" in
        spring) lint_spring; STATUS=$? ;;
        gozero) lint_gozero; STATUS=$? ;;
        nestjs) lint_nestjs; STATUS=$? ;;
        fastapi) lint_fastapi; STATUS=$? ;;
        gateway)
            print_warn "gateway 为 APISIX 配置，无需代码检查，已跳过"
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
            print_info "$SERVICE 检查通过"
            ;;
        2)
            print_warn "$SERVICE 已跳过（对应工具未安装）"
            ;;
        *)
            print_error "$SERVICE 检查未通过"
            FAILED_SERVICES="$FAILED_SERVICES $SERVICE"
            ;;
    esac
done

echo ""
if [ -n "$FAILED_SERVICES" ]; then
    print_error "以下服务检查未通过:$FAILED_SERVICES"
    print_info "可先执行 ./mix format 自动格式化后重试"
    exit 1
fi

print_info "代码检查完成"
