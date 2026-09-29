#!/bin/bash

# 脚本说明：
# 将各服务 docs/ 目录下的静态 OpenAPI 文档同步到 Apifox，并在最后同步 README 到 Apifox 指定 Markdown 文档
#   spring  -> spring/docs/openapi.json
#   gozero  -> gozero/app/docs/openapi.json
#   nestjs  -> nestjs/docs/openapi.json
#   fastapi -> fastapi/docs/openapi.json
#   README  -> apifox-readme-sync.sh（Apifox CLI 的 doc create / doc update，未配置文档 ID 时跳过）
# 只读取仓库内的静态产物，不启动任何服务，也不访问本地中间件
# 依赖：curl、sed、tr、grep、mktemp，均为 Git Bash / WSL / Linux 自带，不需要 Python 或 jq
# 用法：./scripts/apifox-sync.sh [service...] [--dry-run] [--no-readme] [--create-readme]
#   service 可选值：gozero、spring、nestjs、fastapi，不指定时同步全部
#   --no-readme 只同步接口，不处理 README
#   --create-readme README 目标文档不存在时先创建（其余场景跳过并提示）
#   令牌与项目 ID 从根目录 .env 读取，变量说明见 .env.example

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ALL_SERVICES="gozero spring nestjs fastapi"
DEFAULT_BASE_URL="https://api.apifox.com"
DEFAULT_API_VERSION="2024-03-28"
DEFAULT_LOCALE="zh-CN"
DEFAULT_OVERWRITE_BEHAVIOR="AUTO_MERGE"
RETRY_TIMES=3
RETRY_INTERVAL_SECONDS=3
REQUEST_TIMEOUT_SECONDS=180

TMP_DIR=""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

show_usage() {
    echo "用法: ./scripts/apifox-sync.sh [service...] [--dry-run] [--no-readme] [--create-readme]"
    echo "  service 可选值：gozero、spring、nestjs、fastapi，不指定时同步全部"
    echo "  --dry-run 只校验产物与配置，不发起导入请求"
    echo "  --no-readme 只同步接口文档，不处理 README"
    echo "  --create-readme 未配置 README 目标文档时先创建"
}

# ==================== 环境变量读取 ====================

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

env_flag() {
    local name="$1"
    local default_value="$2"
    local raw
    raw=$(trim "${!name}")
    if [ -z "$raw" ]; then
        printf '%s' "$default_value"
        return 0
    fi
    case "$raw" in
        1|true|True|TRUE|yes|Yes|YES|y|Y|on|On|ON) printf 'true' ;;
        *) printf 'false' ;;
    esac
}

env_int() {
    local raw
    raw=$(trim "${!1}")
    printf '%s' "$raw"
}

require_int_if_set() {
    local name="$1"
    local raw
    raw=$(trim "${!name}")
    if [ -z "$raw" ]; then
        return 0
    fi
    case "$raw" in
        *[!0-9]*)
            print_error "环境变量 $name 需要的是「数字 ID」，当前填的是: $raw"
            print_error "Apifox 的目录名不能直接填；接口目录 ID 可用 apifox-cli 获取:"
            print_error "  apifox folder list --project <项目ID> --type endpoint"
            print_error "若暂时不想维护 ID，可把 APIFOX_FOLDER_* 留空，导入时会落到项目根目录"
            return 1
            ;;
    esac
    return 0
}

is_valid_behavior() {
    case "$1" in
        OVERWRITE_EXISTING|AUTO_MERGE|KEEP_EXISTING|CREATE_NEW) return 0 ;;
        *) return 1 ;;
    esac
}

folder_env_name() {
    case "$1" in
        gozero) printf 'APIFOX_FOLDER_GOZERO' ;;
        spring) printf 'APIFOX_FOLDER_SPRING' ;;
        nestjs) printf 'APIFOX_FOLDER_NESTJS' ;;
        fastapi) printf 'APIFOX_FOLDER_FASTAPI' ;;
    esac
}

