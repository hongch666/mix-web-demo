#!/bin/bash

# 脚本说明：
# 生成四个服务的静态 OpenAPI 文档（JSON 与 YAML 各一份），各自落在服务自身的 docs/ 目录
#   spring  -> spring/docs/openapi.json  + openapi.yaml
#   gozero  -> gozero/app/docs/openapi.json + openapi.yaml（JSON 被 docs/embed.go 嵌入二进制）
#   nestjs  -> nestjs/docs/openapi.json  + openapi.yaml
#   fastapi -> fastapi/docs/openapi.json + openapi.yaml
# 四个服务均为离线生成：不启动 HTTP 服务，也不依赖 Nacos、Redis、MySQL、RabbitMQ 等中间件
# 用法：./scripts/swag-init.sh [service...]
#   service 可选值：spring、gozero、nestjs、fastapi，不指定时处理全部

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

# 未指定服务时处理全部服务
if [ $# -gt 0 ]; then
    SERVICES="$*"
else
    SERVICES="spring gozero nestjs fastapi"
fi

# 先把网关的 block-internal URI 黑名单抽取为共享 JSON，供各服务生成器注入 403
# 网关黑名单是服务代码无法自行推导的外部约束，必须在文档生成阶段同步
extract_gateway_blocklist() {
    if command -v python >/dev/null 2>&1; then
        python "$WORKDIR/scripts/gateway-blocklist.py" --check > "$WORKDIR/scripts/generated/gateway-blocklist.json"
    elif command -v python3 >/dev/null 2>&1; then
        python3 "$WORKDIR/scripts/gateway-blocklist.py" --check > "$WORKDIR/scripts/generated/gateway-blocklist.json"
    else
        print_warn "未检测到 python，无法抽取网关黑名单，403 文档注入将跳过"
        return 0
    fi
    local count
    count=$(python -c "import json,sys;print(len(json.load(open(sys.argv[1]))['uris']))" "$WORKDIR/scripts/generated/gateway-blocklist.json" 2>/dev/null || echo '?')
    print_info "网关内部接口黑名单已抽取（${count} 条）"
}

mkdir -p "$WORKDIR/scripts/generated"
extract_gateway_blocklist

# ==================== 各服务生成 ====================
# 返回码约定：0 表示成功，2 表示跳过（工具未安装），其它表示生成失败

gen_spring() {
    command -v mvn >/dev/null 2>&1 || return 2
    print_info "生成 Spring OpenAPI 文档（隔离 Web 层，不依赖中间件）..."
    # 通过环境变量传黑名单绝对路径：mvn 的 fork JVM user.dir 可能不是 spring/，相对路径不可靠
    export GATEWAY_BLOCKLIST_JSON="$WORKDIR/scripts/generated/gateway-blocklist.json"
    # 跳过 Spotless：文档生成不承担格式门禁职责，格式检查由 ./mix lint spring 负责
    (cd "$WORKDIR/spring" && mvn -q test -Dtest=OpenApiDocGenerator -DfailIfNoTests=false \
        -Dspotless.check.skip=true)
}

gen_gozero() {
    command -v goctl >/dev/null 2>&1 || return 2
    print_info "生成 GoZero OpenAPI 文档（goctl 解析 .api）..."
    # 产物固定落在 gozero/app/docs/openapi.json，被 docs/embed.go 嵌入二进制，不要改名
    bash "$WORKDIR/gozero/script/swagger/genSwagger.sh"
}

gen_nestjs() {
    # 必须使用 Bun：项目依赖 uuid@14 为纯 ESM，Node 20 的 CJS 加载器无法 require，
    # ts-node / nest build 产物都会在运行期报 ERR_REQUIRE_ESM
    if ! command -v bun >/dev/null 2>&1; then
        print_warn "未检测到 Bun，NestJS 文档生成需要 Bun（项目默认 Node 运行时）"
        return 2
    fi
    print_info "生成 NestJS OpenAPI 文档（preview 模式，不实例化 provider）..."
    (cd "$WORKDIR/nestjs" && bun src/script/generateOpenapi.ts)
}

gen_fastapi() {
    if command -v uv >/dev/null 2>&1; then
        print_info "生成 FastAPI OpenAPI 文档（导入应用工厂，不启动 uvicorn）..."
        (cd "$WORKDIR/fastapi" && uv run python script/genOpenapi.py)
        return
    fi
    if [ -x "$WORKDIR/fastapi/.venv/Scripts/python.exe" ]; then
        print_info "生成 FastAPI OpenAPI 文档（导入应用工厂，不启动 uvicorn）..."
        (cd "$WORKDIR/fastapi" && .venv/Scripts/python.exe script/genOpenapi.py)
        return
    fi
    if [ -x "$WORKDIR/fastapi/.venv/bin/python" ]; then
        print_info "生成 FastAPI OpenAPI 文档（导入应用工厂，不启动 uvicorn）..."
        (cd "$WORKDIR/fastapi" && .venv/bin/python script/genOpenapi.py)
        return
    fi
    command -v python >/dev/null 2>&1 || return 2
    print_info "生成 FastAPI OpenAPI 文档（导入应用工厂，不启动 uvicorn）..."
    (cd "$WORKDIR/fastapi" && python script/genOpenapi.py)
}

# ==================== 执行生成 ====================

FAILED_SERVICES=""

for SERVICE in $SERVICES; do
    echo ""
    case "$SERVICE" in
        spring) gen_spring; STATUS=$? ;;
        gozero) gen_gozero; STATUS=$? ;;
        nestjs) gen_nestjs; STATUS=$? ;;
        fastapi) gen_fastapi; STATUS=$? ;;
        gateway)
            print_warn "gateway 为 APISIX 配置，无 OpenAPI 产物，已跳过"
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
            print_info "$SERVICE OpenAPI 文档生成完成"
            ;;
        2)
            print_warn "$SERVICE 已跳过（对应工具未安装）"
            ;;
        *)
            print_error "$SERVICE OpenAPI 文档生成失败"
            FAILED_SERVICES="$FAILED_SERVICES $SERVICE"
            ;;
    esac
done

echo ""
if [ -n "$FAILED_SERVICES" ]; then
    print_error "以下服务生成失败:$FAILED_SERVICES"
    exit 1
fi

print_info "静态 OpenAPI 文档已输出到各服务自身的 docs/ 目录"
print_info "如需同步到 Apifox，执行 ./mix apifox"
