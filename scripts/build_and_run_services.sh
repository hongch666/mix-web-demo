#!/bin/bash

# 微服务 Docker 构建和容器部署脚本
# 用途：构建镜像并创建/启动容器（支持配置文件挂载）
# 用法：./build_and_run_services.sh [service1] [service2] ...

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES_CONFIG=(
    "gin:8081"
    "nestjs:8082"
    "spring:8083"
    "fastapi:8084"
)

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

# 声明关联数组存储服务信息
declare -A SERVICE_INFO=(
    [gin]="gin:8081"
    [nestjs]="nestjs:8082"
    [spring]="spring:8083"
    [fastapi]="fastapi:8084"
)

declare -A SERVICE_LANG=(
    [gin]="go"
    [nestjs]="node"
    [spring]="java"
    [fastapi]="python"
)

declare -A SERVICE_PORT=(
    [gin]="8081"
    [nestjs]="8082"
    [spring]="8083"
    [gateway]="9000"
    [fastapi]="8084"
)

# 获取服务列表
get_services() {
    if [ $# -eq 0 ]; then
        echo "gin nestjs spring fastapi"
    else
        echo "$@"
    fi
}

# 构建镜像
build_image() {
    local service=$1
    local service_dir="${PROJECT_DIR}/${service}"

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
    
    docker build -t "mix-${service}:latest" . 2>&1 | tail -20
    
    if [ $? -eq 0 ]; then
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

    # 检查镜像是否存在
    if ! docker image inspect "$image_name" > /dev/null 2>&1; then
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

    # 构建卷挂载参数
    local volume_args=""
    
    case $service in
        gin|nestjs|spring)
            # 这三个服务都有 application.yaml 和 .env 配置
            if [ -f "$service_dir/application.yaml" ]; then
                volume_args="$volume_args -v $service_dir/application.yaml:/app/application.yaml"
            fi
            if [ -f "$service_dir/.env" ]; then
                volume_args="$volume_args -v $service_dir/.env:/app/.env"
            fi
            ;;
        fastapi)
            # FastAPI 服务
            if [ -f "$service_dir/application.yaml" ]; then
                volume_args="$volume_args -v $service_dir/application.yaml:/app/application.yaml"
            fi
            if [ -f "$service_dir/.env" ]; then
                volume_args="$volume_args -v $service_dir/.env:/app/.env"
            fi
            ;;
    esac

    # 挂载日志目录
    mkdir -p "$PROJECT_DIR/logs/$service"
    volume_args="$volume_args -v $PROJECT_DIR/logs/$service:/app/logs/$service"

    # 挂载静态文件目录
    for dir in pic excel upload; do
        mkdir -p "$PROJECT_DIR/static/$dir"
        volume_args="$volume_args -v $PROJECT_DIR/static/$dir:/app/static/$dir"
    done

    # 创建并启动容器
    docker run -d \
        --name "$container_name" \
        -p "$port:$port" \
        $volume_args \
        --restart unless-stopped \
        "$image_name"

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
    
    if ! build_image "$service"; then
        print_warning "跳过 ${service} 容器启动 (镜像构建失败)"
        return 1
    fi
    
    if ! run_container "$service"; then
        return 1
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
  --clean         清理所有容器
  --status        显示容器状态
  --help          显示此帮助信息

服务名称:
  gin      - Gin Go 微服务 (端口 8081)
  nestjs   - NestJS 微服务 (端口 8082)
  spring   - Spring Boot 微服务 (端口 8083)
  gateway  - Spring Cloud Gateway (端口 9000)
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
        services=(gin nestjs spring gateway fastapi)
    fi

    print_info "开始处理服务: ${services[*]}"
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