spec_path_for() {
    case "$1" in
        gozero) printf '%s' "$WORKDIR/gozero/app/docs/openapi.json" ;;
        spring) printf '%s' "$WORKDIR/spring/docs/openapi.json" ;;
        nestjs) printf '%s' "$WORKDIR/nestjs/docs/openapi.json" ;;
        fastapi) printf '%s' "$WORKDIR/fastapi/docs/openapi.json" ;;
    esac
}

load_env() {
    if [ ! -f "$WORKDIR/.env" ]; then
        print_warn "未找到根目录 .env，将仅使用当前环境变量"
        return 0
    fi

    # 先记下调用方已显式传入的 APIFOX_* 变量，sourcing 之后再还原
    # 这样 APIFOX_PROJECT_ID=xxx ./mix apifox 这类临时覆盖不会被 .env 顶掉
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

# ==================== 请求构造 ====================

build_options_json() {
    local service="$1"
    local json
    json='{'
    json="$json\"endpointOverwriteBehavior\":\"$endpoint_behavior\""
    json="$json,\"schemaOverwriteBehavior\":\"$schema_behavior\""
    json="$json,\"updateFolderOfChangedEndpoint\":$update_folder_of_changed"
    # 网关才是真实入口，BasePath 与 Base URL 统一交给 Apifox 环境面板维护
    json="$json,\"prependBasePath\":false"
    json="$json,\"deleteUnmatchedResources\":$delete_unmatched"

    local folder_id
    folder_id=$(env_int "$(folder_env_name "$service")")
    if [ -n "$folder_id" ]; then
        json="$json,\"targetEndpointFolderId\":$folder_id"
    fi

    local schema_folder_id
    schema_folder_id=$(env_int APIFOX_SCHEMA_FOLDER_ID)
    if [ -n "$schema_folder_id" ]; then
        json="$json,\"targetSchemaFolderId\":$schema_folder_id"
    fi

    local branch_id
    branch_id=$(env_int APIFOX_BRANCH_ID)
    if [ -n "$branch_id" ]; then
        json="$json,\"targetBranchId\":$branch_id"
    fi

    local module_id
    module_id=$(env_int APIFOX_MODULE_ID)
    if [ -n "$module_id" ]; then
        json="$json,\"moduleId\":$module_id"
    fi

    json="$json}"
    printf '%s' "$json"
    return 0
}

# 把整份 OpenAPI 文档转义成 JSON 字符串，再拼上 options，落到临时文件
# 走文件而不是命令行参数，避免大文档触发 Windows 命令行长限制
build_payload_file() {
    local spec_file="$1"
    local options_json="$2"
    local out_file="$3"

    {
        printf '{"input":"'
        # JSON 里的换行只是排版空白，直接换成空格，无需跨行累积即可保证不残留裸控制字符
        # 于是只剩两种必须转义的字符：反斜杠与双引号
        tr '\r\n' '  ' < "$spec_file" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
        printf '","options":%s}' "$options_json"
    } > "$out_file"
    return 0
}

extract_counter() {
    local json="$1"
    local key="$2"
    printf '%s' "$json" \
        | grep -o "\"$key\"[[:space:]]*:[[:space:]]*[0-9]\+" \
        | head -n 1 \
        | grep -o '[0-9]\+$'
    return 0
}

extract_error_messages() {
    local json="$1"
    printf '%s' "$json" \
        | grep -o '"message"[[:space:]]*:[[:space:]]*"[^"]*"' \
        | head -n 5 \
        | sed -e 's/^"message"[[:space:]]*:[[:space:]]*"//' -e 's/"$//'
    return 0
}

# ==================== 请求发送 ====================

post_import_openapi() {
    local url="$1"
    local payload_file="$2"
    local response_file="$3"
    local curl_err_file="$4"
    local attempt=1
    local http_status

    while [ "$attempt" -le "$RETRY_TIMES" ]; do
        http_status=$(curl -sS -X POST "$url" \
            -H "Authorization: Bearer $token" \
            -H "X-Apifox-Api-Version: $api_version" \
            -H "Content-Type: application/json" \
            --data-binary "@$payload_file" \
            --max-time "$REQUEST_TIMEOUT_SECONDS" \
            -o "$response_file" \
            -w '%{http_code}' 2>"$curl_err_file")
        http_status=${http_status:-000}

        if [ "$http_status" = "200" ]; then
            return 0
        fi

        if [ "$http_status" = "000" ]; then
            print_error "请求失败: $(tr -d '\r\n' < "$curl_err_file")"
            return 1
        fi

        local detail
        detail=$(tr -d '\r\n' < "$response_file" | cut -c1-500)

        case "$http_status" in
            403|429|500|502|503|504) ;;
            *)
                print_error "HTTP $http_status: $detail"
                return 1
                ;;
        esac

        if [ "$attempt" -eq "$RETRY_TIMES" ]; then
            print_error "HTTP $http_status（已重试 $RETRY_TIMES 次）: $detail"
            return 1
        fi

        print_warn "第 $attempt 次调用返回 HTTP $http_status，${RETRY_INTERVAL_SECONDS} 秒后重试"
        sleep "$RETRY_INTERVAL_SECONDS"
        attempt=$((attempt + 1))
    done

    return 1
}

