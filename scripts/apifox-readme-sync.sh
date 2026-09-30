#!/bin/bash

# 脚本说明：
# 将根目录 README.md 同步到 Apifox 的指定项目 Markdown 文档
#   ./mix apifox 走 Apifox 开放 API，只能导入接口与数据模型，写不了文档
#   本脚本走 Apifox CLI 的 doc create / doc update，写入 API 管理树里的项目 Markdown 文档
# 依赖：apifox CLI（缺失时自动 npm 安装，Node 不低于 16）、sed、tr、grep、awk、mktemp
# 用法：./scripts/apifox-readme-sync.sh [options]
#   --dry-run      只生成并校验导入内容，不写入 Apifox
#   --create       未配置 APIFOX_README_DOC_ID 时按名称创建文档，并打印新文档 ID
#   --skip-if-unset 未配置 APIFOX_README_DOC_ID 时打印提示并跳过，供 ./mix apifox 调用
#   --no-install   未安装 Apifox CLI 时不自动安装（默认自动安装）
#   --keep-toc     保留 README 的「## 目录」章节（默认剔除）
#   --no-verify    写入后不回头校验文档内容
#   -h, --help     显示帮助
# 配置：令牌与项目 ID 从根目录 .env 读取，变量说明见 .env.example

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DEFAULT_README_FILE="README.md"
DEFAULT_FOLDER_ID="0"
DEFAULT_CLI_REGISTRY="https://registry.npmmirror.com/"
DEFAULT_AUTO_INSTALL="true"
MAX_NAME_LENGTH=255
LARGE_CONTENT_BYTES=200000

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
    echo "用法: ./scripts/apifox-readme-sync.sh [--dry-run] [--create] [--skip-if-unset] [--no-install] [--keep-toc] [--no-verify]"
    echo "  目标文档由 APIFOX_README_DOC_ID 指定，未配置时可加 --create 创建"
    echo "  --dry-run   只生成并校验导入内容，不写入 Apifox"
    echo "  --skip-if-unset 未配置文档 ID 时跳过而不报错"
    echo "  --no-install 未安装 Apifox CLI 时不自动安装"
    echo "  --keep-toc  保留 README 的「## 目录」章节"
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

# ID 类变量必须是数字，填成名称会直接报错，与 apifox-sync.sh 的处理保持一致
require_int_if_set() {
    local name="$1"
    local raw
    raw=$(trim "${!name}")
    if [ -z "$raw" ]; then
        return 0
    fi
    case "$raw" in
        *[!0-9]*)
            print_error "环境变量 $name 需要的是数字 ID，当前填的是: $raw"
            print_error "文档 ID 用 apifox doc list --project <项目ID> 查询，目录 ID 用 apifox folder list 查询"
            return 1
            ;;
    esac
    return 0
}

