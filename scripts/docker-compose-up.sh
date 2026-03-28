#!/bin/bash

set -e

# docker-compose 方式启动整套服务
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$WORKDIR/docker-compose.yml"

if ! command -v docker-compose >/dev/null 2>&1 && ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker-compose 或 Docker 未安装"
    exit 1
fi

cd "$WORKDIR"

# 确保与 docker-services.sh 使用同一网络
if ! docker network inspect hcsy >/dev/null 2>&1; then
    echo "Docker网络 hcsy 不存在，正在创建..."
    docker network create hcsy
fi

echo "启动应用服务（5个服务：gateway、spring、gozero、nestjs、fastapi），不含第三方依赖组件。"

echo "请先通过 ./scripts/docker-services.sh 启动 MySQL/Redis/MongoDB/ES/Nacos/RabbitMQ/ClickHouse 等依赖。"

docker-compose -f "$COMPOSE_FILE" up -d --build

echo "应用服务已启动。使用 docker-compose -f $COMPOSE_FILE ps 查看状态。"
