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

# 预创建日志目录并调整权限，避免 GoZero/NestJS 权限问题
for d in spring gozero nestjs fastapi; do
    mkdir -p "$WORKDIR/logs/$d"
    chmod -R 777 "$WORKDIR/logs/$d"
done

# 预创建静态目录
for d in pic excel upload; do
    mkdir -p "$WORKDIR/static/$d"
    chmod -R 777 "$WORKDIR/static/$d"
done

echo "启动应用服务（5个服务：gateway、spring、gozero、nestjs、fastapi），不含第三方依赖组件。"

echo "请先通过 ./scripts/docker-services.sh 启动 MySQL/Redis/MongoDB/ES/Nacos/RabbitMQ/ClickHouse 等依赖。"

$COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build

echo "应用服务已启动。使用 $COMPOSE_CMD -f $COMPOSE_FILE ps 查看状态。"
