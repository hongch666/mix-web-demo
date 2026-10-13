#!/bin/bash

# 脚本说明：
# 生成一枚内部服务令牌（INTERNAL_TOKEN_SECRET 签发的 HS256 JWT），并写入 Apifox 变量后打印出来
# 四个服务的内部接口只校验 X-Internal-Token 的签名与有效期，密钥在各自 .env 中且取值一致，
# 所以一枚令牌对四个服务通用（serviceName 只是 claims 里的标记，当前没有任何接口校验它）
# 因此默认随机挑一个服务签发，需要时用位置参数或 --service 指定服务
# 单枚令牌的签发逻辑在 scripts/internal-token.py（只依赖 Python 标准库）
#
# 用法：./scripts/internal-token.sh [service] [options]
#   service                   可选，spring、gozero、nestjs、fastapi；不传时随机挑一个
#   --service NAME            与位置参数等价
#   --user-id N               令牌里的 userId，-1 表示系统调用（默认 -1）
#   --ttl 24h                 有效期，支持 30s / 5m / 2h / 7d 或纯秒数（默认 24h）
#   --secret VALUE            直接指定签名密钥，优先于 .env 与环境变量
#   --env-file PATH           指定读取 INTERNAL_TOKEN_SECRET 的 .env 文件
#   --header                  只输出一行 X-Internal-Token 请求头
#   --json                    以 JSON 输出令牌与 Apifox 写入结果
#   --quiet                   只输出裸令牌
#   --no-apifox               不写 Apifox 变量
#   --variable-name NAME      写入的 Apifox 变量名（默认 internal_token）
#   --variable-scope SCOPE    global（默认，写项目全局变量）或 environment（写指定环境的环境变量）
#   --apifox-env NAME|ID      scope=environment 时的目标环境，默认取根目录 .env 的 APIFOX_ENVIRONMENT_NAME，否则「单服务环境」
#   --dry-run                 只预览将写入 Apifox 的内容，不实际写入
#
# Apifox 侧用法：环境管理的「全局参数」里配 X-Internal-Token = Bearer {{internal_token}}，
# 本脚本负责把 internal_token 刷新成新令牌；值本身不含 Bearer 前缀，前缀写在全局参数里
# 请求头格式：X-Internal-Token: Bearer <token>，四个服务都会剥掉 Bearer 前缀再校验
# 返回码约定：0 表示成功；1 表示参数或签发失败、或 Apifox 已配置但写入失败；2 表示未找到可用的 Python 解释器

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ALL_SERVICES=(spring gozero nestjs fastapi)
DEFAULT_VARIABLE_NAME="internal_token"
DEFAULT_ENVIRONMENT_NAME="单服务环境"

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
    echo "用法: ./scripts/internal-token.sh [service] [options]"
    echo "  service                   可选，spring、gozero、nestjs、fastapi；不传时随机挑一个"
    echo "  --service NAME            与位置参数等价"
    echo "  --user-id N               令牌里的 userId，-1 表示系统调用（默认 -1）"
    echo "  --ttl 24h                 有效期，支持 30s / 5m / 2h / 7d 或纯秒数（默认 24h）"
    echo "  --secret VALUE            直接指定签名密钥，优先于 .env 与环境变量"
    echo "  --env-file PATH           指定读取 INTERNAL_TOKEN_SECRET 的 .env 文件"
    echo "  --header                  只输出一行 X-Internal-Token 请求头"
    echo "  --json                    以 JSON 输出令牌与 Apifox 写入结果"
    echo "  --quiet                   只输出裸令牌"
    echo "  --no-apifox               不写 Apifox 变量"
    echo "  --variable-name NAME      写入的 Apifox 变量名（默认 $DEFAULT_VARIABLE_NAME）"
    echo "  --variable-scope SCOPE    global（默认）或 environment"
    echo "  --apifox-env NAME|ID      scope=environment 时的目标环境"
    echo "  --dry-run                 只预览将写入 Apifox 的内容"
}

