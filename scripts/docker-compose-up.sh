#!/bin/bash

set -e

# docker-compose 方式启动整套服务
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$WORKDIR/docker-compose.yml"

# 查找可用的 compose 命令
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: docker-compose 或 Docker Compose CLI 未安装"
    exit 1
fi

cd "$WORKDIR"

# 确保与 docker-services.sh 使用同一网络
if ! docker network inspect hcsy >/dev/null 2>&1; then
    echo "Docker网络 hcsy 不存在，正在创建..."
    docker network create hcsy
fi

# 预创建日志目录，网关日志可能由 APISIX 用户创建，不能递归修改已有文件
for d in gateway spring gozero nestjs fastapi; do
    mkdir -p "$WORKDIR/logs/$d"
    chmod 777 "$WORKDIR/logs/$d" 2>/dev/null || \
        echo "警告：无法修改日志目录权限，将由容器初始化步骤处理: $WORKDIR/logs/$d"
done

# 预创建静态目录
for d in pic excel upload; do
    mkdir -p "$WORKDIR/static/$d"
    chmod -R 777 "$WORKDIR/static/$d"
done

app_services=(spring gozero nestjs fastapi)
missing_images=()

for service in "${app_services[@]}"; do
    if ! docker image inspect "mix-${service}:latest" >/dev/null 2>&1; then
        missing_images+=("$service")
    fi
done

if [ ${#missing_images[@]} -gt 0 ]; then
    echo "缺少应用镜像，使用 mix Docker 脚本构建: ${missing_images[*]}"
    bash "$WORKDIR/mix" docker build "${missing_images[@]}"
else
    echo "应用镜像已存在，跳过镜像构建"
fi

# 清理 dev 模式残留的网关容器，根 compose 与 gateway/docker-compose.yml 共用
# container_name: mix-gateway，不清理会因容器名冲突导致本次启动失败
bash "$WORKDIR/scripts/gateway-cleanup.sh"

# 清理 ./mix loki start 独立启动的观测栈容器，观测栈在本编排中
# 内联定义，loki-config/docker-compose.yml 是其独立启动版本，两者容器名相同但属于不同
# compose 项目，独立栈残留会因容器名冲突导致本次启动失败
bash "$WORKDIR/scripts/loki-control.sh" cleanup || true

echo "启动应用与可观测性服务，不含第三方依赖组件"

echo "请先通过 ./scripts/docker-services.sh 启动 MySQL/Redis/MongoDB/ES/Nacos/RabbitMQ/ClickHouse 等依赖"

$COMPOSE_CMD -f "$COMPOSE_FILE" up -d

echo "应用服务已启动，使用 $COMPOSE_CMD -f $COMPOSE_FILE ps 查看状态"
