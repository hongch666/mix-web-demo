#!/bin/bash

# 脚本说明：
# 检查 Apifox 项目里「接口与数据模型的引用」是否完整（只读，不写入任何内容）
#   背景：接口的请求体/响应体以 JSON Schema 存储，模型通过 $ref: #/definitions/<模型ID> 引用，
#   模型被删除或重建后引用不会自动回滚，Apifox「校验响应」会报
#   can't resolve reference #/definitions/<数字ID> from id http://json-schema.org/draft-04/schema#
#   本脚本导出一次项目快照并与现存数据模型比对，列出断链的接口与字段
# 依赖：apifox CLI、python（读取快照）、mktemp
# 用法：./scripts/apifox-check.sh [options]
#   -h, --help        显示帮助
#   --keep <dir>      保留导出的快照与模型清单到指定目录，便于人工排查
#   --examples <n>    打印的断链示例条数，默认 5
#   --no-color        关闭彩色输出
# 配置：令牌与项目 ID 从根目录 .env 读取（APIFOX_ACCESS_TOKEN / APIFOX_PROJECT_ID），变量说明见 .env.example
# 返回码：0 引用完整；1 存在断链；2 缺少配置、CLI 或 python
# 与 ./mix lint 的关系：该检查需要联网并读取 Apifox 项目，默认不并入离线 lint，需显式执行 ./mix apifox-check

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DEFAULT_EXAMPLES=5

TMP_DIR=""
KEEP_DIR=""
EXAMPLES="$DEFAULT_EXAMPLES"
USE_COLOR="true"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    if [ "$USE_COLOR" = "true" ]; then
        echo -e "${GREEN}[INFO]${NC} $1"
    else
        echo "[INFO] $1"
    fi
}

print_warn() {
    if [ "$USE_COLOR" = "true" ]; then
        echo -e "${YELLOW}[WARN]${NC} $1" >&2
    else
        echo "[WARN] $1" >&2
    fi
}

print_error() {
    if [ "$USE_COLOR" = "true" ]; then
        echo -e "${RED}[ERROR]${NC} $1" >&2
    else
        echo "[ERROR] $1" >&2
    fi
}

show_usage() {
    echo "用法: ./scripts/apifox-check.sh [--keep <dir>] [--examples <n>] [--no-color]"
    echo "  检查 Apifox 项目里接口与数据模型的引用是否完整（只读，不写入）"
    echo "  --keep <dir>    保留导出的项目快照与模型清单到指定目录"
    echo "  --examples <n>  打印的断链示例条数，默认 $DEFAULT_EXAMPLES"
    echo "  --no-color      关闭彩色输出"
    echo "返回码: 0 引用完整；1 存在断链；2 缺少配置、Apifox CLI 或 python"
}

trim() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

env_value() {
    local name="$1"
    local default_value="$2"
    local value
    value=$(trim "${!name}")
    if [ -z "$value" ]; then
        printf '%s' "$default_value"
    else
        printf '%s' "$value"
    fi
}

load_env() {
    if [ ! -f "$WORKDIR/.env" ]; then
        print_warn "未找到根目录 .env，将仅使用当前环境变量"
        return 0
    fi

    local preset
    preset=$(env | grep -E '^APIFOX_[A-Z0-9_]+=' || true)

    set -a
    # shellcheck disable=SC1091
    . "$WORKDIR/.env"
    set +a

    if [ -n "$preset" ]; then
        while IFS= read -r assignment; do
            [ -n "$assignment" ] || continue
            export "$assignment"
        done <<< "$preset"
    fi

    return 0
}

# python 只用来读快照，优先 python，其次 python3
resolve_python() {
    if command -v python >/dev/null 2>&1; then
        printf 'python'
        return 0
    fi
    if command -v python3 >/dev/null 2>&1; then
        printf 'python3'
        return 0
    fi
    return 1
}

cleanup() {
    if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}

trap cleanup EXIT

