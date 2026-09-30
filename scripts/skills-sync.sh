#!/bin/bash

# 脚本说明：
# 把仓库 skills/mix-web-demo/ 下的项目技能包同步到本机各 Agent 工具的用户级技能目录
#   - 技能包目录名即技能名，需与 SKILL.md frontmatter 的 name 字段一致
#   - 目标清单见 scripts/skills-targets.conf，<home> 为用户主目录
#   - 只同步「技能根目录已存在」的目标，不存在的目录不创建也不迁移
#   - 同步为镜像覆盖：先删除目标下的同名技能目录再从源目录复制，源目录删掉的文件不会残留
#   - 脚本只使用 bash 内建与 cp、diff，Linux、macOS、Windows（Git Bash）行为一致
# 用法：./scripts/skills-sync.sh [--dry-run] [--list]
#   --dry-run  只打印将要执行的动作，不写任何文件
#   --list     只列出目标清单与检测结果，不同步

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$WORKDIR/skills"
SKILL_NAME="mix-web-demo"
SOURCE_DIR="$SKILLS_DIR/$SKILL_NAME"
TARGETS_FILE="$WORKDIR/scripts/skills-targets.conf"

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

show_help() {
    echo "================================"
    echo "Mix Web Demo - Agent Skills Sync"
    echo "================================"
    echo ""
    echo "用法: ./scripts/skills-sync.sh [--dry-run] [--list]"
    echo ""
    echo "  不带参数    把 skills/mix-web-demo 同步到本机已存在的用户级 Agent 技能目录"
    echo "  --dry-run   只打印将要执行的动作，不写任何文件"
    echo "  --list      只列出目标清单与检测结果，不同步"
    echo ""
    echo "示例:"
    echo "  ./scripts/skills-sync.sh"
    echo "  ./scripts/skills-sync.sh --dry-run"
    echo "  ./scripts/skills-sync.sh --list"
    echo ""
    echo "目标清单: scripts/skills-targets.conf"
    echo "聚合入口: ./mix skills"
}

# ==================== 参数解析 ====================

DRY_RUN=0
LIST_ONLY=0

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            ;;
        --list)
            LIST_ONLY=1
            ;;
        help|--help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

# ==================== 前置检查 ====================

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
    print_error "未找到技能源文件: $SOURCE_DIR/SKILL.md"
    exit 1
fi

if [ ! -f "$TARGETS_FILE" ]; then
    print_error "未找到同步目标清单: $TARGETS_FILE"
    exit 1
fi

# 用户主目录：Unix 用 HOME，Windows 用 USERPROFILE，反斜杠路径统一转成正斜杠
HOME_DIR="${HOME:-$USERPROFILE}"
if [ -z "$HOME_DIR" ]; then
    print_error "无法确定用户主目录（HOME 与 USERPROFILE 均为空）"
    exit 1
fi
HOME_DIR="${HOME_DIR//\\//}"

# 技能包目录名必须与 SKILL.md frontmatter 的 name 一致，Agent 工具按目录名识别技能
FRONTMATTER_NAME=""
IN_FRONTMATTER=0
while IFS= read -r LINE || [ -n "$LINE" ]; do
    LINE="${LINE%$'\r'}"
    if [ "$LINE" = "---" ]; then
        if [ "$IN_FRONTMATTER" -eq 1 ]; then
            break
        fi
        IN_FRONTMATTER=1
        continue
    fi
    if [ "$IN_FRONTMATTER" -eq 1 ]; then
        case "$LINE" in
            name:*)
                VALUE="${LINE#name:}"
                # 去掉首尾空白
                VALUE="${VALUE#"${VALUE%%[![:space:]]*}"}"
                VALUE="${VALUE%"${VALUE##*[![:space:]]}"}"
                if [ -n "$VALUE" ]; then
                    FRONTMATTER_NAME="$VALUE"
                fi
                break
                ;;
        esac
    fi
done < "$SOURCE_DIR/SKILL.md"

if [ -n "$FRONTMATTER_NAME" ] && [ "$FRONTMATTER_NAME" != "$SKILL_NAME" ]; then
    print_error "技能目录名与 SKILL.md 的 name 不一致: $SKILL_NAME != $FRONTMATTER_NAME"
    exit 1
fi

# ==================== 工具函数 ====================

# 展开清单中的占位符，参数为原始路径，输出展开后的绝对路径
expand_target() {
    case "$1" in
        "<home>/"*) printf '%s' "$HOME_DIR/${1#<home>/}" ;;
        *) printf '%s' "$1" ;;
    esac
}

