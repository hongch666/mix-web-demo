#!/bin/bash

# 微服务 Docker 构建和容器部署脚本
# 用途：构建镜像并创建/启动容器（Docker 环境使用 .env.docker）
# 用法：./build_and_run_services.sh [service1] [service2] ...

set -e
set -o pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NETWORK_NAME="hcsy"
# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

declare -A SERVICE_LANG=(
    [gozero]="go"
    [nestjs]="node"
    [spring]="java"
    [fastapi]="python"
)

declare -A SERVICE_PORT=(
    [spring]="8081"
    [gozero]="8082"
    [nestjs]="8083"
    [fastapi]="8084"
)

# 代理排除项：Docker CLI 会把宿主机代理（~/.docker/config.json 的 proxies 配置）注入容器，
# 默认 NO_PROXY 只含 localhost，Go/Node/Python 服务通过容器名访问 nacos/mysql/redis 等
# 会被转发到宿主代理而失败；注意 NO_PROXY 与 no_proxy 是两个独立变量，必须同时设置
# 取值与根目录 docker-compose.yml 的 x-no-proxy 保持一致
NO_PROXY_VALUE="localhost,127.0.0.1,::1,nacos,mysql,redis,mq,es,mongodb,pgvector-db,clickhouse,loki,promtail,grafana,spring,gozero,nestjs,fastapi,gateway,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

ensure_network() {
    if ! docker network inspect "$NETWORK_NAME" > /dev/null 2>&1; then
        print_info "创建 Docker 网络: $NETWORK_NAME"
        docker network create "$NETWORK_NAME" > /dev/null
    fi
}

append_env() {
    local -n target=$1
    local key=$2
    local value=$3

    if [ -n "$value" ]; then
        target+=( -e "$key=$value" )
    fi
}

append_env_file() {
    local -n target=$1
    local env_file=$2

    if [ -f "$env_file" ]; then
        target+=( --env-file "$env_file" )
    else
        print_warning "未找到 Docker 环境文件: $env_file"
    fi
}

get_env_file_path() {
    local service=$1

    case $service in
        gozero)
            echo "${PROJECT_DIR}/gozero/app/.env.docker"
            ;;
        *)
            echo "${PROJECT_DIR}/${service}/.env.docker"
            ;;
    esac
}