main() {
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help) show_usage; return 0 ;;
            --keep)
                case "${2:-}" in
                    ''|-*)
                        print_error "--keep 需要一个目录参数，例如 --keep /tmp/apifox"
                        return 2
                        ;;
                esac
                KEEP_DIR="$2"
                shift 2
                ;;
            --keep=*)
                KEEP_DIR="${1#*=}"
                shift
                ;;
            --examples)
                case "${2:-}" in
                    ''|-*)
                        print_error "--examples 需要一个数字参数，例如 --examples 10"
                        return 2
                        ;;
                esac
                EXAMPLES="$2"
                shift 2
                ;;
            --examples=*)
                EXAMPLES="${1#*=}"
                shift
                ;;
            --no-color)
                USE_COLOR="false"
                shift
                ;;
            *)
                print_error "未知参数: $1"
                show_usage
                return 2
                ;;
        esac
    done
    case "$EXAMPLES" in
        ''|*[!0-9]*)
            print_error "--examples 需要是数字，当前是: $EXAMPLES"
            return 2
            ;;
    esac

    if ! command -v apifox >/dev/null 2>&1; then
        print_error "未找到 apifox 命令，请先安装 Apifox CLI:"
        echo "  npm i -g apifox-cli@latest"
        return 2
    fi

    local python_bin
    if ! python_bin=$(resolve_python); then
        print_error "未找到 python 或 python3，无法读取项目快照"
        return 2
    fi

    local checker="$WORKDIR/scripts/apifox-schema-refs.py"
    if [ ! -f "$checker" ]; then
        print_error "缺少 $checker"
        return 2
    fi

    load_env

    local token project_id
    token=$(env_value APIFOX_ACCESS_TOKEN "")
    project_id=$(env_value APIFOX_PROJECT_ID "")
    if [ -z "$token" ] || [ -z "$project_id" ]; then
        print_error "缺少 Apifox 配置，请在根目录 .env 中设置："
        echo "  APIFOX_ACCESS_TOKEN  # Apifox -> 右上角头像 -> 账号设置 -> API 访问令牌"
        echo "  APIFOX_PROJECT_ID    # 项目 URL 形如 https://app.apifox.com/project/<项目ID>/xxx"
        return 2
    fi

    TMP_DIR=$(mktemp -d 2>/dev/null)
    if [ -z "$TMP_DIR" ] || [ ! -d "$TMP_DIR" ]; then
        print_error "无法创建临时目录，请检查系统 mktemp 是否可用"
        return 2
    fi

    local snapshot="$TMP_DIR/project.apifox.json"
    local models="$TMP_DIR/models.json"
    local branch_args=()
    if [ -n "$(trim "${APIFOX_BRANCH_ID:-}")" ]; then
        branch_args=("--branch" "$(trim "$APIFOX_BRANCH_ID")")
    fi

    print_info "导出 Apifox 项目快照（项目 $project_id）..."
    if ! apifox export --project "$project_id" --access-token "$token" "${branch_args[@]}" \
        --format apifox --scope all --no-include-api-cases --output "$snapshot" >/dev/null 2>&1; then
        print_error "项目快照导出失败，请检查令牌、项目 ID 与网络"
        return 1
    fi
    if ! apifox schema list --project "$project_id" --access-token "$token" "${branch_args[@]}" \
        >"$models" 2>/dev/null; then
        print_error "数据模型清单获取失败，请检查令牌与项目 ID"
        return 1
    fi

    local output dangling endpoints model_count
    output=$("$python_bin" "$checker" --check "$snapshot" --models "$models" --examples "$EXAMPLES" || true)
    dangling=$(printf '%s\n' "$output" | sed -n 's/^DANGLING=//p' | head -n 1)
    endpoints=$(printf '%s\n' "$output" | sed -n 's/^ENDPOINTS=//p' | head -n 1)
    model_count=$(printf '%s\n' "$output" | sed -n 's/^MODELS=//p' | head -n 1)

    if [ -n "$KEEP_DIR" ]; then
        if mkdir -p "$KEEP_DIR" 2>/dev/null; then
            cp "$snapshot" "$KEEP_DIR/project.apifox.json" 2>/dev/null || true
            cp "$models" "$KEEP_DIR/models.json" 2>/dev/null || true
            print_info "已保留快照与模型清单: $KEEP_DIR"
        else
            print_warn "创建目录失败，未保留快照: $KEEP_DIR"
        fi
    fi

    if [ -z "$dangling" ]; then
        print_error "快照解析失败，未得到断链统计结果"
        printf '%s\n' "$output" | sed -n '4,$p' >&2
        return 1
    fi

    print_info "接口 ${endpoints:-?} 个，数据模型 ${model_count:-?} 个"
    if [ "$dangling" = "0" ]; then
        print_info "接口与数据模型的引用完整（无 can't resolve reference 风险）"
        return 0
    fi

    print_error "检测到 $dangling 处模型引用断链，Apifox「校验响应」会报 can't resolve reference"
    printf '%s\n' "$output" | sed -n '4,$p' | while IFS= read -r line; do
        if [ -n "$line" ]; then
            print_error "  $line"
        fi
    done
    print_info "修复：执行 ./mix apifox <service> 重新同步（末尾会自动按覆盖模式重导修好断链）"
    return 1
}

main "$@"
exit $?
