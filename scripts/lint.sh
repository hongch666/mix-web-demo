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

# 常量文件规范检查（四个服务共用：成员注释、分类注释、函数成员在前），python 缺失时跳过
lint_constants() {
    if command -v python >/dev/null 2>&1; then
        python "$WORKDIR/scripts/constants.py" --check "$1"
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 "$WORKDIR/scripts/constants.py" --check "$1"
        return
    fi
    print_warn "未检测到 python，跳过常量文件规范检查"
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

# API 文件格式检查（gozero）：goctl api format 没有只读校验模式，
# 把 .api 复制到临时目录执行格式化后与仓库文件比对，仓库文件只读不修改，goctl 缺失时跳过
lint_api_format() {
    if ! command -v goctl >/dev/null 2>&1; then
        print_warn "未检测到 goctl，跳过 API 文件格式检查"
        return 0
    fi

    local api_dir="$WORKDIR/gozero/api"
    [ -d "$api_dir" ] || return 0

    local work_dir check_dir
    work_dir="$(mktemp -d)"
    check_dir="$work_dir/api"
    mkdir -p "$check_dir"
    cp -r "$api_dir/." "$check_dir/"

    # goctl 是原生程序，Windows 下无法识别 /c/... 这类 POSIX 路径，需要转成本机原生路径
    if command -v cygpath >/dev/null 2>&1; then
        check_dir="$(cygpath -w "$check_dir")"
    fi

    # 在临时目录内执行：goctl 模块识别异常时会以调用者当前目录为基准回退执行 go mod init / go work use，
    # 留在仓库目录会污染根目录的 go.mod 与 go.work
    if ! (cd "$work_dir" && goctl api format -dir "$check_dir" >/dev/null 2>&1); then
        rm -rf "$work_dir"
        print_error "goctl api format 执行失败，请检查 .api 文件语法"
        return 1
    fi

    local diff_rc=0
    diff -r --strip-trailing-cr "$api_dir" "$work_dir/api" >/dev/null 2>&1 || diff_rc=1
    if [ "$diff_rc" -ne 0 ]; then
        print_error "API 文件未通过 goctl api format 格式检查："
        diff -r --strip-trailing-cr "$api_dir" "$work_dir/api" | sed -n '1,60p'
        rm -rf "$work_dir"
        return 1
    fi
    rm -rf "$work_dir"
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
    lint_controller_vo "$WORKDIR/spring/src/main/java/com/hcsy/spring/web/controller" || return 1
    print_info "检查 Spring 常量文件规范（成员注释与分类注释）..."
    lint_constants "$WORKDIR/spring/src/main/java/com/hcsy/spring/common/constants" || return 1
    command -v mvn >/dev/null 2>&1 || return 2
    print_info "检查 Spring 代码格式（Spotless）..."
    (cd "$WORKDIR/spring" && mvn -q spotless:check)
}

lint_gozero() {
    print_info "检查 GoZero 常量文件规范（成员注释与分类注释）..."
    lint_constants "$WORKDIR/gozero/app/common/constants" || return 1
    command -v golangci-lint >/dev/null 2>&1 || return 2
    print_info "检查 GoZero 代码（golangci-lint）..."
    (cd "$WORKDIR/gozero/app" && golangci-lint run) || return 1

    # 校验 .api 文件是否符合 goctl api format 规范
    print_info "检查 GoZero API 文件格式（goctl api format）..."
    lint_api_format || return 1

    # 校验 goctl 生成产物：不允许修改的文件按模板重新生成后比对，允许编辑的文件只校验首行标记注释
    print_info "校验 GoZero 生成产物与 gozero/template 是否一致..."
    bash "$WORKDIR/gozero/script/goctl/checkGenerated.sh" || return 1
}

lint_nestjs() {
    command -v npm >/dev/null 2>&1 || return 2
    print_info "检查 NestJS 代码（ESLint + Prettier）..."
    (cd "$WORKDIR/nestjs" && npm run lint && npm run format:check) || return 1

    # TypeScript 编译类型检查
    print_info "检查 NestJS 类型（tsc --noEmit）..."
    (cd "$WORKDIR/nestjs" && ./node_modules/.bin/tsc --noEmit -p tsconfig.build.json) || return 1

    print_info "检查 NestJS 常量文件规范（成员注释、分类注释、函数成员在前）..."
    lint_constants "$WORKDIR/nestjs/src/common/constants"
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

    print_info "检查 FastAPI 常量文件规范（成员注释、分类注释、函数成员在前）..."
    lint_constants "$WORKDIR/fastapi/app/core/constants" || return 1
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
