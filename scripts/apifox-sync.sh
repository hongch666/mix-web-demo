#!/bin/bash

# 脚本说明：
# 将各服务 docs/ 目录下的静态 OpenAPI 文档同步到 Apifox，并在最后同步 README 到 Apifox 指定 Markdown 文档
#   spring  -> spring/docs/openapi.json
#   gozero  -> gozero/app/docs/openapi.json
#   nestjs  -> nestjs/docs/openapi.json
#   fastapi -> fastapi/docs/openapi.json
#   README  -> apifox-readme-sync.sh（Apifox CLI 的 doc create / doc update，未配置文档 ID 时跳过）
# 只读取仓库内的静态产物，不启动任何服务，也不访问本地中间件
# 导入前会为「本次文档新增」的接口补写 Apifox 责任人扩展 x-apifox-maintainer，默认取令牌账号的用户名
#   已存在接口的责任人只需写入一次：每轮对所有接口重写扩展会让全部接口被 Apifox 判定为已修改，
#   因此先用一次 apifox endpoint list 求差集，只对新增接口注入；有注入时才再导入一次原文档清掉残留扩展行
#   置 APIFOX_MAINTAINER_FORCE=true 可退回「每轮全量重写责任人」的行为；
#   置 APIFOX_MAINTAINER_CLEAN_EXTENSION=false（保留扩展行）时同样按全量注入，保证每轮导入内容一致
# 依赖：curl、sed、tr、grep、awk、mktemp，均为 Git Bash / WSL / Linux 自带；
#   接口清单差集与 WebSocket 接口同步额外需要 Python 与 Apifox CLI，任一缺失时分别回退为全量注入 / 跳过
# 用法：./scripts/apifox-sync.sh [service...] [--dry-run] [--no-readme] [--no-maintainer] [--create-readme]
#   service 可选值：gozero、spring、nestjs、fastapi，不指定时同步全部
#   --no-readme 只同步接口，不处理 README
#   --no-maintainer 只导入接口，不填充责任人
#   --create-readme README 目标文档不存在时先创建（其余场景跳过并提示）
#   令牌与项目 ID 从根目录 .env 读取，变量说明见 .env.example
# 默认以文档为准做全量对齐：清理目标目录下文档里没有的接口与数据模型（置 APIFOX_DELETE_UNMATCHED_RESOURCES=false 回到只增量、不清理）

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ALL_SERVICES="gozero spring nestjs fastapi"
DEFAULT_BASE_URL="https://api.apifox.com"
DEFAULT_API_VERSION="2024-03-28"
DEFAULT_LOCALE="zh-CN"
DEFAULT_OVERWRITE_BEHAVIOR="AUTO_MERGE"
DEFAULT_MAINTAINER_AUTO="true"
DEFAULT_MAINTAINER_CLEAN_EXTENSION="true"
DEFAULT_MAINTAINER_FORCE="false"
# 接口以代码生成的文档为唯一事实来源：默认清理目标目录下文档里没有的接口与数据模型
DEFAULT_DELETE_UNMATCHED_RESOURCES="true"
RETRY_TIMES=3
RETRY_INTERVAL_SECONDS=3
REQUEST_TIMEOUT_SECONDS=180

# 数据模型指纹状态目录（相对仓库根，随仓库提交）：
# 记录每个服务上一次成功同步到共享 Apifox 项目时的 components.schemas 指纹，
# 用于判断模型是否发生变更。它描述的是远端项目的同步基线而不是本机状态，
# 必须提交：否则 A 机器同步后 B 机器没有基线，会把「无历史」误判成「模型有变」，
# 从而用覆盖模式冲掉 A 侧保留的手工 Mock 与示例
SCHEMA_STATE_DIR="$WORKDIR/.apifox-state"

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
    echo "用法: ./scripts/apifox-sync.sh [service...] [--dry-run] [--no-readme] [--no-maintainer] [--create-readme]"
    echo "  service 可选值：gozero、spring、nestjs、fastapi，不指定时同步全部"
    echo "  --dry-run 只校验产物与配置，不发起导入请求"
    echo "  --no-readme 只同步接口文档，不处理 README"
    echo "  --no-maintainer 不填充接口责任人"
    echo "  --create-readme 未配置 README 目标文档时先创建"
    echo "  gozero 的 WebSocket 接口经 Apifox CLI 单独同步，只覆盖 description 与 tags，"
    echo "  名称、参数与目录归属保留 Apifox 侧手工维护的内容；接口缺失时跳过并提示"
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