# ==================== 参数解析 ====================

SERVICE=""
USER_ID="-1"
TTL="24h"
SECRET=""
ENV_FILE=""
OUTPUT_MODE="table"
APIFOX_ENABLED="true"
APIFOX_ENV=""
VARIABLE_NAME="$DEFAULT_VARIABLE_NAME"
VARIABLE_SCOPE="global"
DRY_RUN="false"

while [ $# -gt 0 ]; do
    case "$1" in
        --service) SERVICE="$2"; shift 2 ;;
        --service=*) SERVICE="${1#*=}"; shift ;;
        --user-id) USER_ID="$2"; shift 2 ;;
        --user-id=*) USER_ID="${1#*=}"; shift ;;
        --ttl) TTL="$2"; shift 2 ;;
        --ttl=*) TTL="${1#*=}"; shift ;;
        --secret) SECRET="$2"; shift 2 ;;
        --secret=*) SECRET="${1#*=}"; shift ;;
        --env-file) ENV_FILE="$2"; shift 2 ;;
        --env-file=*) ENV_FILE="${1#*=}"; shift ;;
        --header) OUTPUT_MODE="header"; shift ;;
        --json) OUTPUT_MODE="json"; shift ;;
        --quiet) OUTPUT_MODE="quiet"; shift ;;
        --no-apifox) APIFOX_ENABLED="false"; shift ;;
        --variable-name) VARIABLE_NAME="$2"; shift 2 ;;
        --variable-name=*) VARIABLE_NAME="${1#*=}"; shift ;;
        --variable-scope) VARIABLE_SCOPE="$2"; shift 2 ;;
        --variable-scope=*) VARIABLE_SCOPE="${1#*=}"; shift ;;
        --apifox-env) APIFOX_ENV="$2"; shift 2 ;;
        --apifox-env=*) APIFOX_ENV="${1#*=}"; shift ;;
        --dry-run) DRY_RUN="true"; shift ;;
        -h|--help) show_usage; exit 0 ;;
        -*) print_error "未知参数: $1"; show_usage; exit 1 ;;
        *)
            if [ -n "$SERVICE" ]; then
                print_error "一次只能指定一个服务，当前还多出了: $1"
                exit 1
            fi
            SERVICE="$1"
            shift
            ;;
    esac
done

case "$USER_ID" in
    ''|*[!0-9-]*)
        print_error "userId 需要是整数，当前填的是: $USER_ID"
        exit 1
        ;;
esac

case "$VARIABLE_SCOPE" in
    global|environment) ;;
    *)
        print_error "variable-scope 只能是 global 或 environment，当前填的是: $VARIABLE_SCOPE"
        exit 1
        ;;
esac

# 不指定服务时随机挑一个：令牌四服务通用，服务名只体现在 claims 里，便于排查来源
RANDOM_PICKED="false"
if [ -z "$SERVICE" ]; then
    SERVICE="${ALL_SERVICES[$((RANDOM % ${#ALL_SERVICES[@]}))]}"
    RANDOM_PICKED="true"
fi

case "$SERVICE" in
    spring|gozero|nestjs|fastapi) ;;
    *)
        print_error "未知服务: $SERVICE"
        echo "可选服务: ${ALL_SERVICES[*]}"
        exit 1
        ;;
esac

# ==================== 环境准备 ====================

resolve_python() {
    local candidate
    for candidate in python3 python py; do
        if command -v "$candidate" >/dev/null 2>&1; then
            printf '%s' "$candidate"
            return 0
        fi
    done
    for candidate in "$WORKDIR/fastapi/.venv/bin/python" "$WORKDIR/fastapi/.venv/Scripts/python.exe"; do
        if [ -x "$candidate" ]; then
            printf '%s' "$candidate"
            return 0
        fi
    done
    return 1
}

if ! PYTHON_BIN=$(resolve_python); then
    print_error "未找到可用的 Python 解释器，无法生成内部服务令牌"
    echo "请安装 Python 3，或先执行 ./mix setup 生成 fastapi/.venv"
    exit 2
