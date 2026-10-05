#!/bin/bash

# 脚本说明：
# 这个脚本用于对四个服务执行编译校验（只读，只验证能否编译通过，不产出打包目录）
# 与 ./scripts/build.sh 的区别：build 会清理 dist 并输出可运行产物，这里只做编译检查
# 用法：./scripts/compile.sh [service...]
#   service 可选值：spring、gozero、nestjs、fastapi，不指定时校验全部服务

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

# 未指定服务时校验全部服务
if [ $# -gt 0 ]; then
    SERVICES="$*"
else
    SERVICES="spring gozero nestjs fastapi"
fi

# ==================== 各服务编译校验 ====================
# 返回码约定：0 表示通过，2 表示跳过（工具未安装），其它表示编译失败

# FastAPI 编译校验：对 app、tests、main.py 逐个源码做编译，只报告语法错误
# 不写 __pycache__、不做类型检查（仓库 pyright 基线存在大量既有报错，不适合作为门禁）
PY_COMPILE_SNIPPET='
import pathlib
import sys

roots = [pathlib.Path("app"), pathlib.Path("tests"), pathlib.Path("main.py")]
files = []
for root in roots:
    files.extend([root] if root.is_file() else sorted(root.rglob("*.py")))
failed = []
for path in files:
    try:
        compile(path.read_bytes(), str(path), "exec")
    except SyntaxError as exc:
        failed.append(f"{path}:{exc.lineno}: {exc.msg}")
for item in failed:
    print(item)
sys.exit(1 if failed else 0)
'

compile_spring() {
    command -v mvn >/dev/null 2>&1 || return 2
    print_info "校验 Spring 编译（mvn compile）..."
    # 跳过测试与 Spotless：只验证主源码能否编译通过
    (cd "$WORKDIR/spring" && mvn -q -DskipTests -Dspotless.check.skip=true compile)
}

compile_gozero() {
    command -v go >/dev/null 2>&1 || return 2
    print_info "校验 GoZero 编译（go build ./...）..."
    # go build ./... 只编译不落盘可执行文件，等价于全量编译检查
    (cd "$WORKDIR/gozero/app" && go build ./...)
}

compile_nestjs() {
    if command -v bun >/dev/null 2>&1; then
        print_info "校验 NestJS 编译（tsc --noEmit）..."
        # --noEmit 只做类型检查，不输出 dist，避免与打包产物混用
        (cd "$WORKDIR/nestjs" && bunx tsc --noEmit -p tsconfig.build.json)
        return
    fi
    command -v npx >/dev/null 2>&1 || return 2
    print_info "校验 NestJS 编译（tsc --noEmit）..."
    (cd "$WORKDIR/nestjs" && npx tsc --noEmit -p tsconfig.build.json)
}

compile_fastapi() {
    if command -v uv >/dev/null 2>&1; then
        print_info "校验 FastAPI 编译（字节码编译）..."
        (cd "$WORKDIR/fastapi" && uv run python -c "$PY_COMPILE_SNIPPET")
        return
    fi
    if command -v python3 >/dev/null 2>&1; then
        print_info "校验 FastAPI 编译（字节码编译）..."
        (cd "$WORKDIR/fastapi" && python3 -c "$PY_COMPILE_SNIPPET")
        return
    fi
    if command -v python >/dev/null 2>&1; then
        print_info "校验 FastAPI 编译（字节码编译）..."
        (cd "$WORKDIR/fastapi" && python -c "$PY_COMPILE_SNIPPET")
        return
    fi
    return 2
}

# ==================== 执行校验 ====================

FAILED_SERVICES=""

for SERVICE in $SERVICES; do
    echo ""
    case "$SERVICE" in
        spring) compile_spring; STATUS=$? ;;
        gozero) compile_gozero; STATUS=$? ;;
        nestjs) compile_nestjs; STATUS=$? ;;
        fastapi) compile_fastapi; STATUS=$? ;;
        gateway)
            print_warn "gateway 为 APISIX 配置，无需编译，已跳过"
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
            print_info "$SERVICE 编译校验通过"
            ;;
        2)
            print_warn "$SERVICE 已跳过（对应工具未安装）"
            ;;
        *)
            print_error "$SERVICE 编译校验未通过"
            FAILED_SERVICES="$FAILED_SERVICES $SERVICE"
            ;;
    esac
done

echo ""
if [ -n "$FAILED_SERVICES" ]; then
    print_error "以下服务编译校验未通过:$FAILED_SERVICES"
    exit 1
fi

print_info "编译校验完成"