# ==================== 数据模型变更检测 ====================

schema_state_file() {
    printf '%s/%s.schemas.sha256' "$SCHEMA_STATE_DIR" "$1"
}

read_schema_state() {
    local state_file
    state_file=$(schema_state_file "$1")
    if [ -f "$state_file" ]; then
        tr -d ' \r\n' <"$state_file"
    fi
}

write_schema_state() {
    local service="$1"
    local digest="$2"
    mkdir -p "$SCHEMA_STATE_DIR" 2>/dev/null || return 1
    printf '%s\n' "$digest" >"$(schema_state_file "$service")"
}

# 对 components.schemas 做规范化序列化后取 sha256：
# 只关心模型本身是否增删改，与产物排版、字段书写顺序、paths 调整无关
schemas_digest() {
    local python_bin="$1"
    local spec_file="$2"
    "$python_bin" -c '
import hashlib
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    document = json.load(handle)

schemas = (document.get("components") or {}).get("schemas") or {}
payload = json.dumps(schemas, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
print(hashlib.sha256(payload.encode("utf-8")).hexdigest())
' "$spec_file"
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

extract_json_string() {
    local json="$1"
    local key="$2"
    printf '%s' "$json" \
        | grep -o "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" \
        | head -n 1 \
        | sed -e 's/^"[^"]*"[[:space:]]*:[[:space:]]*"//' -e 's/"$//'
    return 0
}

# ==================== 责任人填充 ====================

# 用令牌反查当前账号信息，取责任人标识
# 优先「用户账户名」（团队内唯一），缺失时回退「昵称」，两者都是 x-apifox-maintainer 的合法取值
# 这里读的是 Apifox CLI auth whoami 同一个账号接口，只是额外拿到了用户名与昵称
resolve_maintainer() {
    local user_json value
    user_json=$(curl -sS -X GET "$base_url/api/v1/user" \
        -H "Authorization: Bearer $token" \
        -H "X-Apifox-Api-Version: $api_version" \
        --max-time "$REQUEST_TIMEOUT_SECONDS" 2>/dev/null)
    if [ -z "$user_json" ]; then
        return 1
    fi

    value=$(extract_json_string "$user_json" username)
    if [ -z "$value" ]; then
        value=$(extract_json_string "$user_json" name)
    fi
    if [ -z "$value" ]; then
        return 1
    fi

    printf '%s' "$value"
    return 0
}

# 拉取 Apifox 侧已存在的 HTTP 接口清单，输出「method path」行（method 统一小写）
# 责任人只在接口首次创建时需要写入，清单用来把「本轮文档新增的接口」从已存在接口里挑出来
# 不按目录过滤：接口以 method + path 在项目内唯一，落在哪个目录都不该重复注入
collect_existing_endpoints() {
    local python_bin="$1"
    local out_file="$2"
    local list_file="$TMP_DIR/endpoint-list.json"

    if ! apifox endpoint list --project "$project_id" --access-token "$token" >"$list_file" 2>/dev/null; then
        return 1
    fi

    "$python_bin" -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    items = json.load(handle).get("data") or []

with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as handle:
    for item in items:
        method = (item.get("method") or "").strip().lower()
        path = (item.get("path") or "").strip()
        if method and path:
            handle.write(method + " " + path + "\n")
' "$list_file" "$out_file"
}

# 用产物与 Apifox 清单求差集，输出需要补写责任人的 operationId（一行一个）
# 用 operationId 而不是 path 定位注入点，是为了让注入仍走逐行插入、产物原排版保持不变
select_new_maintainer_targets() {
    local python_bin="$1"
    local spec_file="$2"
    local existing_file="$3"
    local out_file="$4"

    "$python_bin" - "$spec_file" "$existing_file" "$out_file" <<'PY'
import json
import sys

HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")

spec_file, existing_file, out_file = sys.argv[1:4]

with open(existing_file, encoding="utf-8") as handle:
    existing = {line.strip() for line in handle if line.strip()}

with open(spec_file, encoding="utf-8") as handle:
    spec = json.load(handle)

targets = []
for path, item in (spec.get("paths") or {}).items():
    if not isinstance(item, dict):
        continue
    for method, operation in item.items():
        if method not in HTTP_METHODS or not isinstance(operation, dict):
            continue
        if method + " " + path in existing:
            continue
        operation_id = operation.get("operationId")
        if operation_id:
            targets.append(operation_id)

with open(out_file, "w", encoding="utf-8", newline="\n") as handle:
    if targets:
        handle.write("\n".join(targets) + "\n")
PY
}

# 全量注入（强制模式或保留扩展行）时的目标集合：产物里所有 operationId，纯文本工具即可提取
select_all_maintainer_targets() {
    local spec_file="$1"
    local out_file="$2"

    grep -o '"operationId"[[:space:]]*:[[:space:]]*"[^"]*"' "$spec_file" 2>/dev/null \
        | sed -e 's/.*"\([^"]*\)"$/\1/' > "$out_file" || true
    return 0
}

# 给需要补责任人的 operation 补写 x-apifox-maintainer，导入后接口责任人即被填充
# 扩展字段挂在 operationId 之后，缩进沿用该行，因此四份产物的排版差异都能正确落地
# targets_file 里是一行一个 operationId，只有列在其中的接口才注入：
# 已存在接口保持原样，避免「多出一行扩展」把接口每轮都判定为已修改
inject_maintainer() {
    local spec_file="$1"
    local name="$2"
    local out_file="$3"
    local targets_file="$4"
    local escaped
    escaped=$(printf '%s' "$name" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')

    awk -v maintainer="$escaped" -v targets="$targets_file" '
        BEGIN {
            if (targets != "") {
                while ((getline line < targets) > 0) {
                    if (line != "") {
                        want[line] = 1
                    }
                }
                close(targets)
            }
        }
        {
            if ($0 ~ /^[[:space:]]*"operationId"[[:space:]]*:[[:space:]]*"[^"]*"[[:space:]]*,?[[:space:]]*$/) {
                id = $0
                sub(/^[[:space:]]*"operationId"[[:space:]]*:[[:space:]]*"/, "", id)
                sub(/"[[:space:]]*,?[[:space:]]*$/, "", id)
                if (!(id in want)) {
                    print
                    next
                }
                indent = $0
                sub(/[^[:space:]].*$/, "", indent)
                line = $0
                sub(/[[:space:]]*$/, "", line)
                if (line ~ /,$/) {
                    print line
                    print indent "\"x-apifox-maintainer\": \"" maintainer "\","
                } else {
                    print line ","
                    print indent "\"x-apifox-maintainer\": \"" maintainer "\""
                }
            } else {
                print
            }
        }
    ' "$spec_file" > "$out_file"
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

# ==================== WebSocket 接口同步 ====================
# OpenAPI 规范表达不了 WebSocket：goctl 产物里的 /ws/chat 会被 fix.py 剔除，
# 同时单独产出 docs/websocket.json。这里用 Apifox CLI 的 websocket 命令按 path 匹配后更新，
# 与 HTTP 接口走的 import-openapi 是两条独立通道，互不影响
# update 不是 JSON Patch，会把传入字段整体提交，所以先 get 完整资源、在完整结构上替换
# description 与 tags 再提交；接口名称、参数、公共参数与目录归属由 Apifox 侧手工维护

resolve_python() {
    if command -v python3 >/dev/null 2>&1; then
        printf '%s' "python3"
        return 0
    fi
    if command -v python >/dev/null 2>&1; then
        printf '%s' "python"
        return 0
    fi
    return 1
}

# 从 websocket list 的结果里按 path 取接口 ID，不存在时输出空串
# WS 路径（如 /ws/chat）不是文件路径，但 Git Bash（MSYS）会把传给原生程序、形如 POSIX 路径的
# 参数与环境变量统一改写成 Windows 路径（/ws/chat -> C:/software/Git/ws/chat），按 path 匹配会
# 永远落空；所以路径改走标准输入（内容不会被改写），参数位只留需要转换的真实文件路径
lookup_websocket_id() {
    local python_bin="$1"
    local list_file="$2"
    local path="$3"
    "$python_bin" -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle).get("data") or []
target_path = sys.stdin.readline().rstrip("\r\n")
match = next((item for item in data if item.get("path") == target_path), None)
print(match["id"] if match else "")
' "$list_file" <<< "$path"
}

# 用产物里的 description / tags 覆盖 get 到的完整资源
# websocket-update 的 additionalProperties 为 false，必须剔除 id / projectId / createdAt
# 这类只读字段，否则结构校验会失败
# 注意：这里的 python 程序本身走标准输入，无法再借道 stdin 传路径，故路径单独落一个文件
# 后按文件路径传参（见 lookup_websocket_id 的同源说明）
merge_websocket_payload() {
    local python_bin="$1"
    local detail_file="$2"
    local spec_file="$3"
    local path_file="$4"
    local output_file="$5"
    "$python_bin" - "$detail_file" "$spec_file" "$path_file" "$output_file" <<'PY'
import json
import sys

detail_file, spec_file, path_file, output_file = sys.argv[1:5]

with open(path_file, encoding="utf-8") as handle:
    target_path = handle.readline().rstrip("\r\n")

# websocket-update schema 允许写入的字段
ALLOWED_FIELDS = (
    "name",
    "path",
    "tags",
    "status",
    "folderId",
    "serverId",
    "requestBody",
    "parameters",
    "commonParameters",
    "description",
    "responsibleId",
    "advancedSettings",
    "moduleId",
)

with open(detail_file, encoding="utf-8") as handle:
    detail = json.load(handle).get("data") or {}

with open(spec_file, encoding="utf-8") as handle:
    endpoints = json.load(handle).get("websockets") or []

endpoint = next((item for item in endpoints if item.get("path") == target_path), None)
if endpoint is None:
    sys.exit(1)

payload = {key: detail[key] for key in ALLOWED_FIELDS if key in detail}
for key in ("description", "tags"):
    if key in endpoint:
        payload[key] = endpoint[key]

with open(output_file, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
}

sync_websocket_endpoints() {
    local service="$1"
    local is_dry_run="$2"

    # 目前只有 GoZero 声明 WebSocket 路由
    if [ "$service" != "gozero" ]; then
        return 0
    fi

    local ws_spec="$WORKDIR/gozero/app/docs/websocket.json"
    if [ ! -f "$ws_spec" ]; then
        return 0
    fi

    if ! command -v apifox >/dev/null 2>&1; then
        print_warn "[$service] 未安装 Apifox CLI，跳过 WebSocket 接口同步（npm install -g apifox-cli）"
        return 0
    fi

    # python_bin 由 main 统一解析（责任人的新增接口差集与这里共用），可能为空
    if [ -z "$python_bin" ]; then
        print_warn "[$service] 未检测到 python，跳过 WebSocket 接口同步"
        return 0
    fi

    local paths
    paths=$("$python_bin" -c '
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    endpoints = json.load(handle).get("websockets") or []
print("\n".join(item["path"] for item in endpoints if item.get("path")))
' "$ws_spec")

    if [ -z "$paths" ]; then
        return 0
    fi

    local list_file="$TMP_DIR/websocket-list.json"
    if ! apifox websocket list --project "$project_id" --access-token "$token" >"$list_file" 2>/dev/null; then
        print_error "[$service] 获取 WebSocket 接口列表失败"
        return 1
    fi

    local path id synced=0 missing=0
    while IFS= read -r path; do
        [ -n "$path" ] || continue

        id=$(lookup_websocket_id "$python_bin" "$list_file" "$path")
        if [ -z "$id" ]; then
            print_warn "[$service] Apifox 中不存在 WebSocket 接口 $path，跳过（首次需在 Apifox 手工创建）"
            missing=$((missing + 1))
            continue
        fi

        if [ "$is_dry_run" = "true" ]; then
            print_info "[$service] dry-run：将用产物覆盖 WebSocket 接口 $path（id=$id）的 description 与 tags"
            synced=$((synced + 1))
            continue
        fi

        local detail_file="$TMP_DIR/websocket-detail.json"
        local payload_file="$TMP_DIR/websocket-payload.json"
        local path_file="$TMP_DIR/websocket-target-path.txt"
        printf '%s\n' "$path" > "$path_file"
        if ! apifox websocket get "$id" --project "$project_id" --access-token "$token" >"$detail_file" 2>/dev/null; then
            print_error "[$service] 获取 WebSocket 接口 $path 详情失败"
            return 1
        fi

        if ! merge_websocket_payload "$python_bin" "$detail_file" "$ws_spec" "$path_file" "$payload_file"; then
            print_error "[$service] 构造 WebSocket 接口 $path 的更新内容失败"
            return 1
        fi

        if ! apifox cli-schema validate websocket-update --file "$payload_file" >/dev/null 2>&1; then
            print_error "[$service] WebSocket 接口 $path 的更新内容未通过 Apifox 结构校验"
            return 1
        fi

        if ! apifox websocket update "$id" --project "$project_id" --access-token "$token" --file "$payload_file" >/dev/null 2>&1; then
            print_error "[$service] 更新 WebSocket 接口 $path 失败"
            return 1
        fi

        synced=$((synced + 1))
    done <<< "$paths"

    print_info "[$service] WebSocket 接口：更新 $synced，缺失跳过 $missing（仅同步 description 与 tags）"
    return 0
}

# ==================== 主流程 ====================

main() {
    local dry_run="false"
    local readme_enabled="true"
    local maintainer_enabled="true"
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
            --no-maintainer)
                maintainer_enabled="false"
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

    # 显式配置的覆盖策略优先：用户一旦直接指定，本轮就不再按数据模型指纹自动切换
    local endpoint_behavior_explicit="false"
    local schema_behavior_explicit="false"
    if [ -n "$(env_value APIFOX_ENDPOINT_OVERWRITE_BEHAVIOR "")" ]; then
        endpoint_behavior_explicit="true"
    fi
    if [ -n "$(env_value APIFOX_SCHEMA_OVERWRITE_BEHAVIOR "")" ]; then
        schema_behavior_explicit="true"
    fi
    local resolved_endpoint_behavior="$endpoint_behavior"
    local resolved_schema_behavior="$schema_behavior"

    delete_unmatched=$(env_flag APIFOX_DELETE_UNMATCHED_RESOURCES "$DEFAULT_DELETE_UNMATCHED_RESOURCES")
    update_folder_of_changed=$(env_flag APIFOX_UPDATE_FOLDER_OF_CHANGED_ENDPOINT "true")

    print_info "Apifox 项目: $project_id（$base_url）"
    if [ "$delete_unmatched" = "true" ]; then
        print_info "对齐全量模式：以文档为准，清理目标目录下未匹配的接口与数据模型（置 APIFOX_DELETE_UNMATCHED_RESOURCES=false 可关闭）"
    else
        print_info "增量模式：保留 Apifox 中多出的接口与数据模型（置 APIFOX_DELETE_UNMATCHED_RESOURCES=true 可开启全量对齐）"
    fi
    if [ "$dry_run" = "true" ]; then
        print_info "dry-run 模式：只校验产物与配置，不发起导入请求"
    fi

    # 责任人：显式配置优先，未配置且开启自动解析时取令牌账号的用户名
    local maintainer=""
    if [ "$maintainer_enabled" = "true" ]; then
        maintainer=$(env_value APIFOX_MAINTAINER "")
        if [ -n "$maintainer" ]; then
            print_info "责任人：$maintainer（来自 APIFOX_MAINTAINER）"
        elif [ "$(env_flag APIFOX_MAINTAINER_AUTO "$DEFAULT_MAINTAINER_AUTO")" = "true" ]; then
            maintainer=$(resolve_maintainer || true)
            if [ -n "$maintainer" ]; then
                print_info "责任人：$maintainer（取自令牌账号）"
            else
                print_warn "未能从令牌账号解析出责任人，接口将不带责任人；可用 APIFOX_MAINTAINER 显式指定"
            fi
        fi
    fi

    clean_extension=$(env_flag APIFOX_MAINTAINER_CLEAN_EXTENSION "$DEFAULT_MAINTAINER_CLEAN_EXTENSION")
    maintainer_force=$(env_flag APIFOX_MAINTAINER_FORCE "$DEFAULT_MAINTAINER_FORCE")

    # WebSocket 接口同步与「责任人只补新增接口」的差集都要用 Python，这里统一解析一次
    local python_bin=""
    python_bin=$(resolve_python || true)

    TMP_DIR=$(mktemp -d 2>/dev/null)
    if [ -z "$TMP_DIR" ] || [ ! -d "$TMP_DIR" ]; then
        print_error "无法创建临时目录，请检查系统 mktemp 是否可用"
        return 1
    fi

    # 责任人只在接口首次创建时需要写入：重复给已存在接口注入扩展会让全部接口每轮被判定为已修改
    # 所以先拉一次 Apifox 现有接口清单，注入时只保留文档里新增的接口（拉不到就退回全量注入）
    local existing_endpoints_file=""
    if [ -n "$maintainer" ] && [ "$maintainer_force" != "true" ] && [ "$clean_extension" = "true" ]; then
        if [ -z "$python_bin" ]; then
            print_warn "未检测到 python，无法比对 Apifox 接口清单，回退为全量重写责任人（接口会被判定为已修改）"
        else
            existing_endpoints_file="$TMP_DIR/endpoint-list.txt"
            if collect_existing_endpoints "$python_bin" "$existing_endpoints_file"; then
                print_info "责任人增量补写：Apifox 现有接口 $(wc -l < "$existing_endpoints_file" | tr -d ' ') 个，只为本轮新增接口写入"
            else
                existing_endpoints_file=""
                print_warn "获取 Apifox 接口清单失败，回退为全量重写责任人（接口会被判定为已修改）"
            fi
        fi
    fi

    local services="${service_args:-$ALL_SERVICES}"
    local failed_services=""
    local schema_state_updated="false"
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

        # 数据模型变更检测：AUTO_MERGE 不重写已存在接口的响应绑定，而全量对齐会清理文档里
        # 已不存在的模型；模型一旦重建或删除，接口上残留的 $ref 就指向不存在的 Apifox 内部
        # 模型 ID，表现为「校验响应」报 can't resolve reference。因此指纹变化时本轮改用
        # OVERWRITE_EXISTING 把绑定整体重写一次，指纹未变则继续走默认的 AUTO_MERGE
        local current_digest=""
        local previous_digest=""
        local models_changed="false"
        if [ -n "$python_bin" ]; then
            current_digest=$(schemas_digest "$python_bin" "$spec_file" 2>/dev/null || true)
        fi
        if [ -n "$current_digest" ]; then
            previous_digest=$(read_schema_state "$service")
            if [ "$current_digest" != "$previous_digest" ]; then
                models_changed="true"
            fi
        fi

        endpoint_behavior="$resolved_endpoint_behavior"
        schema_behavior="$resolved_schema_behavior"
        if [ "$models_changed" = "true" ]; then
            if [ "$endpoint_behavior_explicit" = "false" ]; then
                endpoint_behavior="OVERWRITE_EXISTING"
            fi
            if [ "$schema_behavior_explicit" = "false" ]; then
                schema_behavior="OVERWRITE_EXISTING"
            fi
            if [ -z "$previous_digest" ]; then
                print_info "[$service] 数据模型无历史指纹，本轮按覆盖模式同步以避免残留引用断链"
            else
                print_info "[$service] 检测到数据模型变更，本轮按覆盖模式同步以避免残留引用断链"
            fi
        fi

        options_json=$(build_options_json "$service")

        # 有责任人时先生成一份带 x-apifox-maintainer 的副本，导入用它，仓库产物保持不动
        # 默认只给「Apifox 里还不存在」的接口注入：已存在接口重复注入扩展会让接口每轮被判定为已修改
        local import_spec="$spec_file"
        local injected_spec="false"
        if [ -n "$maintainer" ]; then
            local targets_file="$TMP_DIR/$service-maintainer-targets.txt"
            if [ -n "$existing_endpoints_file" ]; then
                if ! select_new_maintainer_targets "$python_bin" "$spec_file" "$existing_endpoints_file" "$targets_file"; then
                    print_warn "[$service] 计算责任人待补写接口失败，回退为全量重写责任人（接口会被判定为已修改）"
                    select_all_maintainer_targets "$spec_file" "$targets_file"
                fi
            else
                select_all_maintainer_targets "$spec_file" "$targets_file"
            fi

            local target_count
            target_count=$(grep -c . "$targets_file" 2>/dev/null)
            target_count=${target_count:-0}

            if [ "$target_count" = "0" ]; then
                print_info "[$service] 责任人已覆盖，跳过注入与扩展清理"
            else
                import_spec="$TMP_DIR/$service-spec.json"
                inject_maintainer "$spec_file" "$maintainer" "$import_spec" "$targets_file"
                injected_spec="true"
                local injected
                injected=$(grep -c '"x-apifox-maintainer"[[:space:]]*:' "$import_spec" 2>/dev/null)
                injected=${injected:-0}
                if [ "$injected" != "$target_count" ]; then
                    print_warn "[$service] 责任人注入数（$injected）与待补写接口数（$target_count）不一致，部分接口可能未带上责任人"
                fi
                print_info "[$service] 责任人：为 $target_count 个新增接口补写 x-apifox-maintainer"
            fi
        fi

        # WebSocket 接口无法用 OpenAPI 表达，走 Apifox CLI 的 websocket 命令单独同步
        if ! sync_websocket_endpoints "$service" "$dry_run"; then
            failed_services="$failed_services $service(websocket)"
        fi

        if [ "$dry_run" = "true" ]; then
            print_info "[$service] 文档 $(wc -c < "$spec_file" | tr -d ' ') 字节，导入选项 $options_json${maintainer:+，责任人 $maintainer}"
            continue
        fi

        payload_file="$TMP_DIR/$service-payload.json"
        response_file="$TMP_DIR/$service-response.json"
        curl_err_file="$TMP_DIR/$service-curl.err"
        build_payload_file "$import_spec" "$options_json" "$payload_file"

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
            continue
        fi

        # Apifox 解析责任人后仍会把扩展原样留在接口的 oasExtensions 里，文档页会多渲染一行
        # 用不带扩展的原文档再导入一次即可清掉，责任人字段已经落库不受影响
        if [ "$injected_spec" = "true" ] && [ "$clean_extension" = "true" ]; then
            payload_file="$TMP_DIR/$service-payload-clean.json"
            build_payload_file "$spec_file" "$options_json" "$payload_file"
            if post_import_openapi "$url" "$payload_file" "$response_file" "$curl_err_file"; then
                print_info "[$service] 已清理接口文档残留的 x-apifox-maintainer 扩展行"
            else
                print_warn "[$service] 扩展残留清理失败，接口文档可能多出一行 x-apifox-maintainer"
            fi
        fi

        # 只有导入成功才记录指纹：失败时保留旧指纹，下次同步仍会按覆盖模式重试
        if [ -n "$current_digest" ]; then
            if write_schema_state "$service" "$current_digest"; then
                schema_state_updated="true"
            else
                print_warn "[$service] 数据模型指纹写入失败，下次同步会再次按覆盖模式执行"
            fi
        fi
    done

    # 基线是共享的：只有提交之后其他机器才能据此判断「模型没变、无需覆盖」
    if [ "$schema_state_updated" = "true" ]; then
        echo ""
        print_info "数据模型同步基线已更新，请与 docs/ 产物一起提交 .apifox-state/"
        print_info "（其他机器靠它判断模型是否变更，漏提交会让它们误判为模型有变并触发覆盖同步）"
    fi

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