# ==================== 主流程 ====================

main() {
    local dry_run="false"
    local readme_enabled="true"
    local create_readme="false"
    local service_args=""
    local arg
    for arg in "$@"; do
        case "$arg" in
            --dry-run)
                dry_run="true"
                ;;
            --no-readme)
                readme_enabled="false"
                ;;
            --create-readme)
                create_readme="true"
                ;;
            -h|--help)
                show_usage
                return 0
                ;;
            -*)
                print_error "未知参数: $arg"
                show_usage
                return 1
                ;;
            *)
                service_args="$service_args $arg"
                ;;
        esac
    done

    local service
    for service in $service_args; do
        case " $ALL_SERVICES " in
            *" $service "*)
                ;;
            *)
                print_error "未知服务: $service"
                show_usage
                return 1
                ;;
        esac
    done

    if ! command -v curl >/dev/null 2>&1; then
        print_error "未找到 curl，请先安装 curl 后重试"
        return 1
    fi

    load_env

    token=$(env_value APIFOX_ACCESS_TOKEN "")
    project_id=$(env_value APIFOX_PROJECT_ID "")
    if [ -z "$token" ] || [ -z "$project_id" ]; then
        print_error "缺少 Apifox 配置，请在根目录 .env 中设置："
        echo "  APIFOX_ACCESS_TOKEN  # Apifox -> 右上角头像 -> 账号设置 -> API 访问令牌"
        echo "  APIFOX_PROJECT_ID    # 项目 URL 形如 https://app.apifox.com/project/<项目ID>/xxx"
        return 1
    fi

    base_url=$(env_value APIFOX_BASE_URL "$DEFAULT_BASE_URL")
    base_url="${base_url%/}"
    api_version=$(env_value APIFOX_API_VERSION "$DEFAULT_API_VERSION")
    locale=$(env_value APIFOX_LOCALE "$DEFAULT_LOCALE")

    local name
    for name in APIFOX_FOLDER_GOZERO APIFOX_FOLDER_SPRING APIFOX_FOLDER_NESTJS APIFOX_FOLDER_FASTAPI \
        APIFOX_SCHEMA_FOLDER_ID APIFOX_BRANCH_ID APIFOX_MODULE_ID; do
        require_int_if_set "$name" || return 1
    done

    endpoint_behavior=$(env_value APIFOX_ENDPOINT_OVERWRITE_BEHAVIOR "$DEFAULT_OVERWRITE_BEHAVIOR" | tr '[:lower:]' '[:upper:]')
    if ! is_valid_behavior "$endpoint_behavior"; then
        print_error "APIFOX_ENDPOINT_OVERWRITE_BEHAVIOR 取值非法: $endpoint_behavior"
        print_error "可选值：OVERWRITE_EXISTING、AUTO_MERGE、KEEP_EXISTING、CREATE_NEW"
        return 1
    fi

    schema_behavior=$(env_value APIFOX_SCHEMA_OVERWRITE_BEHAVIOR "$DEFAULT_OVERWRITE_BEHAVIOR" | tr '[:lower:]' '[:upper:]')
    if ! is_valid_behavior "$schema_behavior"; then
        print_error "APIFOX_SCHEMA_OVERWRITE_BEHAVIOR 取值非法: $schema_behavior"
        print_error "可选值：OVERWRITE_EXISTING、AUTO_MERGE、KEEP_EXISTING、CREATE_NEW"
        return 1
    fi

    delete_unmatched=$(env_flag APIFOX_DELETE_UNMATCHED_RESOURCES "false")
    update_folder_of_changed=$(env_flag APIFOX_UPDATE_FOLDER_OF_CHANGED_ENDPOINT "true")

    print_info "Apifox 项目: $project_id（$base_url）"
    if [ "$dry_run" = "true" ]; then
        print_info "dry-run 模式：只校验产物与配置，不发起导入请求"
    fi

    TMP_DIR=$(mktemp -d 2>/dev/null)
    if [ -z "$TMP_DIR" ] || [ ! -d "$TMP_DIR" ]; then
        print_error "无法创建临时目录，请检查系统 mktemp 是否可用"
        return 1
    fi

    local services="${service_args:-$ALL_SERVICES}"
    local failed_services=""
    local spec_file options_json payload_file response_file curl_err_file response
    local url created updated ignored failed errors

    for service in $services; do
        echo ""
        spec_file=$(spec_path_for "$service")
        if [ ! -f "$spec_file" ]; then
            print_error "[$service] 未找到静态文档 $spec_file，请先执行 ./mix swag $service"
            failed_services="$failed_services $service"
            continue
        fi

        options_json=$(build_options_json "$service")

        if [ "$dry_run" = "true" ]; then
            print_info "[$service] 文档 $(wc -c < "$spec_file" | tr -d ' ') 字节，导入选项 $options_json"
            continue
        fi

        payload_file="$TMP_DIR/$service-payload.json"
        response_file="$TMP_DIR/$service-response.json"
        curl_err_file="$TMP_DIR/$service-curl.err"
        build_payload_file "$spec_file" "$options_json" "$payload_file"

        url="$base_url/v1/projects/$project_id/import-openapi?locale=$locale"
        if ! post_import_openapi "$url" "$payload_file" "$response_file" "$curl_err_file"; then
            print_error "[$service] 同步失败"
            failed_services="$failed_services $service"
            continue
        fi

        response=$(cat "$response_file")
        created=$(extract_counter "$response" endpointCreated)
        updated=$(extract_counter "$response" endpointUpdated)
        ignored=$(extract_counter "$response" endpointIgnored)
        failed=$(extract_counter "$response" endpointFailed)
        created=${created:-0}
        updated=${updated:-0}
        ignored=${ignored:-0}
        failed=${failed:-0}

        print_info "[$service] 新增 $created / 更新 $updated / 忽略 $ignored / 失败 $failed"

        if [ "$failed" != "0" ]; then
            errors=$(extract_error_messages "$response")
            if [ -n "$errors" ]; then
                echo "$errors" | while IFS= read -r line; do
                    print_error "  $line"
                done
            fi
            failed_services="$failed_services $service"
        fi
    done

    if [ "$readme_enabled" = "true" ]; then
        echo ""
        print_info "开始同步 README 到 Apifox 项目 Markdown 文档"
        local readme_args=("--skip-if-unset")
        if [ "$dry_run" = "true" ]; then
            readme_args+=("--dry-run")
        fi
        if [ "$create_readme" = "true" ]; then
            readme_args+=("--create")
        fi
        if ! bash "$WORKDIR/scripts/apifox-readme-sync.sh" "${readme_args[@]}"; then
            failed_services="$failed_services README"
        fi
    fi

    echo ""
    if [ -n "$failed_services" ]; then
        print_error "以下资源同步未全部成功:$failed_services"
        return 1
    fi

    print_info "Apifox 同步完成"
    return 0
}

cleanup() {
    if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}

trap cleanup EXIT

print_info "开始同步 OpenAPI 文档到 Apifox..."
if main "$@"; then
    print_info "Apifox 同步流程结束"
    exit 0
fi

print_error "Apifox 同步失败"
exit 1
