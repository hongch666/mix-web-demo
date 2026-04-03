#!/bin/bash

# 微服务 Docker 镜像推送脚本
# 用途：将已构建的项目镜像推送到远程镜像仓库
# 用法：./scripts/docker-push-images.sh --prefix <远程前缀> [--tag <tag>] [service1] [service2] ...

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_SERVICES=(gateway spring gozero nestjs fastapi)

IMAGE_PREFIX="${DOCKER_IMAGE_PREFIX:-}"
IMAGE_TAG="${DOCKER_IMAGE_TAG:-latest}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << 'EOF'
Docker 镜像推送脚本

用法: ./scripts/docker-push-images.sh --prefix <远程镜像前缀> [--tag <tag>] [service...]

参数:
  --prefix <前缀>   远程镜像前缀，例如 docker.io/username 或 registry.example.com/project
  --tag <tag>       推送到远程仓库时使用的 tag，默认 latest

说明:
  - 不传 service 时，默认推送 gateway spring gozero nestjs fastapi
  - 本地镜像默认读取 mix-<service>:latest
  - 远程镜像会被重新打标签为 <prefix>/mix-<service>:<tag>

示例:
  ./mix docker push --prefix docker.io/yourname
  ./mix docker push --prefix registry.example.com/team --tag v1.0.0 spring gozero
EOF
}

require_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker 未安装"
        exit 1
    fi

    if ! docker ps >/dev/null 2>&1; then
        log_error "Docker 守护进程未运行"
        exit 1
    fi
}

normalize_prefix() {
    local prefix=$1

    prefix="${prefix%/}"
    echo "$prefix"
}

push_service() {
    local service=$1
    local local_image="mix-${service}:latest"
    local remote_image="${IMAGE_PREFIX}/mix-${service}:${IMAGE_TAG}"

    if ! docker image inspect "$local_image" >/dev/null 2>&1; then
        log_error "本地镜像不存在: $local_image"
        return 1
    fi

    log_info "开始推送 ${service} 镜像: ${remote_image}"
    docker tag "$local_image" "$remote_image"
    docker push "$remote_image"
    log_success "${service} 镜像推送完成"
}

main() {
    local services=()

    while [ $# -gt 0 ]; do
        case $1 in
            --prefix|--registry|--repo-prefix)
                IMAGE_PREFIX="$2"
                shift 2
                ;;
            --tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --)
                shift
                break
                ;;
            *)
                services+=("$1")
                shift
                ;;
        esac
    done

    while [ $# -gt 0 ]; do
        services+=("$1")
        shift
    done

    if [ ${#services[@]} -eq 0 ]; then
        services=("${DEFAULT_SERVICES[@]}")
    fi

    if [ -z "$IMAGE_PREFIX" ]; then
        log_error "请通过 --prefix 或环境变量 DOCKER_IMAGE_PREFIX 指定远程镜像前缀"
        show_help
        exit 1
    fi

    IMAGE_PREFIX="$(normalize_prefix "$IMAGE_PREFIX")"

    if [ -z "$IMAGE_PREFIX" ]; then
        log_error "远程镜像前缀不能为空"
        exit 1
    fi

    cd "$PROJECT_DIR"
    require_docker

    log_info "准备推送镜像，远程前缀: ${IMAGE_PREFIX}，Tag: ${IMAGE_TAG}"

    for service in "${services[@]}"; do
        case $service in
            gateway|spring|gozero|nestjs|fastapi)
                push_service "$service"
                ;;
            *)
                log_warning "跳过未知服务: $service"
                ;;
        esac
    done

    log_success "镜像推送完成"
}

main "$@"