load_env() {
    if [ ! -f "$WORKDIR/.env" ]; then
        print_warn "未找到根目录 .env，将仅使用当前环境变量"
        return 0
    fi

    # 先记下调用方已显式传入的 APIFOX_* 变量，sourcing 之后再还原
    # 这样 APIFOX_README_DOC_ID=xxx ./mix apifox-readme 这类临时覆盖不会被 .env 顶掉
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

# ==================== 路径与转义 ====================

# Apifox CLI 是 Node 程序，识别不了 Git Bash 的 MSYS 路径，需要转成 Windows 原生路径
native_path() {
    local path="$1"
    local converted
    if command -v cygpath >/dev/null 2>&1; then
        converted=$(cygpath -w "$path" 2>/dev/null)
        if [ -n "$converted" ]; then
            printf '%s' "$converted"
            return 0
        fi
    fi
    printf '%s' "$path"
}

# 单行文本转 JSON 字符串内容（不追加换行）
json_escape_inline() {
    tr -d '\r' | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' | tr -d '\n'
}

# 多行文本转 JSON 字符串内容，换行统一输出为 \n 转义
json_escape_multiline() {
    tr -d '\r' | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' -e 's/$/\\n/' | tr -d '\n'
}

# ==================== 正文准备 ====================

# 生成待同步正文：原样同步 README，可选剔除「## 目录」锚点章节
# 锚点目录在 Apifox 侧跳转不了，留着只会误导阅读
prepare_content() {
    local source_file="$1"
    local target_file="$2"
    local strip_toc="$3"

    : > "$target_file"

    if [ "$strip_toc" = "true" ]; then
        awk '
            /^##[[:space:]]+目录[[:space:]]*$/ { skip_toc = 1; next }
            skip_toc && /^##[[:space:]]/ { skip_toc = 0 }
            !skip_toc { print }
        ' "$source_file" >> "$target_file"
    else
        cat "$source_file" >> "$target_file"
    fi

    return 0
}

# 文档名优先取 APIFOX_README_DOC_NAME，其次取 README 第一个一级标题
resolve_doc_name() {
    local source_file="$1"
    local name
    name=$(env_value APIFOX_README_DOC_NAME "")
    if [ -z "$name" ]; then
        name=$(grep -m 1 -E '^#[[:space:]]+' "$source_file" | sed -e 's/^#[[:space:]]*//' -e 's/[[:space:]]*$//')
    fi
    if [ -z "$name" ]; then
        name="README"
    fi
    printf '%s' "${name:0:$MAX_NAME_LENGTH}"
    return 0
}

# 读取正文里的第一个一级标题，写入后用它校验文档内容
resolve_content_marker() {
    local source_file="$1"
    local marker
    marker=$(grep -m 1 -E '^#[[:space:]]+' "$source_file" | sed -e 's/^#[[:space:]]*//' -e 's/[[:space:]]*$//')
    printf '%s' "$marker"
    return 0
}

# ==================== 请求构造 ====================

# 生成 doc create / doc update 的 --file 内容
# doc_name 为空表示不改名：update 会把传入字段直接提交，不传 name 才保得住 Apifox 侧手工改过的标题
build_payload_file() {
    local doc_name="$1"
    local content_file="$2"
    local folder_id="$3"
    local module_id="$4"
    local out_file="$5"

    {
        printf '{'
        if [ -n "$doc_name" ]; then
            printf '"name":"'
            printf '%s' "$doc_name" | json_escape_inline
            printf '",'
        fi
        printf '"content":"'
        json_escape_multiline < "$content_file"
        printf '"'
        if [ -n "$folder_id" ]; then
            printf ',"folderId":%s' "$folder_id"
        fi
        if [ -n "$module_id" ]; then
            printf ',"moduleId":%s' "$module_id"
        fi
        printf '}'
    } > "$out_file"

    return 0
}

apifox_cli() {
    local branch_args=()
    if [ -n "$branch" ]; then
        branch_args=(--branch "$branch")
    fi
    apifox "$@" --project "$project_id" --access-token "$token" "${branch_args[@]}"
}

# 未安装 Apifox CLI 时自动安装，安装源与开关见 APIFOX_CLI_REGISTRY / APIFOX_CLI_AUTO_INSTALL
ensure_apifox_cli() {
    if command -v apifox >/dev/null 2>&1; then
        return 0
    fi

    if [ "$auto_install" != "true" ]; then
        print_error "未找到 apifox 命令，请先安装 Apifox CLI:"
        echo "  npm i -g apifox-cli@latest --registry=$cli_registry"
        return 1
    fi

    if ! command -v npm >/dev/null 2>&1; then
        print_error "未找到 npm，无法自动安装 Apifox CLI"
        print_error "请先安装 Node.js 16 及以上版本，再执行: npm i -g apifox-cli@latest"
        return 1
    fi

    print_info "未检测到 apifox 命令，开始自动安装 Apifox CLI（安装源 $cli_registry）"
    if ! npm i -g apifox-cli@latest --registry="$cli_registry"; then
        print_error "Apifox CLI 自动安装失败，可手动重试:"
        print_error "  npm i -g apifox-cli@latest --registry=$cli_registry"
        return 1
    fi

    # 清掉命令位置缓存，避免刚装完仍在当前 shell 里找不到
    hash -r 2>/dev/null || true

    if ! command -v apifox >/dev/null 2>&1; then
        print_error "安装完成但当前终端仍找不到 apifox 命令"
        print_error "请重开终端，或确认 npm 全局 bin 目录已在 PATH 中"
        return 1
    fi

    print_info "Apifox CLI 安装完成，版本 $(apifox --version 2>/dev/null)"
    return 0
}

# 403075 是 Apifox 对自动化调用者的写保护，单独提示两种放行方式
print_write_rejected_hint() {
    local output_file="$1"
    if grep -q '403075' "$output_file" 2>/dev/null; then
        print_error "Apifox 拦截了自动化调用者直接写分支（403075），两种放行方式："
        print_error "  1. Apifox 客户端 2.8.31+ 开启「项目设置 → 功能设置 → AI 功能设置 → 外部 AI 编辑权限 → 主分支直接编辑权限」，再重试"
        print_error "  2. 走 AI 分支：apifox branch create --project $project_id --type ai --name <分支名> --from <源分支>"
        print_error "     已有文档先 apifox branch pick-to --type ai --from <源分支> --to <分支名> --doc-ids $doc_id"
        print_error "     再用 APIFOX_README_BRANCH=<分支名> 重试，确认无误后发起合并"
    fi
    return 0
}

extract_doc_id() {
    local json="$1"
    printf '%s' "$json" \
        | grep -o '"id"[[:space:]]*:[[:space:]]*[0-9]\+' \
        | head -n 1 \
        | grep -o '[0-9]\+$'
    return 0
}

# ==================== 主流程 ====================

main() {
    local dry_run="false"
    local allow_create="false"
    local strip_toc="true"
    local verify="true"
    local skip_if_unset="false"
    local no_install="false"
    local arg

    for arg in "$@"; do
        case "$arg" in
            --dry-run)
                dry_run="true"
                ;;
            --create)
                allow_create="true"
                ;;
            --keep-toc)
                strip_toc="false"
                ;;
            --no-verify)
                verify="false"
                ;;
            --skip-if-unset)
                skip_if_unset="true"
                ;;
            --no-install)
                no_install="true"
                ;;
            -h|--help)
                show_usage
                return 0
                ;;
            *)
                print_error "未知参数: $arg"
                show_usage
                return 1
                ;;
        esac
    done

    load_env

    cli_registry=$(env_value APIFOX_CLI_REGISTRY "$DEFAULT_CLI_REGISTRY")
    cli_registry="${cli_registry%/}"
    auto_install=$(env_flag APIFOX_CLI_AUTO_INSTALL "$DEFAULT_AUTO_INSTALL")
    if [ "$no_install" = "true" ]; then
        auto_install="false"
    fi

    if ! ensure_apifox_cli; then
        if [ "$skip_if_unset" = "true" ]; then
            print_warn "跳过 README 同步；Apifox CLI 就绪后可参与同步"
            return 0
        fi
        print_error "缺少 Apifox CLI，无法同步 README"
        return 1
    fi

    token=$(env_value APIFOX_ACCESS_TOKEN "")
    project_id=$(env_value APIFOX_PROJECT_ID "")
    if [ -z "$token" ] || [ -z "$project_id" ]; then
        print_error "缺少 Apifox 配置，请在根目录 .env 中设置："
        echo "  APIFOX_ACCESS_TOKEN  # Apifox -> 右上角头像 -> 账号设置 -> API 访问令牌"
        echo "  APIFOX_PROJECT_ID    # 项目 URL 形如 https://app.apifox.com/project/<项目ID>/xxx"
        return 1
    fi

    branch=$(env_value APIFOX_README_BRANCH "")
    doc_id=$(env_value APIFOX_README_DOC_ID "")
    # 归属只认显式配置：update 会把传入字段直接提交，默认值 0 会把已有文档挪到根目录
    folder_id=$(env_value APIFOX_README_DOC_FOLDER_ID "")
    module_id=$(env_value APIFOX_README_DOC_MODULE_ID "")

    local id_var
    for id_var in APIFOX_README_DOC_ID APIFOX_README_DOC_FOLDER_ID APIFOX_README_DOC_MODULE_ID; do
        require_int_if_set "$id_var" || return 1
    done

    local readme_file
    readme_file="$WORKDIR/$(env_value APIFOX_README_FILE "$DEFAULT_README_FILE")"
    if [ ! -f "$readme_file" ]; then
        print_error "未找到 README 文件 $readme_file"
        return 1
    fi

    # 目标文档名：已指定 ID 时不改名，除非显式配置了 APIFOX_README_DOC_NAME
    local doc_name=""
    if [ -z "$doc_id" ] || [ -n "$(env_value APIFOX_README_DOC_NAME "")" ]; then
        doc_name=$(resolve_doc_name "$readme_file")
    fi

    TMP_DIR=$(mktemp -d 2>/dev/null)
    if [ -z "$TMP_DIR" ] || [ ! -d "$TMP_DIR" ]; then
        print_error "无法创建临时目录，请检查系统 mktemp 是否可用"
        return 1
    fi

    local content_file="$TMP_DIR/readme-content.md"
    local payload_file="$TMP_DIR/doc-payload.json"
    local schema_key="doc-update"

    prepare_content "$readme_file" "$content_file" "$strip_toc"

    if [ -z "$doc_id" ]; then
        if [ "$allow_create" = "true" ]; then
            print_info "未配置 APIFOX_README_DOC_ID，将创建新文档「$doc_name」"
            schema_key="doc-create"
        elif [ "$dry_run" = "true" ]; then
            print_info "未配置 APIFOX_README_DOC_ID，dry-run 按创建新文档「$doc_name」校验"
            schema_key="doc-create"
        else
            if [ "$skip_if_unset" = "true" ]; then
                print_warn "未配置 APIFOX_README_DOC_ID，跳过 README 同步"
                print_warn "在根目录 .env 填写文档 ID 即可参与同步，首次创建用 ./mix apifox-readme --create"
                return 0
            fi
            print_error "未配置目标文档，请二选一："
            echo "  1. 在 .env 设置 APIFOX_README_DOC_ID=<文档ID>（用 apifox doc list --project $project_id 查询）"
            echo "  2. 执行 ./mix apifox-readme --create，由脚本创建文档后回填 ID"
            return 1
        fi
        # 创建时目录 ID 固定传值，0 表示与接口目录同级（API 目录树根）
        folder_id=$(env_value APIFOX_README_DOC_FOLDER_ID "$DEFAULT_FOLDER_ID")
    fi

    local placement
    if [ -z "$doc_id" ]; then
        placement="新建于项目 $project_id / 模块 ${module_id:-默认模块} / 目录 ${folder_id:-0}（与接口目录同级）"
    elif [ -n "$folder_id" ] || [ -n "$module_id" ]; then
        placement="项目 $project_id / 目录 ${folder_id:-不变} / 模块 ${module_id:-不变}（按 .env 调整）"
    else
        placement="项目 $project_id / 目录与模块保持不变"
    fi
    print_info "归属：$placement，与接口同项目${branch:+ / 分支 $branch}"

    local content_bytes
    content_bytes=$(wc -c < "$content_file" | tr -d ' ')
    if [ "$content_bytes" -gt "$LARGE_CONTENT_BYTES" ]; then
        print_warn "正文 $content_bytes 字节，偏大；Apifox 侧渲染与版本对比会变慢，必要时拆分 README"
    fi

    build_payload_file "$doc_name" "$content_file" "$folder_id" "$module_id" "$payload_file"

    local payload_native
    payload_native=$(native_path "$payload_file")

    if ! apifox cli-schema validate "$schema_key" --file "$payload_native" >/dev/null 2>&1; then
        print_error "导入内容未通过 $schema_key 结构校验，详细信息："
        apifox cli-schema validate "$schema_key" --file "$payload_native"
        return 1
    fi

    local source_lines content_lines
    source_lines=$(wc -l < "$readme_file" | tr -d ' ')
    content_lines=$(wc -l < "$content_file" | tr -d ' ')
    print_info "正文 $content_bytes 字节 / $content_lines 行（源文件 $source_lines 行），payload 结构校验通过（$schema_key）"

    if [ "$dry_run" = "true" ]; then
        print_info "dry-run 模式：未写入 Apifox，临时 payload 随流程清理"
        print_info "提交字段：$(grep -o '"name"\|"content"\|"folderId"\|"moduleId"' "$payload_file" | tr '\n' ' ')"
        print_info "正文预览：$(head -n 4 "$content_file" | tr -d '\r' | tr '\n' ' ' | cut -c1-160)"
        return 0
    fi

    local output_file="$TMP_DIR/cli-output.json"
    local marker
    marker=$(resolve_content_marker "$readme_file")

    if [ -z "$doc_id" ]; then
        if ! apifox_cli doc create --file "$payload_native" > "$output_file" 2>&1; then
            print_error "创建文档失败："
            cat "$output_file"
            print_write_rejected_hint "$output_file"
            return 1
        fi
        doc_id=$(extract_doc_id "$(cat "$output_file")")
        if [ -z "$doc_id" ]; then
            print_warn "已创建文档，但未能从输出中解析出文档 ID，请手工查看后回填 .env"
            cat "$output_file"
            return 0
        fi
        print_info "已创建文档，ID: $doc_id"
        print_info "请把该 ID 写入根目录 .env 的 APIFOX_README_DOC_ID，后续同步即为原地更新"
    else
        print_info "更新文档 $doc_id"
        if ! apifox_cli doc update "$doc_id" --file "$payload_native" > "$output_file" 2>&1; then
            print_error "更新文档失败："
            cat "$output_file"
            print_write_rejected_hint "$output_file"
            return 1
        fi
    fi

    if [ "$verify" != "true" ]; then
        print_info "已跳过写入后校验"
        return 0
    fi

    local verify_file="$TMP_DIR/cli-verify.json"
    if ! apifox_cli doc get "$doc_id" > "$verify_file" 2>&1; then
        print_warn "无法回读文档校验，输出如下："
        cat "$verify_file"
        return 0
    fi

    if [ -n "$marker" ] && ! grep -q -F -- "$marker" "$verify_file"; then
        print_error "回读文档未找到正文标记「$marker」，同步结果可能与预期不一致"
        return 1
    fi

    print_info "文档 $doc_id 内容校验通过，README 同步完成"
    return 0
}

cleanup() {
    if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}

trap cleanup EXIT

print_info "开始同步 README 到 Apifox 项目 Markdown 文档..."
if main "$@"; then
    print_info "README 同步流程结束"
    exit 0
fi

print_error "README 同步失败"
exit 1
