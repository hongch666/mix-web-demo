#!/bin/bash

# 日志观测组件控制脚本 - 管理 Loki、Promtail、Grafana
# 用于 ./mix dist start（宿主机进程模式）下独立启动日志观测栈并查看日志
# 使用方式: ./scripts/loki-control.sh [start|stop|restart|status|logs|delete|help] [--dist]
#   --dist  采集 dist/logs（dist 模式），缺省采集根目录 logs/（容器与 dev 模式）
# 推荐通过 ./mix loki <command> [--dist] 调用

set -e

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$WORKDIR/loki-config/docker-compose.yml"
COMPOSE_PROJECT="loki"

# 固定容器名（与 loki-config/docker-compose.yml 的 container_name 保持一致），
# 用于检测并清理其他编排栈（如根目录 docker-compose.yml）占用的同名容器
NAMED_CONTAINERS=(loki promtail grafana)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 查找可用的 compose 命令
detect_compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        log_error "docker-compose 或 Docker Compose CLI 未安装"
        exit 1
    fi
}

# 检查 Docker 是否可用
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker 未安装"
        exit 1
    fi
    if ! docker ps >/dev/null 2>&1; then
        log_error "Docker 守护进程未运行，请先启动 Docker"
        exit 1
    fi
}

compose() {
    $COMPOSE_CMD -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT" "$@"
}

# 准备日志目录，两套日志目录（logs/ 与 dist/logs/）都可能被挂载，
# 目录不存在时容器挂载会产生 root 属主的空目录，这里提前创建以保证权限一致
prepare_dirs() {
    log_info "准备日志目录..."
    for d in spring gozero nestjs fastapi gateway; do
        mkdir -p "$WORKDIR/logs/$d" "$WORKDIR/dist/logs/$d"
    done
}

# 清理其他编排栈占用的同名容器
# 根目录 docker-compose.yml 内联了同一套观测组件，容器名与本栈相同（loki/promtail/grafana），
# 但属于不同 compose 项目，任何一方残留都会导致另一方启动时报名称冲突
# 参数 keep_project: 需要保留容器的编排项目名，默认为本栈
cleanup_conflicts() {
    local keep_project=${1:-$COMPOSE_PROJECT}

    for name in "${NAMED_CONTAINERS[@]}"; do
        if ! docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$name"; then
            continue
        fi

        local project
        project=$(docker inspect -f '{{ index .Config.Labels "com.docker.compose.project" }}' "$name" 2>/dev/null || true)
        if [ "$project" != "$keep_project" ]; then
            log_warn "容器 $name 属于其他编排栈（${project:-非 compose}），先移除以避免名称冲突"
            docker rm -f "$name" >/dev/null 2>&1 || true
        fi
    done
}

# 移除本栈（./mix loki start 独立启动）占用的同名容器
# 供根目录 docker-compose.yml 启动前调用：此时保留容器的是根编排项目，
# 本栈容器必须让位，只清理属于本栈项目的容器，不会误删根编排自身的容器
remove_standalone_containers() {
    for name in "${NAMED_CONTAINERS[@]}"; do
        if ! docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$name"; then
            continue
        fi

        local project
        project=$(docker inspect -f '{{ index .Config.Labels "com.docker.compose.project" }}' "$name" 2>/dev/null || true)
        if [ "$project" = "$COMPOSE_PROJECT" ]; then
            log_warn "移除独立启动的观测容器 $name，避免与根编排的容器名冲突"
            docker rm -f "$name" >/dev/null 2>&1 || true
        fi
    done

    # 本栈的一次性初始化容器，无固定 container_name，按项目命名规则清理
    local init_container="${COMPOSE_PROJECT}-loki-data-init-1"
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$init_container"; then
        docker rm -f "$init_container" >/dev/null 2>&1 || true
    fi
}