# 获取服务列表
get_services() {
    if [ $# -eq 0 ]; then
        echo "gozero nestjs spring gateway fastapi"
    else
        echo "$@"
    fi
}

start_only=false

# 构建镜像
build_image() {
    local service=$1
    local service_dir="${PROJECT_DIR}/${service}"

    # 网关使用官方 apache/apisix 镜像，仅通过 compose 启动，不构建本地镜像
    if [ "$service" = "gateway" ]; then
        print_info "gateway 使用官方 apache/apisix 镜像，跳过镜像构建"
        return 0
    fi

    if [ ! -d "$service_dir" ]; then
        print_error "服务目录不存在: $service_dir"
        return 1
    fi

    if [ ! -f "$service_dir/Dockerfile" ]; then
        print_error "Dockerfile 不存在: $service_dir/Dockerfile"
        return 1
    fi

    print_info "构建 ${service} 镜像..."
    cd "$service_dir"

    # 不接管道（如 | tail）：BuildKit 的构建进度需要实时输出，接了管道会被缓冲到构建结束才一次性打印，构建期间看起来像卡死
    # --progress=plain 会输出每一步的完整日志（apt/pip 等），便于排查构建问题
    local build_status=0
    docker build --progress=plain -t "mix-${service}:latest" . || build_status=$?

    if [ $build_status -eq 0 ]; then
        print_success "${service} 镜像构建完成"
    else
        print_error "${service} 镜像构建失败"
        return 1
    fi

    cd "$PROJECT_DIR"
}

# 创建和启动容器
run_container() {
    local service=$1
    local port=${SERVICE_PORT[$service]}
    local image_name="mix-${service}:latest"
    local container_name="mix-${service}-container"
    local service_dir="${PROJECT_DIR}/${service}"
    local env_file

    # 检查镜像是否存在
    if ! docker image inspect "$image_name" > /dev/null 2>&1; then
        if [ "$start_only" = true ]; then
            print_error "${service} 镜像不存在，请先执行 ./mix docker build ${service}"
            return 1
        fi

        print_warning "${service} 镜像不存在，开始构建..."
        if ! build_image "$service"; then
            return 1
        fi
    fi

    # 检查容器是否已运行
    if docker ps | grep -q "$container_name"; then
        print_warning "${service} 容器已在运行，跳过..."
        return 0
    fi

    # 检查容器是否存在但未运行
    if docker ps -a | grep -q "$container_name"; then
        print_info "删除已存在的 ${service} 容器..."
        docker rm "$container_name" > /dev/null
    fi

    print_info "启动 ${service} 容器..."

    # 构建启动参数，不映射宿主机端口，容器间经 Nacos 发现与 hcsy 网络直连，对外统一走 gateway 的 8080
    local run_args=(docker run -d --name "$container_name" --network "$NETWORK_NAME")
    local env_args=()
    local volume_args=()
    env_file="$(get_env_file_path "$service")"

    case $service in
        gozero)
            append_env env_args "SERVER_IP" "0.0.0.0"
            append_env env_args "NACOS_IP" "nacos"
            append_env env_args "DB_MYSQL_HOST" "mysql"
            append_env env_args "DB_ES_HOST" "es"
            append_env env_args "DB_MONGODB_HOST" "mongodb"
            append_env env_args "RABBITMQ_HOST" "mq"
            append_env env_args "LOGS_PATH" "/app/logs/gozero"
            ;;
        nestjs)
            append_env env_args "SERVER_IP" "0.0.0.0"
            append_env env_args "NACOS_SERVER" "nacos"
            append_env env_args "NACOS_PORT" "8848"
            append_env env_args "DB_HOST" "mysql"
            append_env env_args "DB_MONGODB_HOST" "mongodb"
            append_env env_args "RABBITMQ_HOST" "mq"
            append_env env_args "LOGS_PATH" "/app/logs/nestjs"
            ;;
        spring)
            append_env env_args "NACOS_SERVER" "nacos:8848"
            append_env env_args "DB_HOST" "mysql"
            append_env env_args "REDIS_HOST" "redis"
            append_env env_args "RABBITMQ_HOST" "mq"
            append_env env_args "LOGGING_PATH" "/app/logs/spring"
            ;;
        fastapi)
            append_env env_args "SERVER_IP" "0.0.0.0"
            append_env env_args "NACOS_SERVER" "nacos:8848"
            append_env env_args "RABBITMQ_HOST" "mq"
            append_env env_args "DB_MYSQL_HOST" "mysql"
            append_env env_args "DB_POSTGRES_HOST" "pgvector-db"
            append_env env_args "DB_MONGODB_HOST" "mongodb"
            append_env env_args "DB_REDIS_HOST" "redis"
            append_env env_args "DB_CLICKHOUSE_HOST" "clickhouse"
            append_env env_args "LOGS_PATH" "/app/logs/fastapi"
            ;;
    esac

    append_env_file env_args "$env_file"

    case $service in
        gozero|spring)
            # 这两个服务都有 application.yaml 配置
            if [ -f "$service_dir/application.yaml" ]; then
                volume_args+=( -v "$service_dir/application.yaml:/app/application.yaml" )
            fi
            ;;
        nestjs)
            # NestJS 配置已迁移到 src/config/application.yaml
            if [ -f "$service_dir/src/config/application.yaml" ]; then
                volume_args+=( -v "$service_dir/src/config/application.yaml:/app/dist/config/application.yaml" )
            fi
            ;;
        fastapi)
            # FastAPI 服务
            if [ -f "$service_dir/application.yaml" ]; then
                volume_args+=( -v "$service_dir/application.yaml:/app/application.yaml" )
            fi
            ;;
    esac

    # 挂载日志目录
    mkdir -p "$PROJECT_DIR/logs/$service"
    chmod -R a+rwX "$PROJECT_DIR/logs/$service"
    volume_args+=( -v "$PROJECT_DIR/logs/$service:/app/logs/$service" )

    # 挂载静态文件目录
    for dir in pic excel upload; do
        mkdir -p "$PROJECT_DIR/static/$dir"
        volume_args+=( -v "$PROJECT_DIR/static/$dir:/app/static/$dir" )
    done

    # 使用宿主机当前用户的 uid/gid 运行容器，避免挂载目录被 root 占用后，
    # 宿主机开发模式（./mix dev seq）写入日志时出现 Permission denied
    run_args+=( --user "$(id -u):$(id -g)" )

    # 排除代理，避免服务通过容器名访问中间件（nacos/mysql/redis 等）时被转发到宿主代理
    run_args+=( -e "NO_PROXY=$NO_PROXY_VALUE" -e "no_proxy=$NO_PROXY_VALUE" )

    # 创建并启动容器
    run_args+=( "${env_args[@]}" )
    run_args+=( "${volume_args[@]}" )
    run_args+=( --restart unless-stopped "$image_name" )
    "${run_args[@]}"

    if [ $? -eq 0 ]; then
        print_success "${service} 容器启动成功 (端口: $port, 容器: $container_name)"
    else
        print_error "${service} 容器启动失败"
        return 1
    fi
}