fi

TMP_DIR=$(mktemp -d)
cleanup() {
    [ -n "$TMP_DIR" ] && rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# 输出模式为 json / quiet 时，说明性文字走 stderr，stdout 只留机器可读内容
note() {
    case "$OUTPUT_MODE" in
        json|quiet) echo "$1" >&2 ;;
        *) echo "$1" ;;
    esac
}

# 从根目录 .env 读取 Apifox 配置，调用方显式传入的 APIFOX_* 变量优先
load_env() {
    if [ ! -f "$WORKDIR/.env" ]; then
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
}

env_value() {
    local name="$1"
    local default_value="$2"
    local value
    value="${!name}"
    if [ -z "$value" ]; then
        printf '%s' "$default_value"
    else
        printf '%s' "$value"
    fi
}

# ==================== 令牌签发 ====================

TOKEN=""
EXPIRES_AT=""
EXPIRES_IN=""
SECRET_SOURCE=""

generate_token() {
    local args=(--service-name "$SERVICE" --user-id "$USER_ID" --ttl "$TTL" --json --quiet)

    if [ -n "$SECRET" ]; then
        args+=(--secret "$SECRET")
    fi
    if [ -n "$ENV_FILE" ]; then
        args+=(--env-file "$ENV_FILE")
    fi

    "$PYTHON_BIN" "$WORKDIR/scripts/internal-token.py" "${args[@]}" 2>/dev/null |
        "$PYTHON_BIN" -c '
import json
import sys

data = json.loads(sys.stdin.read())
print("\t".join([
    data["token"],
    data["expiresAt"],
    str(data["expiresIn"]),
    data.get("secretSource", ""),
]))
'
}

if ! REPORT=$(generate_token); then
    print_error "生成内部令牌失败"
    exit 1
fi

if [ -z "$REPORT" ]; then
    print_error "生成内部令牌失败，请确认 .env 中已配置 INTERNAL_TOKEN_SECRET"
    exit 1
fi

IFS=$'\t' read -r TOKEN EXPIRES_AT EXPIRES_IN SECRET_SOURCE <<< "$REPORT"
HEADER_LINE="X-Internal-Token: Bearer $TOKEN"

# ==================== 控制台输出 ====================

print_token() {
    case "$OUTPUT_MODE" in
        quiet)
            printf '%s\n' "$TOKEN"
            ;;
        json)
            # json 模式在 Apifox 写入完成后统一输出
            ;;
        header)
            note "[INFO] 服务=$SERVICE 有效期至 $EXPIRES_AT（userId=$USER_ID，密钥来源：$SECRET_SOURCE）"
            note "$HEADER_LINE"
            ;;
        *)
            if [ "$RANDOM_PICKED" = "true" ]; then
                note "[INFO] 未指定服务，随机选用 $SERVICE（令牌对四个服务通用，serviceName 只用于排查来源）"
            fi
            note "[INFO] 已生成内部令牌：service=$SERVICE userId=$USER_ID 有效期至 $EXPIRES_AT（密钥来源：$SECRET_SOURCE）"
            note ""
            note "$HEADER_LINE"
            note ""
            ;;
    esac
}

# ==================== Apifox 写入 ====================

APIFOX_RESULT="skipped"
APIFOX_DETAIL=""

# 在 environment list 的结果里解析目标环境，输出 "id<TAB>名称"
resolve_environment() {
    "$PYTHON_BIN" - "$1" "$APIFOX_ENV" "$(env_value APIFOX_ENVIRONMENT_NAME '')" "$DEFAULT_ENVIRONMENT_NAME" <<'PY'
import json
import sys

list_file, requested, configured, default_name = sys.argv[1:5]

with open(list_file, encoding="utf-8") as handle:
    environments = json.load(handle).get("data") or []


def emit(item):
    print("{}\t{}".format(item.get("id", ""), item.get("name", "")))


def find_by_name(name):
    return next((item for item in environments if item.get("name") == name), None)


if requested:
    if requested.isdigit():
        match = next(
            (item for item in environments if str(item.get("id")) == requested), None
        )
        emit(match if match else {"id": requested, "name": requested})
    else:
        match = find_by_name(requested)
        if match:
            emit(match)
else:
    for name in (configured, default_name):
        if name:
            match = find_by_name(name)
            if match:
                emit(match)
                sys.exit(0)
    if environments:
        emit(environments[0])
PY
}