# 获取 promtail 当前实际挂载的采集配置文件名（容器未运行时输出空）
current_promtail_config() {
    local source
    source=$(docker inspect -f '{{ range .Mounts }}{{ if eq .Destination "/etc/promtail/config.yaml" }}{{ .Source }}{{ end }}{{ end }}' promtail 2>/dev/null || true)
    if [ -z "$source" ]; then
        echo ""
        return
    fi
    # 兼容 Linux 与 Windows 两种路径分隔符
    echo "$source" | sed 's#.*[\\/]##'
}

# 采集配置文件名转换为可读的日志来源说明
describe_config() {
    case $1 in
        promtail-dist.yaml) echo "dist/logs（./mix dist start）" ;;
        promtail.yaml) echo "根目录 logs/（容器与 dev 模式）" ;;
        *) echo "未知配置" ;;
    esac
}

show_status() {
    echo ""
    log_info "日志观测组件状态:"
    echo ""
    compose ps
    echo ""

    local active_config
    active_config=$(current_promtail_config)
    if [ -n "$active_config" ]; then
        log_info "当前采集配置: $active_config -> $(describe_config "$active_config")"
    else
        log_info "当前采集配置: 未运行（--dist 采集 dist/logs，缺省采集根目录 logs/）"
    fi

    log_info "访问地址: Loki http://localhost:3100，Grafana http://localhost:3000（匿名 Admin，数据源已预置）"
    echo ""
}

# 启动观测栈
start_all() {
    log_info "启动日志观测组件 (Loki/Promtail/Grafana)..."
    log_info "日志来源: $LOG_SOURCE_DESC"
    prepare_dirs
    cleanup_conflicts
    compose up -d
    show_status
}

# 停止观测栈，保留数据卷（Grafana 面板与 Loki 索引数据不丢失）
stop_all() {
    log_info "停止日志观测组件（保留数据卷）..."
    compose down --remove-orphans || log_warn "停止过程中出现异常，请检查容器状态"

    # down 只作用于本栈项目名下的容器，若同名容器仍然存在，说明它们由其他编排栈
    # （根目录 docker-compose.yml 的 ./mix compose up）创建，需要由对应入口停止
    local remaining=()
    for name in "${NAMED_CONTAINERS[@]}"; do
        if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$name"; then
            remaining+=("$name")
        fi
    done
    if [ ${#remaining[@]} -gt 0 ]; then
        log_warn "同名容器仍由其他编排栈持有: ${remaining[*]}，请改为执行 ./mix compose down"
    fi

    log_info "日志观测组件已停止，Loki 与 Grafana 数据卷保留"
}

# 删除观测栈及其数据卷
delete_all() {
    log_warn "停止并删除日志观测组件及其数据卷..."
    read -p "确认删除 Loki/Grafana 数据卷? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_warn "已取消删除操作"
        return 0
    fi
    compose down -v --remove-orphans || log_warn "删除过程中出现异常，请检查容器状态"
    log_info "日志观测组件已删除"
}

# 重启观测栈（切换日志来源时相当于重建 promtail，使新配置生效）
restart_all() {
    log_info "重启日志观测组件..."
    log_info "日志来源: $LOG_SOURCE_DESC"
    prepare_dirs
    cleanup_conflicts
    compose up -d --force-recreate
    show_status
}

# 查看容器日志
show_logs() {
    local service=$1

    if [ -z "$service" ]; then
        compose logs -f --tail 100
        return
    fi

    case $service in
        loki|promtail|grafana)
            compose logs -f --tail 100 "$service"
            ;;
        *)
            log_error "未知的服务: $service"
            echo "可用服务: loki, promtail, grafana"
            return 1
            ;;
    esac
}