# 构建和运行服务
build_and_run() {
    local service=$1

    print_info "处理服务: $service"

    if [ "$service" = "gateway" ]; then
        print_info "通过 Docker Compose 启动 Apache APISIX 网关..."
        (cd "$PROJECT_DIR/gateway" && docker compose up -d)
        return
    fi

    if [ "$start_only" = true ]; then
        if ! run_container "$service"; then
            return 1
        fi
    else
        if ! build_image "$service"; then
            print_warning "跳过 ${service} 容器启动 (镜像构建失败)"
            return 1
        fi

        if ! run_container "$service"; then
            return 1
        fi
    fi
}

# 显示所有运行中的容器
show_status() {
    print_info "当前运行的容器状态:"
    echo ""
    docker ps | grep "mix-" || echo "未找到mix-的容器"
    echo ""
}

# 清理所有服务容器
cleanup_containers() {
    print_warning "清理所有 mix- 前缀的容器..."
    (cd "$PROJECT_DIR/gateway" && docker compose down) || true

    docker ps -a --format "table {{.Names}}" | grep "mix-" | while read container; do
        print_info "停止容器: $container"
        docker stop "$container" 2>/dev/null || true
        docker rm "$container" 2>/dev/null || true
    done

    print_success "清理完成"
}

# 显示帮助信息
show_help() {
    cat << EOF
微服务 Docker 构建和部署脚本

用法: $0 [OPTIONS] [SERVICE...]

选项:
  --build-only    仅构建镜像，不启动容器
  --start-only    仅启动已构建镜像，不重新构建
  --clean         清理所有容器
  --status        显示容器状态
  --help          显示此帮助信息

服务名称:
  gateway  - Apache APISIX 网关 (端口 8080)
  spring   - Spring Boot 微服务 (端口 8081)
  gozero   - GoZero 微服务 (端口 8082)
  nestjs   - NestJS 微服务 (端口 8083)
  fastapi  - FastAPI 微服务 (端口 8084)

示例:
  # 构建和启动所有服务
  $0

  # 构建和启动特定服务
  $0 spring fastapi

  # 仅构建镜像
  $0 --build-only spring

  # 显示容器状态
  $0 --status

  # 清理所有容器
  $0 --clean

EOF
}

# 主函数
main() {
    local build_only=false
    local services=()

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build-only)
                build_only=true
                shift
                ;;
            --start-only)
                start_only=true
                shift
                ;;
            --clean)
                cleanup_containers
                exit 0
                ;;
            --status)
                show_status
                exit 0
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                services+=("$1")
                shift
                ;;
        esac
    done

    # 如果没有指定服务，使用所有服务
    if [ ${#services[@]} -eq 0 ]; then
        services=(gozero nestjs spring gateway fastapi)
    fi

    print_info "开始处理服务: ${services[*]}"
    echo ""

    ensure_network
    echo ""

    local failed=0
    for service in "${services[@]}"; do
        if [ "$build_only" = true ]; then
            if ! build_image "$service"; then
                ((failed++))
            fi
        else
            if ! build_and_run "$service"; then
                ((failed++))
            fi
        fi
        echo ""
    done

    show_status

    if [ $failed -gt 0 ]; then
        print_warning "部分服务处理失败 ($failed 个)"
        exit 1
    else
        print_success "所有服务处理完成！"
        exit 0
    fi
}

# 执行主函数
main "$@"
