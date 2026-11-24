#!/bin/bash

# 脚本说明：
# 只读检测静态 OpenAPI 产物是否与当前代码一致，用于发现「改了接口但没重新生成文档」的情况
# 原理：备份现有产物 -> 调用 swag-init.sh 重新生成 -> 逐文件比对 -> 恢复备份，执行完不修改仓库
# 用法：./scripts/docs/swag-check.sh [service...]
#   service 可选值：spring、gozero、nestjs、fastapi，不指定时检测全部
# 返回码：0 产物一致；1 产物未同步；2 工具缺失或重新生成失败（无法完成检测）

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="$(mktemp -d)"
BACKUP_DIR="$TMP_DIR/backup"
MANIFEST="$TMP_DIR/manifest"
mkdir -p "$BACKUP_DIR"
: > "$MANIFEST"

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

# 每个服务需要检测的产物；网关黑名单 scripts/generated/gateway-blocklist.json 是每次从
# apisix.yaml 抽取的中间输入（被 .gitignore 忽略、不提交），不属于校验产物，不在此列
artifacts_for() {
    case "$1" in
        spring)
            echo "spring/docs/openapi.json"
            echo "spring/docs/openapi.yaml"
            ;;
        gozero)
            echo "gozero/app/docs/openapi.json"
            echo "gozero/app/docs/openapi.yaml"
            echo "gozero/app/docs/websocket.json"
            ;;
        nestjs)
            echo "nestjs/docs/openapi.json"
            echo "nestjs/docs/openapi.yaml"
            ;;
        fastapi)
            echo "fastapi/docs/openapi.json"
            echo "fastapi/docs/openapi.yaml"
            ;;
    esac
}

if [ $# -gt 0 ]; then
    SERVICES="$*"
else
    SERVICES="spring gozero nestjs fastapi"
fi

# 校验服务名并收集产物路径，去重后写入待检测清单
ARTIFACT_LIST="$TMP_DIR/artifacts"
: > "$ARTIFACT_LIST"
for SERVICE in $SERVICES; do
    case "$SERVICE" in
        spring|gozero|nestjs|fastapi) ;;
        gateway)
            print_warn "gateway 无 OpenAPI 产物，已跳过"
            continue
            ;;
        *)
            print_error "未知服务: $SERVICE（可选 spring、gozero、nestjs、fastapi）"
            exit 2
            ;;
    esac
    artifacts_for "$SERVICE" >> "$ARTIFACT_LIST"
done
sort -u "$ARTIFACT_LIST" -o "$ARTIFACT_LIST"

# 备份：记录每个产物是否存在，存在则复制到临时目录
while IFS= read -r REL; do
    [ -z "$REL" ] && continue
    SRC="$WORKDIR/$REL"
    DST="$BACKUP_DIR/$REL"
    if [ -f "$SRC" ]; then
        mkdir -p "$(dirname "$DST")"
        cp "$SRC" "$DST"
        echo "1|$REL" >> "$MANIFEST"
    else
        echo "0|$REL" >> "$MANIFEST"
    fi
done < "$ARTIFACT_LIST"

# 恢复：无论成功失败都把工作区产物还原到检测前的状态
restore_artifacts() {
    [ -f "$MANIFEST" ] || return 0
    while IFS='|' read -r STATUS REL; do
        [ -z "$REL" ] && continue
        CURRENT="$WORKDIR/$REL"
        if [ "$STATUS" = "1" ]; then
            mkdir -p "$(dirname "$CURRENT")"
            cp "$BACKUP_DIR/$REL" "$CURRENT"
        else
            rm -f "$CURRENT"
        fi
    done < "$MANIFEST"
}
trap 'restore_artifacts; rm -rf "$TMP_DIR"' EXIT