# 显示帮助信息
show_help() {
    cat << 'EOF'
日志观测组件控制脚本

用法: ./scripts/loki-control.sh [命令] [参数]
      通常通过 ./mix loki [命令] [参数] 调用

命令:
  start           启动 Loki/Promtail/Grafana (默认)
  stop            停止容器，保留 Loki 与 Grafana 数据卷
  restart         重启容器
  status          查看容器状态与当前采集配置
  logs [service]  查看容器日志 (loki|promtail|grafana)，不指定则查看全部
  delete          停止并删除容器及数据卷
  cleanup         清理本栈残留的同名容器（供根编排启动前调用）
  help            显示本帮助

选项 (start / restart):
  --dist          采集 dist/logs，配合 ./mix dist start
  --local         采集根目录 logs/，配合 ./mix compose up 或 ./mix dev seq（默认）
  --mode MODE     等价写法，MODE 为 local 或 dist

说明:
  两套日志目录各自独立、互不导入，同一时刻只采集其中一套：
    local -> promtail.yaml      采集 /app/logs      （根目录 logs/）
    dist  -> promtail-dist.yaml 采集 /app/dist-logs （dist/logs）
  切换来源会重建 promtail 容器；进入 Loki 的数据带 mode=local 或 mode=dist 标签，
  可用 {service="spring", mode="dist"} 精确查询
  根编排（./mix compose up）固定使用 local 配置
  本栈与根编排的容器同名但属于不同 compose 项目，交叉启动时会自动清理对方容器

示例:
  ./mix loki start              # 启动观测栈并采集根目录 logs/
  ./mix loki start --dist       # 启动观测栈并采集 dist/logs
  ./mix loki restart --dist     # 切换到 dist 日志来源
  ./mix loki restart            # 切回根目录 logs/
  ./mix loki status             # 查看状态与当前采集配置
  ./mix loki logs promtail      # 查看 Promtail 日志
  ./mix loki stop               # 停止观测栈（保留数据）
EOF
}

# 日志来源模式：local 采集根目录 logs/，dist 采集 dist/logs
LOG_MODE="local"
LOG_SOURCE_DESC="根目录 logs/（容器与 dev 模式）"
LOKI_PROMTAIL_CONFIG="promtail.yaml"
REST_ARGS=()

# 从参数中解析 --dist / --local / --mode，其余参数回填到 REST_ARGS
parse_mode_args() {
    REST_ARGS=()

    while [ $# -gt 0 ]; do
        case $1 in
            --dist|--mode=dist)
                LOG_MODE="dist"
                ;;
            --local|--mode=local)
                LOG_MODE="local"
                ;;
            --mode)
                if [ $# -lt 2 ]; then
                    log_error "选项 --mode 缺少取值（local 或 dist）"
                    exit 1
                fi
                LOG_MODE="$2"
                shift
                ;;
            *)
                REST_ARGS+=("$1")
                ;;
        esac
        shift
    done

    case $LOG_MODE in
        local)
            LOKI_PROMTAIL_CONFIG="promtail.yaml"
            LOG_SOURCE_DESC="根目录 logs/（容器与 dev 模式）"
            ;;
        dist)
            LOKI_PROMTAIL_CONFIG="promtail-dist.yaml"
            LOG_SOURCE_DESC="dist/logs（./mix dist start）"
            ;;
        *)
            log_error "未知的日志来源模式: $LOG_MODE（可选: local, dist）"
            exit 1
            ;;
    esac

    # 供 compose 插值选择 promtail 采集配置
    export LOKI_PROMTAIL_CONFIG
}

main() {
    local command=${1:-start}
    shift || true

    parse_mode_args "$@"

    case $command in
        start|up)
            check_docker
            start_all
            ;;
        stop|down)
            check_docker
            stop_all
            ;;
        restart)
            check_docker
            restart_all
            ;;
        status|ps)
            check_docker
            show_status
            ;;
        logs)
            check_docker
            show_logs "${REST_ARGS[0]:-}"
            ;;
        delete)
            check_docker
            delete_all
            ;;
        cleanup)
            check_docker
            remove_standalone_containers
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

detect_compose

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "未找到编排文件: $COMPOSE_FILE"
    exit 1
fi

cd "$WORKDIR"

main "$@"