# 读取环境已有的变量
# environment get / list 都不返回 variables 字段（服务端只在该通道给基础字段），
# 只有 Apifox 格式的项目导出里带 variables，所以这里用 export 回读，避免 update 覆盖掉手工维护的变量
fetch_existing_variables() {
    local project_id="$1"
    local token="$2"
    local env_id="$3"
    local output_file="$4"
    local export_file="$TMP_DIR/apifox-export.json"

    if ! apifox export --project "$project_id" --format apifox --scope all --no-include-api-cases \
        --environment-ids "$env_id" --output "$export_file" --access-token "$token" >/dev/null 2>&1; then
        return 1
    fi

    "$PYTHON_BIN" - "$export_file" "$env_id" "$output_file" <<'PY'
import json
import sys

export_file, environment_id, output_file = sys.argv[1:4]

with open(export_file, encoding="utf-8") as handle:
    exported = json.load(handle)

target = next(
    (
        environment
        for environment in exported.get("environments") or []
        if str(environment.get("id")) == str(environment_id)
    ),
    None,
)

with open(output_file, "w", encoding="utf-8", newline="\n") as handle:
    json.dump((target or {}).get("variables") or [], handle, ensure_ascii=False)
PY
}

# 在完整环境结构上合并变量，再产出 update 用的 payload
# update 不是 JSON Patch，会把传入字段整体提交，所以必须先取到完整结构再改
merge_environment_payload() {
    "$PYTHON_BIN" - "$1" "$2" "$3" "$4" "$5" <<'PY'
import json
import sys

detail_file, existing_file, name, value, output_file = sys.argv[1:6]

# environment-update schema 允许写入的字段，id / projectId 这类只读字段必须剔除
ALLOWED_FIELDS = (
    "name",
    "baseUrl",
    "baseUrls",
    "websocketBaseUrls",
    "socketioBaseUrls",
    "parameters",
    "type",
    "visibility",
    "variables",
    "ordering",
    "tags",
    "registrationCenters",
    "servers",
    "advancedSettings",
)

with open(detail_file, encoding="utf-8") as handle:
    environment = json.load(handle).get("data") or {}

with open(existing_file, encoding="utf-8") as handle:
    variables = [item for item in (json.load(handle) or []) if isinstance(item, dict)]

positions = {}
for index, item in enumerate(variables):
    item_name = item.get("name") or item.get("key")
    if item_name:
        positions[item_name] = index

# initialValue 对应 Apifox 的远程值、value 对应本地值，请求运行时读本地值，
# isBindInitial 让本地值跟随远程值，团队共享时两边都拿到令牌
entry = {
    "name": name,
    "value": value,
    "type": "string",
    "enabled": True,
    "initialValue": value,
    "isBindInitial": True,
}
if name in positions:
    variables[positions[name]].update(entry)
else:
    variables.append(entry)

payload = {key: environment[key] for key in ALLOWED_FIELDS if key in environment}
payload["variables"] = variables

with open(output_file, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

print("环境变量 {} 个".format(len(variables)))
PY
}

# ==================== Apifox 变量写入 ====================

# 写项目全局变量（环境管理 → 全局变量 → 项目内共享）
set_global_variable() {
    local project_id="$1"
    local token="$2"

    if ! apifox variables set --project "$project_id" --scope global \
        --key "$VARIABLE_NAME" --value "$TOKEN" --access-token "$token" >/dev/null 2>&1; then
        APIFOX_RESULT="failed"
        APIFOX_DETAIL="写入 Apifox 全局变量 $VARIABLE_NAME 失败"
        print_error "$APIFOX_DETAIL"
        return 1
    fi

    # 回读校验，避免写了个空值还以为成功
    local detail_file="$TMP_DIR/global-variable.json"
    if apifox variables get --project "$project_id" --scope global \
        --key "$VARIABLE_NAME" --access-token "$token" >"$detail_file" 2>/dev/null; then
        if ! "$PYTHON_BIN" - "$detail_file" "$TOKEN" <<'PY'
import json
import sys

detail_file, expected = sys.argv[1:3]

with open(detail_file, encoding="utf-8") as handle:
    data = json.load(handle).get("data") or {}

sys.exit(0 if data.get("value") == expected else 1)
PY
        then
            print_warn "全局变量 $VARIABLE_NAME 回读值与本枚令牌不一致，请到 Apifox 里确认"
        fi
    fi

    APIFOX_RESULT="ok"
    APIFOX_DETAIL="全局变量 $VARIABLE_NAME"
    note "[INFO] 已写入 Apifox 全局变量「$VARIABLE_NAME」（全局参数里写 X-Internal-Token = Bearer {{$VARIABLE_NAME}} 即可）"
    return 0
}

# 写指定环境的环境变量（供 --variable-scope environment 使用）
set_environment_variable() {
    local project_id="$1"
    local token="$2"

    local list_file="$TMP_DIR/environments.json"
    if ! apifox environment list --project "$project_id" --access-token "$token" >"$list_file" 2>/dev/null; then
        APIFOX_RESULT="failed"
        APIFOX_DETAIL="获取 Apifox 环境列表失败"
        print_error "$APIFOX_DETAIL"
        return 1
    fi

    local target env_id env_name
    target=$(resolve_environment "$list_file")
    if [ -z "$target" ]; then
        APIFOX_RESULT="failed"
        APIFOX_DETAIL="Apifox 中找不到环境：${APIFOX_ENV:-$DEFAULT_ENVIRONMENT_NAME}"
        print_error "$APIFOX_DETAIL"
        return 1
    fi
    IFS=$'\t' read -r env_id env_name <<< "$target"

    local detail_file="$TMP_DIR/environment-detail.json"
    if ! apifox environment get "$env_id" --project "$project_id" --access-token "$token" >"$detail_file" 2>/dev/null; then
        APIFOX_RESULT="failed"
        APIFOX_DETAIL="获取环境「$env_name」详情失败"
        print_error "$APIFOX_DETAIL"
        return 1
    fi

    local existing_file="$TMP_DIR/environment-variables.json"
    if ! fetch_existing_variables "$project_id" "$token" "$env_id" "$existing_file"; then
        APIFOX_RESULT="failed"
        APIFOX_DETAIL="导出环境「$env_name」已有变量失败，已中止写入以免覆盖手工维护的变量"
        print_error "$APIFOX_DETAIL"
        return 1
    fi

    local payload_file="$TMP_DIR/environment-payload.json"
    local merge_summary
    if ! merge_summary=$(merge_environment_payload "$detail_file" "$existing_file" \
        "$VARIABLE_NAME" "$TOKEN" "$payload_file"); then
        APIFOX_RESULT="failed"
        APIFOX_DETAIL="构造环境变量更新内容失败"
        print_error "$APIFOX_DETAIL"
        return 1
    fi

    if [ "$DRY_RUN" = "true" ]; then
        APIFOX_RESULT="dry-run"
        APIFOX_DETAIL="环境「$env_name」变量 $VARIABLE_NAME"
        note "[INFO] dry-run：将向 Apifox 环境「$env_name」写入变量 $VARIABLE_NAME（$merge_summary）"
        return 0
    fi

    if ! apifox cli-schema validate environment-update --file "$payload_file" >/dev/null 2>&1; then
        APIFOX_RESULT="failed"
        APIFOX_DETAIL="环境变量更新内容未通过 Apifox 结构校验"
        print_error "$APIFOX_DETAIL"
        return 1
    fi

    if ! apifox environment update "$env_id" --project "$project_id" --access-token "$token" --file "$payload_file" >/dev/null 2>&1; then
        APIFOX_RESULT="failed"
        APIFOX_DETAIL="写入 Apifox 环境「$env_name」失败"
        print_error "$APIFOX_DETAIL"
        return 1
    fi

    APIFOX_RESULT="ok"
    APIFOX_DETAIL="环境「$env_name」变量 $VARIABLE_NAME"
    note "[INFO] 已写入 Apifox 环境「$env_name」的变量 $VARIABLE_NAME（$merge_summary）"
    return 0
}

sync_apifox() {
    if [ "$APIFOX_ENABLED" != "true" ]; then
        APIFOX_DETAIL="已通过 --no-apifox 关闭"
        return 0
    fi

    load_env

    local token project_id
    token=$(env_value APIFOX_ACCESS_TOKEN "")
    project_id=$(env_value APIFOX_PROJECT_ID "")
    if [ -z "$token" ] || [ -z "$project_id" ]; then
        APIFOX_DETAIL="根目录 .env 缺少 APIFOX_ACCESS_TOKEN 或 APIFOX_PROJECT_ID"
        print_warn "跳过 Apifox 写入：$APIFOX_DETAIL"
        return 0
    fi

    if ! command -v apifox >/dev/null 2>&1; then
        APIFOX_DETAIL="未安装 Apifox CLI（npm install -g apifox-cli）"
        print_warn "跳过 Apifox 写入：$APIFOX_DETAIL"
        return 0
    fi

    if [ "$DRY_RUN" = "true" ] && [ "$VARIABLE_SCOPE" = "global" ]; then
        APIFOX_RESULT="dry-run"
        APIFOX_DETAIL="全局变量 $VARIABLE_NAME"
        note "[INFO] dry-run：将把令牌写入 Apifox 全局变量「$VARIABLE_NAME」（项目 ID $project_id）"
        return 0
    fi

    if [ "$VARIABLE_SCOPE" = "global" ]; then
        set_global_variable "$project_id" "$token" || return 1
    else
        set_environment_variable "$project_id" "$token" || return 1
    fi

    return 0
}

print_token

APIFOX_STATUS=0
sync_apifox || APIFOX_STATUS=$?

# ==================== JSON 输出 ====================

if [ "$OUTPUT_MODE" = "json" ]; then
    MIX_APIFOX_RESULT="$APIFOX_RESULT" MIX_APIFOX_DETAIL="$APIFOX_DETAIL" \
        MIX_VARIABLE_NAME="$VARIABLE_NAME" MIX_VARIABLE_SCOPE="$VARIABLE_SCOPE" \
        "$PYTHON_BIN" - "$TOKEN" "$SERVICE" "$USER_ID" "$SECRET_SOURCE" "$EXPIRES_AT" "$EXPIRES_IN" "$RANDOM_PICKED" <<'PY'
import json
import os
import sys

token, service, user_id, secret_source, expires_at, expires_in, random_picked = sys.argv[1:8]

print(
    json.dumps(
        {
            "service": service,
            "randomService": random_picked == "true",
            "userId": int(user_id),
            "token": token,
            "header": "X-Internal-Token: Bearer " + token,
            "expiresAt": expires_at,
            "expiresIn": int(expires_in),
            "secretSource": secret_source,
            "apifox": {
                "result": os.environ.get("MIX_APIFOX_RESULT", "skipped"),
                "detail": os.environ.get("MIX_APIFOX_DETAIL", ""),
                "variableName": os.environ.get("MIX_VARIABLE_NAME", ""),
                "variableScope": os.environ.get("MIX_VARIABLE_SCOPE", ""),
            },
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY
fi

exit "$APIFOX_STATUS"