# 重新生成：swag-init.sh 返回 2 表示工具缺失跳过，此时无法判定一致性，CI 应视为失败
print_info "重新生成 OpenAPI 产物以进行一致性比对..."
bash "$WORKDIR/scripts/docs/swag-init.sh" $SERVICES
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
    print_error "重新生成失败或有服务因工具缺失被跳过（返回码 $STATUS），无法完成一致性检测"
    exit 2
fi

# Python 探测：digest 算法必须与 apifox-sync.sh 的 schemas_digest 完全一致
PYTHON_BIN=""
for candidate in python python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

# 计算 components.schemas 规范化序列化后的 sha256，逻辑与 apifox-sync.sh 一致
schemas_digest() {
    local spec_file="$1"
    "$PYTHON_BIN" -c '
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

# 比对：区分「仓库缺失但新产出」「仓库存在但新未产出」「内容不一致」三种差异
DIFF_FOUND=0
while IFS='|' read -r STATUS REL; do
    [ -z "$REL" ] && continue
    CURRENT="$WORKDIR/$REL"
    BACKUP="$BACKUP_DIR/$REL"
    if [ "$STATUS" = "0" ]; then
        if [ -f "$CURRENT" ]; then
            print_error "产物未提交：$REL（仓库中不存在，重新生成后有内容）"
            diff -u /dev/null "$CURRENT" | head -60 || true
            DIFF_FOUND=1
        fi
        continue
    fi
    if [ ! -f "$CURRENT" ]; then
        print_error "产物缺失：$REL（重新生成后未产出）"
        DIFF_FOUND=1
        continue
    fi
    if ! cmp -s "$BACKUP" "$CURRENT"; then
        print_error "产物与代码不一致：$REL"
        diff -u "$BACKUP" "$CURRENT" | head -60 || true
        DIFF_FOUND=1
    fi
done < "$MANIFEST"

# Apifox 数据模型指纹基线校验：用新生成文档算 digest，与 .apifox/<service>.schemas.sha256 比对
# 基线是「上次成功同步到 Apifox 的模型版本」，不一致说明改了模型但没跑 ./mix apifox
if [ -n "$PYTHON_BIN" ]; then
    for SERVICE in $SERVICES; do
        case "$SERVICE" in
            spring) SPEC="spring/docs/openapi.json" ;;
            gozero) SPEC="gozero/app/docs/openapi.json" ;;
            nestjs) SPEC="nestjs/docs/openapi.json" ;;
            fastapi) SPEC="fastapi/docs/openapi.json" ;;
            *) continue ;;
        esac
        BASELINE="$WORKDIR/.apifox/$SERVICE.schemas.sha256"
        if [ ! -f "$WORKDIR/$SPEC" ]; then
            continue
        fi
        CURRENT_DIGEST="$(schemas_digest "$WORKDIR/$SPEC" 2>/dev/null || true)"
        if [ -z "$CURRENT_DIGEST" ]; then
            print_warn "$SERVICE 文档 digest 计算失败，跳过基线校验"
            continue
        fi
        if [ ! -f "$BASELINE" ]; then
            print_error "$SERVICE 缺少 Apifox 基线文件 .apifox/$SERVICE.schemas.sha256"
            DIFF_FOUND=1
            continue
        fi
        STORED_DIGEST="$(tr -d ' \r\n' < "$BASELINE")"
        if [ "$CURRENT_DIGEST" != "$STORED_DIGEST" ]; then
            print_error "$SERVICE Apifox 基线未同步：当前文档模型 $CURRENT_DIGEST，基线 $STORED_DIGEST"
            DIFF_FOUND=1
        fi
    done
else
    print_warn "未检测到 Python，跳过 Apifox 基线校验"
fi

echo ""
if [ "$DIFF_FOUND" -ne 0 ]; then
    print_error "静态产物或 Apifox 基线未同步，请依次执行 ./mix swag $SERVICES 与 ./mix apifox $SERVICES 后重新提交"
    exit 1
fi

print_info "静态 OpenAPI 产物与 Apifox 基线均与当前代码一致"