# 比较源目录与目标目录内容是否一致，diff 不可用时按不一致处理（走覆盖）
dirs_identical() {
    if ! command -v diff >/dev/null 2>&1; then
        return 1
    fi
    diff -r -q "$1" "$2" >/dev/null 2>&1
}

# 同步单个技能根目录，参数为技能根目录，返回 0 表示成功
sync_target() {
    ROOT="$1"
    TARGET="$ROOT/$SKILL_NAME"

    case "$TARGET" in
        ""|"/"|*"//"*)
            print_error "非法目标路径: $TARGET"
            return 1
            ;;
    esac
    if [ "$TARGET" = "$ROOT" ]; then
        print_error "非法目标路径: $TARGET"
        return 1
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
        if [ -d "$TARGET" ]; then
            print_warn "[DRY-RUN] 将覆盖: $TARGET"
        else
            print_warn "[DRY-RUN] 将新建: $TARGET"
        fi
        return 0
    fi

    if [ -d "$TARGET" ] && dirs_identical "$SOURCE_DIR" "$TARGET"; then
        print_info "内容一致，跳过: $TARGET"
        UNCHANGED_COUNT=$((UNCHANGED_COUNT + 1))
        return 0
    fi

    if [ -d "$TARGET" ]; then
        rm -rf "$TARGET" || {
            print_error "清理旧技能目录失败: $TARGET"
            return 1
        }
    fi

    mkdir -p "$ROOT" || {
        print_error "创建技能根目录失败: $ROOT"
        return 1
    }

    cp -R "$SOURCE_DIR" "$TARGET" || {
        print_error "复制技能失败: $TARGET"
        return 1
    }

    print_info "已同步: $TARGET"
    SYNCED_COUNT=$((SYNCED_COUNT + 1))
    return 0
}

# ==================== 执行同步 ====================

DETECTED_COUNT=0
SKIPPED_COUNT=0
SYNCED_COUNT=0
UNCHANGED_COUNT=0
FAILED_COUNT=0

print_info "技能源目录: $SOURCE_DIR"
print_info "技能名称: $SKILL_NAME"
if [ "$DRY_RUN" -eq 1 ]; then
    print_warn "DRY-RUN 模式：只打印动作，不写文件"
fi
echo ""

while IFS= read -r LINE || [ -n "$LINE" ]; do
    LINE="${LINE%$'\r'}"
    # 去掉行首空白
    LINE="${LINE#"${LINE%%[![:space:]]*}"}"
    if [ -z "$LINE" ]; then
        continue
    fi
    case "$LINE" in
        \#*)
            continue
            ;;
    esac

    # 第一个空白之前是路径，之后是注释
    RAW="${LINE%%[[:space:]]*}"
    ROOT="$(expand_target "$RAW")"
    if [ ! -d "$ROOT" ]; then
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        if [ "$LIST_ONLY" -eq 1 ]; then
            print_warn "未检测到技能根目录，跳过: $ROOT"
        fi
        continue
    fi

    DETECTED_COUNT=$((DETECTED_COUNT + 1))

    if [ "$LIST_ONLY" -eq 1 ]; then
        if [ ! -d "$ROOT/$SKILL_NAME" ]; then
            print_warn "未安装: $ROOT/$SKILL_NAME"
        elif dirs_identical "$SOURCE_DIR" "$ROOT/$SKILL_NAME"; then
            print_info "已同步: $ROOT/$SKILL_NAME"
        else
            print_warn "存在差异: $ROOT/$SKILL_NAME"
        fi
        continue
    fi

    print_info "同步目标: $ROOT"
    if ! sync_target "$ROOT"; then
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
done < "$TARGETS_FILE"

echo ""
print_info "目标清单: $TARGETS_FILE"
print_info "检测到技能根目录 $DETECTED_COUNT 个，未检测到 $SKIPPED_COUNT 个（未检测到的目录不创建也不迁移）"

if [ "$LIST_ONLY" -eq 1 ]; then
    print_info "执行 ./mix skills 开始同步"
    exit 0
fi

if [ "$FAILED_COUNT" -gt 0 ]; then
    print_error "同步失败 $FAILED_COUNT 个目标"
    exit 1
fi

if [ "$DRY_RUN" -eq 1 ]; then
    print_info "DRY-RUN 完成，实际执行请去掉 --dry-run"
    exit 0
fi

print_info "同步完成：覆盖 $SYNCED_COUNT 个，内容一致跳过 $UNCHANGED_COUNT 个"
